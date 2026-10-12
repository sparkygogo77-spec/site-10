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
import net.minecraft.world.level.block.WallBlock;
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


	// Hope Quartz: what the Blue Lantern bearers' hard-light buildings set into (J, 2026-10-12:
	// "high value quartz like good looking blue/white materials that embody the hard light
	// construct colours"). Polished white crystal with blue light in its seams. Like Skystone, no
	// recipe: Blue Lantern buildings are the only place to get it.
	public static final Block HOPE_QUARTZ = block("hope_quartz", Block::new, quartz());
	public static final Block HOPE_QUARTZ_BRICKS = block("hope_quartz_bricks", Block::new, quartz());
	public static final Block HOPE_QUARTZ_PILLAR = block("hope_quartz_pillar", RotatedPillarBlock::new, quartz());
	public static final Block HOPE_QUARTZ_STAIRS = block("hope_quartz_stairs",
			p -> new StairBlock(HOPE_QUARTZ_BRICKS.defaultBlockState(), p), quartz());
	public static final Block HOPE_QUARTZ_SLAB = block("hope_quartz_slab", SlabBlock::new, quartz());
	/** Hope Quartz with a channel of hard light set in it: the buildings' glowing trim bands. */
	public static final Block HOPE_INLAY = block("hope_inlay", Block::new, quartz().lightLevel(state -> 11));
	/** See-through blue crystal in a quartz frame: the buildings' windows and domes. */
	public static final Block HOPE_CRYSTAL = block("hope_crystal", TransparentBlock::new, BlockBehaviour.Properties.of()
			.mapColor(MapColor.COLOR_LIGHT_BLUE)
			.strength(0.6f)
			.lightLevel(state -> 6)
			.sound(SoundType.AMETHYST)
			.noOcclusion()
			.isValidSpawn(Blocks::never)
			.isRedstoneConductor(Blocks::never)
			.isSuffocating(Blocks::never)
			.isViewBlocking((state, level, pos, box) -> false));

	// Hope Bricks: what a Blue Lantern aerial drop sets into (see corps/HopeDrop). J (2026-10-12) likes
	// polished deepslate bricks, nether bricks and the dome's bricks, "denser bricks by like 1.25x".
	public static final Block HOPE_BRICKS = block("hope_bricks", Block::new, bricks());
	public static final Block HOPE_BRICK_WALL = block("hope_brick_wall", WallBlock::new, bricks().forceSolidOn());

	static final List<Block> ALL = List.of(SKYSTONE_BRICKS, SKYSTONE_TILES, SKYSTONE_PILLAR, SKYSTONE_STAIRS, SKYSTONE_SLAB, HOPE_LAMP, SKY_LIGHT,
			HOPE_QUARTZ, HOPE_QUARTZ_BRICKS, HOPE_QUARTZ_PILLAR, HOPE_QUARTZ_STAIRS, HOPE_QUARTZ_SLAB, HOPE_INLAY, HOPE_CRYSTAL);

	private static BlockBehaviour.Properties quartz() {
		return BlockBehaviour.Properties.of()
				.mapColor(MapColor.QUARTZ)
				.requiresCorrectToolForDrops()
				.strength(1.2f, 6f)
				.sound(SoundType.AMETHYST);
	}

	private static BlockBehaviour.Properties bricks() {
		return BlockBehaviour.Properties.of()
				.mapColor(MapColor.COLOR_BLUE)
				.requiresCorrectToolForDrops()
				.strength(3.5f, 6f)
				.sound(SoundType.DEEPSLATE_BRICKS);
	}

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
			output.accept(HOPE_BRICKS);
			output.accept(HOPE_BRICK_WALL);
		});
	}

	private CityBlocks() {
	}
}
