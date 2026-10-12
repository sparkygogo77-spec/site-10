package com.sparky.lanternring.block;

import com.sparky.lanternring.ClientHooks;
import com.sparky.lanternring.HeldConstructs;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

/** Glowing green brick of the Dome shield. It only exists while the bearer holds it up. */
public class ConstructBrickBlock extends Block {
	public ConstructBrickBlock(Properties properties) {
		super(properties);
	}

	@Override
	protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean movedByPiston) {
		if (!oldState.is(this)) level.scheduleTick(pos, this, HeldConstructs.CHECK_TICKS);
	}

	@Override
	protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
		if (HeldConstructs.isLive(level, pos)) level.scheduleTick(pos, this, HeldConstructs.CHECK_TICKS);
		else level.removeBlock(pos, false);
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		if (random.nextInt(4) == 0) ClientHooks.constructAmbient.animate(level, pos, random);
	}
}
