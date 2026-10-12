package com.sparky.lanternring.block;

import com.mojang.serialization.MapCodec;
import com.sparky.lanternring.item.PowerRingItem;
import net.minecraft.block.BlockState;
import net.minecraft.block.TransparentBlock;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.random.Random;
import net.minecraft.world.World;

/** Hard light made by a power ring. It holds for a while, then fades away by itself. */
public class LightConstructBlock extends TransparentBlock {
	public static final MapCodec<LightConstructBlock> CODEC = createCodec(LightConstructBlock::new);
	/** How long a construct lasts, in ticks (10 seconds). */
	public static final int LIFETIME = 200;

	public LightConstructBlock(Settings settings) {
		super(settings);
	}

	@Override
	protected MapCodec<? extends TransparentBlock> getCodec() {
		return CODEC;
	}

	@Override
	protected void onBlockAdded(BlockState state, World world, BlockPos pos, BlockState oldState, boolean notify) {
		world.scheduleBlockTick(pos, this, LIFETIME);
	}

	@Override
	protected void scheduledTick(BlockState state, ServerWorld world, BlockPos pos, Random random) {
		world.removeBlock(pos, false);
		world.spawnParticles(PowerRingItem.GREEN_LIGHT, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5,
				4, 0.3, 0.3, 0.3, 0);
		if (random.nextInt(4) == 0) {
			world.playSound(null, pos, SoundEvents.BLOCK_AMETHYST_BLOCK_CHIME, SoundCategory.BLOCKS, 0.5f, 1.4f);
		}
	}
}
