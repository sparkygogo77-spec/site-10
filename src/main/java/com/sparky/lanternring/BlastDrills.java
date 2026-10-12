package com.sparky.lanternring;

import com.sparky.lanternring.block.BlastGlowBlock;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import com.sparky.lanternring.item.PowerRingItem;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.item.ItemStack;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * BLAST: a spinning hard-light drill flies out along the player's aim and bores a tunnel, breaking
 * each block as its tip reaches it. Holding right-click charges it: the reach builds from
 * MIN_LENGTH to LENGTH over RingTuning.BLAST_CHARGE and the shot goes on release. Left-click while
 * holding picks the level (3x3, 5x5 or 7x7) and starts the charge over. The drill moves at
 * LENGTH blocks per RingTuning.BLAST_DRILL_TIME. Clients draw the same drill at the same speed (client BlastDrillFx),
 * so the tip you see is where blocks are breaking.
 */
public final class BlastDrills {
	public static final double LENGTH = 50;
	/** The reach of a tap; holding builds it up to LENGTH. */
	public static final double MIN_LENGTH = 10;
	/** Tunnel width per level (index 1 to 3). */
	private static final int[] WIDTH = {3, 3, 5, 7};
	private static final float DAMAGE = 10.0f;
	/** The drill model from tip to back, in blocks (blast_drill.bbmodel is 100 pixels long). */
	public static final double DRILL_LENGTH = 100 / 16.0;
	/** How far ahead of the tunnel's start the drill's back appears, so it doesn't fill the screen. */
	public static final double START = 1.5;

	private record Cut(double t, BlockPos pos) {
	}

	private static final class Drill {
		final ServerLevel level;
		final Player owner;
		final Vec3 origin;
		final Vec3 look;
		final Vec3 right;
		final Vec3 up;
		final double speed;
		final double length;
		final double reach;
		final List<Cut> cuts = new ArrayList<>();
		final Set<BlockPos> wet = new HashSet<>();
		final Set<UUID> hit = new HashSet<>();
		int next;
		double tip;
		double nextLight = 2.0;
		double nextBubbles = 1.0;
		boolean gurgled;
		/** Whose drill it is: its tunnel lights take that corps' colour. */
		final Corps corps = Corps.current();

		Drill(ServerLevel level, Player owner, Vec3 origin, Vec3 look, Vec3 right, Vec3 up, double speed, double length, int width) {
			this.level = level;
			this.owner = owner;
			this.origin = origin;
			this.look = look;
			this.right = right;
			this.up = up;
			this.speed = speed;
			this.length = length;
			// How far from the middle a mob can be and still be hit: the tunnel's half width plus a bit.
			this.reach = width / 2.0 + 0.5;
		}
	}

	private static final List<Drill> DRILLS = new ArrayList<>();
	/** When each charging player's charge started (game time); a level change restarts it. */
	private static final Map<UUID, Long> CHARGING = new HashMap<>();

	private BlastDrills() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(BlastDrills::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			DRILLS.clear();
			CHARGING.clear();
		});
	}

	/** Blocks per tick, from the Durations menu's time for the whole tunnel. */
	public static double speed() {
		return LENGTH / Math.max(1, RingTuning.BLAST_DRILL_TIME.ticks());
	}

	/** Where the tip is when the drill appears. */
	public static double startTip() {
		return START + DRILL_LENGTH;
	}

	// ---- levels and charging -------------------------------------------------------------

	public static int level(ItemStack ring) {
		int level = ring.getOrDefault(ModComponents.BLAST_LEVEL, 1);
		return level >= 1 && level <= 3 ? level : 1;
	}

	public static int width(int level) {
		return WIDTH[Mth.clamp(level, 1, 3)];
	}

	/**
	 * Charge for a shot charged this far (0 to 1): 0.5% to 1% of a full ring at level 1, 1.5x that
	 * at level 2 and 2x at level 3 (PowerRingItem.MAX_CHARGE = 1000, so 5 = 0.5%).
	 */
	public static int cost(int level, float fraction) {
		float base = 5 + 5 * Mth.clamp(fraction, 0f, 1f);
		float times = level >= 3 ? 2f : level == 2 ? 1.5f : 1f;
		return Math.round(base * times);
	}

	/** How far a charge held for this many ticks reaches, 0 to 1. */
	public static float fraction(long heldTicks) {
		return Mth.clamp(heldTicks / (float) Math.max(1, RingTuning.BLAST_CHARGE.ticks()), 0f, 1f);
	}

	public static double length(float fraction) {
		return MIN_LENGTH + (LENGTH - MIN_LENGTH) * fraction;
	}

	/** Right-click pressed in Blast mode: the charge starts building. */
	public static void beginCharge(ServerPlayer player) {
		CHARGING.put(player.getUUID(), player.level().getGameTime());
	}

	/** Charging stopped without letting go on purpose (switched to a lantern charge): no drill. */
	public static void cancel(ServerPlayer player) {
		CHARGING.remove(player.getUUID());
	}

	/** How far the player's current charge reaches, 0 to 1, or -1 when not charging. */
	public static float charged(ServerPlayer player) {
		Long since = CHARGING.get(player.getUUID());
		return since == null ? -1f : fraction(player.level().getGameTime() - since);
	}

	/** Left-click while charging: the next level, and the charge starts over. */
	public static void cycleLevel(ServerPlayer player) {
		ItemStack ring = player.getUseItem();
		if (!(ring.getItem() instanceof PowerRingItem) || PowerRingItem.getMode(ring) != RingMode.BLAST || !CHARGING.containsKey(player.getUUID())) {
			return;
		}
		int next = level(ring) % 3 + 1;
		ring.set(ModComponents.BLAST_LEVEL, next);
		beginCharge(player);
		player.sendOverlayMessage(levelText(next).copy().withStyle(ChatFormatting.GREEN));
		player.level().playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1f, 1.6f - 0.2f * next);
	}

	public static Component levelText(int level) {
		int w = width(level);
		return Component.translatable("message.lanternring.blast_level", level, w, w,
				percent(cost(level, 0f)), percent(cost(level, 1f)));
	}

	/** Charge points as a percent of a full ring: 5 -> "0.5", 10 -> "1", 15 -> "1.5". */
	private static String percent(int points) {
		return points % 10 == 0 ? String.valueOf(points / 10) : String.valueOf(points / 10.0);
	}

	/** Right-click let go: the drill goes, as far as it was charged, if the ring has the charge. */
	public static boolean release(ServerLevel level, ServerPlayer player, ItemStack ring) {
		Long since = CHARGING.remove(player.getUUID());
		if (since == null) return false;
		float fraction = fraction(level.getGameTime() - since);
		int lvl = level(ring);
		int cost = cost(lvl, fraction);
		if (!player.isCreative() && PowerRingItem.getCharge(ring) < cost) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.no_charge").withStyle(ChatFormatting.RED));
			level.playSound(null, player.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.6f, 1.4f);
			return false;
		}
		start(level, player, length(fraction), lvl);
		if (!player.isCreative()) PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - cost);
		player.getCooldowns().addCooldown(ring, RingTuning.cooldownTicks(RingMode.BLAST));
		player.sendOverlayMessage(PowerRingItem.chargeText(ring));
		return true;
	}

	/** While charging: a click each time the reach grows by a fifth, and a chime when it's full. */
	public static void chargeTick(ServerPlayer player) {
		Long since = CHARGING.get(player.getUUID());
		if (since == null) return;
		long held = player.level().getGameTime() - since;
		int full = Math.max(1, RingTuning.BLAST_CHARGE.ticks());
		if (held > 0 && held <= full && held % Math.max(1, full / 5) == 0) {
			float f = fraction(held);
			player.level().playSound(null, player.blockPosition(), held == full ? SoundEvents.BEACON_POWER_SELECT : SoundEvents.NOTE_BLOCK_HAT.value(),
					SoundSource.PLAYERS, 0.5f, 0.8f + 0.8f * f);
			player.sendOverlayMessage(Component.translatable("message.lanternring.blast_reach", Math.round(length(f)))
					.withStyle(held >= full ? ChatFormatting.WHITE : ChatFormatting.GREEN));
		}
	}

	// ---- the drill ------------------------------------------------------------------------

	/** Fires a drill reaching length blocks at the given level (1 to 3). */
	public static boolean start(ServerLevel level, Player player, double length, int lvl) {
		Vec3 look = player.getLookAngle();
		Vec3 right = look.cross(new Vec3(0, 1, 0));
		if (right.lengthSqr() < 1.0e-4) {
			// Looking straight up or down: use the way the player's body faces.
			Direction side = player.getDirection().getClockWise();
			right = new Vec3(side.getStepX(), 0, side.getStepZ());
		}
		right = right.normalize();
		Vec3 up = right.cross(look).normalize();

		// Centre the tunnel slightly below the eyes so the player's whole body fits through it. Wider
		// tunnels grow upward and sideways from the same floor.
		int width = width(lvl);
		int half = width / 2;
		Vec3 origin = player.getEyePosition().subtract(0, 0.6, 0).add(up.scale(half - 1));
		Drill drill = new Drill(level, player, origin, look, right, up, speed(), Math.min(LENGTH, length), width);
		// Each block is cut when the tip first reaches it.
		Map<BlockPos, Double> first = new LinkedHashMap<>();
		for (double t = 1.0; t <= drill.length; t += 0.4) {
			Vec3 center = origin.add(look.scale(t));
			for (int a = -half; a <= half; a++) {
				for (int b = -half; b <= half; b++) {
					first.putIfAbsent(BlockPos.containing(center.add(right.scale(a)).add(up.scale(b))), t);
				}
			}
		}
		first.forEach((pos, t) -> drill.cuts.add(new Cut(t, pos)));
		DRILLS.add(drill);

		RingFx.send(level, Kind.BLAST, origin, origin.add(look.scale(drill.length)), (float) drill.speed, lvl, player);
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.WARDEN_SONIC_BOOM,
				SoundSource.PLAYERS, 1.0f, 1.6f);
		// The first stretch goes straight away, so the drill never appears inside a block.
		advance(drill, startTip());
		return true;
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Drill> it = DRILLS.iterator(); it.hasNext(); ) {
			Drill drill = it.next();
			Corps before = Corps.enter(drill.corps);
			try {
				advance(drill, drill.tip + drill.speed);
			} finally {
				Corps.restore(before);
			}
			if (drill.tip >= drill.length) it.remove();
		}
	}

	private static void advance(Drill drill, double tip) {
		ServerLevel level = drill.level;
		double from = drill.tip;
		drill.tip = Math.min(drill.length, tip);

		// Water and plants are cleared too; the surrounding water then flows back in by itself.
		BlockState loudest = null;
		while (drill.next < drill.cuts.size() && drill.cuts.get(drill.next).t <= drill.tip) {
			BlockPos pos = drill.cuts.get(drill.next++).pos;
			if (level.getFluidState(pos).is(FluidTags.WATER)) drill.wet.add(pos);
			BlockState state = level.getBlockState(pos);
			if (state.isAir() || state.getBlock() instanceof BlastGlowBlock || state.getDestroySpeed(level, pos) < 0 || state.hasBlockEntity()
					|| !level.mayInteract(drill.owner, pos)) {
				continue;
			}
			level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
			// Plain water has no debris worth showing; it only clouded the shot underwater.
			if (!state.is(Blocks.WATER)) HeldConstructs.debris(level, pos, state);
			if (state.getFluidState().isEmpty() && (loudest == null || state.getDestroySpeed(level, pos) > loudest.getDestroySpeed(level, pos))) {
				loudest = state;
			}
		}
		if (loudest != null) {
			// One grinding crunch per tick, in the sound of the hardest block the drill just broke.
			Vec3 at = drill.origin.add(drill.look.scale(drill.tip));
			level.playSound(null, at.x, at.y, at.z, loudest.getSoundType().getBreakSound(), SoundSource.PLAYERS, 1.0f, 0.7f);
		}

		lightTunnel(drill);
		bubbleTrail(drill);

		Vec3 a = drill.origin.add(drill.look.scale(Math.max(0, from - DRILL_LENGTH)));
		Vec3 b = drill.origin.add(drill.look.scale(drill.tip));
		for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, new AABB(a, b).inflate(drill.reach),
				e -> e != drill.owner && e.isAlive() && !e.isSpectator() && !drill.hit.contains(e.getUUID())
						&& reached(e.getBoundingBox().getCenter(), drill))) {
			drill.hit.add(target.getUUID());
			target.hurtServer(level, level.damageSources().indirectMagic(drill.owner, drill.owner), DAMAGE);
		}
	}

	/** Whether the drill (tip and body) has got to this point and it is within the tunnel. */
	private static boolean reached(Vec3 point, Drill drill) {
		Vec3 rel = point.subtract(drill.origin);
		double along = rel.dot(drill.look);
		return along >= 0 && along <= drill.tip && rel.subtract(drill.look.scale(along)).length() < drill.reach;
	}

	/**
	 * Underwater, the sea folds back over the tunnel almost at once, so the drill also leaves a
	 * trail of bubbles bursting out of the tunnel walls behind it to show where it went.
	 */
	private static void bubbleTrail(Drill drill) {
		ServerLevel level = drill.level;
		Vec3 look = drill.look;
		for (; drill.nextBubbles <= drill.tip; drill.nextBubbles += 1.5) {
			double t = drill.nextBubbles;
			Vec3 center = drill.origin.add(look.scale(t));
			if (!drill.wet.contains(BlockPos.containing(center))) continue;
			for (int i = 0; i < 8; i++) {
				double a = i * Math.PI / 4 + t;
				Vec3 out = drill.right.scale(Math.cos(a)).add(drill.up.scale(Math.sin(a)));
				Vec3 at = center.add(out.scale(drill.reach - 0.5));
				// Count 0 makes the offsets a velocity: bubbles spray outwards and a little forwards.
				level.sendParticles(ParticleTypes.BUBBLE, at.x, at.y, at.z, 0, out.x + look.x * 0.5, out.y + look.y * 0.5, out.z + look.z * 0.5, 0.35);
			}
			level.sendParticles(ParticleTypes.BUBBLE_COLUMN_UP, center.x, center.y, center.z, 3, 1.2, 1.2, 1.2, 0.05);
			if (!drill.gurgled) {
				drill.gurgled = true;
				level.playSound(null, drill.origin.x, drill.origin.y, drill.origin.z, SoundEvents.BUBBLE_COLUMN_WHIRLPOOL_INSIDE, SoundSource.PLAYERS, 1.0f, 1.2f);
			}
		}
	}

	/**
	 * Leaves a few invisible lights down the middle of the tunnel behind the drill, so the glowing
	 * scar lights its walls. Plain block light, so it works with any shader pack.
	 */
	private static void lightTunnel(Drill drill) {
		if (RingTuning.BLAST_AFTERGLOW.ticks() <= 0) return;
		BlockState glow = Corps.state(ModRegistry.BLAST_GLOW);
		for (; drill.nextLight <= drill.tip; drill.nextLight += 4.0) {
			BlockPos pos = BlockPos.containing(drill.origin.add(drill.look.scale(drill.nextLight)));
			if (drill.level.getBlockState(pos).isAir() && drill.level.mayInteract(drill.owner, pos)) {
				drill.level.setBlock(pos, glow.setValue(BlastGlowBlock.WATERLOGGED, drill.wet.contains(pos)), 3);
			}
		}
	}
}
