package com.sparky.lanternring;

import com.sparky.lanternring.mixin.ShulkerBulletAccessor;
import com.sparky.lanternring.net.RingFxPayload;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityReference;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.FishingHook;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.entity.projectile.ShulkerBullet;
import net.minecraft.world.entity.projectile.arrow.AbstractArrow;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * The Shield: a flat riot shield of hard light held upright in front of the bearer, body height,
 * with angled shoulders and a tapered foot (clients draw it, see RiotShields; it places no
 * blocks). Every tick it's held, projectiles about to hit it (arrows, tridents, ghast and blaze
 * fireballs, wither skulls, wind charges, shulker bullets...) are turned around and sent back at
 * whoever shot them, a little faster, with a flash and a chime. The bearer then owns the shot, so
 * it hurts the shooter and not them.
 */
public final class ShieldReflect {
	/** How far in front of the bearer's feet the shield stands, in blocks. */
	public static final double DISTANCE = 0.9;
	/**
	 * The shield's outline, bottom to top: {height above the feet, half its width there}. Between
	 * rows the edge runs straight, so this gives the tapered foot, the notched shoulders and the
	 * clipped top corners.
	 */
	public static final double[][] OUTLINE = {
			{0.15, 0.52},
			{0.40, 0.70},
			{1.55, 0.70},
			{1.70, 0.52},
			{2.40, 0.52},
			{2.60, 0.38},
	};
	/** Extra reach around the outline for catching shots, so near misses at the edge still bounce. */
	private static final double MARGIN = 0.35;
	/** How far ahead to look for incoming shots, in ticks, so fast arrows can't slip through between checks. */
	private static final int LOOKAHEAD = 2;
	/** Reflected shots come back this much faster. */
	private static final double SPEED_UP = 1.2;
	/** How far back a shooter can be and still be aimed at, in blocks. */
	private static final double AIM_RANGE = 64;
	/** Arrows and tridents fall this much per tick per tick (AbstractArrow's default gravity). */
	private static final double ARROW_GRAVITY = 0.05;

	private ShieldReflect() {
	}

	/** Which way a shield held by someone facing {@code yaw} (degrees) points, flat on the ground. */
	public static Vec3 facing(float yaw) {
		double r = Math.toRadians(yaw);
		return new Vec3(-Math.sin(r), 0, Math.cos(r));
	}

	/** Half the shield's width at {@code y} blocks above the feet, or -1 above or below it. */
	public static double halfWidth(double y) {
		if (y < OUTLINE[0][0] || y > OUTLINE[OUTLINE.length - 1][0]) return -1;
		for (int i = 1; i < OUTLINE.length; i++) {
			double[] a = OUTLINE[i - 1], b = OUTLINE[i];
			if (y <= b[0]) return a[1] + (b[1] - a[1]) * (y - a[0]) / (b[0] - a[0]);
		}
		return -1;
	}

	static void tick(ServerLevel level, ServerPlayer player) {
		Vec3 n = facing(player.getYRot());
		Vec3 side = new Vec3(-n.z, 0, n.x);
		Vec3 feet = player.position();
		Vec3 face = feet.add(n.scale(DISTANCE));
		AABB box = new AABB(face, face).inflate(10);
		for (Projectile shot : level.getEntitiesOfClass(Projectile.class, box, p -> incoming(p, player))) {
			Vec3 pos = shot.position().add(0, shot.getBbHeight() / 2, 0);
			Vec3 v = shot.getDeltaMovement();
			double closing = -v.dot(n);
			// Only shots heading into the shield's front.
			if (closing <= 1e-3) continue;
			double before = pos.subtract(face).dot(n);
			// Already well past it (it came round the side), or not reaching it within the lookahead.
			if (before < -0.6 || before - closing * LOOKAHEAD > 0.3) continue;
			// Where it crosses the shield's plane, in the shield's own coordinates.
			Vec3 hit = pos.add(v.scale(Math.max(0, before) / closing));
			double across = hit.subtract(face).dot(side);
			double up = hit.y - feet.y;
			double half = halfWidth(Math.clamp(up, OUTLINE[0][0], OUTLINE[OUTLINE.length - 1][0]));
			if (up < OUTLINE[0][0] - MARGIN || up > OUTLINE[OUTLINE.length - 1][0] + MARGIN) continue;
			if (Math.abs(across) > half + MARGIN) continue;
			reflect(level, player, shot, n);
		}
	}

	private static boolean incoming(Projectile shot, ServerPlayer player) {
		if (!shot.isAlive() || shot instanceof FishingHook) return false;
		// Arrows stuck in the ground have stopped; leave those (and the bearer's own shots) alone.
		return shot.getOwner() != player && shot.getDeltaMovement().lengthSqr() > 0.0025;
	}

	private static void reflect(ServerLevel level, ServerPlayer player, Projectile shot, Vec3 normal) {
		Entity shooter = shot.getOwner();
		Vec3 v = shot.getDeltaMovement();
		double speed = Math.max(0.8, v.length() * SPEED_UP);
		Vec3 out;
		if (shooter instanceof LivingEntity living && living.isAlive() && living.level() == level
				&& living.distanceTo(player) < AIM_RANGE) {
			// Straight back at the shooter's chest, aiming a little high for arrows so the drop lands on them.
			Vec3 target = living.position().add(0, living.getBbHeight() * 0.6, 0);
			Vec3 to = target.subtract(shot.position());
			if (shot instanceof AbstractArrow) {
				double ticks = to.length() / speed;
				to = to.add(0, 0.5 * ARROW_GRAVITY * ticks * ticks, 0);
			}
			out = to.normalize().scale(speed);
		} else {
			// No one to send it back to: bounce it off the shield like a mirror.
			out = v.subtract(normal.scale(2 * v.dot(normal))).normalize().scale(speed);
		}
		if (shot instanceof ShulkerBullet bullet) {
			// Shulker bullets home in on their target: turn them on the shulker that fired them,
			// heading the way they were sent until they pick their next turn.
			ShulkerBulletAccessor homing = (ShulkerBulletAccessor) bullet;
			homing.lanternring$setFinalTarget(shooter == null ? null : EntityReference.of(shooter));
			homing.lanternring$setFlightSteps(0);
			homing.lanternring$setTargetDeltaX(out.x);
			homing.lanternring$setTargetDeltaY(out.y);
			homing.lanternring$setTargetDeltaZ(out.z);
		}
		shot.setDeltaMovement(out);
		shot.setOwner(player);
		shot.needsSync = true;

		Vec3 at = shot.position();
		level.playSound(null, at.x, at.y, at.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.2f, 1.7f);
		level.playSound(null, at.x, at.y, at.z, SoundEvents.SHIELD_BLOCK, SoundSource.PLAYERS, 0.6f, 1.3f);
		RingFx.send(level, RingFxPayload.Kind.REFLECT, at);
	}
}
