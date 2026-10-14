package com.sparky.lanternring.mixin;

import com.sparky.lanternring.RingSlot;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/** Mining with an empty hand and a worn ring uses the ring (its construct tools), like holding it. */
@Mixin(Player.class)
abstract class PlayerToolMixin {
	@Redirect(method = {"getDestroySpeed", "hasCorrectToolForDrops"},
			at = @At(value = "INVOKE", target = "Lnet/minecraft/world/entity/player/Inventory;getSelectedItem()Lnet/minecraft/world/item/ItemStack;"))
	private ItemStack lanternring$wornTool(Inventory inventory) {
		ItemStack held = inventory.getSelectedItem();
		return held.isEmpty() ? RingSlot.worn((Player) (Object) this) : held;
	}
}
