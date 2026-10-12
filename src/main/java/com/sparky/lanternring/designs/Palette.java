package com.sparky.lanternring.designs;

import java.util.List;
import net.minecraft.core.Direction;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.Half;
import net.minecraft.world.level.block.state.properties.SlabType;

/** The materials one version of a generated build is made of. */
public record Palette(String name, Block wallBlock, Block frameBlock, Block floorBlock, Block baseBlock, Block roofBlock, Block roofStairs,
		Block roofSlab, Block windowBlock, Block glassBlock, Block doorBlock, Block fenceBlock, Block lightBlock) {

	public static final Palette OAK = new Palette("Oak", Blocks.OAK_PLANKS, Blocks.OAK_LOG, Blocks.SPRUCE_PLANKS, Blocks.COBBLESTONE,
			Blocks.DARK_OAK_PLANKS, Blocks.DARK_OAK_STAIRS, Blocks.DARK_OAK_SLAB, Blocks.GLASS_PANE, Blocks.GLASS, Blocks.OAK_DOOR, Blocks.OAK_FENCE, Blocks.LANTERN);
	public static final Palette SPRUCE = new Palette("Spruce", Blocks.SPRUCE_PLANKS, Blocks.SPRUCE_LOG, Blocks.SPRUCE_PLANKS, Blocks.COBBLESTONE,
			Blocks.COBBLED_DEEPSLATE, Blocks.COBBLED_DEEPSLATE_STAIRS, Blocks.COBBLED_DEEPSLATE_SLAB, Blocks.GLASS_PANE, Blocks.GLASS, Blocks.SPRUCE_DOOR, Blocks.SPRUCE_FENCE, Blocks.LANTERN);
	public static final Palette BIRCH = new Palette("Birch", Blocks.BIRCH_PLANKS, Blocks.BIRCH_LOG, Blocks.OAK_PLANKS, Blocks.STONE_BRICKS,
			Blocks.OAK_PLANKS, Blocks.OAK_STAIRS, Blocks.OAK_SLAB, Blocks.GLASS_PANE, Blocks.GLASS, Blocks.BIRCH_DOOR, Blocks.BIRCH_FENCE, Blocks.LANTERN);
	public static final Palette DARK_OAK = new Palette("Dark Oak", Blocks.DARK_OAK_PLANKS, Blocks.DARK_OAK_LOG, Blocks.DARK_OAK_PLANKS, Blocks.COBBLED_DEEPSLATE,
			Blocks.DEEPSLATE_TILES, Blocks.DEEPSLATE_TILE_STAIRS, Blocks.DEEPSLATE_TILE_SLAB, Blocks.GLASS_PANE, Blocks.GLASS, Blocks.DARK_OAK_DOOR, Blocks.DARK_OAK_FENCE, Blocks.LANTERN);
	public static final Palette JUNGLE = new Palette("Jungle", Blocks.JUNGLE_PLANKS, Blocks.JUNGLE_LOG, Blocks.JUNGLE_PLANKS, Blocks.MOSSY_COBBLESTONE,
			Blocks.MOSSY_COBBLESTONE, Blocks.MOSSY_COBBLESTONE_STAIRS, Blocks.MOSSY_COBBLESTONE_SLAB, Blocks.GLASS_PANE, Blocks.GLASS, Blocks.JUNGLE_DOOR, Blocks.JUNGLE_FENCE, Blocks.LANTERN);
	public static final Palette ACACIA = new Palette("Acacia", Blocks.ACACIA_PLANKS, Blocks.ACACIA_LOG, Blocks.ACACIA_PLANKS, Blocks.TERRACOTTA,
			Blocks.ACACIA_PLANKS, Blocks.ACACIA_STAIRS, Blocks.ACACIA_SLAB, Blocks.GLASS_PANE, Blocks.GLASS, Blocks.ACACIA_DOOR, Blocks.ACACIA_FENCE, Blocks.LANTERN);
	public static final Palette CHERRY = new Palette("Cherry", Blocks.CHERRY_PLANKS, Blocks.CHERRY_LOG, Blocks.CHERRY_PLANKS, Blocks.STONE_BRICKS,
			Blocks.CHERRY_PLANKS, Blocks.CHERRY_STAIRS, Blocks.CHERRY_SLAB, Blocks.GLASS_PANE, Blocks.GLASS, Blocks.CHERRY_DOOR, Blocks.CHERRY_FENCE, Blocks.LANTERN);
	public static final Palette MANGROVE = new Palette("Mangrove", Blocks.MANGROVE_PLANKS, Blocks.MANGROVE_LOG, Blocks.MANGROVE_PLANKS, Blocks.MUD_BRICKS,
			Blocks.MUD_BRICKS, Blocks.MUD_BRICK_STAIRS, Blocks.MUD_BRICK_SLAB, Blocks.GLASS_PANE, Blocks.GLASS, Blocks.MANGROVE_DOOR, Blocks.MANGROVE_FENCE, Blocks.LANTERN);
	public static final Palette STONE = new Palette("Stone Brick", Blocks.STONE_BRICKS, Blocks.CHISELED_STONE_BRICKS, Blocks.POLISHED_ANDESITE, Blocks.COBBLESTONE,
			Blocks.STONE_BRICKS, Blocks.STONE_BRICK_STAIRS, Blocks.STONE_BRICK_SLAB, Blocks.GLASS_PANE, Blocks.GLASS, Blocks.SPRUCE_DOOR, Blocks.SPRUCE_FENCE, Blocks.LANTERN);
	public static final Palette SANDSTONE = new Palette("Sandstone", Blocks.CUT_SANDSTONE, Blocks.CHISELED_SANDSTONE, Blocks.SMOOTH_SANDSTONE, Blocks.SANDSTONE,
			Blocks.SMOOTH_SANDSTONE, Blocks.SANDSTONE_STAIRS, Blocks.SANDSTONE_SLAB, Blocks.GLASS_PANE, Blocks.GLASS, Blocks.JUNGLE_DOOR, Blocks.JUNGLE_FENCE, Blocks.LANTERN);
	public static final Palette RED_SANDSTONE = new Palette("Red Sandstone", Blocks.CUT_RED_SANDSTONE, Blocks.CHISELED_RED_SANDSTONE, Blocks.SMOOTH_RED_SANDSTONE, Blocks.RED_SANDSTONE,
			Blocks.SMOOTH_RED_SANDSTONE, Blocks.RED_SANDSTONE_STAIRS, Blocks.RED_SANDSTONE_SLAB, Blocks.GLASS_PANE, Blocks.GLASS, Blocks.ACACIA_DOOR, Blocks.ACACIA_FENCE, Blocks.LANTERN);
	public static final Palette DEEPSLATE = new Palette("Deepslate", Blocks.DEEPSLATE_BRICKS, Blocks.POLISHED_DEEPSLATE, Blocks.POLISHED_DEEPSLATE, Blocks.COBBLED_DEEPSLATE,
			Blocks.DEEPSLATE_TILES, Blocks.DEEPSLATE_TILE_STAIRS, Blocks.DEEPSLATE_TILE_SLAB, Blocks.STAINED_GLASS_PANE.gray(), Blocks.STAINED_GLASS.gray(), Blocks.DARK_OAK_DOOR, Blocks.DARK_OAK_FENCE, Blocks.SOUL_LANTERN);
	public static final Palette BLACKSTONE = new Palette("Blackstone", Blocks.POLISHED_BLACKSTONE_BRICKS, Blocks.CHISELED_POLISHED_BLACKSTONE, Blocks.POLISHED_BLACKSTONE, Blocks.BLACKSTONE,
			Blocks.BLACKSTONE, Blocks.BLACKSTONE_STAIRS, Blocks.BLACKSTONE_SLAB, Blocks.STAINED_GLASS_PANE.red(), Blocks.STAINED_GLASS.red(), Blocks.CRIMSON_DOOR, Blocks.CRIMSON_FENCE, Blocks.SOUL_LANTERN);
	public static final Palette QUARTZ = new Palette("Quartz", Blocks.QUARTZ_BLOCK, Blocks.QUARTZ_PILLAR, Blocks.SMOOTH_QUARTZ, Blocks.QUARTZ_BRICKS,
			Blocks.SMOOTH_QUARTZ, Blocks.QUARTZ_STAIRS, Blocks.QUARTZ_SLAB, Blocks.STAINED_GLASS_PANE.lightBlue(), Blocks.STAINED_GLASS.lightBlue(), Blocks.BIRCH_DOOR, Blocks.BIRCH_FENCE, Blocks.SEA_LANTERN);
	public static final Palette PRISMARINE = new Palette("Prismarine", Blocks.PRISMARINE_BRICKS, Blocks.DARK_PRISMARINE, Blocks.PRISMARINE, Blocks.DARK_PRISMARINE,
			Blocks.DARK_PRISMARINE, Blocks.DARK_PRISMARINE_STAIRS, Blocks.DARK_PRISMARINE_SLAB, Blocks.STAINED_GLASS_PANE.cyan(), Blocks.STAINED_GLASS.cyan(), Blocks.WARPED_DOOR, Blocks.WARPED_FENCE, Blocks.SEA_LANTERN);
	public static final Palette BRICK = new Palette("Brick", Blocks.BRICKS, Blocks.STRIPPED_OAK_LOG, Blocks.OAK_PLANKS, Blocks.STONE_BRICKS,
			Blocks.DEEPSLATE_TILES, Blocks.DEEPSLATE_TILE_STAIRS, Blocks.DEEPSLATE_TILE_SLAB, Blocks.GLASS_PANE, Blocks.GLASS, Blocks.OAK_DOOR, Blocks.OAK_FENCE, Blocks.LANTERN);
	public static final Palette TUFF = new Palette("Tuff", Blocks.TUFF_BRICKS, Blocks.CHISELED_TUFF, Blocks.POLISHED_TUFF, Blocks.TUFF,
			Blocks.POLISHED_TUFF, Blocks.TUFF_BRICK_STAIRS, Blocks.TUFF_BRICK_SLAB, Blocks.GLASS_PANE, Blocks.GLASS, Blocks.SPRUCE_DOOR, Blocks.SPRUCE_FENCE, Blocks.LANTERN);
	public static final Palette WHITE = new Palette("White", Blocks.CONCRETE.white(), Blocks.SMOOTH_STONE, Blocks.POLISHED_DIORITE, Blocks.STONE_BRICKS,
			Blocks.CONCRETE.lightGray(), Blocks.DIORITE_STAIRS, Blocks.DIORITE_SLAB, Blocks.STAINED_GLASS_PANE.lightBlue(), Blocks.STAINED_GLASS.lightBlue(), Blocks.IRON_DOOR, Blocks.BIRCH_FENCE, Blocks.SEA_LANTERN);
	/** Ring green: emerald and green glass, in honour of the lantern. */
	public static final Palette LANTERN = new Palette("Lantern Green", Blocks.CONCRETE.green(), Blocks.EMERALD_BLOCK, Blocks.POLISHED_DEEPSLATE, Blocks.DEEPSLATE_BRICKS,
			Blocks.DYED_TERRACOTTA.green(), Blocks.PRISMARINE_STAIRS, Blocks.PRISMARINE_SLAB, Blocks.STAINED_GLASS_PANE.lime(), Blocks.STAINED_GLASS.lime(), Blocks.WARPED_DOOR, Blocks.WARPED_FENCE, Blocks.SEA_LANTERN);

	public static final List<Palette> WOOD = List.of(OAK, SPRUCE, BIRCH, DARK_OAK, JUNGLE, ACACIA, CHERRY, MANGROVE, BRICK);
	public static final List<Palette> MASONRY = List.of(STONE, SANDSTONE, RED_SANDSTONE, DEEPSLATE, BLACKSTONE, QUARTZ, PRISMARINE, TUFF);
	public static final List<Palette> MODERN = List.of(WHITE, QUARTZ, DEEPSLATE, PRISMARINE, LANTERN, BLACKSTONE);
	public static final List<Palette> ALL = List.of(OAK, SPRUCE, BIRCH, DARK_OAK, JUNGLE, ACACIA, CHERRY, MANGROVE, BRICK,
			STONE, SANDSTONE, RED_SANDSTONE, DEEPSLATE, BLACKSTONE, QUARTZ, PRISMARINE, TUFF, WHITE, LANTERN);

	public BlockState wall() {
		return wallBlock.defaultBlockState();
	}

	/** Logs and pillars stand upright. */
	public BlockState frame() {
		return frameBlock.defaultBlockState();
	}

	public BlockState floor() {
		return floorBlock.defaultBlockState();
	}

	public BlockState base() {
		return baseBlock.defaultBlockState();
	}

	public BlockState roof() {
		return roofBlock.defaultBlockState();
	}

	public BlockState glass() {
		return glassBlock.defaultBlockState();
	}

	public BlockState window() {
		return windowBlock.defaultBlockState();
	}

	public BlockState fence() {
		return fenceBlock.defaultBlockState();
	}

	public BlockState door() {
		return doorBlock.defaultBlockState();
	}

	public BlockState light() {
		return lightBlock.defaultBlockState();
	}

	/** Roof stairs whose tall back faces {@code facing} (toward the ridge). */
	public BlockState stairs(Direction facing) {
		return stairs(roofStairs, facing, false);
	}

	public BlockState slab(boolean top) {
		BlockState s = roofSlab.defaultBlockState();
		return s.hasProperty(BlockStateProperties.SLAB_TYPE) ? s.setValue(BlockStateProperties.SLAB_TYPE, top ? SlabType.TOP : SlabType.BOTTOM) : s;
	}

	static BlockState stairs(Block block, Direction facing, boolean upsideDown) {
		BlockState s = block.defaultBlockState();
		if (s.hasProperty(BlockStateProperties.HORIZONTAL_FACING)) s = s.setValue(BlockStateProperties.HORIZONTAL_FACING, facing);
		if (s.hasProperty(BlockStateProperties.HALF)) s = s.setValue(BlockStateProperties.HALF, upsideDown ? Half.TOP : Half.BOTTOM);
		return s;
	}
}
