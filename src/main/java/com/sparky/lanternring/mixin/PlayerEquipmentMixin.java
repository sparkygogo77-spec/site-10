package com.sparky.lanternring.mixin;

import com.sparky.lanternring.RingSlot;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.player.PlayerEquipment;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.ModifyVariable;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * The worn ring (RingSlot) works as the main-hand item while the hand is empty, so every power that
 * reads the held ring keeps working. It's never copied into a real slot: setting the worn ring
 * itself anywhere (like swapping hands with F) sets an empty hand instead.
 */
@Mixin(PlayerEquipment.class)
abstract class PlayerEquipmentMixin {
	@Shadow
	@Final
	private Player player;

	@Inject(method = "get", at = @At("RETURN"), cancellable = true)
	private void lanternring$wornRing(EquipmentSlot slot, CallbackInfoReturnable<ItemStack> cir) {
		if (slot != EquipmentSlot.MAINHAND || !cir.getReturnValue().isEmpty()) return;
		ItemStack worn = RingSlot.worn(player);
		if (!worn.isEmpty()) cir.setReturnValue(worn);
	}

	@ModifyVariable(method = "set", at = @At("HEAD"), argsOnly = true)
	private ItemStack lanternring$keepWorn(ItemStack stack) {
		return !stack.isEmpty() && stack == RingSlot.worn(player) ? ItemStack.EMPTY : stack;
	}
}
