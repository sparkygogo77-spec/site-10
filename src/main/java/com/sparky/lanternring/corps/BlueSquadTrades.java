package com.sparky.lanternring.corps;

import com.sparky.lanternring.city.CityBlocks;
import java.util.Optional;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.alchemy.PotionContents;
import net.minecraft.world.item.alchemy.Potions;
import net.minecraft.world.item.trading.ItemCost;
import net.minecraft.world.item.trading.MerchantOffer;
import net.minecraft.world.item.trading.MerchantOffers;
import net.minecraft.world.level.ItemLike;

/**
 * What a Blue Lantern rescue squad member trades (J, 2026-10-13: 31c, 32b). Better deals than any
 * village gives, themed on what the squad does: rescue gear for everyone, flight for the flyers,
 * the hammer's heavy core for the warrior, beast gear for the rider, and a rare gift of Hope.
 * Talking to one also shows its record: role, health, who it carried in and monsters it beat.
 * The squad's own hard-light weapons join these once J's textures for them are in.
 */
final class BlueSquadTrades {
	private BlueSquadTrades() {
	}

	static void add(CorpsVillager v, MerchantOffers offers) {
		// Everyone: rescue gear, cheap.
		sell(offers, 1, Items.GOLDEN_CARROT, 6);
		sell(offers, 1, Items.LEAD, 4);
		sell(offers, 2, Items.NAME_TAG, 1);
		sell(offers, 1, CityBlocks.HOPE_QUARTZ_BRICKS, 16);
		sell(offers, PotionContents.createItemStack(Items.POTION, Potions.LONG_REGENERATION), 4);
		switch (v.squadRole()) {
			case FLYER -> {
				sell(offers, PotionContents.createItemStack(Items.POTION, Potions.LONG_SLOW_FALLING), 2);
				sell(offers, 3, Items.ENDER_PEARL, 3);
				// Wings for anyone who brings what phantoms leave behind.
				trade(offers, 30, Items.PHANTOM_MEMBRANE, 4, new ItemStack(Items.ELYTRA), 1);
			}
			case WARRIOR -> {
				sell(offers, 2, Items.SHIELD, 1);
				sell(offers, 1, Items.IRON_INGOT, 6);
				// The heart of a hammer like its own.
				trade(offers, 18, Items.BREEZE_ROD, 2, new ItemStack(Items.HEAVY_CORE), 1);
			}
			case RIDER -> {
				sell(offers, 2, Items.SADDLE, 1);
				sell(offers, 6, Items.DIAMOND_HORSE_ARMOR, 1);
				trade(offers, 4, Items.LEATHER, 4, new ItemStack(Items.GOAT_HORN), 2);
			}
			default -> {
			}
		}
		// A rare gift of Hope: you can only have one now and then.
		trade(offers, 20, Items.GOLD_BLOCK, 1, new ItemStack(Items.TOTEM_OF_UNDYING), 1);
	}

	/** Its record, in chat above the trading screen. */
	static void status(CorpsVillager v, ServerPlayer player, int rescued, int beaten) {
		Component role = Component.translatable("message.lanternring.blue_squad_role." + v.squadRole().name().toLowerCase(java.util.Locale.ROOT));
		player.sendSystemMessage(Component.translatable("message.lanternring.blue_squad_status", role,
				Math.round(v.getHealth()), Math.round(v.getMaxHealth()), rescued, beaten).withStyle(ChatFormatting.AQUA));
	}

	private static void sell(MerchantOffers offers, int emeralds, ItemLike item, int count) {
		sell(offers, new ItemStack(item, count), emeralds);
	}

	private static void sell(MerchantOffers offers, ItemStack result, int emeralds) {
		if (has(offers, result)) return;
		offers.add(new MerchantOffer(new ItemCost(Items.EMERALD, emeralds), result, 12, 3, 0.02f));
	}

	private static void trade(MerchantOffers offers, int emeralds, Item also, int alsoCount, ItemStack result, int uses) {
		if (has(offers, result)) return;
		offers.add(new MerchantOffer(new ItemCost(Items.EMERALD, emeralds), Optional.of(new ItemCost(also, alsoCount)), result, uses, 10, 0.02f));
	}

	private static boolean has(MerchantOffers offers, ItemStack result) {
		for (MerchantOffer o : offers) {
			if (ItemStack.isSameItemSameComponents(o.getResult(), result)) return true;
		}
		return false;
	}
}
