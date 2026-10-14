package com.sparky.lanternring.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;

/**
 * Sprint-flying with the ring steers like an elytra: you fly wherever you look, up and down
 * included, instead of staying on one level. Slow flight keeps vanilla's level flying (jump to
 * rise, sneak to sink). Player movement is client-side, so this only touches the local player.
 *
 * Unlike an elytra, bumping into things doesn't end the glide: it slides along walls and skims
 * over the ground (see LocalPlayerMixin). You land by letting go of sprint or forward and
 * touching down in slow flight, or by switching flight off.
 */
public final class FastFlight {
	/** Vanilla flight keeps 91% of horizontal speed each tick; the glide settles where input refills that. */
	private static final float DRAG = 0.91f;
	/** How quickly the glide speed reaches its top speed (or slows to it). */
	private static final float ACCEL = 0.12f;

	private static boolean gliding;
	private static float speed;

	static void tick(Minecraft mc) {
		LocalPlayer p = mc.player;
		// The rocket takeoff and ground flight drive their own movement (FlightMoves).
		if (p == null || FlightMoves.controls() || CombatInput.controls() || !shouldGlide(mc, p)) {
			gliding = false;
			return;
		}
		Vec3 look = p.getLookAngle();
		// Diving into the ground skims along it instead of grinding into it.
		if (p.verticalCollisionBelow && look.y < 0) look = new Vec3(look.x, 0, look.z).normalize();
		if (!gliding) {
			gliding = true;
			speed = (float) p.getDeltaMovement().length();
		}
		// Vanilla sprint flight adds this much forward push per tick.
		float push = p.getAbilities().getFlyingSpeed() * 2;
		float top = push * DRAG / (1 - DRAG);
		speed += (top - speed) * ACCEL;

		// Next tick vanilla adds its own level forward push before moving; take it out so the
		// whole move points along the look direction.
		float yaw = p.getYRot() * Mth.DEG_TO_RAD;
		Vec3 vanillaPush = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw)).scale(push);
		p.setDeltaMovement(look.scale(speed).subtract(vanillaPush));
	}

	/** The ram barrier hit a wall: the glide stops dead and has to build up again from nothing. */
	public static void stop(LocalPlayer p) {
		speed = 0;
		p.setDeltaMovement(Vec3.ZERO);
	}

	/** The glide's speed in blocks a tick (its top is about 1.62); 0 when not gliding. */
	public static float speed() {
		return gliding ? speed : 0f;
	}

	/** True while the local player is in the ring glide, so walls and the ground don't end it. */
	public static boolean isGliding(LocalPlayer p) {
		return gliding && p.getAbilities().flying && Minecraft.getInstance().options.keyUp.isDown();
	}

	private static boolean shouldGlide(Minecraft mc, LocalPlayer p) {
		// Once gliding, touching the ground doesn't stop it; it only has to start in the air.
		return p.getAbilities().flying && p.isSprinting() && mc.options.keyUp.isDown()
				&& (gliding || !p.onGround()) && !p.isInWater() && !p.isPassenger() && !p.isSpectator()
				&& FlightPoses.carriesRing(p);
	}

	private FastFlight() {
	}
}
