package com.sparky.lanternring.mixin;

import com.sparky.lanternring.RingSlot;
import com.sparky.lanternring.item.PowerRingItem;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.InventoryMenu;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Adds the ring slot (RingSlot) to the player's inventory, above the off hand slot. */
@Mixin(InventoryMenu.class)
abstract class InventoryMenuMixin {
	@Inject(method = "<init>", at = @At("TAIL"))
	private void lanternring$ringSlot(Inventory inventory, boolean active, Player owner, CallbackInfo ci) {
		((AbstractContainerMenuInvoker) this).lanternring$addSlot(new RingSlot.WornSlot(owner, RingSlot.X, RingSlot.Y));
	}

	/** Shift-click: the worn ring goes back to the inventory; a ring in the inventory goes on. */
	@Inject(method = "quickMoveStack", at = @At("HEAD"), cancellable = true)
	private void lanternring$quickMove(Player player, int index, CallbackInfoReturnable<ItemStack> cir) {
		InventoryMenu menu = (InventoryMenu) (Object) this;
		if (index < 0 || index >= menu.slots.size()) return;
		Slot slot = menu.slots.get(index);
		AbstractContainerMenuInvoker invoker = (AbstractContainerMenuInvoker) this;
		if (slot instanceof RingSlot.WornSlot) {
			ItemStack ring = slot.getItem();
			if (ring.isEmpty()) {
				cir.setReturnValue(ItemStack.EMPTY);
				return;
			}
			ItemStack copy = ring.copy();
			if (!invoker.lanternring$moveItemStackTo(ring, InventoryMenu.INV_SLOT_START, InventoryMenu.USE_ROW_SLOT_END, false)) {
				cir.setReturnValue(ItemStack.EMPTY);
				return;
			}
			slot.setByPlayer(ItemStack.EMPTY);
			cir.setReturnValue(copy);
			return;
		}
		if (index < InventoryMenu.INV_SLOT_START || index >= InventoryMenu.USE_ROW_SLOT_END) return;
		ItemStack stack = slot.getItem();
		if (!(stack.getItem() instanceof PowerRingItem)) return;
		for (Slot s : menu.slots) {
			if (s instanceof RingSlot.WornSlot worn && !worn.hasItem()) {
				worn.setByPlayer(stack.split(1));
				slot.setChanged();
				cir.setReturnValue(ItemStack.EMPTY);
				return;
			}
		}
	}
}
