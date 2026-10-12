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
 * The Shield's reflection: every tick it's held, projectiles about to reach the panel in front of
 * the bearer (arrows, tridents, ghast and blaze fireballs, wither skulls, wind charges, shulker
 * bullets...) are turned around and sent back at whoever shot them, a little faster, with a flash
 * and a chime. The bearer then owns the shot, so it hurts the shooter and not them.
 */
public final class ShieldReflect {
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

	static void tick(ServerLevel level, ServerPlayer player) {
		Vec3 center = player.position().add(0, 1.0, 0);
		Vec3 look = player.getLookAngle();
		double reach = HeldConstructs.SHIELD_RADIUS + 1.5;
		AABB box = new AABB(center, center).inflate(reach + 8);
		for (Projectile shot : level.getEntitiesOfClass(Projectile.class, box, p -> incoming(p, player))) {
			Vec3 pos = shot.position();
			Vec3 v = shot.getDeltaMovement();
			Vec3 toShot = pos.subtract(center);
			double dist = toShot.length();
			if (dist < 0.5) continue;
			// Only shots coming from in front, within the panel's spread (with a little give at the edges).
			if (toShot.dot(look) / dist < HeldConstructs.SHIELD_COS - 0.15) continue;
			// Heading at the bearer, and inside the panel within the next few ticks.
			if (v.dot(toShot) >= 0) continue;
			if (closest(pos, v.scale(LOOKAHEAD), center) > reach) continue;
			reflect(level, player, shot, center, toShot.scale(1 / dist));
		}
	}

	private static boolean incoming(Projectile shot, ServerPlayer player) {
		if (!shot.isAlive() || shot instanceof FishingHook) return false;
		// Arrows stuck in the ground have stopped; leave those (and the bearer's own shots) alone.
		return shot.getOwner() != player && shot.getDeltaMovement().lengthSqr() > 0.0025;
	}

	/** Closest distance from {@code c} to the segment from {@code p} to {@code p + d}. */
	private static double closest(Vec3 p, Vec3 d, Vec3 c) {
		double len2 = d.lengthSqr();
		double t = len2 < 1e-6 ? 0 : Math.clamp(c.subtract(p).dot(d) / len2, 0, 1);
		return p.add(d.scale(t)).distanceTo(c);
	}

	private static void reflect(ServerLevel level, ServerPlayer player, Projectile shot, Vec3 center, Vec3 normal) {
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
			// No one to send it back to: bounce it off the panel like a mirror.
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
