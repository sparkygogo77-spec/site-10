package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.RingSlot;
import net.minecraft.world.Container;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyArg;

/** On the creative inventory tab the ring slot sits left of the off hand slot instead of over the hotbar. */
@Mixin(targets = "net.minecraft.client.gui.screens.inventory.CreativeModeInventoryScreen$SlotWrapper")
abstract class CreativeSlotWrapperMixin {
	@ModifyArg(method = "<init>", at = @At(value = "INVOKE", target = "Lnet/minecraft/world/inventory/Slot;<init>(Lnet/minecraft/world/Container;III)V"), index = 2)
	private static int lanternring$ringX(Container container, int slot, int x, int y) {
		return container instanceof RingSlot.Worn ? RingSlot.CREATIVE_X : x;
	}

	@ModifyArg(method = "<init>", at = @At(value = "INVOKE", target = "Lnet/minecraft/world/inventory/Slot;<init>(Lnet/minecraft/world/Container;III)V"), index = 3)
	private static int lanternring$ringY(Container container, int slot, int x, int y) {
		return container instanceof RingSlot.Worn ? RingSlot.CREATIVE_Y : y;
	}
}
