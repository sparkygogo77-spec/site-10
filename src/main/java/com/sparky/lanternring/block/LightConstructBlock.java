package com.sparky.lanternring.block;

import com.sparky.lanternring.item.PowerRingItem;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.TransparentBlock;
import net.minecraft.world.level.block.state.BlockState;

/** Hard light made by a power ring. It holds for a while, then fades away by itself. */
public class LightConstructBlock extends TransparentBlock {
	/** How long a construct lasts, in ticks (10 seconds). */
	public static final int LIFETIME = 200;

	public LightConstructBlock(Properties properties) {
		super(properties);
	}

	@Override
	protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean movedByPiston) {
		level.scheduleTick(pos, this, LIFETIME);
	}

	@Override
	protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
		level.removeBlock(pos, false);
		level.sendParticles(PowerRingItem.GREEN_LIGHT, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5,
				4, 0.3, 0.3, 0.3, 0);
		if (random.nextInt(4) == 0) {
			level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 0.5f, 1.4f);
		}
	}
}
