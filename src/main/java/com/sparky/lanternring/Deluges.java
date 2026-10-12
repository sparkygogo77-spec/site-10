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
import net.minecraft.core.particles.DustParticleOptions;
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
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LiquidBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * DELUGE: aimed and dropped like the Anvil (hold right-click for the marker, let go to drop,
 * left-click while aiming for the level). A glowing hard-light ball of liquid forms high above the
 * marker the moment you let go, and the bearer's ring glows as it makes it. The ball's bottom
 * half crashes straight down while the top half dissolves from its top surface down in a
 * quick spray, so nothing is left floating. The burst: a geyser of green liquid shoots up, a hit
 * and a shove for everything nearby, and a flood of hard-light liquid (ModFluids) races out over
 * the ground. Then rings of waves roll out from the middle like a little tsunami, tall crests of
 * liquid that sweep mobs along. Bigger levels spread further, hit harder, and send more and taller
 * waves. The liquid is water to the game and to shader packs, so it swims, splashes and reflects
 * like water. It lasts 15, 20 or 25 seconds by level, then drains from the edge in, and a last
 * sweep takes up every drop of it that ran off, so nothing is left behind.
 */
public final class Deluges {
	/** The levels a left-click while aiming cycles through: how far the liquid spreads. */
	public static final int[] RADII = {7, 13, 20};
	/** The falling globe's radius in blocks, per level. */
	private static final int[] GLOBE = {2, 3, 5};
	/** How many waves roll out after the burst, per level. */
	private static final int[] WAVES = {2, 3, 4};
	/** How many blocks tall a wave's crest is as it leaves the middle (it shrinks as it goes). */
	private static final int[] CREST = {2, 3, 4};
	/** How fast the waves roll out, blocks per tick. */
	private static final double[] WAVE_SPEED = {0.45, 0.55, 0.65};
	/** Ticks between one wave and the next. */
	private static final int WAVE_GAP = 9;
	/** The red Deluge's heavy waves roll out much slower than the green ones, further apart. */
	private static final double[] RED_WAVE_SPEED = {0.2, 0.24, 0.28};
	private static final int RED_WAVE_GAP = 16;

	private static double waveSpeed(Drop drop) {
		return drop.lava() ? RED_WAVE_SPEED[drop.lvl] : WAVE_SPEED[drop.lvl];
	}
	/** How tall the geyser at the middle shoots up. */
	private static final int[] GEYSER = {5, 8, 12};
	/** The burst's hit at its middle; it falls off to nothing past the splash's edge. */
	private static final float[] IMPACT_DAMAGE = {8f, 14f, 22f};
	/** How hard the burst and the waves shove. */
	private static final double[] SHOVE = {1.5, 2.2, 3.0};
	/** Each wave's hit on whatever it sweeps up. */
	private static final float[] WAVE_DAMAGE = {2f, 4f, 7f};
	/** How high above the marker the ball forms (plus its radius). */
	private static final int HEIGHT = 16;
	/** Ticks the whole ball hangs before its bottom tears away. */
	private static final int FORM_TICKS = 3;
	/** The torn-off bottom is thrown down, not dropped: its starting speed and how fast it gains more, blocks per tick. */
	private static final double TEAR_SPEED = 0.9, TEAR_GRAVITY = 0.25;
	/** However it goes, a globe that hasn't landed by now is gone. */
	private static final int MAX_FALL_TICKS = 200;
	/** How far above and below the burst the splash looks for the ground in each column. */
	private static final int REACH_UP = 6, REACH_DOWN = 10;
	/** The red Deluge's spray: fine drops of blood-red water. */
	private static final DustParticleOptions BLOOD = new DustParticleOptions(0xA00A12, 0.7f);
	/** How far past the pool's edge the waves still break onto the land. */
	private static final int WAVE_OVERRUN = 4;

	/** How far past the pool's edge this Deluge's waves break: the red one throws its liquid much further. */
	private static int overrun(Drop drop) {
		return drop.lava() ? WAVE_OVERRUN + 3 + 2 * drop.lvl : WAVE_OVERRUN;
	}

	private static final class Aim {
		ServerLevel level;
		int lvl = 0;
		BlockPos mark;
		long lastTick;
	}

	private static final class Wave {
		final long start;
		final Set<Integer> hit = new HashSet<>();

		Wave(long start) {
			this.start = start;
		}
	}

	private static final class Drop {
		final ServerLevel level;
		final Player owner;
		final int lvl;
		final int globe;
		final double x, z;
		/** The middle of the ball's falling bottom half. */
		double y;
		double speed;
		final long born;
		/** The ball's middle, where it hangs: its top half stays held here until it runs down. */
		double hang;
		final List<Display.BlockDisplay> top = new ArrayList<>(), bottom = new ArrayList<>();
		final List<int[]> topOffsets = new ArrayList<>(), bottomOffsets = new ArrayList<>();
		/** When the bottom tears away: the top then dissolves, from its top surface down. */
		long goneFrom = Long.MAX_VALUE;
		Vec3 center;
		/** The ground under each column the flood and its waves reach, by BlockPos.asLong(x, 0, z). */
		final Map<Long, BlockPos> ground = new HashMap<>();
		/** Liquid sources still to pour, nearest the burst first; then the ones poured. */
		List<BlockPos> pour;
		int poured;
		int perTick;
		/** The flood's sources in the world. */
		final Set<BlockPos> placed = new HashSet<>();
		/** The waves' crests this tick, and the geyser: liquid that comes and goes. */
		final Set<BlockPos> crest = new HashSet<>();
		final List<BlockPos> geyser = new ArrayList<>();
		long burstAt;
		final List<Wave> waves = new ArrayList<>();
		long drainAt = Long.MAX_VALUE;
		long endAt = Long.MAX_VALUE;
		/** Sources to take away, outer edge first. */
		List<BlockPos> drain;
		int drained;
		int minY = Integer.MAX_VALUE, maxY = Integer.MIN_VALUE;
		/** Whose Deluge it is: green hard light, or the Red Lantern's burning ember liquid. */
		final Corps corps;
		final Block liquid;
		/** Red only: the ground the liquid has melted into. */
		final Set<BlockPos> sunk = new HashSet<>();
		/** How many layers of ground the red liquid has melted so far (it melts two). */
		int melted;
		/** Called back into the ring: every block of its liquid, furthest from the bearer first, and how many are gone. */
		List<BlockPos> recall;
		int recalled;
		long recallEnd;

		Drop(ServerLevel level, Player owner, int lvl, BlockPos mark) {
			this.corps = Corps.current();
			this.liquid = corps == Corps.RED ? ModFluids.EMBER_BLOCK : ModFluids.BLOCK;
			this.level = level;
			this.owner = owner;
			this.lvl = lvl;
			this.globe = GLOBE[lvl];
			this.x = mark.getX();
			this.z = mark.getZ();
			this.born = level.getGameTime();
		}

		boolean holds(BlockPos pos) {
			return placed.contains(pos) || crest.contains(pos) || geyser.contains(pos) || sunk.contains(pos);
		}

		boolean lava() {
			return corps == Corps.RED;
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
				sweep(drop);
			}
			AIMS.clear();
			DROPS.clear();
			NO_CHARGE_NOTE.clear();
		});
	}

	public static boolean isLive(ServerLevel level, BlockPos pos) {
		for (Drop drop : DROPS) {
			if (drop.level == level && drop.holds(pos)) return true;
		}
		return false;
	}

	/** Whether a Deluge is going on near pos (its liquid may be flowing there). */
	public static boolean isNear(ServerLevel level, BlockPos pos) {
		for (Drop drop : DROPS) {
			if (drop.level != level || drop.center == null) continue;
			double r = RADII[drop.lvl] + overrun(drop) + 16;
			if (sq(pos.getX() + 0.5 - drop.center.x) + sq(pos.getZ() + 0.5 - drop.center.z) < r * r) return true;
		}
		return false;
	}

	/** How long a Deluge's liquid lasts from the burst: the Durations value at level 1, 5 s more per level. */
	public static int lifetimeTicks(int level) {
		return RingTuning.DELUGE_LIFETIME.ticks() + level * 100;
	}

	// ---- levels ---------------------------------------------------------------------------

	/** 0, 1 or 2. */
	public static int level(ItemStack ring) {
		return Mth.clamp(ring.getOrDefault(ModComponents.DELUGE_LEVEL, 0), 0, RADII.length - 1);
	}

	/** Charge per drop: 1%, 2.5% or 4% of a full ring (PowerRingItem.MAX_CHARGE = 1000). */
	public static int cost(int level) {
		return 10 + 15 * level;
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
			RingFx.send(level, Kind.DELUGE_MARK, at, at.add(RADII[aim.lvl], 0, 0), 0f, 0, player);
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
		int top = mark.getY() + HEIGHT + r;
		while (top > mark.getY() + r + 1 && !clear(level, mark.atY(top), r)) top--;
		drop.y = drop.hang = top;
		// A hollow ball of glowing glass in two halves, each closed off flat where they tear apart.
		for (int dx = -r; dx <= r; dx++) {
			for (int dy = -r; dy <= r; dy++) {
				for (int dz = -r; dz <= r; dz++) {
					double d = Math.sqrt(dx * dx + dy * dy + dz * dz);
					if (d > r + 0.5) continue;
					boolean shell = d > r - 1.2;
					if (dy >= 0 && (shell || dy == 0)) drop.topOffsets.add(new int[] {dx, dy, dz});
					if (dy < 0 && (shell || dy == -1)) drop.bottomOffsets.add(new int[] {dx, dy, dz});
				}
			}
		}
		BlockState glass = Corps.state(ModRegistry.LIGHT_CONSTRUCT)
				.setValue(LightConstructBlock.HELD, true).setValue(LightConstructBlock.RIM, true);
		for (int[] o : drop.topOffsets) addBody(drop, drop.top, glass, drop.x + o[0], drop.y + o[1], drop.z + o[2]);
		for (int[] o : drop.bottomOffsets) addBody(drop, drop.bottom, glass, drop.x + o[0], drop.y + o[1], drop.z + o[2]);
		drop.goneFrom = level.getGameTime() + FORM_TICKS;
		DROPS.add(drop);
		RingFx.send(level, Kind.CONSTRUCT, RingPowers.handPos(owner), new Vec3(drop.x + 0.5, drop.y + 0.5, drop.z + 0.5));
		level.playSound(null, mark.atY(top), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 2.0f, 0.6f);
		level.playSound(null, mark.atY(top), SoundEvents.BUBBLE_COLUMN_UPWARDS_AMBIENT, SoundSource.PLAYERS, 2.0f, 0.8f);
	}

	private static void addBody(Drop drop, List<Display.BlockDisplay> into, BlockState state, double x, double y, double z) {
		Display.BlockDisplay body = EntityTypes.BLOCK_DISPLAY.create(drop.level, EntitySpawnReason.TRIGGERED);
		if (body == null) return;
		body.setBlockState(state);
		body.setBrightnessOverride(Brightness.FULL_BRIGHT);
		body.setPosRotInterpolationDuration(1);
		body.setPos(x, y, z);
		drop.level.addFreshEntity(body);
		into.add(body);
	}

	/** Every other tick while the ball is held: tells the clients to flare the bearer's ring and pour light into it, power 0..1. */
	private static void form(Drop drop, float power) {
		if (drop.level.getGameTime() % 2 != 0) return;
		Vec3 mid = new Vec3(drop.x + 0.5, drop.hang + 0.5, drop.z + 0.5);
		RingFx.send(drop.level, Kind.DELUGE_FORM, mid, mid, power, drop.globe, drop.owner);
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
			Corps before = Corps.enter(drop.corps);
			try {
				if (tick(drop)) continue;
				discardBodies(drop);
				it.remove();
				sweep(drop);
				scorch(drop);
			} finally {
				Corps.restore(before);
			}
		}
	}

	/** @return false once the Deluge is over */
	private static boolean tick(Drop drop) {
		ServerLevel level = drop.level;
		long now = level.getGameTime();
		if (drop.recall != null) return recallTick(drop, now);
		if (drop.pour == null) {
			if (now - drop.born > MAX_FALL_TICKS) return false;
			fall(drop);
			return true;
		}
		vanish(drop, now);
		pour(drop);
		geyser(drop, now);
		if (drop.lava() && drop.melted < MELT_LAYERS && now < drop.drainAt
				&& now >= drop.burstAt + (long) (drop.melted + 1) * Math.max(1, RingTuning.LAVA_MELT.ticks())) {
			melt(drop);
		}
		if (now < drop.drainAt) {
			waves(drop, now);
			return true;
		}
		clearCrest(drop);
		drain(drop);
		return now < drop.endAt;
	}

	private static void fall(Drop drop) {
		form(drop, 1f);
		vanish(drop, drop.level.getGameTime());
		if (drop.level.getGameTime() - drop.born < FORM_TICKS) return;
		// The bottom tears away and is thrown down hard.
		drop.speed = drop.speed == 0 ? TEAR_SPEED : drop.speed + TEAR_GRAVITY;
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
		for (int i = 0; i < drop.bottom.size(); i++) {
			int[] o = drop.bottomOffsets.get(i);
			drop.bottom.get(i).setPos(drop.x + o[0], drop.y + o[1], drop.z + o[2]);
		}
		// Green drips shaken off as it falls (the red globe sheds fine blood-red drops instead of glow squares).
		if (drop.lava()) {
			drop.level.sendParticles(BLOOD, drop.x + 0.5, drop.y + 0.5, drop.z + 0.5,
					2 + drop.globe, drop.globe * 0.6, drop.globe * 0.6, drop.globe * 0.6, 0);
		} else if (drop.level.getGameTime() % 2 == 0) {
			drop.level.sendParticles(ModParticles.of(ModParticles.DRIP), drop.x + 0.5, drop.y + 0.5, drop.z + 0.5,
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

	/**
	 * The globe hits the ground: it bursts, shoves and hurts everything around, a geyser shoots
	 * up, the flood starts racing outward, and the waves are lined up behind it.
	 */
	private static void burst(Drop drop) {
		ServerLevel level = drop.level;
		long now = level.getGameTime();
		// Only the bottom half is gone; the top stays held up there until the waves are nearly out.
		for (Display.BlockDisplay body : drop.bottom) body.discard();
		drop.bottom.clear();
		int radius = RADII[drop.lvl];
		Vec3 center = new Vec3(drop.x + 0.5, Math.floor(drop.y) - drop.globe, drop.z + 0.5);
		drop.center = center;
		drop.burstAt = now;
		BlockPos c = BlockPos.containing(center);

		// The flood's edge wobbles a little so it isn't a perfect circle.
		double[] edge = new double[16];
		for (int i = 0; i < edge.length; i++) edge[i] = radius * (0.85 + 0.2 * level.getRandom().nextDouble());
		List<BlockPos> pour = new ArrayList<>();
		int reach = radius + overrun(drop);
		for (int dx = -reach; dx <= reach; dx++) {
			for (int dz = -reach; dz <= reach; dz++) {
				double dist = Math.sqrt(dx * dx + dz * dz);
				if (dist > reach) continue;
				BlockPos surface = surface(level, c.offset(dx, 0, dz));
				if (surface == null) continue;
				drop.ground.put(BlockPos.asLong(surface.getX(), 0, surface.getZ()), surface);
				drop.minY = Math.min(drop.minY, surface.getY());
				drop.maxY = Math.max(drop.maxY, surface.getY());
				double angle = (Math.atan2(dz, dx) / (Math.PI * 2) + 1) * edge.length;
				int i0 = (int) Math.floor(angle) % edge.length;
				double t = angle - Math.floor(angle);
				// The red pool is one smooth, unbroken sheet (J: no sharp angles), so no gobs past its edge or holes in it.
				if (dist > Mth.lerp(t, edge[i0], edge[(i0 + 1) % edge.length])) continue;
				pour.add(surface);
				// The middle of the flood is deeper.
				if (!drop.lava() && dist < radius * 0.4 && passable(level.getBlockState(surface.above()))) pour.add(surface.above());
			}
		}
		if (drop.minY == Integer.MAX_VALUE) drop.minY = drop.maxY = c.getY();
		pour.sort(Comparator.comparingDouble(p -> sq(p.getX() + 0.5 - center.x) + sq(p.getZ() + 0.5 - center.z) + p.getY() * 0.01));
		drop.pour = pour;
		int spreadTicks = Math.max(1, RingTuning.DELUGE_SPREAD.ticks());
		drop.perTick = Math.max(1, (int) Math.ceil(pour.size() / (double) spreadTicks));
		// All of it is gone this long after the burst: 15, 20 or 25 s by level, drain included.
		drop.endAt = now + Math.max(spreadTicks + 20, lifetimeTicks(drop.lvl));
		drop.drainAt = Math.max(now + spreadTicks, drop.endAt - Math.max(1, RingTuning.DELUGE_DRAIN.ticks()));
		int waves = WAVES[drop.lvl] + (drop.lava() ? 1 : 0);
		int gap = drop.lava() ? RED_WAVE_GAP : WAVE_GAP;
		for (int i = 0; i < waves; i++) drop.waves.add(new Wave(now + 4 + (long) i * gap));
		if (drop.lava()) {
			// The red one lasts as long as its waves: the moment the last wave has rolled out to its
			// edge, the whole pool starts to drain away, outer edge first.
			long lastStart = now + 4 + (long) (waves - 1) * gap;
			long wavesDone = lastStart + (long) Math.ceil((radius + overrun(drop) - 1.5) / waveSpeed(drop)) + 2;
			drop.drainAt = Math.max(now + spreadTicks, wavesDone);
			drop.endAt = drop.drainAt + Math.max(1, RingTuning.DELUGE_DRAIN.ticks());
		}

		// The geyser: a column of liquid shooting up out of the middle (a plus shape at bigger levels).
		BlockPos base = drop.ground.getOrDefault(BlockPos.asLong(c.getX(), 0, c.getZ()), c);
		// The red one has no column: it bursts straight into its rolling waves (J: no spiky middle).
		int geyser = drop.lava() ? 0 : GEYSER[drop.lvl];
		int[][] columns = drop.lvl == 0 ? new int[][] {{0, 0}} : new int[][] {{0, 0}, {1, 0}, {-1, 0}, {0, 1}, {0, -1}};
		for (int h = 1; h <= geyser; h++) {
			for (int[] col : columns) {
				if (col[0] != 0 || col[1] != 0) {
					if (h > geyser * 2 / 3) continue;
				}
				BlockPos pos = base.offset(col[0], h, col[1]);
				if (!passable(level.getBlockState(pos)) || !level.mayInteract(drop.owner, pos)) continue;
				level.setBlock(pos, drop.liquid.defaultBlockState(), 2);
				drop.geyser.add(pos.immutable());
			}
		}
		drop.maxY = Math.max(drop.maxY, base.getY() + geyser + 1);

		double hitReach = radius + 3;
		for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, new AABB(center, center).inflate(hitReach),
				e -> e != drop.owner && e.isAlive() && !e.isSpectator())) {
			Vec3 away = target.position().subtract(center);
			double d = away.length();
			if (d > hitReach) continue;
			away = away.multiply(1, 0, 1);
			away = away.lengthSqr() < 1.0e-4 ? new Vec3(1, 0, 0) : away.normalize();
			float falloff = (float) (1 - d / hitReach);
			target.hurtServer(level, level.damageSources().indirectMagic(drop.owner, drop.owner), IMPACT_DAMAGE[drop.lvl] * falloff + 1);
			if (drop.lava()) target.igniteForSeconds(4 + 2 * drop.lvl);
			double shove = SHOVE[drop.lvl];
			target.setDeltaMovement(away.x * shove * falloff, 0.5 + 0.35 * shove * falloff, away.z * shove * falloff);
			RingPowers.syncVelocity(target);
		}

		RingFx.send(level, Kind.DELUGE_SPLASH, center, center.add(radius + (drop.lava() ? overrun(drop) - WAVE_OVERRUN : 0), 0, 0), 0f, drop.globe);
		if (drop.lava()) {
			lavaBurst(drop, center, radius);
			return;
		}
		level.sendParticles(ParticleTypes.SPLASH, center.x, center.y + 1, center.z, 250 * (drop.lvl + 1), radius * 0.4, 1.0, radius * 0.4, 0.6);
		level.sendParticles(ParticleTypes.SPLASH, center.x, center.y + GEYSER[drop.lvl], center.z, 80 * (drop.lvl + 1), 1.2, 1.5, 1.2, 0.5);
		level.sendParticles(ParticleTypes.BUBBLE_POP, center.x, center.y + 1, center.z, 60 * (drop.lvl + 1), radius * 0.3, 0.5, radius * 0.3, 0.1);
		if (drop.lvl >= 1) level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, center.x, center.y + 1, center.z, 1, 0, 0, 0, 0);
		level.playSound(null, center.x, center.y, center.z, SoundEvents.PLAYER_SPLASH_HIGH_SPEED, SoundSource.PLAYERS, 5.0f, 0.4f);
		level.playSound(null, center.x, center.y, center.z, SoundEvents.GENERIC_SPLASH, SoundSource.PLAYERS, 5.0f, 0.5f);
		level.playSound(null, center.x, center.y, center.z, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.PLAYERS, 3.0f, 0.5f);
		level.playSound(null, center.x, center.y, center.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 2.0f + 1.5f * drop.lvl, 1.1f - 0.15f * drop.lvl);
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

	/** Puts the next ring of liquid down, so the flood spreads outward from the burst. */
	private static void pour(Drop drop) {
		if (drop.poured >= drop.pour.size()) return;
		ServerLevel level = drop.level;
		int end = Math.min(drop.pour.size(), drop.poured + drop.perTick);
		for (; drop.poured < end; drop.poured++) {
			BlockPos pos = drop.pour.get(drop.poured);
			if (!place(drop, pos, 3)) continue;
			drop.placed.add(pos.immutable());
			if (level.getRandom().nextInt(6) == 0) {
				if (drop.lava()) level.sendParticles(BLOOD, pos.getX() + 0.5, pos.getY() + 1, pos.getZ() + 0.5, 4, 0.4, 0.2, 0.4, 0.3);
				else level.sendParticles(ParticleTypes.SPLASH, pos.getX() + 0.5, pos.getY() + 1, pos.getZ() + 0.5, 10, 0.4, 0.2, 0.4, 0.3);
			}
		}
	}

	/** Puts a liquid source at pos if the spot is open (or already ours). */
	private static boolean place(Drop drop, BlockPos pos, int flags) {
		return place(drop, pos, 0, flags);
	}

	/** Puts the liquid at pos with the given level (0 a full source, 1 to 7 lower) if the spot is open (or already ours). */
	private static boolean place(Drop drop, BlockPos pos, int liquidLevel, int flags) {
		BlockState there = drop.level.getBlockState(pos);
		if (there.is(drop.liquid)) {
			int now = there.getValue(LiquidBlock.LEVEL);
			// A source stays a source; a partial block takes the new level.
			if (now == liquidLevel || now == 0 && drop.placed.contains(pos)) return true;
		} else if (!passable(there)) {
			return false;
		}
		if (there.hasBlockEntity() || !drop.level.mayInteract(drop.owner, pos)) return false;
		drop.level.setBlock(pos, drop.liquid.defaultBlockState().setValue(LiquidBlock.LEVEL, liquidLevel), flags);
		return true;
	}

	/**
	 * The top half of the ball doesn't stay floating: from the moment the bottom tears away it
	 * dissolves layer by layer from its top surface down, faster than the bottom falls, each
	 * layer bursting into a quick spray as it goes.
	 */
	private static void vanish(Drop drop, long now) {
		if (drop.top.isEmpty() || now < drop.goneFrom) return;
		int rows = drop.globe + 1;
		float t = (now - drop.goneFrom + 1) / (float) Math.max(1, RingTuning.DELUGE_VANISH.ticks());
		int keepBelow = Math.round(rows * (1f - t));
		ServerLevel level = drop.level;
		Set<Integer> burst = new HashSet<>();
		for (int i = drop.top.size() - 1; i >= 0; i--) {
			int[] o = drop.topOffsets.get(i);
			if (o[1] < keepBelow) continue;
			drop.top.remove(i).discard();
			drop.topOffsets.remove(i);
			burst.add(o[1]);
		}
		for (int dy : burst) {
			// A spray blown out from the layer that just went, as wide as the ball is there.
			double across = Math.sqrt(Math.max(0.25, sq(drop.globe + 0.5) - dy * dy)) * 0.6;
			double y = drop.hang + dy + 0.5;
			if (drop.lava()) {
				level.sendParticles(BLOOD, drop.x + 0.5, y, drop.z + 0.5, 12 + 6 * drop.globe, across, 0.15, across, 0.25);
			} else {
				level.sendParticles(ParticleTypes.SPLASH, drop.x + 0.5, y, drop.z + 0.5, 20 + 8 * drop.globe, across, 0.15, across, 0.4);
				level.sendParticles(ModParticles.of(ModParticles.MOTE), drop.x + 0.5, y, drop.z + 0.5, 4 + 2 * drop.globe, across, 0.1, across, 0.08);
			}
		}
		if (!burst.isEmpty() && drop.top.isEmpty()) {
			level.playSound(null, drop.x, drop.hang, drop.z, SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.PLAYERS, 1.5f, 1.4f);
		}
	}

	/** The geyser falls back in: its top blocks go first, a couple a tick. */
	private static void geyser(Drop drop, long now) {
		if (drop.geyser.isEmpty() || now < drop.burstAt + 6) return;
		for (int i = 0; i < 2 + drop.lvl && !drop.geyser.isEmpty(); i++) {
			BlockPos pos = drop.geyser.remove(drop.geyser.size() - 1);
			if (!drop.placed.contains(pos) && !drop.crest.contains(pos)) removeIfOurs(drop.level, pos);
		}
	}

	/**
	 * The waves: each a ring of tall liquid rolling outward from the burst, shrinking as it goes and
	 * breaking a little way onto the land past the flood. Whatever it reaches is swept outward.
	 */
	private static void waves(Drop drop, long now) {
		if (drop.waves.isEmpty()) return;
		ServerLevel level = drop.level;
		int radius = RADII[drop.lvl];
		double end = radius + overrun(drop);
		// Each crest block and its liquid level: 0 is a full source, 1 to 7 a lower, partial block on top.
		Map<BlockPos, Integer> next = new HashMap<>();
		Vec3 c = drop.center;
		for (Iterator<Wave> it = drop.waves.iterator(); it.hasNext(); ) {
			Wave wave = it.next();
			if (now < wave.start) continue;
			double w = (now - wave.start) * waveSpeed(drop) + 1.5;
			if (w > end) {
				it.remove();
				continue;
			}
			double fade = w / end;
			int crest = CREST[drop.lvl] + (drop.lava() ? 1 : 0);
			int height = Math.max(1, (int) Math.round(crest * (1 - 0.7 * fade)));
			if (drop.lava()) {
				height = roll(drop, next, w, fade);
			} else {
				int ri = (int) Math.ceil(w + 1);
				for (int dx = -ri; dx <= ri; dx++) {
					for (int dz = -ri; dz <= ri; dz++) {
						double d = Math.sqrt(sq(dx) + sq(dz));
						if (d < w - 1.3 || d > w + 0.3) continue;
						BlockPos ground = drop.ground.get(BlockPos.asLong(Mth.floor(c.x) + dx, 0, Mth.floor(c.z) + dz));
						if (ground == null) continue;
						// On top of the flood (or on bare ground past it): stack the crest.
						int added = 0;
						for (int j = 0; j < height + 2 && added < height; j++) {
							BlockPos pos = ground.above(j);
							if (drop.placed.contains(pos)) continue;
							next.put(pos, 0);
							added++;
						}
					}
				}
			}
			// Spray along the crest, and the roar of it.
			for (int i = 0; i < (drop.lava() ? 3 + 2 * drop.lvl : 6 + 4 * drop.lvl); i++) {
				double a = level.getRandom().nextDouble() * Math.PI * 2;
				double px = c.x + Math.cos(a) * w, pz = c.z + Math.sin(a) * w;
				BlockPos ground = drop.ground.get(BlockPos.asLong(Mth.floor(px), 0, Mth.floor(pz)));
				double py = (ground != null ? ground.getY() : c.y) + height + 0.3;
				if (drop.lava()) {
					// Fine blood-red spray thrown off the crest; no big glow squares.
					level.sendParticles(BLOOD, px, py, pz, 6, 0.5, 0.2, 0.5, 0.2);
					continue;
				}
				level.sendParticles(ParticleTypes.SPLASH, px, py, pz, 8, 0.4, 0.15, 0.4, 0.35);
				if (i % 3 == 0) level.sendParticles(ModParticles.of(ModParticles.DRIP), px, py, pz, 2, 0.3, 0.2, 0.3, 0.05);
			}
			if ((now - wave.start) % 6 == 0) {
				level.playSound(null, c.x, c.y, c.z, drop.lava() ? SoundEvents.LAVA_AMBIENT : SoundEvents.GENERIC_SPLASH, SoundSource.PLAYERS,
						2.0f + drop.lvl, 0.6f + 0.2f * (float) fade);
			}
			sweepUp(drop, wave, w, height);
		}
		for (BlockPos pos : drop.crest) {
			if (!next.containsKey(pos) && !drop.placed.contains(pos) && !drop.geyser.contains(pos)) removeIfOurs(level, pos);
		}
		drop.crest.clear();
		for (Map.Entry<BlockPos, Integer> e : next.entrySet()) {
			// Crests come and go every tick: no neighbour updates, so they don't flood the world as they pass.
			if (place(drop, e.getKey(), e.getValue(), 2)) drop.crest.add(e.getKey());
		}
	}

	/**
	 * The red Deluge's wave: a broad, rounded swell instead of a wall. Its cross-section is a smooth
	 * bump several blocks across, built of full blocks topped with a partly filled one, so the game's
	 * liquid surface slopes smoothly over it. It rises as it rolls out of the middle and sinks as it
	 * spreads. Returns its tallest height in blocks.
	 */
	private static int roll(Drop drop, Map<BlockPos, Integer> next, double w, double fade) {
		Vec3 c = drop.center;
		double half = 2.0 + 0.6 * drop.lvl;
		double rise = Math.min(1.0, 0.3 + (w - 1.5) / 5.0);
		double peak = (CREST[drop.lvl] + 0.5) * (1 - 0.65 * fade) * rise;
		int ri = (int) Math.ceil(w + half);
		for (int dx = -ri; dx <= ri; dx++) {
			for (int dz = -ri; dz <= ri; dz++) {
				double off = Math.sqrt(sq(dx) + sq(dz)) - w;
				if (Math.abs(off) > half) continue;
				BlockPos ground = drop.ground.get(BlockPos.asLong(Mth.floor(c.x) + dx, 0, Mth.floor(c.z) + dz));
				if (ground == null) continue;
				double h = peak * 0.5 * (1 + Math.cos(Math.PI * off / half));
				int full = (int) h;
				int eighths = (int) Math.round((h - full) * 8);
				if (eighths >= 8) {
					full++;
					eighths = 0;
				}
				// Stack on top of the flood (or on the bare ground past it), skipping the flood's own blocks.
				int added = 0;
				int target = full + (eighths > 0 ? 1 : 0);
				for (int j = 0; j < target + 2 && added < target; j++) {
					BlockPos pos = ground.above(j);
					if (drop.placed.contains(pos)) continue;
					added++;
					next.put(pos, added <= full ? 0 : 8 - eighths);
				}
			}
		}
		return Math.max(1, (int) Math.ceil(peak));
	}

	/** Mobs (and players other than the bearer) caught by a wave are swept outward, and hit once. */
	private static void sweepUp(Drop drop, Wave wave, double w, int height) {
		ServerLevel level = drop.level;
		Vec3 c = drop.center;
		AABB box = new AABB(c, c).inflate(w + 2, 0, w + 2).expandTowards(0, height + 3, 0).move(0, -2, 0);
		double shove = SHOVE[drop.lvl] * (1 - 0.5 * w / (RADII[drop.lvl] + overrun(drop)));
		for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, box,
				e -> e != drop.owner && e.isAlive() && !e.isSpectator())) {
			Vec3 away = target.position().subtract(c).multiply(1, 0, 1);
			double d = away.length();
			if (d < w - 2 || d > w + 1.5) continue;
			away = d < 1.0e-3 ? new Vec3(1, 0, 0) : away.scale(1 / d);
			target.setDeltaMovement(away.x * shove * 0.7, Math.max(target.getDeltaMovement().y, 0.3 + 0.08 * height), away.z * shove * 0.7);
			RingPowers.syncVelocity(target);
			if (wave.hit.add(target.getId())) {
				target.hurtServer(level, level.damageSources().indirectMagic(drop.owner, drop.owner), WAVE_DAMAGE[drop.lvl]);
				if (drop.lava()) target.igniteForSeconds(3 + 2 * drop.lvl);
			}
		}
	}

	private static void clearCrest(Drop drop) {
		for (BlockPos pos : drop.crest) {
			if (!drop.placed.contains(pos)) removeIfOurs(drop.level, pos);
		}
		drop.crest.clear();
		drop.waves.clear();
	}

	/** Takes the sources away a few at a time, outer edge first; what ran off them goes with the sweep at the end. */
	private static void drain(Drop drop) {
		ServerLevel level = drop.level;
		if (drop.drain == null) {
			drop.drain = new ArrayList<>(drop.placed);
			Vec3 c = drop.center;
			drop.drain.sort(Comparator.comparingDouble(p -> -(sq(p.getX() + 0.5 - c.x) + sq(p.getZ() + 0.5 - c.z)) - p.getY() * 0.01));
			level.playSound(null, BlockPos.containing(c), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1.5f, 0.7f);
		}
		long left = Math.max(1, drop.endAt - level.getGameTime());
		int perTick = Math.max(1, (int) Math.ceil((drop.drain.size() - drop.drained) / (double) left));
		int end = Math.min(drop.drain.size(), drop.drained + perTick);
		for (; drop.drained < end; drop.drained++) {
			BlockPos pos = drop.drain.get(drop.drained);
			drop.placed.remove(pos);
			removeIfOurs(level, pos);
			if (level.getRandom().nextInt(12) == 0) {
				// Green light motes rise as it drains; the red liquid leaves a fleck of red.
				level.sendParticles(drop.lava() ? BLOOD : ModParticles.of(ModParticles.MOTE),
						pos.getX() + 0.5, pos.getY() + 0.6, pos.getZ() + 0.5, 1, 0.3, 0.1, 0.3, 0.02);
			}
		}
	}

	/**
	 * The end: every block of hard-light liquid anywhere around the Deluge goes, sources and the
	 * flowing liquid that ran off them, down waterfalls too, unless another Deluge still holds it.
	 */
	private static void sweep(Drop drop) {
		ServerLevel level = drop.level;
		drop.placed.clear();
		drop.crest.clear();
		drop.geyser.clear();
		if (drop.center == null) return;
		int r = RADII[drop.lvl] + overrun(drop) + 8;
		BlockPos c = BlockPos.containing(drop.center);
		int low = Math.max(level.getMinY(), drop.minY - 32), high = drop.maxY + CREST[drop.lvl] + 5;
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		for (int dx = -r; dx <= r; dx++) {
			for (int dz = -r; dz <= r; dz++) {
				for (int y = low; y <= high; y++) {
					pos.set(c.getX() + dx, y, c.getZ() + dz);
					if (!level.isLoaded(pos) || !ModFluids.isDelugeLiquid(level.getBlockState(pos)) || isLive(level, pos)) continue;
					level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
				}
			}
		}
	}

	// ---- calling it back -------------------------------------------------------------------

	/**
	 * Left-click held in Deluge mode (not aiming): every Deluge of this bearer's is sucked back
	 * into the ring over DELUGE_RECALL, the liquid furthest from them going first, streaming
	 * through the air into the ring as it goes.
	 */
	public static void recall(ServerPlayer player) {
		long now = player.level().getGameTime();
		boolean any = false;
		for (Drop drop : DROPS) {
			if (drop.owner != player || drop.recall != null) continue;
			any = true;
			discardBodies(drop);
			Corps before = Corps.enter(drop.corps);
			try {
				startRecall(drop, now);
			} finally {
				Corps.restore(before);
			}
		}
		if (any) {
			player.level().playSound(null, player.blockPosition(), SoundEvents.BUCKET_FILL, SoundSource.PLAYERS, 1.5f, 0.6f);
			player.level().playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.2f, 1.6f);
		}
	}

	private static void startRecall(Drop drop, long now) {
		ServerLevel level = drop.level;
		drop.waves.clear();
		drop.geyser.clear();
		List<BlockPos> all = new ArrayList<>();
		if (drop.center != null) {
			int r = RADII[drop.lvl] + overrun(drop) + 8;
			BlockPos c = BlockPos.containing(drop.center);
			int low = Math.max(level.getMinY(), drop.minY - 32), high = drop.maxY + CREST[drop.lvl] + 5;
			for (int dx = -r; dx <= r; dx++) {
				for (int dz = -r; dz <= r; dz++) {
					for (int y = low; y <= high; y++) {
						BlockPos pos = new BlockPos(c.getX() + dx, y, c.getZ() + dz);
						if (!level.isLoaded(pos) || !ModFluids.isDelugeLiquid(level.getBlockState(pos)) || heldByOther(drop, pos)) continue;
						all.add(pos);
					}
				}
			}
		}
		Vec3 eye = drop.owner.getEyePosition();
		all.sort(Comparator.comparingDouble(p -> -eye.distanceToSqr(p.getX() + 0.5, p.getY() + 0.5, p.getZ() + 0.5)));
		drop.recall = all;
		drop.recalled = 0;
		drop.recallEnd = now + Math.max(1, RingTuning.DELUGE_RECALL.ticks());
	}

	private static boolean heldByOther(Drop drop, BlockPos pos) {
		for (Drop other : DROPS) {
			if (other != drop && other.level == drop.level && other.holds(pos)) return true;
		}
		return false;
	}

	/** One tick of the recall: the next share of the liquid goes, and some of it is seen streaming to the ring. */
	private static boolean recallTick(Drop drop, long now) {
		ServerLevel level = drop.level;
		int left = drop.recall.size() - drop.recalled;
		long ticks = Math.max(1, drop.recallEnd - now);
		int n = left <= 0 ? 0 : (int) Math.ceil(left / (double) ticks);
		int shown = 0;
		int every = Math.max(1, n / 14);
		for (int i = 0; i < n; i++) {
			BlockPos pos = drop.recall.get(drop.recalled++);
			drop.placed.remove(pos);
			drop.crest.remove(pos);
			drop.sunk.remove(pos);
			// No neighbour updates: nothing flows into the gaps while it's being drawn up.
			if (ModFluids.isDelugeLiquid(level.getBlockState(pos))) level.setBlock(pos, Blocks.AIR.defaultBlockState(), 2);
			if (i % every == 0 && shown < 14) {
				shown++;
				Vec3 at = new Vec3(pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5);
				RingFx.send(level, Kind.DELUGE_RECALL, at, at, 0f, drop.lava() ? 1 : 0, drop.owner);
			}
		}
		return drop.recalled < drop.recall.size() || now < drop.recallEnd;
	}

	// ---- the Red Lantern's lava -------------------------------------------------------------

	/** How many layers of ground the red liquid melts down through, one every LAVA_MELT. */
	private static final int MELT_LAYERS = 2;
	/** How much of the deeper layer is left soaked blood red (the rest stays as it was). */
	private static final double SOAK_SHARE = 0.75;

	/** The red burst: a spray of fine blood-red drops and splashes, and a roar of flame (the grass at the edge still catches). */
	private static void lavaBurst(Drop drop, Vec3 center, int radius) {
		ServerLevel level = drop.level;
		int n = drop.lvl + 1;
		level.sendParticles(BLOOD, center.x, center.y + 1, center.z, 120 * n, radius * 0.4, 1.0, radius * 0.4, 0.6);
		level.sendParticles(ParticleTypes.SPLASH, center.x, center.y + 1, center.z, 120 * n, radius * 0.45, 0.6, radius * 0.45, 0.5);
		level.sendParticles(BLOOD, center.x, center.y + GEYSER[drop.lvl], center.z, 80 * n, 1.5, 1.5, 1.5, 0.3);
		if (drop.lvl >= 1) level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, center.x, center.y + 1, center.z, 1, 0, 0, 0, 0);
		level.playSound(null, center.x, center.y, center.z, SoundEvents.FIRECHARGE_USE, SoundSource.PLAYERS, 5.0f, 0.5f);
		level.playSound(null, center.x, center.y, center.z, SoundEvents.LAVA_POP, SoundSource.PLAYERS, 5.0f, 0.6f);
		level.playSound(null, center.x, center.y, center.z, SoundEvents.BLAZE_SHOOT, SoundSource.PLAYERS, 3.0f, 0.5f);
		level.playSound(null, center.x, center.y, center.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 2.0f + 1.5f * drop.lvl, 0.9f - 0.15f * drop.lvl);
		// The grass around the edge catches.
		for (BlockPos ground : drop.ground.values()) {
			double d = Math.sqrt(sq(ground.getX() + 0.5 - center.x) + sq(ground.getZ() + 0.5 - center.z));
			if (d < radius - 1 || level.getRandom().nextInt(3) != 0) continue;
			if (level.getBlockState(ground).isAir() && level.mayInteract(drop.owner, ground)
					&& Blocks.FIRE.defaultBlockState().canSurvive(level, ground)) {
				level.setBlock(ground, Blocks.FIRE.defaultBlockState(), 3);
			}
		}
	}

	/**
	 * The red liquid melts the ground under it, a layer at a time. The first layer melts away into
	 * more liquid, so the pool sinks into the ground as it drains; the layer under that is mostly
	 * soaked blood red (nether wart block), the floor of the pit it leaves.
	 */
	private static void melt(Drop drop) {
		ServerLevel level = drop.level;
		drop.melted++;
		boolean first = drop.melted == 1;
		List<BlockPos> above = first ? new ArrayList<>(drop.placed) : new ArrayList<>(drop.sunk);
		int sounds = 0;
		for (BlockPos pos : above) {
			BlockPos at = pos.below();
			if (drop.placed.contains(at) || drop.sunk.contains(at) || !melts(drop, at)) continue;
			if (first) {
				level.setBlock(at, drop.liquid.defaultBlockState(), 2);
				drop.sunk.add(at.immutable());
				drop.minY = Math.min(drop.minY, at.getY());
			} else if (level.getRandom().nextDouble() < SOAK_SHARE) {
				level.setBlock(at, Blocks.NETHER_WART_BLOCK.defaultBlockState(), 3);
			} else {
				continue;
			}
			if (level.getRandom().nextInt(5) == 0) {
				level.sendParticles(BLOOD, at.getX() + 0.5, at.getY() + 2, at.getZ() + 0.5, 3, 0.3, 0.1, 0.3, 0.1);
			}
			if (sounds < 8 && level.getRandom().nextInt(12) == 0) {
				sounds++;
				level.playSound(null, at, SoundEvents.LAVA_POP, SoundSource.BLOCKS, 1.0f, 0.7f + level.getRandom().nextFloat() * 0.4f);
			}
		}
		Vec3 c = drop.center;
		level.playSound(null, c.x, c.y, c.z, SoundEvents.LAVA_EXTINGUISH, SoundSource.BLOCKS, 2.0f + drop.lvl, 0.5f);
	}

	/** Soft ground the red liquid can melt through: dirt, sand, stone; not ores' tougher kin, blocks with contents, or anything protected. */
	private static boolean melts(Drop drop, BlockPos pos) {
		BlockState state = drop.level.getBlockState(pos);
		if (state.isAir() || !state.getFluidState().isEmpty() || state.hasBlockEntity()) return false;
		if (state.is(ModRegistry.LIGHT_CONSTRUCT) || state.is(ModRegistry.CONSTRUCT_BRICK)) return false;
		float hardness = state.getDestroySpeed(drop.level, pos);
		return hardness >= 0 && hardness <= 3.5f && drop.level.mayInteract(drop.owner, pos);
	}

	/** After the red liquid is gone: forget where it melted (the soaked floor is already in place). */
	private static void scorch(Drop drop) {
		drop.sunk.clear();
	}

	private static void discardBodies(Drop drop) {
		for (Display.BlockDisplay body : drop.top) body.discard();
		for (Display.BlockDisplay body : drop.bottom) body.discard();
		drop.top.clear();
		drop.bottom.clear();
	}

	private static void removeIfOurs(ServerLevel level, BlockPos pos) {
		if (ModFluids.isDelugeLiquid(level.getBlockState(pos))) level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
	}
}
