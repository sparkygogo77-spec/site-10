package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.AnvilInputPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.world.item.ItemStack;

/**
 * Saw mode with right-click held (see Saws): left-click held spins the saw and rolls it forward
 * (sent every tick it's down). Left-click doesn't hit or mine meanwhile (see MinecraftMixin via
 * AnvilInput.ownsLeftClick).
 */
public final class SawInput {
	private SawInput() {
	}

	/** Right-click is held with the ring in Saw mode. */
	public static boolean active(Minecraft mc) {
		if (mc.player == null || !mc.player.isUsingItem() || LanternCharge.started(mc.player)) return false;
		ItemStack used = mc.player.getUseItem();
		return used.getItem() instanceof PowerRingItem && PowerRingItem.getMode(used) == RingMode.SAW;
	}

	public static void tick(Minecraft mc) {
		if (!active(mc) || mc.gui.screen() != null || !ClientPlayNetworking.canSend(AnvilInputPayload.TYPE)) return;
		// Vanilla drops left-clicks while an item is in use; clear them so none pile up for later.
		while (mc.options.keyAttack.consumeClick()) {
		}
		if (mc.options.keyAttack.isDown()) ClientPlayNetworking.send(new AnvilInputPayload(AnvilInputPayload.SAW_SPIN));
	}
}
