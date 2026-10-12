package com.sparky.lanternring.block;

import com.sparky.lanternring.Deluges;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.LevelAccessor;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LiquidBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.material.FlowingFluid;

/**
 * The Deluge's liquid as a block. Its sources only last while their Deluge does (see Deluges);
 * any left behind (the world was saved mid-Deluge, or an older version left some) dries up the next
 * time it gets a random tick.
 */
public class HardLightLiquidBlock extends LiquidBlock {
	public HardLightLiquidBlock(FlowingFluid fluid, Properties properties) {
		super(fluid, properties);
	}

	@Override
	protected boolean isRandomlyTicking(BlockState state) {
		return true;
	}

	@Override
	protected void randomTick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
		if (state.getValue(LEVEL) == 0 ? !Deluges.isLive(level, pos) : !Deluges.isNear(level, pos)) {
			level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
		}
	}

	/** Hard light can't be bottled: a bucket comes back empty and the liquid stays. */
	@Override
	public ItemStack pickupBlock(LivingEntity user, LevelAccessor level, BlockPos pos, BlockState state) {
		return ItemStack.EMPTY;
	}
}
