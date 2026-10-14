package com.sparky.lanternring;

import com.sparky.lanternring.net.CombatFxPayload.Kind;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
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
 * J's flying flurry (Blender pass 509, F2 picked: jab, cross, spinning backfist). A melee hit on a living mob while
 * ring-flying starts the string, which then plays by itself at the Blender's timings: the hit is the jab, the cross
 * lands RingTuning flurry_cross later (5 ticks) and the spinning backfist flurry_backfist after the jab (12).
 * <ul>
 * <li>From the first hit the target is carried 1.7 blocks in front of you, nudged 0.25 to 0.3 blocks the way each
 * punch goes (the local client slows you to 10 blocks a second meanwhile and eases you to a hover after the
 * backfist, CombatInput).
 * <li>The backfist launches it at 2.4 blocks a tick along the angle of the hit (where you look), gravity 0.03 a tick,
 * drag 0.99, tumbling (drawn by each client).
 * <li>Whatever it hits first craters: a block takes a 3x3 crater across the face it hit (D0 rule: ring d lights at
 * tick d and is gone at 4 + 2d) with an impact ring and dirt, and it sticks in there; a mob in the way is
 * knocked along and both are hurt.
 * <li>50 blocks with no hit: it regains control, stops tumbling, rights itself, brakes and drops onto its feet.
 * </ul>
 */
public final class FlyingFlurries {
	/** How far ahead of you the target is carried, and each punch's nudge (jab, cross, backfist). */
	public static final double CARRY = 1.7;
	private static final double[] NUDGE = {0.25, 0.3, 0.28};
	/** The cross's and backfist's damage (the jab is the hit that started it). */
	private static final float CROSS_DAMAGE = 5f, BACKFIST_DAMAGE = 7f, IMPACT_DAMAGE = 10f;
	/** The launch: blocks a tick, gravity and drag per tick, and the flight before it regains control. */
	public static final double LAUNCH_SPEED = 2.4, GRAVITY = 0.03, DRAG = 0.99, REGAIN_AFTER = 50;
	/** The longest a string or a launch is followed, in ticks. */
	private static final int MAX_STRING = 40, MAX_FLIGHT = 80, SOFT_LANDING = 100;

	private static final class Flurry {
		final ServerLevel level;
		final LivingEntity target;
		final Corps corps;
		final boolean hadGravity;
		Vec3 nudge = Vec3.ZERO;
		int t;
		boolean crossed;

		Flurry(ServerLevel level, LivingEntity target, Corps corps) {
			this.level = level;
			this.target = target;
			this.corps = corps;
			this.hadGravity = !target.isNoGravity();
		}
	}

	private static final class Flight {
		final ServerLevel level;
		final LivingEntity target;
		final ServerPlayer owner;
		final Corps corps;
		final boolean hadGravity;
		Vec3 pos, vel;
		double travelled;
		int t;

		Flight(ServerLevel level, LivingEntity target, ServerPlayer owner, Corps corps, Vec3 vel, boolean hadGravity) {
			this.level = level;
			this.target = target;
			this.owner = owner;
			this.corps = corps;
			this.pos = target.position();
			this.vel = vel;
			this.hadGravity = hadGravity;
		}
	}

	private static final Map<UUID, Flurry> FLURRIES = new HashMap<>();
	private static final Map<Integer, Flight> FLIGHTS = new HashMap<>();
	/** Targets that regained control: no fall damage until this tick, so they land on their feet. */
	private static final Map<LivingEntity, Integer> SOFT = new HashMap<>();

	private FlyingFlurries() {
	}

	static void register() {
		AttackEntityCallback.EVENT.register((player, level, hand, entity, hit) -> {
			if (!level.isClientSide() && player instanceof ServerPlayer p && entity instanceof LivingEntity target) start(p, target);
			return InteractionResult.PASS;
		});
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
			Flurry f = FLURRIES.remove(handler.player.getUUID());
			if (f != null && f.hadGravity) f.target.setNoGravity(false);
		});
	}

	/** Whether this player is in a flying flurry's string right now. */
	public static boolean inString(Player player) {
		return FLURRIES.containsKey(player.getUUID());
	}

	/** A melee hit: starts the string if they're ring-flying and the target is free. */
	static void start(ServerPlayer p, LivingEntity target) {
		if (!p.getAbilities().flying || p.isSpectator() || CombatMoves.chargedRing(p).isEmpty()) return;
		if (FLURRIES.containsKey(p.getUUID()) || FLIGHTS.containsKey(target.getId()) || target instanceof Player || !target.isAlive()
				|| CombatMoves.spared(target, p)) return;
		for (Flurry other : FLURRIES.values()) if (other.target == target) return;
		Corps corps = Corps.of(CombatMoves.chargedRing(p));
		Flurry f = new Flurry(p.level(), target, corps);
		target.setNoGravity(true);
		FLURRIES.put(p.getUUID(), f);
		punch(p, f, 0);
	}

	/** Punch i (0 jab, 1 cross, 2 backfist) lands: nudged the way it goes, and every client sees it. */
	private static void punch(ServerPlayer p, Flurry f, int i) {
		Vec3 look = p.getLookAngle();
		Vec3 side = look.cross(new Vec3(0, 1, 0));
		side = side.lengthSqr() < 1e-4 ? Vec3.ZERO : side.normalize();
		// The jab goes straight, the cross comes across from the ring side, the backfist sweeps back the other way.
		Vec3 way = i == 0 ? look : i == 1 ? look.add(side.scale(-0.35)).normalize() : look.add(side.scale(0.35)).normalize();
		f.nudge = f.nudge.add(way.scale(NUDGE[i]));
		if (i == 1) f.target.hurtServer(f.level, f.level.damageSources().playerAttack(p), CROSS_DAMAGE);
		Vec3 at = f.target.getBoundingBox().getCenter();
		Corps before = Corps.enter(f.corps);
		try {
			CombatMoves.send(f.level, Kind.FLURRY_HIT, at, at.add(way), 0f, i, p, f.target.getId());
			f.level.sendParticles(ModParticles.of(ModParticles.SPARK, f.corps), at.x, at.y, at.z, 4 + 4 * i, 0.15, 0.15, 0.15, 0.2);
		} finally {
			Corps.restore(before);
		}
		f.level.playSound(null, at.x, at.y, at.z, i == 2 ? SoundEvents.PLAYER_ATTACK_CRIT : SoundEvents.PLAYER_ATTACK_STRONG, SoundSource.PLAYERS,
				1f, 0.8f + 0.15f * i);
	}

	private static void backfist(ServerPlayer p, Flurry f) {
		punch(p, f, 2);
		f.target.hurtServer(f.level, f.level.damageSources().playerAttack(p), BACKFIST_DAMAGE);
		if (!f.target.isAlive()) {
			if (f.hadGravity) f.target.setNoGravity(false);
			return;
		}
		Vec3 vel = p.getLookAngle().scale(LAUNCH_SPEED);
		Flight flight = new Flight(f.level, f.target, p, f.corps, vel, f.hadGravity);
		FLIGHTS.put(f.target.getId(), flight);
		Corps before = Corps.enter(f.corps);
		try {
			CombatMoves.send(f.level, Kind.FLURRY_LAUNCH, flight.pos, flight.pos.add(vel), (float) LAUNCH_SPEED, 0, p, f.target.getId());
		} finally {
			Corps.restore(before);
		}
		f.level.playSound(null, flight.pos.x, flight.pos.y, flight.pos.z, SoundEvents.MACE_SMASH_AIR, SoundSource.PLAYERS, 1.2f, 0.7f);
	}

	static void tick(MinecraftServer server) {
		int now = CombatMoves.now();
		for (Iterator<Map.Entry<UUID, Flurry>> it = FLURRIES.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<UUID, Flurry> e = it.next();
			Flurry f = e.getValue();
			ServerPlayer p = server.getPlayerList().getPlayer(e.getKey());
			f.t++;
			if (p == null || !p.isAlive() || p.level() != f.level || !f.target.isAlive() || f.target.isRemoved() || f.t > MAX_STRING
					|| p.distanceTo(f.target) > 8) {
				if (f.hadGravity) f.target.setNoGravity(false);
				it.remove();
				continue;
			}
			// Carried in front of you, where the punches have nudged it.
			Vec3 hold = p.getEyePosition().add(p.getLookAngle().scale(CARRY)).add(f.nudge).subtract(0, f.target.getBbHeight() / 2, 0);
			Vec3 move = hold.subtract(f.target.position());
			f.target.teleportTo(hold.x, hold.y, hold.z);
			f.target.setDeltaMovement(move);
			f.target.resetFallDistance();
			RingPowers.syncVelocity(f.target);
			if (!f.crossed && f.t >= RingTuning.FLURRY_CROSS.ticks()) {
				f.crossed = true;
				punch(p, f, 1);
			}
			if (f.t >= Math.max(RingTuning.FLURRY_BACKFIST.ticks(), RingTuning.FLURRY_CROSS.ticks() + 1)) {
				it.remove();
				backfist(p, f);
			}
		}
		for (Iterator<Flight> it = FLIGHTS.values().iterator(); it.hasNext(); ) {
			Flight f = it.next();
			if (!f.target.isAlive() || f.target.isRemoved() || f.target.level() != f.level) {
				it.remove();
				continue;
			}
			if (fly(f)) {
				it.remove();
				if (f.hadGravity) f.target.setNoGravity(false);
			}
		}
		SOFT.entrySet().removeIf(e -> {
			e.getKey().resetFallDistance();
			return now > e.getValue() || !e.getKey().isAlive() || e.getKey().onGround() && now > e.getValue() - SOFT_LANDING + 10;
		});
	}

	/** One tick of the launch; true once it's over (cratered, hit a mob, or regained control). */
	private static boolean fly(Flight f) {
		f.t++;
		Vec3 half = new Vec3(0, f.target.getBbHeight() / 2, 0);
		Vec3 from = f.pos.add(half), to = from.add(f.vel);
		BlockHitResult block = f.level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, f.target));
		double reach = block.getType() == HitResult.Type.MISS ? f.vel.length() : block.getLocation().distanceTo(from);
		LivingEntity hit = null;
		double best = reach;
		AABB sweep = f.target.getBoundingBox().expandTowards(f.vel).inflate(0.5);
		for (LivingEntity e : f.level.getEntitiesOfClass(LivingEntity.class, sweep,
				e -> e != f.target && e != f.owner && e.isAlive() && !e.isSpectator() && !CombatMoves.spared(e, f.owner))) {
			Optional<Vec3> at = e.getBoundingBox().inflate(f.target.getBbWidth() / 2).clip(from, to);
			if (at.isPresent() && at.get().distanceTo(from) < best) {
				best = at.get().distanceTo(from);
				hit = e;
			}
		}
		Corps before = Corps.enter(f.corps);
		try {
			if (hit != null) {
				Vec3 at = from.add(f.vel.normalize().scale(best));
				f.target.teleportTo(at.x - half.x, at.y - half.y, at.z - half.z);
				var source = f.level.damageSources().playerAttack(f.owner);
				hit.hurtServer(f.level, source, IMPACT_DAMAGE);
				f.target.hurtServer(f.level, source, IMPACT_DAMAGE * 0.6f);
				Vec3 push = f.vel.normalize().scale(0.9);
				hit.setDeltaMovement(push.x, Math.max(0.3, push.y), push.z);
				RingPowers.syncVelocity(hit);
				f.target.setDeltaMovement(f.vel.scale(0.1));
				RingPowers.syncVelocity(f.target);
				CombatMoves.send(f.level, Kind.FLURRY_IMPACT, at, at.subtract(f.vel.normalize()), 0f, -1, f.owner, f.target.getId());
				f.level.playSound(null, at.x, at.y, at.z, SoundEvents.MACE_SMASH_GROUND, SoundSource.PLAYERS, 1.2f, 0.8f);
				return true;
			}
			if (block.getType() != HitResult.Type.MISS) {
				crater(f, block);
				return true;
			}
			f.pos = to.subtract(half);
			f.travelled += f.vel.length();
			f.vel = f.vel.scale(DRAG).subtract(0, GRAVITY, 0);
			f.target.teleportTo(f.pos.x, f.pos.y, f.pos.z);
			f.target.setDeltaMovement(f.vel);
			f.target.resetFallDistance();
			RingPowers.syncVelocity(f.target);
			if (f.t % 2 == 0) f.level.sendParticles(ModParticles.of(ModParticles.MOTE, f.corps), from.x, from.y, from.z, 2, 0.2, 0.2, 0.2, 0.01);
			if (f.travelled >= REGAIN_AFTER || f.t > MAX_FLIGHT) {
				// Nothing hit in 50 blocks: it rights itself, brakes and drops onto its feet.
				f.target.setDeltaMovement(f.vel.scale(0.15));
				RingPowers.syncVelocity(f.target);
				SOFT.put(f.target, CombatMoves.now() + SOFT_LANDING);
				CombatMoves.send(f.level, Kind.FLURRY_REGAIN, f.pos, f.pos.add(f.vel), 0f, 0, f.owner, f.target.getId());
				return true;
			}
			return false;
		} finally {
			Corps.restore(before);
		}
	}

	/** It hit a block: a 3x3 crater across that face (D0 rule), stuck in at that angle. */
	private static void crater(Flight f, BlockHitResult block) {
		Vec3 at = block.getLocation();
		Direction face = block.getDirection();
		Vec3 half = new Vec3(0, f.target.getBbHeight() / 2, 0);
		Vec3 rest = at.subtract(f.vel.normalize().scale(0.2)).subtract(half);
		f.target.teleportTo(rest.x, rest.y, rest.z);
		f.target.setDeltaMovement(Vec3.ZERO);
		RingPowers.syncVelocity(f.target);
		f.target.hurtServer(f.level, f.level.damageSources().playerAttack(f.owner), IMPACT_DAMAGE);
		BlockPos centre = block.getBlockPos();
		for (int[] c : craterCells(face)) CombatMoves.clear(f.level, f.owner, centre.offset(c[0], c[1], c[2]), c[4]);
		BlockState state = f.level.getBlockState(centre);
		Vec3 n = new Vec3(face.getStepX(), face.getStepY(), face.getStepZ());
		CombatMoves.send(f.level, Kind.FLURRY_IMPACT, at, at.add(n), 0f, face.get3DDataValue(), f.owner, f.target.getId());
		if (!state.isAir()) {
			f.level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, state), at.x, at.y, at.z, 50, 0.8, 0.8, 0.8, 0.3);
		}
		f.level.playSound(null, at.x, at.y, at.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.PLAYERS, 1.5f, 0.7f);
		f.level.playSound(null, at.x, at.y, at.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 0.6f, 0.8f);
	}

	/**
	 * The 3x3 crater across a face: {dx, dy, dz, the tick it lights, the tick it's gone} for each block, D0 rule (ring
	 * d lights at tick d and is gone at 4 + 2d). Shared with every client's drawing.
	 */
	public static int[][] craterCells(@Nullable Direction face) {
		Direction.Axis axis = face == null ? Direction.Axis.Y : face.getAxis();
		int[][] out = new int[9][];
		int i = 0;
		for (int a = -1; a <= 1; a++) {
			for (int b = -1; b <= 1; b++) {
				int d = (int) Math.round(Math.sqrt(a * a + b * b));
				int dx = axis == Direction.Axis.X ? 0 : a;
				int dy = axis == Direction.Axis.Y ? 0 : axis == Direction.Axis.X ? a : b;
				int dz = axis == Direction.Axis.Z ? 0 : b;
				out[i++] = new int[] {dx, dy, dz, d, 4 + 2 * d};
			}
		}
		return out;
	}

	/** Whether this entity is flying from a backfist right now. */
	public static boolean launched(Entity e) {
		return FLIGHTS.containsKey(e.getId());
	}
}
