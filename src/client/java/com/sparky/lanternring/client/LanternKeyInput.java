package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternSlot;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.net.LanternKeyPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;

/**
 * The lantern key (R, see LanternSlot). Crouch + R summons the lantern (stowing a held one first) or
 * dismisses it. With it summoned, holding R alone for {@link RingTuning#LANTERN_POWER_HOLD} sets off
 * its corps' power; a plain tap does nothing, so the lantern is never let go by accident.
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
			letGo();
			return;
		}
		boolean crouch = mc.player.isShiftKeyDown();
		if (pressed && held < 0) {
			// With a 1911 in hand, R reloads it at once (the server sees the pistol and reloads).
			// Crouch + R summons or dismisses the lantern; a plain R never lets it go (J, 2026-10-13).
			if (crouch || mc.player.getMainHandItem().getItem() instanceof com.sparky.lanternring.item.Pistol1911Item) {
				send(crouch, false, false);
			} else if (LanternSlot.out(mc.player)) {
				// Held with it summoned: its corps' power.
				held = 0;
				powered = false;
			}
			return;
		}
		if (held < 0) return;
		if (key.isDown()) {
			if (!powered && ++held >= Math.max(1, RingTuning.LANTERN_POWER_HOLD.ticks())) {
				powered = true;
				send(false, true, false);
			}
		} else {
			letGo();
		}
	}

	/** The key is up: a power that lasts while held (the Green fortress) ends. */
	private static void letGo() {
		if (held >= 0 && powered) send(false, false, true);
		held = -1;
		powered = false;
	}

	private static void send(boolean crouch, boolean power, boolean release) {
		if (ClientPlayNetworking.canSend(LanternKeyPayload.TYPE)) ClientPlayNetworking.send(new LanternKeyPayload(crouch, power, release));
	}
}
