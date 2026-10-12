package com.sparky.lanternring.client;

import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.AnvilInputPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.world.item.ItemStack;

/**
 * Anvil mode aims with left-click: while it's held, the server gets a tick every tick (it moves
 * the marker), and letting go drops the anvil. Left-clicking while right-click is held picks the
 * next size instead. Left-click doesn't mine or hit with the ring in Anvil mode (see MinecraftMixin).
 */
public final class AnvilInput {
	private static boolean wasHeld;
	private static boolean attackWasDown;

	private AnvilInput() {
	}

	/** The ring in the main hand is in Anvil mode, so left-click belongs to it. */
	public static boolean ownsLeftClick(Minecraft mc) {
		if (mc.player == null) return false;
		ItemStack stack = mc.player.getMainHandItem();
		return stack.getItem() instanceof PowerRingItem && PowerRingItem.getMode(stack) == RingMode.ANVIL;
	}

	public static void tick(Minecraft mc) {
		boolean attack = mc.options.keyAttack.isDown();
		boolean pressed = attack && !attackWasDown;
		attackWasDown = attack;
		boolean ours = mc.player != null && mc.mouseHandler.isMouseGrabbed() && ownsLeftClick(mc);
		boolean holdingRight = ours && mc.player.isUsingItem();
		boolean held = ours && attack && !holdingRight;
		if (!ClientPlayNetworking.canSend(AnvilInputPayload.TYPE)) {
			wasHeld = false;
			return;
		}
		if (holdingRight && pressed) {
			ClientPlayNetworking.send(new AnvilInputPayload(AnvilInputPayload.CYCLE));
		}
		if (held) {
			ClientPlayNetworking.send(new AnvilInputPayload(AnvilInputPayload.AIM));
		} else if (wasHeld) {
			ClientPlayNetworking.send(new AnvilInputPayload(AnvilInputPayload.RELEASE));
		}
		wasHeld = held;
	}
}
