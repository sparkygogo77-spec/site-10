package com.sparky.lanternring.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;

/**
 * A damped pendulum for the lantern in your off hand: it swings back as you start walking, sideways
 * as you turn, and settles when you stop. Angles are in degrees, updated once per client tick and
 * interpolated when drawn.
 */
public final class LanternSway {
	/** Pull back toward hanging straight down, per tick. */
	public static float stiffness = 0.14f;
	/** Fraction of swing speed kept each tick. */
	public static float damping = 0.86f;

	private static float roll, rollO, rollV;
	private static float pitch, pitchO, pitchV;
	private static float lastYaw, lastPitch;
	private static Vec3 lastVelocity = Vec3.ZERO;
	private static boolean primed;

	private LanternSway() {
	}

	static void tick(Minecraft mc) {
		LocalPlayer p = mc.player;
		if (p == null || mc.isPaused()) {
			primed = false;
			return;
		}
		float yaw = p.getYRot();
		float lookPitch = p.getXRot();
		Vec3 velocity = p.getDeltaMovement();
		if (!primed) {
			lastYaw = yaw;
			lastPitch = lookPitch;
			lastVelocity = velocity;
			primed = true;
		}
		float dYaw = Mth.wrapDegrees(yaw - lastYaw);
		float dPitch = lookPitch - lastPitch;
		// Acceleration in the player's own frame: forward and to the right.
		Vec3 accel = velocity.subtract(lastVelocity);
		double rad = Math.toRadians(yaw);
		double forward = -accel.x * Math.sin(rad) + accel.z * Math.cos(rad);
		double rightward = -accel.x * Math.cos(rad) - accel.z * Math.sin(rad);
		double speed = velocity.horizontalDistance();

		rollO = roll;
		pitchO = pitch;
		rollV += -stiffness * roll + dYaw * 0.35f + (float) rightward * 90f;
		pitchV += -stiffness * pitch - (float) forward * 120f + dPitch * 0.15f
				+ (float) (Math.sin(p.tickCount * 0.65) * speed * 6);
		rollV *= damping;
		pitchV *= damping;
		roll = Mth.clamp(roll + rollV, -40f, 40f);
		pitch = Mth.clamp(pitch + pitchV, -40f, 40f);

		lastYaw = yaw;
		lastPitch = lookPitch;
		lastVelocity = velocity;
	}

	static float roll(float partialTick) {
		return Mth.lerp(partialTick, rollO, roll);
	}

	static float pitch(float partialTick) {
		return Mth.lerp(partialTick, pitchO, pitch);
	}
}
