package com.sparky.lanternring;

import com.sparky.lanternring.block.BlastGlowBlock;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.ArrayList;
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
import net.minecraft.server.level.ServerLevel;
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
 * BLAST: a spinning hard-light drill flies out along the player's aim and bores a 3x3 tunnel
 * LENGTH blocks long, breaking each block as its tip reaches it. It crosses the whole length in
 * RingTuning.BLAST_DRILL_TIME. Clients draw the same drill at the same speed (client BlastDrillFx),
 * so the tip you see is where blocks are breaking.
 */
public final class BlastDrills {
	public static final double LENGTH = 50;
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
		final List<Cut> cuts = new ArrayList<>();
		final Set<BlockPos> wet = new HashSet<>();
		final Set<UUID> hit = new HashSet<>();
		int next;
		double tip;
		double nextLight = 2.0;
		double nextBubbles = 1.0;
		boolean gurgled;

		Drill(ServerLevel level, Player owner, Vec3 origin, Vec3 look, Vec3 right, Vec3 up, double speed) {
			this.level = level;
			this.owner = owner;
			this.origin = origin;
			this.look = look;
			this.right = right;
			this.up = up;
			this.speed = speed;
		}
	}

	private static final List<Drill> DRILLS = new ArrayList<>();

	private BlastDrills() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(BlastDrills::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> DRILLS.clear());
	}

	/** Blocks per tick, from the Durations menu's time for the whole tunnel. */
	public static double speed() {
		return LENGTH / Math.max(1, RingTuning.BLAST_DRILL_TIME.ticks());
	}

	/** Where the tip is when the drill appears. */
	public static double startTip() {
		return START + DRILL_LENGTH;
	}

	static boolean start(ServerLevel level, Player player) {
		Vec3 look = player.getLookAngle();
		Vec3 right = look.cross(new Vec3(0, 1, 0));
		if (right.lengthSqr() < 1.0e-4) {
			// Looking straight up or down: use the way the player's body faces.
			Direction side = player.getDirection().getClockWise();
			right = new Vec3(side.getStepX(), 0, side.getStepZ());
		}
		right = right.normalize();
		Vec3 up = right.cross(look).normalize();

		// Centre the tunnel slightly below the eyes so the player's whole body fits through it.
		Vec3 origin = player.getEyePosition().subtract(0, 0.6, 0);
		Drill drill = new Drill(level, player, origin, look, right, up, speed());
		// Each block is cut when the tip first reaches it.
		Map<BlockPos, Double> first = new LinkedHashMap<>();
		for (double t = 1.0; t <= LENGTH; t += 0.4) {
			Vec3 center = origin.add(look.scale(t));
			for (int a = -1; a <= 1; a++) {
				for (int b = -1; b <= 1; b++) {
					first.putIfAbsent(BlockPos.containing(center.add(right.scale(a)).add(up.scale(b))), t);
				}
			}
		}
		first.forEach((pos, t) -> drill.cuts.add(new Cut(t, pos)));
		DRILLS.add(drill);

		RingFx.send(level, Kind.BLAST, origin, origin.add(look.scale(LENGTH)), (float) drill.speed);
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.WARDEN_SONIC_BOOM,
				SoundSource.PLAYERS, 1.0f, 1.6f);
		// The first stretch goes straight away, so the drill never appears inside a block.
		advance(drill, startTip());
		return true;
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Drill> it = DRILLS.iterator(); it.hasNext(); ) {
			Drill drill = it.next();
			advance(drill, drill.tip + drill.speed);
			if (drill.tip >= LENGTH) it.remove();
		}
	}

	private static void advance(Drill drill, double tip) {
		ServerLevel level = drill.level;
		double from = drill.tip;
		drill.tip = Math.min(LENGTH, tip);

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
		for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, new AABB(a, b).inflate(2.0),
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
		return along >= 0 && along <= drill.tip && rel.subtract(drill.look.scale(along)).length() < 2.0;
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
				Vec3 at = center.add(out.scale(2.0));
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
		BlockState glow = ModRegistry.BLAST_GLOW.defaultBlockState();
		for (; drill.nextLight <= drill.tip; drill.nextLight += 4.0) {
			BlockPos pos = BlockPos.containing(drill.origin.add(drill.look.scale(drill.nextLight)));
			if (drill.level.getBlockState(pos).isAir() && drill.level.mayInteract(drill.owner, pos)) {
				drill.level.setBlock(pos, glow.setValue(BlastGlowBlock.WATERLOGGED, drill.wet.contains(pos)), 3);
			}
		}
	}
}
