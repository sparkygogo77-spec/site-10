package com.sparky.lanternring;

import com.sparky.lanternring.block.LightConstructBlock;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Brightness;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * DELUGE: aimed and dropped like the Anvil (hold right-click for the marker, let go to drop,
 * left-click while aiming for the level). A glowing hard-light globe full of liquid forms high
 * above the marker and falls; where it lands it bursts, knocking everything back, and a wave of
 * green hard-light liquid (ModFluids) races out over the ground. The liquid is water to the game
 * and to shader packs, so it swims, splashes and reflects like water. Then rings of real liquid
 * waves roll outward from the burst like a little tsunami, throwing spray and shoving mobs out of
 * the way (more waves, taller and harder at higher levels). After 15, 20 or 25 seconds (by level,
 * see RingTuning) it has all drained, the outer edge first, and whatever is left is swept away.
 */
public final class Deluges {
	/** The levels a left-click while aiming cycles through: how far the liquid spreads. */
	public static final int[] RADII = {7, 12, 17};
	/** The falling globe's radius in blocks, per level. */
	private static final int[] GLOBE = {2, 3, 4};
	/** How high above the marker the globe forms. */
	private static final int HEIGHT = 16;
	private static final double GRAVITY = 0.08;
	private static final double DRAG = 0.98;
	/** The burst's hit at its middle; it falls off to nothing at the splash's edge. */
	private static final float IMPACT_DAMAGE = 8f;
	/** However it goes, a globe that hasn't landed by now is gone. */
	private static final int MAX_FALL_TICKS = 200;
	/** How far above and below the burst the splash looks for the ground in each column. */
	private static final int REACH_UP = 6, REACH_DOWN = 10;
	/** Per level: how many waves roll out, the first one's height in blocks, and how hard they shove. */
	private static final int[] WAVES = {1, 2, 3};
	private static final int[] CREST = {2, 3, 4};
	private static final double[] WAVE_PUSH = {1.0, 1.5, 2.1};
	/** Blocks a wave front moves per tick, and ticks between one wave and the next. */
	private static final double WAVE_SPEED = 0.7;
	private static final int WAVE_GAP = 9;
	/** How far past the splash's edge the waves keep rolling (they shrink to nothing there). */
	private static final int WAVE_OVERRUN = 4;

	private static final class Aim {
		ServerLevel level;
		int lvl = 0;
		BlockPos mark;
		long lastTick;
	}

	private static final class Drop {
		final ServerLevel level;
		final Player owner;
		final int lvl;
		final int globe;
		final double x, z;
		double y;
		double speed;
		final long born;
		final List<Display.BlockDisplay> bodies = new ArrayList<>();
		final List<int[]> offsets = new ArrayList<>();
		/** Liquid sources still to pour, nearest the burst first; then the ones poured. */
		List<BlockPos> pour;
		int poured;
		int perTick;
		final Set<BlockPos> placed = new HashSet<>();
		long drainAt = Long.MAX_VALUE;
		/** Sources to take away, outer edge first. */
		List<BlockPos> drain;
		int drained;
		/** When the globe burst, and when every last drop must be gone. */
		long burstAt;
		long endAt = Long.MAX_VALUE;
		Vec3 center;
		/** The ground height in each column the waves cross, found before any liquid went down. */
		final Map<Long, Integer> ground = new HashMap<>();
		/** The liquid making up the waves' crests right now (not part of the pool). */
		final Set<BlockPos> crest = new HashSet<>();
		/** Who each wave has already shoved, so it shoves them once. */
		final List<Set<UUID>> shoved = new ArrayList<>();

		Drop(ServerLevel level, Player owner, int lvl, BlockPos mark) {
			this.level = level;
			this.owner = owner;
			this.lvl = lvl;
			this.globe = GLOBE[lvl];
			this.x = mark.getX();
			this.z = mark.getZ();
			this.born = level.getGameTime();
		}
	}

	private static final Map<UUID, Aim> AIMS = new HashMap<>();
	private static final List<Drop> DROPS = new ArrayList<>();
	private static final Map<UUID, Long> NO_CHARGE_NOTE = new HashMap<>();

	private Deluges() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(Deluges::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			for (Drop drop : DROPS) {
				discardBodies(drop);
				// Don't leave a lake behind in the saved world.
				finish(drop);
			}
			AIMS.clear();
			DROPS.clear();
			NO_CHARGE_NOTE.clear();
		});
	}

	public static boolean isLive(ServerLevel level, BlockPos pos) {
		for (Drop drop : DROPS) {
			if (drop.level == level && (drop.placed.contains(pos) || drop.crest.contains(pos))) return true;
		}
		return false;
	}

	// ---- levels ---------------------------------------------------------------------------

	/** 0, 1 or 2. */
	public static int level(ItemStack ring) {
		return Mth.clamp(ring.getOrDefault(ModComponents.DELUGE_LEVEL, 0), 0, RADII.length - 1);
	}

	/** Charge per drop: 1%, 2% or 3% of a full ring (PowerRingItem.MAX_CHARGE = 1000). */
	public static int cost(int level) {
		return 10 * (level + 1);
	}

	public static void cycleLevel(ServerPlayer player, ItemStack ring) {
		int next = (level(ring) + 1) % RADII.length;
		ring.set(ModComponents.DELUGE_LEVEL, next);
		player.sendOverlayMessage(levelText(next).copy().withStyle(ChatFormatting.GREEN));
		player.level().playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1f, 1.5f - 0.2f * next);
	}

	public static Component levelText(int level) {
		int across = RADII[level] * 2 + 1;
		return Component.translatable("message.lanternring.deluge_level", level + 1, across, String.valueOf(cost(level) / 10.0));
	}

	// ---- aiming ---------------------------------------------------------------------------

	/** Every tick right-click is held in Deluge mode (from PowerRingItem.onUseTick): moves the marker. */
	public static void aimTick(ServerPlayer player, ItemStack ring) {
		if (!AIMS.containsKey(player.getUUID())) {
			if (player.getCooldowns().isOnCooldown(ring)) return;
			if (!player.isCreative() && PowerRingItem.getCharge(ring) < cost(level(ring))) {
				long now = player.level().getGameTime();
				if (now - NO_CHARGE_NOTE.getOrDefault(player.getUUID(), Long.MIN_VALUE / 2) > 20) {
					NO_CHARGE_NOTE.put(player.getUUID(), now);
					player.sendOverlayMessage(Component.translatable("message.lanternring.no_charge").withStyle(ChatFormatting.RED));
					player.level().playSound(null, player.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.6f, 1.4f);
				}
				return;
			}
		}
		ServerLevel level = player.level();
		Aim aim = AIMS.computeIfAbsent(player.getUUID(), id -> new Aim());
		aim.level = level;
		aim.lvl = level(ring);
		aim.lastTick = level.getGameTime();
		aim.mark = Anvils.findMark(level, player);
		if (aim.mark != null && level.getGameTime() % 2 == 0) {
			Vec3 at = new Vec3(aim.mark.getX() + 0.5, aim.mark.getY(), aim.mark.getZ() + 0.5);
			// How far "to" is from "from" tells the client the splash's radius.
			RingFx.send(level, Kind.DELUGE_MARK, at, at.add(RADII[aim.lvl], 0, 0));
		}
	}

	/** Right-click let go: drops the globe over the marker, and pays for it. */
	public static void release(ServerPlayer player, ItemStack ring) {
		Aim aim = AIMS.remove(player.getUUID());
		if (aim == null || aim.mark == null || aim.level != player.level()) return;
		int cost = cost(aim.lvl);
		if (!player.isCreative()) {
			if (PowerRingItem.getCharge(ring) < cost) return;
			PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - cost);
		}
		drop(aim.level, player, aim.mark, aim.lvl);
		player.getCooldowns().addCooldown(ring, RingTuning.cooldownTicks(RingMode.DELUGE));
		player.sendOverlayMessage(PowerRingItem.chargeText(ring));
	}

	public static void cancel(Player player) {
		AIMS.remove(player.getUUID());
	}

	// ---- the globe ------------------------------------------------------------------------

	private static void drop(ServerLevel level, Player owner, BlockPos mark, int lvl) {
		Drop drop = new Drop(level, owner, lvl, mark);
		int r = drop.globe;
		// Build it as high as it fits under a ceiling, but never below the marker.
		int top = mark.getY() + HEIGHT;
		while (top > mark.getY() + r + 1 && !clear(level, mark.atY(top), r)) top--;
		drop.y = top;
		// A hollow ball of glowing glass: the shell is all that shows, so leave the inside out.
		for (int dx = -r; dx <= r; dx++) {
			for (int dy = -r; dy <= r; dy++) {
				for (int dz = -r; dz <= r; dz++) {
					double d = Math.sqrt(dx * dx + dy * dy + dz * dz);
					if (d <= r + 0.5 && d > r - 1.2) drop.offsets.add(new int[] {dx, dy, dz});
				}
			}
		}
		BlockState glass = ModRegistry.LIGHT_CONSTRUCT.defaultBlockState()
				.setValue(LightConstructBlock.HELD, true).setValue(LightConstructBlock.RIM, true);
		for (int[] o : drop.offsets) {
			Display.BlockDisplay body = EntityTypes.BLOCK_DISPLAY.create(level, EntitySpawnReason.TRIGGERED);
			if (body == null) continue;
			body.setBlockState(glass);
			body.setBrightnessOverride(Brightness.FULL_BRIGHT);
			body.setPosRotInterpolationDuration(1);
			body.setPos(drop.x + o[0], drop.y + o[1], drop.z + o[2]);
			level.addFreshEntity(body);
			drop.bodies.add(body);
		}
		DROPS.add(drop);
		RingFx.send(level, Kind.CONSTRUCT, RingPowers.handPos(owner), new Vec3(drop.x + 0.5, drop.y + 0.5, drop.z + 0.5));
		level.playSound(null, mark.atY(top), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 2.0f, 0.6f);
		level.playSound(null, mark.atY(top), SoundEvents.BUBBLE_COLUMN_UPWARDS_AMBIENT, SoundSource.PLAYERS, 2.0f, 0.8f);
	}

	/** Room for a ball of radius r around center. */
	private static boolean clear(ServerLevel level, BlockPos center, int r) {
		for (BlockPos pos : BlockPos.betweenClosed(center.offset(-r, -r, -r), center.offset(r, r, r))) {
			if (!passable(level.getBlockState(pos))) return false;
		}
		return true;
	}

	private static boolean passable(BlockState state) {
		return state.isAir() || state.is(ModRegistry.BLAST_GLOW) || state.is(ModRegistry.BEAM_GLOW)
				|| state.canBeReplaced() && state.getFluidState().isEmpty();
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Map.Entry<UUID, Aim>> it = AIMS.entrySet().iterator(); it.hasNext(); ) {
			Aim aim = it.next().getValue();
			if (aim.level == null || aim.level.getGameTime() - aim.lastTick > 5) it.remove();
		}
		for (Iterator<Drop> it = DROPS.iterator(); it.hasNext(); ) {
			Drop drop = it.next();
			if (tick(drop)) continue;
			discardBodies(drop);
			finish(drop);
			it.remove();
		}
	}

	/** @return false once the Deluge is over */
	private static boolean tick(Drop drop) {
		ServerLevel level = drop.level;
		long now = level.getGameTime();
		if (drop.pour == null) {
			if (now - drop.born > MAX_FALL_TICKS) return false;
			fall(drop);
			return true;
		}
		pour(drop);
		waves(drop);
		if (now >= drop.endAt) return false;
		if (now >= drop.drainAt) drain(drop);
		return true;
	}

	private static void fall(Drop drop) {
		drop.speed = (drop.speed + GRAVITY) * DRAG;
		double target = drop.y - drop.speed;
		// Step down a block at a time so it can't skip through a thin floor.
		while (drop.y > target) {
			double next = Math.max(target, drop.y - 1);
			if (!clearBelow(drop, next)) {
				burst(drop);
				return;
			}
			drop.y = next;
		}
		for (int i = 0; i < drop.bodies.size(); i++) {
			int[] o = drop.offsets.get(i);
			drop.bodies.get(i).setPos(drop.x + o[0], drop.y + o[1], drop.z + o[2]);
		}
		// Green drips shaken off as it falls.
		if (drop.level.getGameTime() % 2 == 0) {
			drop.level.sendParticles(ModParticles.DRIP, drop.x + 0.5, drop.y + 0.5, drop.z + 0.5,
					4 + drop.globe * 2, drop.globe * 0.6, drop.globe * 0.6, drop.globe * 0.6, 0.02);
		}
	}

	/** Whether the ball's lower half fits with its middle block at height y. */
	private static boolean clearBelow(Drop drop, double y) {
		int r = drop.globe;
		int base = Mth.floor(y);
		if (base - r <= drop.level.getMinY()) return false;
		for (int dx = -r + 1; dx <= r - 1; dx++) {
			for (int dz = -r + 1; dz <= r - 1; dz++) {
				int depth = (int) Math.floor(Math.sqrt(Math.max(0, r * r - dx * dx - dz * dz)));
				BlockPos pos = BlockPos.containing(drop.x + dx, base - depth, drop.z + dz);
				if (!passable(drop.level.getBlockState(pos))) return false;
			}
		}
		return true;
	}

	/** The globe hits the ground: it bursts, knocks everything back, and the liquid races outward. */
	private static void burst(Drop drop) {
		ServerLevel level = drop.level;
		discardBodies(drop);
		int radius = RADII[drop.lvl];
		Vec3 center = new Vec3(drop.x + 0.5, Math.floor(drop.y) - drop.globe, drop.z + 0.5);
		BlockPos c = BlockPos.containing(center);

		// The splash's edge wobbles a little so it isn't a perfect circle.
		double[] edge = new double[16];
		for (int i = 0; i < edge.length; i++) edge[i] = radius * (0.85 + 0.2 * level.getRandom().nextDouble());
		List<BlockPos> pour = new ArrayList<>();
		for (int dx = -radius - 2; dx <= radius + 2; dx++) {
			for (int dz = -radius - 2; dz <= radius + 2; dz++) {
				double dist = Math.sqrt(dx * dx + dz * dz);
				double angle = (Math.atan2(dz, dx) / (Math.PI * 2) + 1) * edge.length;
				int i0 = (int) Math.floor(angle) % edge.length;
				double t = angle - Math.floor(angle);
				double reach = Mth.lerp(t, edge[i0], edge[(i0 + 1) % edge.length]);
				if (dist > reach) continue;
				BlockPos surface = surface(level, c.offset(dx, 0, dz));
				if (surface == null) continue;
				pour.add(surface);
				// The middle of the splash is deeper.
				if (dist < reach * 0.4 && passable(level.getBlockState(surface.above()))) pour.add(surface.above());
			}
		}
		pour.sort(Comparator.comparingDouble(p -> sq(p.getX() + 0.5 - center.x) + sq(p.getZ() + 0.5 - center.z) + p.getY() * 0.01));
		drop.pour = pour;
		int spreadTicks = Math.max(1, RingTuning.DELUGE_SPREAD.ticks());
		drop.perTick = Math.max(1, (int) Math.ceil(pour.size() / (double) spreadTicks));
		drop.burstAt = level.getGameTime();
		drop.center = center;
		drop.endAt = drop.burstAt + Math.max(spreadTicks + 20, RingTuning.delugeLifetime(drop.lvl).ticks());
		// Drain so it's all gone half a second before the end; the end sweeps up any stragglers.
		drop.drainAt = Math.max(drop.burstAt + spreadTicks, drop.endAt - 10 - Math.max(1, RingTuning.DELUGE_DRAIN.ticks()));
		int waveReach = radius + WAVE_OVERRUN;
		for (int dx = -waveReach; dx <= waveReach; dx++) {
			for (int dz = -waveReach; dz <= waveReach; dz++) {
				if (dx * dx + dz * dz > (waveReach + 1) * (waveReach + 1)) continue;
				BlockPos surface = surface(level, c.offset(dx, 0, dz));
				if (surface != null) drop.ground.put(column(dx, dz), surface.getY());
			}
		}
		for (int i = 0; i < WAVES[drop.lvl]; i++) drop.shoved.add(new HashSet<>());

		double reachHit = radius + 2;
		for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, new AABB(center, center).inflate(reachHit),
				e -> e != drop.owner && e.isAlive() && !e.isSpectator())) {
			Vec3 away = target.position().subtract(center);
			double d = away.length();
			if (d > reachHit) continue;
			away = away.multiply(1, 0, 1);
			away = away.lengthSqr() < 1.0e-4 ? new Vec3(1, 0, 0) : away.normalize();
			float falloff = (float) (1 - d / reachHit);
			target.hurtServer(level, level.damageSources().indirectMagic(drop.owner, drop.owner), IMPACT_DAMAGE * (1 + drop.lvl * 0.9f) * falloff);
			double hit = 1.6 + drop.lvl * 0.8;
			target.setDeltaMovement(away.x * hit * falloff, 0.45 + (0.5 + drop.lvl * 0.25) * falloff, away.z * hit * falloff);
			RingPowers.syncVelocity(target);
		}

		RingFx.send(level, Kind.DELUGE_SPLASH, center, center.add(radius, 0, 0), 0f, drop.globe);
		// A geyser of real water thrown straight up, and spray everywhere.
		level.sendParticles(ParticleTypes.SPLASH, center.x, center.y + 1, center.z, 200 * (drop.lvl + 1), radius * 0.4, 0.6, radius * 0.4, 0.6);
		for (int i = 0; i < 6 + drop.lvl * 4; i++) {
			level.sendParticles(ParticleTypes.SPLASH, center.x, center.y + 1 + i * 0.8, center.z, 40, drop.globe * 0.5, 0.4, drop.globe * 0.5, 0.5);
			level.sendParticles(ModParticles.DRIP, center.x, center.y + 1 + i * 0.8, center.z, 8 + drop.lvl * 4, drop.globe * 0.5, 0.4, drop.globe * 0.5, 0.25);
		}
		level.sendParticles(ParticleTypes.BUBBLE_POP, center.x, center.y + 1, center.z, 80 * (drop.lvl + 1), radius * 0.5, 0.4, radius * 0.5, 0.1);
		level.sendParticles(ParticleTypes.CLOUD, center.x, center.y + 1, center.z, 20 * (drop.lvl + 1), drop.globe, 0.5, drop.globe, 0.12);
		level.playSound(null, center.x, center.y, center.z, SoundEvents.PLAYER_SPLASH_HIGH_SPEED, SoundSource.PLAYERS, 4.0f, 0.5f);
		level.playSound(null, center.x, center.y, center.z, SoundEvents.GENERIC_SPLASH, SoundSource.PLAYERS, 4.0f, 0.6f);
		level.playSound(null, center.x, center.y, center.z, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.PLAYERS, 3.0f, 0.5f);
		level.playSound(null, center.x, center.y, center.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 1.5f + drop.lvl, 1.2f - 0.15f * drop.lvl);
		if (drop.lvl > 0) level.playSound(null, center.x, center.y, center.z, SoundEvents.TRIDENT_THUNDER.value(), SoundSource.PLAYERS, 1.0f + drop.lvl, 1.3f);
	}

	private static long column(int dx, int dz) {
		return ((long) dx << 32) ^ (dz & 0xffffffffL);
	}

	/**
	 * The tsunami: each wave is a ring of liquid a few blocks tall rolling outward from the burst.
	 * Its crest is real liquid put down at the front and taken away behind it, so it reads (and
	 * swims) like a wall of water; it throws spray off its top and shoves whatever it reaches.
	 */
	private static void waves(Drop drop) {
		ServerLevel level = drop.level;
		long age = level.getGameTime() - drop.burstAt;
		int radius = RADII[drop.lvl];
		double reach = radius + WAVE_OVERRUN;
		Set<BlockPos> next = new HashSet<>();
		boolean any = false;
		for (int w = 0; w < WAVES[drop.lvl]; w++) {
			double front = (age - w * WAVE_GAP) * WAVE_SPEED + 1.5;
			if (front < 1.5 || front > reach) continue;
			any = true;
			// Tallest near the burst, sinking to nothing at the far edge; each later wave is smaller.
			double fade = 1 - front / reach;
			int height = (int) Math.round((CREST[drop.lvl] - w * 0.8) * (0.35 + 0.65 * fade));
			int band = (int) Math.ceil(front) + 1;
			for (int dx = -band; dx <= band; dx++) {
				for (int dz = -band; dz <= band; dz++) {
					double d = Math.sqrt(dx * dx + dz * dz);
					if (d < front - 1.2 || d > front + 0.5) continue;
					Integer g = drop.ground.get(column(dx, dz));
					if (g == null) continue;
					// The back of the wave is a block lower than its front.
					int h = d < front - 0.6 ? height - 1 : height;
					for (int k = 0; k <= h; k++) next.add(new BlockPos(Mth.floor(drop.x) + dx, g + k, Mth.floor(drop.z) + dz));
				}
			}
			spray(drop, front, height, w);
			shove(drop, front, height, w, fade);
			if (age == w * WAVE_GAP) {
				level.playSound(null, drop.center.x, drop.center.y, drop.center.z, SoundEvents.PLAYER_SPLASH_HIGH_SPEED, SoundSource.PLAYERS, 3.0f, 0.4f + 0.1f * w);
			}
		}
		BlockState liquid = ModFluids.BLOCK.defaultBlockState();
		for (BlockPos pos : drop.crest) {
			if (!next.contains(pos) && !drop.placed.contains(pos)) removeIfOurs(level, pos);
		}
		drop.crest.clear();
		if (!any) return;
		for (BlockPos pos : next) {
			if (drop.placed.contains(pos)) continue;
			BlockState there = level.getBlockState(pos);
			if (there.is(ModFluids.BLOCK)) {
				if (!there.getFluidState().isSource()) level.setBlock(pos, liquid, 3);
			} else {
				if (!passable(there) || there.hasBlockEntity() || !level.mayInteract(drop.owner, pos)) continue;
				level.setBlock(pos, liquid, 3);
			}
			drop.crest.add(pos);
		}
	}

	/** Spray thrown up and forward off a wave's crest, all the way round. */
	private static void spray(Drop drop, double front, int height, int wave) {
		ServerLevel level = drop.level;
		int points = (int) (front * 2.2);
		double y0 = drop.center.y + height + 0.8;
		for (int i = 0; i < points; i++) {
			if (level.getRandom().nextInt(3) != 0) continue;
			double a = level.getRandom().nextDouble() * Math.PI * 2;
			double px = drop.center.x + Math.cos(a) * front, pz = drop.center.z + Math.sin(a) * front;
			Integer g = drop.ground.get(column(Mth.floor(px) - Mth.floor(drop.x), Mth.floor(pz) - Mth.floor(drop.z)));
			double y = g == null ? y0 : g + height + 0.9;
			level.sendParticles(ParticleTypes.SPLASH, px, y, pz, 10, 0.5, 0.3, 0.5, 0.35);
			level.sendParticles(ParticleTypes.BUBBLE_POP, px, y - 0.3, pz, 2, 0.4, 0.2, 0.4, 0.05);
			if (level.getRandom().nextInt(3) == 0) {
				// Green drops flung up and outward.
				level.sendParticles(ModParticles.DRIP, px, y, pz, 0, Math.cos(a) * 0.35, 0.35 + 0.1 * (drop.lvl - wave), Math.sin(a) * 0.35, 1);
			}
		}
		if (level.getRandom().nextInt(4) == 0) {
			double a = level.getRandom().nextDouble() * Math.PI * 2;
			level.playSound(null, drop.center.x + Math.cos(a) * front, drop.center.y, drop.center.z + Math.sin(a) * front,
					SoundEvents.GENERIC_SPLASH, SoundSource.PLAYERS, 1.5f, 0.6f + level.getRandom().nextFloat() * 0.4f);
		}
	}

	/** A wave reaching a mob (or player) shoves it outward and up, and stings a little. */
	private static void shove(Drop drop, double front, int height, int wave, double fade) {
		ServerLevel level = drop.level;
		Vec3 c = drop.center;
		AABB box = new AABB(c, c).inflate(front + 1.5, 0, front + 1.5).expandTowards(0, height + 3, 0).move(0, -2, 0);
		Set<UUID> done = drop.shoved.get(wave);
		for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, box,
				e -> e != drop.owner && e.isAlive() && !e.isSpectator())) {
			if (done.contains(target.getUUID())) continue;
			Vec3 away = target.position().subtract(c).multiply(1, 0, 1);
			double d = away.length();
			if (d < front - 1.5 || d > front + 1.5) continue;
			done.add(target.getUUID());
			away = d < 1.0e-2 ? new Vec3(1, 0, 0) : away.scale(1 / d);
			double push = WAVE_PUSH[drop.lvl] * (0.4 + 0.6 * fade) * (1 - wave * 0.2);
			target.hurtServer(level, level.damageSources().indirectMagic(drop.owner, drop.owner), (2f + 2f * drop.lvl) * (float) fade);
			Vec3 v = target.getDeltaMovement();
			target.setDeltaMovement(v.x * 0.3 + away.x * push, Math.max(v.y, 0.3 + 0.15 * drop.lvl), v.z * 0.3 + away.z * push);
			RingPowers.syncVelocity(target);
		}
	}

	/** In the column through pos: the lowest open block resting on the ground, near the burst's height. */
	private static BlockPos surface(ServerLevel level, BlockPos pos) {
		BlockPos at = pos.above(REACH_UP);
		boolean openAbove = false;
		for (int i = 0; i < REACH_UP + REACH_DOWN; i++, at = at.below()) {
			BlockState state = level.getBlockState(at);
			if (passable(state)) {
				openAbove = true;
				continue;
			}
			// Hit something: the block above it is the surface, if that was open.
			if (!openAbove) return null;
			// Don't pour on top of water or into a block's space that holds liquid already.
			if (!state.getFluidState().isEmpty()) return null;
			return at.above();
		}
		return null;
	}

	private static double sq(double v) {
		return v * v;
	}

	/** Puts the next ring of liquid down, so the wave spreads outward from the burst. */
	private static void pour(Drop drop) {
		if (drop.poured >= drop.pour.size()) return;
		ServerLevel level = drop.level;
		BlockState liquid = ModFluids.BLOCK.defaultBlockState();
		int end = Math.min(drop.pour.size(), drop.poured + drop.perTick);
		for (; drop.poured < end; drop.poured++) {
			BlockPos pos = drop.pour.get(drop.poured);
			BlockState there = level.getBlockState(pos);
			if (!passable(there) && !there.is(ModFluids.BLOCK)) continue;
			if (there.hasBlockEntity() || !level.mayInteract(drop.owner, pos)) continue;
			level.setBlock(pos, liquid, 3);
			drop.placed.add(pos.immutable());
			if (level.getRandom().nextInt(10) == 0) {
				level.sendParticles(ParticleTypes.SPLASH, pos.getX() + 0.5, pos.getY() + 1, pos.getZ() + 0.5, 6, 0.4, 0.1, 0.4, 0.2);
			}
		}
	}

	/** Takes the sources away a few at a time, outer edge first; what flowed off them dries up after. */
	private static boolean drain(Drop drop) {
		ServerLevel level = drop.level;
		if (drop.drain == null) {
			drop.drain = new ArrayList<>(drop.placed);
			Vec3 c = new Vec3(drop.x + 0.5, 0, drop.z + 0.5);
			drop.drain.sort(Comparator.comparingDouble(p -> -(sq(p.getX() + 0.5 - c.x) + sq(p.getZ() + 0.5 - c.z)) - p.getY() * 0.01));
			level.playSound(null, BlockPos.containing(c.x, drop.y, c.z), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1.5f, 0.7f);
		}
		int perTick = Math.max(1, (int) Math.ceil(drop.drain.size() / (double) Math.max(1, RingTuning.DELUGE_DRAIN.ticks())));
		int end = Math.min(drop.drain.size(), drop.drained + perTick);
		for (; drop.drained < end; drop.drained++) {
			BlockPos pos = drop.drain.get(drop.drained);
			drop.placed.remove(pos);
			removeIfOurs(level, pos);
			if (level.getRandom().nextInt(12) == 0) {
				level.sendParticles(ModParticles.MOTE, pos.getX() + 0.5, pos.getY() + 0.6, pos.getZ() + 0.5, 1, 0.3, 0.1, 0.3, 0.02);
			}
		}
		return drop.drained < drop.drain.size();
	}

	/** The end: every source and every flowing bit of this Deluge's liquid goes, wherever it ran. */
	private static void finish(Drop drop) {
		ServerLevel level = drop.level;
		for (BlockPos pos : drop.placed) removeIfOurs(level, pos);
		for (BlockPos pos : drop.crest) removeIfOurs(level, pos);
		drop.placed.clear();
		drop.crest.clear();
		if (drop.center == null) return;
		// The liquid runs about 3 blocks past whatever fed it, and down slopes; sweep a bit wider.
		int r = RADII[drop.lvl] + WAVE_OVERRUN + 6;
		BlockPos c = BlockPos.containing(drop.center);
		for (BlockPos pos : BlockPos.betweenClosed(c.offset(-r, -REACH_DOWN - 6, -r), c.offset(r, REACH_UP + CREST[drop.lvl] + 2, r))) {
			BlockState state = level.getBlockState(pos);
			if (state.is(ModFluids.BLOCK) && !isLive(level, pos)) level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
		}
	}

	private static void discardBodies(Drop drop) {
		for (Display.BlockDisplay body : drop.bodies) body.discard();
		drop.bodies.clear();
	}

	private static void removeIfOurs(ServerLevel level, BlockPos pos) {
		if (level.getBlockState(pos).is(ModFluids.BLOCK)) level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
	}
}
