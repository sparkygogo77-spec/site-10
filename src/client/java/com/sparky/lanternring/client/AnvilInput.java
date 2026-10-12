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
	/** Ticks into the current right-click hold when the Blast's level last changed (its charge restarts). */
	static int blastRestart;

	private AnvilInput() {
	}

	/** The ring in the main hand is in Anvil mode, so left-click belongs to it. */
	public static boolean ownsLeftClick(Minecraft mc) {
		if (mc.player == null) return false;
		ItemStack stack = mc.player.getMainHandItem();
		return stack.getItem() instanceof PowerRingItem && PowerRingItem.getMode(stack) == RingMode.ANVIL;
	}

	/**
	 * Before vanilla handles the keys: each left-click while right-click is held is a size step.
	 * Counting clicks (rather than watching the key) catches a click shorter than a tick, and
	 * vanilla throws these clicks away while an item is in use anyway.
	 */
	public static void startTick(Minecraft mc) {
		if (mc.player == null || !mc.player.isUsingItem() || !ClientPlayNetworking.canSend(AnvilInputPayload.TYPE)) return;
		// The Blast picks its level the same way while it charges.
		ItemStack used = mc.player.getUseItem();
		int action = ownsLeftClick(mc) ? AnvilInputPayload.CYCLE
				: used.getItem() instanceof PowerRingItem && PowerRingItem.getMode(used) == RingMode.BLAST ? AnvilInputPayload.BLAST_CYCLE : -1;
		if (action < 0) return;
		while (mc.options.keyAttack.consumeClick()) {
			ClientPlayNetworking.send(new AnvilInputPayload(action));
			if (action == AnvilInputPayload.BLAST_CYCLE) blastRestart = mc.player.getTicksUsingItem();
		}
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
