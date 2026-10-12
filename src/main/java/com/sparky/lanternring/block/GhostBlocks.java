package com.sparky.lanternring.block;

import com.sparky.lanternring.Builds;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.CarpetBlock;
import net.minecraft.world.level.block.DoorBlock;
import net.minecraft.world.level.block.FenceBlock;
import net.minecraft.world.level.block.FenceGateBlock;
import net.minecraft.world.level.block.IronBarsBlock;
import net.minecraft.world.level.block.LadderBlock;
import net.minecraft.world.level.block.LanternBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.TransparentBlock;
import net.minecraft.world.level.block.TrapDoorBlock;
import net.minecraft.world.level.block.WallBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockSetType;
import net.minecraft.world.level.block.state.properties.WoodType;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Green hard-light versions of blocks that aren't plain cubes (stairs, slabs, fences, panes,
 * walls, doors, trapdoors, gates, carpets, ladders, lanterns, leaves and plants), so a Build
 * mode preview keeps the real shapes. Each one goes away by itself once Builds no longer needs it.
 */
public final class GhostBlocks {
	private GhostBlocks() {
	}

	static void placed(Block block, Level level, BlockPos pos, BlockState old) {
		if (!old.is(block)) level.scheduleTick(pos, block, 20);
	}

	/** Marks every green shape, so Builds can tell them from real blocks. */
	public interface Ghost {
	}

	static void check(Block block, ServerLevel level, BlockPos pos) {
		if (Builds.isLive(level, pos)) level.scheduleTick(pos, block, 20);
		else level.removeBlock(pos, false);
	}

	public static class Stairs extends StairBlock implements Ghost {
		public Stairs(BlockState base, Properties p) { super(base, p); }
		@Override protected void onPlace(BlockState s, Level l, BlockPos pos, BlockState old, boolean m) { super.onPlace(s, l, pos, old, m); placed(this, l, pos, old); }
		@Override protected void tick(BlockState s, ServerLevel l, BlockPos pos, RandomSource r) { check(this, l, pos); }
	}

	public static class Slab extends SlabBlock implements Ghost {
		public Slab(Properties p) { super(p); }
		@Override protected void onPlace(BlockState s, Level l, BlockPos pos, BlockState old, boolean m) { super.onPlace(s, l, pos, old, m); placed(this, l, pos, old); }
		@Override protected void tick(BlockState s, ServerLevel l, BlockPos pos, RandomSource r) { check(this, l, pos); }
	}

	public static class Fence extends FenceBlock implements Ghost {
		public Fence(Properties p) { super(p); }
		@Override protected void onPlace(BlockState s, Level l, BlockPos pos, BlockState old, boolean m) { super.onPlace(s, l, pos, old, m); placed(this, l, pos, old); }
		@Override protected void tick(BlockState s, ServerLevel l, BlockPos pos, RandomSource r) { check(this, l, pos); }
	}

	public static class Pane extends IronBarsBlock implements Ghost {
		public Pane(Properties p) { super(p); }
		@Override protected void onPlace(BlockState s, Level l, BlockPos pos, BlockState old, boolean m) { super.onPlace(s, l, pos, old, m); placed(this, l, pos, old); }
		@Override protected void tick(BlockState s, ServerLevel l, BlockPos pos, RandomSource r) { check(this, l, pos); }
	}

	public static class Wall extends WallBlock implements Ghost {
		public Wall(Properties p) { super(p); }
		@Override protected void onPlace(BlockState s, Level l, BlockPos pos, BlockState old, boolean m) { super.onPlace(s, l, pos, old, m); placed(this, l, pos, old); }
		@Override protected void tick(BlockState s, ServerLevel l, BlockPos pos, RandomSource r) { check(this, l, pos); }
	}

	public static class Door extends DoorBlock implements Ghost {
		public Door(Properties p) { super(BlockSetType.OAK, p); }
		@Override protected void onPlace(BlockState s, Level l, BlockPos pos, BlockState old, boolean m) { super.onPlace(s, l, pos, old, m); placed(this, l, pos, old); }
		@Override protected void tick(BlockState s, ServerLevel l, BlockPos pos, RandomSource r) { check(this, l, pos); }
	}

	public static class Trapdoor extends TrapDoorBlock implements Ghost {
		public Trapdoor(Properties p) { super(BlockSetType.OAK, p); }
		@Override protected void onPlace(BlockState s, Level l, BlockPos pos, BlockState old, boolean m) { super.onPlace(s, l, pos, old, m); placed(this, l, pos, old); }
		@Override protected void tick(BlockState s, ServerLevel l, BlockPos pos, RandomSource r) { check(this, l, pos); }
	}

	public static class Gate extends FenceGateBlock implements Ghost {
		public Gate(Properties p) { super(WoodType.OAK, p); }
		@Override protected void onPlace(BlockState s, Level l, BlockPos pos, BlockState old, boolean m) { super.onPlace(s, l, pos, old, m); placed(this, l, pos, old); }
		@Override protected void tick(BlockState s, ServerLevel l, BlockPos pos, RandomSource r) { check(this, l, pos); }
	}

	public static class Carpet extends CarpetBlock implements Ghost {
		public Carpet(Properties p) { super(p); }
		@Override protected void onPlace(BlockState s, Level l, BlockPos pos, BlockState old, boolean m) { super.onPlace(s, l, pos, old, m); placed(this, l, pos, old); }
		@Override protected void tick(BlockState s, ServerLevel l, BlockPos pos, RandomSource r) { check(this, l, pos); }
	}

	public static class Ladder extends LadderBlock implements Ghost {
		public Ladder(Properties p) { super(p); }
		@Override protected void onPlace(BlockState s, Level l, BlockPos pos, BlockState old, boolean m) { super.onPlace(s, l, pos, old, m); placed(this, l, pos, old); }
		@Override protected void tick(BlockState s, ServerLevel l, BlockPos pos, RandomSource r) { check(this, l, pos); }
	}

	public static class Lantern extends LanternBlock implements Ghost {
		public Lantern(Properties p) { super(p); }
		@Override protected void onPlace(BlockState s, Level l, BlockPos pos, BlockState old, boolean m) { super.onPlace(s, l, pos, old, m); placed(this, l, pos, old); }
		@Override protected void tick(BlockState s, ServerLevel l, BlockPos pos, RandomSource r) { check(this, l, pos); }
	}

	/** Leaves: a see-through cube with a leafy pattern. */
	public static class Leaves extends TransparentBlock implements Ghost {
		public Leaves(Properties p) { super(p); }
		@Override protected void onPlace(BlockState s, Level l, BlockPos pos, BlockState old, boolean m) { placed(this, l, pos, old); }
		@Override protected void tick(BlockState s, ServerLevel l, BlockPos pos, RandomSource r) { check(this, l, pos); }
	}

	/** Flowers, grass, crops, saplings, torches: a glowing cross you can walk through. */
	public static class Plant extends Block implements Ghost {
		private static final VoxelShape SHAPE = Block.box(2, 0, 2, 14, 13, 14);
		public Plant(Properties p) { super(p); }
		@Override protected VoxelShape getShape(BlockState s, BlockGetter l, BlockPos pos, CollisionContext c) { return SHAPE; }
		@Override protected void onPlace(BlockState s, Level l, BlockPos pos, BlockState old, boolean m) { placed(this, l, pos, old); }
		@Override protected void tick(BlockState s, ServerLevel l, BlockPos pos, RandomSource r) { check(this, l, pos); }
	}
}
