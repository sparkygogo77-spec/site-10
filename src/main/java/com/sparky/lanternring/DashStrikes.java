package com.sparky.lanternring;

import com.sparky.lanternring.net.CombatFxPayload.Kind;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;

/**
 * J's dash strike (Blender pass 505, R3a-3 picked: the flying ring fist) and the ring-hand punch (pass 502). Player
 * movement is client side, so the local client (CombatInput) dashes: left click on a mob out of reach (up to 6.5
 * blocks) leans for RingTuning dash_windup, covers up to 4 blocks in dash_time (3 ticks, 27 blocks a second) and the
 * ring fist lands as the dash ends. The server checks it, hurts and knocks the target away, and tells every client
 * to draw it (the pose, the afterimages, the flash and pixels at the hit). A plain punch is only passed on, for
 * everyone else to draw the viewer's Ring Lab punch.
 */
public final class DashStrikes {
	/** The ring fist's damage, and the knock: blocks a tick forward and up (Blender: 0.75 along, 0.5 up). */
	private static final float DAMAGE = 7f;
	private static final double KNOCK = 0.75, KNOCK_UP = 0.45;
	/** How near the target the dash has to end (blocks, eyes to its middle), and how long after the dash the hit may come. */
	private static final double HIT_REACH = 4.5;
	private static final int HIT_WINDOW = 30;
	/** A dash may start this far from the target at most (CombatInput's 6.5, with room for lag). */
	private static final double START_REACH = 9;
	/** Punches passed on at most this often per player (ticks). */
	private static final int PUNCH_EVERY = 3;

	private record Dash(int target, int at) {
	}

	private static final Map<UUID, Dash> DASHES = new HashMap<>();
	private static final Map<UUID, Integer> PUNCHED = new HashMap<>();

	private DashStrikes() {
	}

	/** Left click with the ring hand: everyone else draws the punch. */
	static void punch(ServerPlayer p) {
		if (p.isSpectator() || !(RingSlot.ring(p).getItem() instanceof com.sparky.lanternring.item.PowerRingItem)) return;
		int now = CombatMoves.now();
		Integer last = PUNCHED.get(p.getUUID());
		if (last != null && now - last < PUNCH_EVERY && now >= last) return;
		PUNCHED.put(p.getUUID(), now);
		WhatsNew.done(p, "combat.punch");
		Vec3 eye = p.getEyePosition();
		Corps before = Corps.enter(Corps.of(RingSlot.ring(p)));
		try {
			CombatMoves.send(p.level(), Kind.PUNCH, eye, eye.add(p.getLookAngle()), 0f, 0, p, -1);
		} finally {
			Corps.restore(before);
		}
	}

	/** The dash leaves "at" with this move per tick, at the mob with this id. */
	static void dash(ServerPlayer p, Vec3 at, Vec3 step, int targetId) {
		if (p.isSpectator() || CombatMoves.chargedRing(p).isEmpty()) return;
		ServerLevel level = p.level();
		if (!(level.getEntity(targetId) instanceof LivingEntity target) || !target.isAlive() || target == p
				|| p.getEyePosition().distanceTo(target.getBoundingBox().getCenter()) > START_REACH) return;
		DASHES.put(p.getUUID(), new Dash(targetId, CombatMoves.now()));
		Vec3 end = at.add(step.scale(Math.max(1, RingTuning.DASH_TIME.ticks())));
		Corps before = Corps.enter(Corps.of(CombatMoves.chargedRing(p)));
		try {
			CombatMoves.send(level, Kind.DASH, at, end, 0f, 0, p, targetId);
		} finally {
			Corps.restore(before);
		}
		level.playSound(null, at.x, at.y, at.z, SoundEvents.MACE_SMASH_AIR, SoundSource.PLAYERS, 0.8f, 1.4f);
	}

	/** The dash ended at "at": the ring fist lands, if the target is still there. */
	static void hit(ServerPlayer p, Vec3 at, int targetId) {
		Dash d = DASHES.remove(p.getUUID());
		if (d == null || d.target() != targetId || CombatMoves.now() - d.at() > HIT_WINDOW) return;
		ServerLevel level = p.level();
		if (!(level.getEntity(targetId) instanceof LivingEntity target) || !target.isAlive()) return;
		Vec3 mid = target.getBoundingBox().getCenter();
		if (p.getEyePosition().distanceTo(mid) > HIT_REACH + target.getBbWidth() / 2) return;
		if (CombatMoves.spared(target, p)) return;
		Vec3 way = mid.subtract(p.getEyePosition());
		way = new Vec3(way.x, 0, way.z);
		way = way.lengthSqr() < 1e-6 ? p.getLookAngle() : way.normalize();
		Corps before = Corps.enter(Corps.of(RingSlot.ring(p)));
		try {
			target.hurtServer(level, level.damageSources().playerAttack(p), DAMAGE);
			WhatsNew.done(p, "combat.dash_strike");
			if (target.isAlive()) {
				target.setDeltaMovement(way.x * KNOCK, KNOCK_UP, way.z * KNOCK);
				RingPowers.syncVelocity(target);
			}
			CombatMoves.send(level, Kind.DASH_HIT, mid, mid.add(way), 0f, 0, p, targetId);
		} finally {
			Corps.restore(before);
		}
		level.playSound(null, mid.x, mid.y, mid.z, SoundEvents.PLAYER_ATTACK_STRONG, SoundSource.PLAYERS, 1.1f, 0.85f);
	}
}
