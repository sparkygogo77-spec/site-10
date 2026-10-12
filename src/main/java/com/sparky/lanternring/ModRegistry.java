package com.sparky.lanternring;

import com.sparky.lanternring.block.LightConstructBlock;
import com.sparky.lanternring.block.PowerBatteryBlock;
import com.sparky.lanternring.item.PowerRingItem;
import net.minecraft.block.AbstractBlock;
import net.minecraft.block.Block;
import net.minecraft.block.Blocks;
import net.minecraft.block.MapColor;
import net.minecraft.block.piston.PistonBehavior;
import net.minecraft.item.BlockItem;
import net.minecraft.item.Item;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.sound.BlockSoundGroup;
import net.minecraft.util.Rarity;

public final class ModRegistry {
	public static final Block POWER_BATTERY = Registry.register(Registries.BLOCK, LanternRing.id("power_battery"),
			new PowerBatteryBlock(AbstractBlock.Settings.create()
					.mapColor(MapColor.EMERALD_GREEN)
					.strength(3.5f, 6f)
					.requiresTool()
					.luminance(state -> 13)
					.sounds(BlockSoundGroup.LANTERN)
					.nonOpaque()));

	public static final Block LIGHT_CONSTRUCT = Registry.register(Registries.BLOCK, LanternRing.id("light_construct"),
			new LightConstructBlock(AbstractBlock.Settings.create()
					.mapColor(MapColor.EMERALD_GREEN)
					.strength(-1f, 3600000f)
					.dropsNothing()
					.luminance(state -> 10)
					.sounds(BlockSoundGroup.GLASS)
					.nonOpaque()
					.allowsSpawning(Blocks::never)
					.solidBlock(Blocks::never)
					.suffocates(Blocks::never)
					.blockVision(Blocks::never)
					.pistonBehavior(PistonBehavior.BLOCK)));

	public static final Item POWER_RING = Registry.register(Registries.ITEM, LanternRing.id("power_ring"),
			new PowerRingItem(new Item.Settings()
					.maxCount(1)
					.rarity(Rarity.EPIC)
					.fireproof()
					.component(ModComponents.CHARGE, PowerRingItem.MAX_CHARGE)
					.component(ModComponents.MODE, 0)
					.component(ModComponents.FLIGHT, false)));

	public static final Item POWER_BATTERY_ITEM = Registry.register(Registries.ITEM, LanternRing.id("power_battery"),
			new BlockItem(POWER_BATTERY, new Item.Settings().rarity(Rarity.RARE)));

	static void init() {
	}

	private ModRegistry() {
	}
}
