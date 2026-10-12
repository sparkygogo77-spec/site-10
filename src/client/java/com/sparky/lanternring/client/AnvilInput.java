package com.sparky.lanternring.client;

import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.AnvilInputPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.world.item.ItemStack;

/**
 * Anvil mode aims with left-click: while it's held, the server gets a tick every tick (it moves
 * the marker), and letting go drops the anvil. Left-click doesn't mine or hit with the ring in
 * Anvil mode (see MinecraftMixin).
 */
public final class AnvilInput {
	private static boolean wasHeld;

	private AnvilInput() {
	}

	/** The ring in the main hand is in Anvil mode, so left-click belongs to it. */
	public static boolean ownsLeftClick(Minecraft mc) {
		if (mc.player == null) return false;
		ItemStack stack = mc.player.getMainHandItem();
		return stack.getItem() instanceof PowerRingItem && PowerRingItem.getMode(stack) == RingMode.ANVIL;
	}

	public static void tick(Minecraft mc) {
		boolean held = mc.player != null && mc.mouseHandler.isMouseGrabbed() && mc.options.keyAttack.isDown()
				&& !mc.player.isUsingItem() && ownsLeftClick(mc);
		if (!ClientPlayNetworking.canSend(AnvilInputPayload.TYPE)) {
			wasHeld = false;
			return;
		}
		if (held) {
			ClientPlayNetworking.send(new AnvilInputPayload(true));
		} else if (wasHeld) {
			ClientPlayNetworking.send(new AnvilInputPayload(false));
		}
		wasHeld = held;
	}
}
