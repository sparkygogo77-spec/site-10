package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.AnvilInputPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.world.item.ItemStack;

/**
 * Bridge mode with right-click held (see Bridges): left-click held builds the bridge out (sent
 * every tick it's down), and a press of space or crouch raises or lowers the deck a level.
 * Left-click doesn't hit or mine meanwhile (see MinecraftMixin via AnvilInput.ownsLeftClick).
 */
public final class BridgeInput {
	private static boolean jumpWas;
	private static boolean sneakWas;

	private BridgeInput() {
	}

	/** Right-click is held with the ring in Bridge mode. */
	public static boolean active(Minecraft mc) {
		if (mc.player == null || !mc.player.isUsingItem() || LanternCharge.started(mc.player)) return false;
		ItemStack used = mc.player.getUseItem();
		return used.getItem() instanceof PowerRingItem && PowerRingItem.getMode(used) == RingMode.BRIDGE;
	}

	public static void tick(Minecraft mc) {
		boolean jump = mc.options.keyJump.isDown();
		boolean sneak = mc.options.keyShift.isDown();
		if (active(mc) && mc.gui.screen() == null && ClientPlayNetworking.canSend(AnvilInputPayload.TYPE)) {
			// Vanilla drops left-clicks while an item is in use; clear them so none pile up for later.
			while (mc.options.keyAttack.consumeClick()) {
			}
			if (mc.options.keyAttack.isDown()) ClientPlayNetworking.send(new AnvilInputPayload(AnvilInputPayload.BRIDGE_BUILD));
			if (jump && !jumpWas) ClientPlayNetworking.send(new AnvilInputPayload(AnvilInputPayload.BRIDGE_UP));
			if (sneak && !sneakWas) ClientPlayNetworking.send(new AnvilInputPayload(AnvilInputPayload.BRIDGE_DOWN));
		}
		jumpWas = jump;
		sneakWas = sneak;
	}
}
