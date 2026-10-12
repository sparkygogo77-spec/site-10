package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.net.PlaceLanternPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.world.phys.HitResult;

/**
 * Setting the off-hand lantern down: double-click right-click on a block and hold the second click
 * for {@link RingTuning#LANTERN_PLACE_HOLD}. The second click (and the hold after it) is kept from
 * the ring, so the gesture doesn't fire a power too; every other click goes to the ring as normal.
 */
public final class LanternPlaceInput {
	private static int ticks;
	private static int lastPress = -1000;
	private static boolean wasDown;
	/** The current press is the second click of a double-click. */
	private static boolean armed;
	private static boolean placed;
	private static int held;

	private LanternPlaceInput() {
	}

	/**
	 * Called from Minecraft.startUseItem (see MinecraftMixin), which runs on a fresh right-click
	 * and every few ticks while it is held. Returns true to keep that use from the ring.
	 */
	public static boolean consumesUse(Minecraft mc) {
		if (mc.player == null || !LanternCharge.holdsBattery(mc.player)) return false;
		if (armed) return true;
		boolean fresh = !wasDown;
		boolean onBlock = mc.hitResult != null && mc.hitResult.getType() == HitResult.Type.BLOCK;
		if (!fresh) return false;
		if (onBlock && !mc.player.isShiftKeyDown() && ticks - lastPress <= RingTuning.LANTERN_DOUBLE_CLICK.ticks()) {
			// A third quick click starts over instead of counting as another double-click.
			lastPress = -1000;
			armed = true;
			placed = false;
			held = 0;
			return true;
		}
		lastPress = ticks;
		return false;
	}

	public static void tick(Minecraft mc) {
		ticks++;
		boolean down = mc.options.keyUse.isDown();
		if (mc.player == null || !LanternCharge.holdsBattery(mc.player)) {
			armed = false;
			wasDown = down;
			return;
		}
		if (armed) {
			if (!down) {
				armed = false;
			} else if (!placed && ++held >= Math.max(1, RingTuning.LANTERN_PLACE_HOLD.ticks())) {
				placed = true;
				if (ClientPlayNetworking.canSend(PlaceLanternPayload.TYPE)) ClientPlayNetworking.send(new PlaceLanternPayload());
			}
		}
		wasDown = down;
	}
}
