package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.AnvilInputPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.world.item.ItemStack;

/**
 * Anvil mode aims with right-click (the server moves the marker while it's held, and letting go
 * drops the anvil; see PowerRingItem). A left-click while aiming picks the next size. With the
 * lantern in the off hand, holding that left-click for the charge time charges from the lantern
 * instead (see LanternChargeInput), so the size only changes when the click is let go quickly.
 * Left-click doesn't mine or hit with the ring while aiming (see MinecraftMixin).
 */
public final class AnvilInput {
	/** A left-click while aiming with the lantern held, waiting to see if it's a click or a charge. */
	private static boolean pending;
	private static int pendingTicks;

	private AnvilInput() {
	}

	/** Aiming the Anvil: right-click held with the ring in Anvil mode, and not charging from the lantern. */
	public static boolean aiming(Minecraft mc) {
		if (mc.player == null || !mc.player.isUsingItem() || LanternCharge.started(mc.player)) return false;
		ItemStack stack = mc.player.getUseItem();
		return stack.getItem() instanceof PowerRingItem && PowerRingItem.getMode(stack) == RingMode.ANVIL;
	}

	/** While aiming, left-click belongs to the size (or the lantern charge). */
	public static boolean ownsLeftClick(Minecraft mc) {
		return aiming(mc);
	}

	/**
	 * Before vanilla handles the keys: each left-click while aiming is a size step. Counting clicks
	 * (rather than watching the key) catches a click shorter than a tick, and vanilla throws these
	 * clicks away while an item is in use anyway.
	 */
	public static void startTick(Minecraft mc) {
		if (!aiming(mc)) {
			pending = false;
			return;
		}
		while (mc.options.keyAttack.consumeClick()) {
			if (LanternChargeInput.armed(mc)) {
				if (!pending) pendingTicks = 0;
				pending = true;
			} else {
				cycle();
			}
		}
	}

	public static void tick(Minecraft mc) {
		if (!pending) return;
		if (!aiming(mc)) {
			pending = false;
			return;
		}
		if (!mc.options.keyAttack.isDown()) {
			pending = false;
			cycle();
		} else if (++pendingTicks >= LanternCharge.hold()) {
			// Held long enough with right-click: it's a lantern charge, so the aim is called off.
			pending = false;
			LanternChargeInput.switchToCharge(mc);
		}
	}

	private static void cycle() {
		if (ClientPlayNetworking.canSend(AnvilInputPayload.TYPE)) ClientPlayNetworking.send(new AnvilInputPayload(AnvilInputPayload.CYCLE));
	}
}
