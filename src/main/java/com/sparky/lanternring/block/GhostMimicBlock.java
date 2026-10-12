package com.sparky.lanternring.block;

import com.sparky.lanternring.Corps;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * A hard-light copy of any block: its block entity holds the real block, the client draws that
 * block's own model in the ring's colour (GhostMimicRenderer), and it takes the real block's
 * shape. Build mode uses it for every block that isn't a plain cube (plants, crops, flowers,
 * leaves, stairs, beds, torches...). Goes away by itself once Builds no longer needs it.
 */
public class GhostMimicBlock extends BaseEntityBlock implements GhostBlocks.Ghost {
	public GhostMimicBlock(Properties properties) {
		super(properties);
		registerDefaultState(defaultBlockState().setValue(Corps.PROPERTY, Corps.GREEN));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(Corps.PROPERTY);
	}

	@Override
	public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new GhostMimicBlockEntity(pos, state);
	}

	@Override
	protected RenderShape getRenderShape(BlockState state) {
		return RenderShape.INVISIBLE;
	}

	private static BlockState real(BlockGetter level, BlockPos pos) {
		return level.getBlockEntity(pos) instanceof GhostMimicBlockEntity mimic ? mimic.real() : null;
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		BlockState real = real(level, pos);
		if (real == null) return Shapes.block();
		VoxelShape shape = real.getShape(level, pos, context);
		return shape.isEmpty() ? Block.box(2, 0, 2, 14, 12, 14) : shape;
	}

	@Override
	protected VoxelShape getCollisionShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		BlockState real = real(level, pos);
		return real == null ? Shapes.empty() : real.getCollisionShape(level, pos, context);
	}

	@Override
	protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState old, boolean moved) {
		GhostBlocks.placed(this, level, pos, old);
	}

	@Override
	protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
		GhostBlocks.check(this, level, pos);
	}
}
