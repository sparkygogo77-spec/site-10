package com.sparky.lanternring.city;

import com.sparky.lanternring.LanternRing;
import java.util.List;
import java.util.function.Function;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.TransparentBlock;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.MapColor;

/**
 * The Blue Lantern sky city's own blocks. Skystone and Hope Lamps have no recipe and no other
 * structure uses them: mining a sky city is the only way to get them. Sky Light is the city's
 * permanent blue hard light (bridges, lifts, window bands) and drops nothing.
 */
public final class CityBlocks {
	public static final Block SKYSTONE_BRICKS = block("skystone_bricks", Block::new, stone());
	public static final Block SKYSTONE_TILES = block("skystone_tiles", Block::new, stone());
	public static final Block SKYSTONE_PILLAR = block("skystone_pillar", RotatedPillarBlock::new, stone());
	public static final Block SKYSTONE_STAIRS = block("skystone_stairs",
			p -> new StairBlock(SKYSTONE_BRICKS.defaultBlockState(), p), stone());
	public static final Block SKYSTONE_SLAB = block("skystone_slab", SlabBlock::new, stone());
	public static final Block HOPE_LAMP = block("hope_lamp", Block::new, BlockBehaviour.Properties.of()
			.mapColor(MapColor.COLOR_LIGHT_BLUE)
			.strength(0.6f)
			.lightLevel(state -> 15)
			.sound(SoundType.AMETHYST));
	public static final Block SKY_LIGHT = block("sky_light", TransparentBlock::new, BlockBehaviour.Properties.of()
			.mapColor(MapColor.COLOR_LIGHT_BLUE)
			.strength(0.4f)
			.noLootTable()
			.lightLevel(state -> 12)
			.sound(SoundType.GLASS)
			.noOcclusion()
			.isValidSpawn(Blocks::never)
			.isRedstoneConductor(Blocks::never)
			.isSuffocating(Blocks::never)
			.isViewBlocking((state, level, pos, box) -> false));

	static final List<Block> ALL = List.of(SKYSTONE_BRICKS, SKYSTONE_TILES, SKYSTONE_PILLAR, SKYSTONE_STAIRS, SKYSTONE_SLAB, HOPE_LAMP, SKY_LIGHT);

	private static BlockBehaviour.Properties stone() {
		return BlockBehaviour.Properties.of()
				.mapColor(MapColor.COLOR_LIGHT_BLUE)
				.requiresCorrectToolForDrops()
				.strength(1.5f, 6f)
				.sound(SoundType.CALCITE);
	}

	private static Block block(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties props) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, LanternRing.id(name));
		Block block = Registry.register(BuiltInRegistries.BLOCK, key, factory.apply(props.setId(key)));
		ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, LanternRing.id(name));
		Registry.register(BuiltInRegistries.ITEM, itemKey, new BlockItem(block, new Item.Properties().setId(itemKey).useBlockDescriptionPrefix()));
		return block;
	}

	/** Whether the city put this block there (it may rebuild or carve through it). */
	public static boolean isCity(BlockState state) {
		for (Block b : ALL) {
			if (state.is(b)) return true;
		}
		return false;
	}

	public static void register() {
		CreativeModeTabEvents.modifyOutputEvent(CreativeModeTabs.BUILDING_BLOCKS).register(output -> {
			for (Block b : ALL) output.accept(b);
		});
	}

	private CityBlocks() {
	}
}
