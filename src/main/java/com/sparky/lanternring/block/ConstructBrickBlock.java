package com.sparky.lanternring.block;

import com.sparky.lanternring.Corps;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.StateDefinition;

import com.sparky.lanternring.ClientHooks;
import com.sparky.lanternring.HeldConstructs;
import com.sparky.lanternring.ReplacedBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.HalfTransparentBlock;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Glowing green brick of the Wall, slightly see-through (faces between two bricks are skipped, like
 * glass). It removes itself once its wall's time is up.
 */
public class ConstructBrickBlock extends HalfTransparentBlock {
	public ConstructBrickBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(Corps.PROPERTY, Corps.GREEN));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(Corps.PROPERTY);
	}

	@Override
	protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean movedByPiston) {
		if (!oldState.is(this)) level.scheduleTick(pos, this, HeldConstructs.CHECK_TICKS);
	}

	@Override
	protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
		if (HeldConstructs.isLive(level, pos)) level.scheduleTick(pos, this, HeldConstructs.CHECK_TICKS);
		else ReplacedBlocks.restore(level, pos);
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		if (random.nextInt(4) == 0) ClientHooks.constructAmbient.animate(level, pos, random);
	}
}
