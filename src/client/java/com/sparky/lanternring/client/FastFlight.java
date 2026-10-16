package com.sparky.lanternring.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;

/**
 * Sprint-flying with the ring steers like an elytra: you fly wherever you look, up and down
 * included, instead of staying on one level; jump tilts it up. Shift held while flying forward is hyper speed
 * (J, 2026-10-14): up to 50 blocks a second, with the sonic boom as it kicks in (FlightMoves). Left click in flight
 * no longer boosts (J removed pass 515 super speed, 2026-10-16). Slow flight keeps vanilla's level flying (jump to
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
	/** How far jump tilts the glide up off the look direction, as a vertical part added to it (about 31 degrees level). */
	private static final double TILT = 0.6;
	/** Hyper speed (shift held while flying forward, J 2026-10-14): its top speed in blocks a tick (50 b/s) and how fast it gets there. */
	private static final float HYPER_TOP = 2.5f, HYPER_ACCEL = 0.25f;

	private static boolean gliding, hyper;
	private static float speed;

	static void tick(Minecraft mc) {
		LocalPlayer p = mc.player;
		// The rocket takeoff and ground flight drive their own movement (FlightMoves).
		if (p == null || FlightMoves.controls() || CombatInput.controls() || !shouldGlide(mc, p)) {
			gliding = hyper = false;
			return;
		}
		hyper = mc.options.keyShift.isDown();
		Vec3 look = p.getLookAngle();
		// Jump still rises in the glide; to go down, look down (shift is hyper speed now).
		if (mc.options.keyJump.isDown()) look = new Vec3(look.x, look.y + TILT, look.z).normalize();
		// Diving into the ground skims along it instead of grinding into it.
		if (p.verticalCollisionBelow && look.y < 0) look = new Vec3(look.x, 0, look.z).normalize();
		if (!gliding) {
			gliding = true;
			speed = (float) p.getDeltaMovement().length();
		}
		// Vanilla sprint flight adds this much forward push per tick.
		float push = p.getAbilities().getFlyingSpeed() * 2;
		float top = hyper ? HYPER_TOP : push * DRAG / (1 - DRAG);
		speed += (top - speed) * (hyper ? HYPER_ACCEL : ACCEL);

		// Next tick vanilla adds its own forward push (and sneak's sink) before moving; take them out so the
		// whole move points along the look direction.
		Vec3 vanilla = FlightMoves.vanillaPush(mc, p);
		if (hyper) vanilla = vanilla.add(0, -p.getAbilities().getFlyingSpeed() * 3, 0);
		p.setDeltaMovement(look.scale(speed).subtract(vanilla));
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

	/** True in hyper speed: gliding with shift held. */
	public static boolean hyper() {
		return gliding && hyper;
	}

	/** True while the local player is in the ring glide, so walls and the ground don't end it. */
	public static boolean isGliding(LocalPlayer p) {
		return gliding && p.getAbilities().flying && Minecraft.getInstance().options.keyUp.isDown();
	}

	private static boolean shouldGlide(Minecraft mc, LocalPlayer p) {
		// Once gliding, touching the ground doesn't stop it; it only has to start in the air.
		boolean keys = (p.isSprinting() || mc.options.keyShift.isDown()) && mc.options.keyUp.isDown();
		return p.getAbilities().flying && keys
				&& (gliding || !p.onGround()) && !p.isInWater() && !p.isPassenger() && !p.isSpectator()
				&& FlightPoses.carriesRing(p);
	}

	private FastFlight() {
	}
}
