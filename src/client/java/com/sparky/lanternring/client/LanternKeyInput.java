package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternSlot;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.net.LanternKeyPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;

/**
 * The lantern key (R, see LanternSlot). With no lantern summoned a press acts at once: it stows a
 * held lantern and summons it (crouching: hands it back). With it summoned, a tap dismisses it and
 * holding for {@link RingTuning#LANTERN_POWER_HOLD} sets off its corps' power instead.
 */
public final class LanternKeyInput {
	/** Ticks the key has been held with the lantern out, or -1 when it isn't being timed. */
	private static int held = -1;
	private static boolean powered;

	private LanternKeyInput() {
	}

	public static void tick(Minecraft mc, KeyMapping key) {
		boolean pressed = false;
		while (key.consumeClick()) pressed = true;
		if (mc.player == null || mc.gui.screen() != null) {
			held = -1;
			return;
		}
		boolean crouch = mc.player.isShiftKeyDown();
		if (pressed && held < 0) {
			// With a 1911 in hand, R reloads it at once (the server sees the pistol and reloads).
			if (!LanternSlot.out(mc.player) || crouch || mc.player.getMainHandItem().getItem() instanceof com.sparky.lanternring.item.Pistol1911Item) {
				send(crouch, false);
			} else {
				held = 0;
				powered = false;
			}
			return;
		}
		if (held < 0) return;
		if (key.isDown()) {
			if (!powered && ++held >= Math.max(1, RingTuning.LANTERN_POWER_HOLD.ticks())) {
				powered = true;
				send(false, true);
			}
		} else {
			if (!powered) send(false, false);
			held = -1;
		}
	}

	private static void send(boolean crouch, boolean power) {
		if (ClientPlayNetworking.canSend(LanternKeyPayload.TYPE)) ClientPlayNetworking.send(new LanternKeyPayload(crouch, power));
	}
}
