package com.sparky.lanternring;

import com.sparky.lanternring.net.CombatFxPayload.Kind;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * J's construct hammer (Blender pass 503, R2): ring only, no hand motions. Tap right-click in Hammer mode and a
 * hammer of hard light assembles in the air from construct pixels and swings down on whatever is 4 blocks in front
 * of you: overhead by default (R2a), in from the side when you hit a wall (R2b; every client draws the swing, see
 * ConstructHammerFx). Timed from the press, 20 ticks a second:
 * <ul>
 * <li>ticks 10-22 the hammer forms, 26-33 it swings (angle grows with progress squared), 33 it hits;
 * <li>a 3x3 crater on the face it hit (D0 rule: ring d lights at tick d, gone at 4 + 2d), a shockwave ring, and mobs
 * at the hit knocked away 0.55 blocks a tick forward and 0.5 up;
 * <li>0.7 s after the hit (RingTuning hammer_linger) it breaks into construct pixels.
 * </ul>
 */
public final class ConstructHammers {
	/** How far ahead the hammer lands, in blocks, and how far down it looks for the ground out there. */
	public static final double REACH = 4, DROP = 4;
	/** Ticks from the press: the hammer forms, starts its swing, hits. */
	public static final int FORM = 10, SWING = 26, HIT = 33;
	/** The mobs it catches: within this of the hit. */
	private static final double CATCH = 1.8;
	private static final float DAMAGE = 12f;

	private record Strike(ServerLevel level, ServerPlayer owner, Vec3 at, Vec3 forward, @Nullable BlockPos block, @Nullable Direction face,
			Corps corps, int hitAt) {
	}

	private static final Map<UUID, Strike> STRIKES = new HashMap<>();

	private ConstructHammers() {
	}

	/** Whether this player's hammer is still out. */
	public static boolean swinging(Player player) {
		return STRIKES.containsKey(player.getUUID());
	}

	/** Where the hammer lands for this player: the block 4 ahead along the look, else the ground under that point. */
	public static @Nullable BlockHitResult target(ServerLevel level, Player player) {
		Vec3 eye = player.getEyePosition(), look = player.getLookAngle();
		BlockHitResult hit = level.clip(new ClipContext(eye, eye.add(look.scale(REACH + 0.5)), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
		if (hit.getType() != HitResult.Type.MISS) return hit;
		Vec3 ahead = eye.add(look.scale(REACH));
		BlockHitResult ground = level.clip(new ClipContext(ahead, ahead.add(0, -DROP - player.getEyeHeight(), 0), ClipContext.Block.COLLIDER,
				ClipContext.Fluid.NONE, player));
		return ground.getType() == HitResult.Type.MISS ? null : ground;
	}

	/**
	 * The wall rule: a wall is a side face, or a block with another solid block on top of it (so the hammer would
	 * hit a step in a wall from the side rather than land on it).
	 */
	public static boolean wall(ServerLevel level, BlockPos block, Direction face) {
		if (face.getAxis().isHorizontal()) return true;
		if (face != Direction.UP) return false;
		BlockPos above = block.above();
		return !level.getBlockState(above).getCollisionShape(level, above).isEmpty();
	}

	/** Right-click tapped in Hammer mode, held for {@code held} ticks: the hammer forms and swings. */
	public static void start(ServerPlayer player, int held) {
		if (swinging(player) || player.isSpectator()) return;
		ServerLevel level = player.level();
		Corps corps = Corps.of(RingFlight.findRing(player));
		Vec3 look = player.getLookAngle();
		Vec3 forward = new Vec3(look.x, 0, look.z);
		forward = forward.lengthSqr() < 1e-4 ? Vec3.directionFromRotation(0, player.getYRot()) : forward.normalize();
		BlockHitResult hit = target(level, player);
		Vec3 at;
		BlockPos block = null;
		Direction face = null;
		int variant = -1;
		if (hit != null) {
			at = hit.getLocation();
			block = hit.getBlockPos();
			face = hit.getDirection();
			variant = face.get3DDataValue() + (wall(level, block, face) ? 8 : 0);
		} else {
			at = player.getEyePosition().add(look.scale(REACH));
		}
		int since = Mth.clamp(held, 0, FORM - 1);
		STRIKES.put(player.getUUID(), new Strike(level, player, at, forward, block, face, corps, CombatMoves.now() + HIT - since));
		WhatsNew.done(player, "mode.hammer.swing");
		Corps before = Corps.enter(corps);
		try {
			// Every client draws the hammer forming and swinging, timed from the press (value: ticks since it).
			CombatMoves.send(level, Kind.HAMMER_FORM, at, at.add(forward), since, variant, player, -1);
		} finally {
			Corps.restore(before);
		}
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 0.6f, 1.6f);
	}

	static void tick(MinecraftServer server) {
		int now = CombatMoves.now();
		for (Iterator<Strike> it = STRIKES.values().iterator(); it.hasNext(); ) {
			Strike s = it.next();
			if (!s.owner().isAlive() || s.owner().level() != s.level()) {
				it.remove();
				continue;
			}
			if (now < s.hitAt()) continue;
			if (now > s.hitAt() + RingTuning.HAMMER_LINGER.ticks()) {
				it.remove();
				continue;
			}
			if (now != s.hitAt()) continue;
			Corps before = Corps.enter(s.corps());
			try {
				hit(s);
			} finally {
				Corps.restore(before);
			}
		}
	}

	/** The hammer lands: the crater on the face it hit, the shockwave, and every mob at the hit knocked away. */
	private static void hit(Strike s) {
		ServerLevel level = s.level();
		Vec3 at = s.at();
		if (s.block() != null && s.face() != null) {
			for (int[] c : FlyingFlurries.craterCells(s.face())) CombatMoves.clear(level, s.owner(), s.block().offset(c[0], c[1], c[2]), c[4]);
			BlockState state = level.getBlockState(s.block());
			if (!state.isAir()) {
				level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, state), at.x, at.y, at.z, 50, 0.8, 0.5, 0.8, 0.3);
			}
		}
		Vec3 n = s.face() == null ? new Vec3(0, 1, 0) : new Vec3(s.face().getStepX(), s.face().getStepY(), s.face().getStepZ());
		CombatMoves.send(level, Kind.HAMMER_HIT, at, at.add(n), 0f, s.face() == null ? -1 : s.face().get3DDataValue(), s.owner(), -1);
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(at, at).inflate(CATCH, 2, CATCH),
				e -> e != s.owner() && e.isAlive() && !e.isSpectator() && !CombatMoves.spared(e, s.owner()))) {
			if (!(e instanceof Player other && other.isCreative())) {
				e.hurtServer(level, level.damageSources().indirectMagic(s.owner(), s.owner()), DAMAGE);
			}
			e.setDeltaMovement(s.forward().x * 0.55, 0.5, s.forward().z * 0.55);
			RingPowers.syncVelocity(e);
		}
		level.sendParticles(ModParticles.of(ModParticles.SHARD, s.corps()), at.x, at.y + 0.2, at.z, 14, 0.8, 0.2, 0.8, 0.25);
		level.playSound(null, at.x, at.y, at.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.PLAYERS, 1.6f, 0.7f);
		level.playSound(null, at.x, at.y, at.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1f, 0.6f);
	}
}
