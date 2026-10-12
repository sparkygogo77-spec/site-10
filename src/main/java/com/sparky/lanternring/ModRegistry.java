package com.sparky.lanternring;

import com.sparky.lanternring.block.BlastGlowBlock;
import com.sparky.lanternring.block.ConstructBrickBlock;
import com.sparky.lanternring.block.LightConstructBlock;
import com.sparky.lanternring.block.PowerBatteryBlock;
import com.sparky.lanternring.item.PowerRingItem;
import java.util.function.Function;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;

public final class ModRegistry {
	public static final Block POWER_BATTERY = block("power_battery", PowerBatteryBlock::new, BlockBehaviour.Properties.of()
			.mapColor(MapColor.EMERALD)
			.strength(3.5f, 6f)
			.requiresCorrectToolForDrops()
			.lightLevel(state -> 13)
			.sound(SoundType.LANTERN)
			.noOcclusion());

	public static final Block LIGHT_CONSTRUCT = block("light_construct", LightConstructBlock::new, BlockBehaviour.Properties.of()
			.mapColor(MapColor.EMERALD)
			.strength(-1f, 3600000f)
			.noLootTable()
			.lightLevel(state -> 10)
			.sound(SoundType.GLASS)
			.noOcclusion()
			.isValidSpawn(Blocks::never)
			.isRedstoneConductor(Blocks::never)
			.isSuffocating(Blocks::never)
			.isViewBlocking((state, level, pos, box) -> false)
			.pushReaction(PushReaction.IMMOVEABLE));

	public static final Block CONSTRUCT_BRICK = block("construct_brick", ConstructBrickBlock::new, BlockBehaviour.Properties.of()
			.mapColor(MapColor.EMERALD)
			.strength(-1f, 3600000f)
			.noLootTable()
			.lightLevel(state -> 12)
			.sound(SoundType.NETHER_BRICKS)
			.isValidSpawn(Blocks::never)
			.pushReaction(PushReaction.IMMOVEABLE));

	/** Invisible, short-lived light left along a Blast tunnel. */
	public static final Block BLAST_GLOW = block("blast_glow", BlastGlowBlock::new, BlockBehaviour.Properties.of()
			.replaceable()
			.noCollision()
			.noLootTable()
			.lightLevel(state -> state.getValue(BlastGlowBlock.LEVEL)));

	public static final Item POWER_RING = item("power_ring", PowerRingItem::new, new Item.Properties()
			.stacksTo(1)
			.rarity(Rarity.EPIC)
			.fireResistant()
			.component(ModComponents.CHARGE, PowerRingItem.MAX_CHARGE)
			.component(ModComponents.MODE, 0)
			.component(ModComponents.FLIGHT, false));

	public static final Item POWER_BATTERY_ITEM = item("power_battery",
			props -> new BlockItem(POWER_BATTERY, props),
			new Item.Properties().rarity(Rarity.RARE).useBlockDescriptionPrefix());

	private static Block block(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties props) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, LanternRing.id(name));
		return Registry.register(BuiltInRegistries.BLOCK, key, factory.apply(props.setId(key)));
	}

	private static Item item(String name, Function<Item.Properties, Item> factory, Item.Properties props) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, LanternRing.id(name));
		return Registry.register(BuiltInRegistries.ITEM, key, factory.apply(props.setId(key)));
	}

	static void init() {
	}

	private ModRegistry() {
	}
}
