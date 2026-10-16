package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternCharge;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.phys.Vec3;

/**
 * Holds you where the charge began until it's over (J, 2026-10-16: walking away mid-charge stretched and broke the
 * charge animations). Letting go of the clicks still ends the charge and frees you straight away.
 */
public final class ChargeLock {
	/** Where you stood when the ring started charging, or null when not locked. */
	private static Vec3 at;

	private ChargeLock() {
	}

	public static void tick(Minecraft mc) {
		LocalPlayer player = mc.player;
		float t = LanternFirstPerson.held(0f);
		if (player == null || t < LanternCharge.hold() || t >= LanternCharge.done() + LanternCharge.SETTLE) {
			at = null;
			return;
		}
		if (at == null) at = player.position();
		boolean flying = player.getAbilities().flying;
		// Standing, gravity still settles you onto the ground; flying, you hang in the air where you stopped.
		double y = flying ? at.y : player.getY();
		if (player.position().distanceToSqr(at.x, y, at.z) > 1.0e-6) player.setPos(at.x, y, at.z);
		Vec3 v = player.getDeltaMovement();
		player.setDeltaMovement(0, flying ? 0 : Math.min(v.y, 0), 0);
	}

	/** True while the charge holds you in place. */
	public static boolean locked() {
		return at != null;
	}
}
