package com.sparky.lanternring.block;

import com.sparky.lanternring.ClientHooks;
import com.sparky.lanternring.HeldConstructs;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.TransparentBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;

/**
 * Hard light made by a power ring: dark, see-through jade, with RIM blocks glowing bright along a
 * construct's outline. HELD blocks last while the bearer keeps holding the ring's power; the rest
 * fade by themselves after a while.
 */
public class LightConstructBlock extends TransparentBlock {
	public static final BooleanProperty RIM = BooleanProperty.create("rim");
	public static final BooleanProperty HELD = BooleanProperty.create("held");
	/** How long an unheld construct lasts, in ticks (10 seconds). */
	public static final int LIFETIME = 200;

	public LightConstructBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(RIM, false).setValue(HELD, false));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(RIM, HELD);
	}

	@Override
	protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean movedByPiston) {
		if (!oldState.is(this)) level.scheduleTick(pos, this, state.getValue(HELD) ? HeldConstructs.CHECK_TICKS : LIFETIME);
	}

	@Override
	protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
		if (state.getValue(HELD) && HeldConstructs.isLive(level, pos)) {
			level.scheduleTick(pos, this, HeldConstructs.CHECK_TICKS);
			return;
		}
		level.removeBlock(pos, false);
		if (random.nextInt(4) == 0) {
			level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 0.5f, 1.4f);
		}
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		if (state.getValue(RIM)) ClientHooks.constructAmbient.animate(level, pos, random);
	}
}
