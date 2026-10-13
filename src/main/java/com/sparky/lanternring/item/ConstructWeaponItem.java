package com.sparky.lanternring.item;

import com.sparky.lanternring.ModComponents;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;

/**
 * A yellow construct weapon the Fear Nuke's gas hands a frenzied mob (see corps/FearFrenzy): the
 * rifle, the crossbow or the blade. Only fear holds it together, so it never lasts in a player's
 * hands and fades from a mob when its frenzy ends. Stand-in textures until J's models land.
 */
public class ConstructWeaponItem extends Item {
	public ConstructWeaponItem(Properties properties) {
		super(properties);
	}

	@Override
	public void inventoryTick(ItemStack stack, ServerLevel level, Entity owner, EquipmentSlot slot) {
		if (owner instanceof Player) stack.setCount(0);
	}

	/** Whether this construct weapon's time is up. */
	public static boolean faded(ItemStack stack, long now) {
		Long at = stack.get(ModComponents.FADES_AT);
		return at == null || now >= at;
	}
}
