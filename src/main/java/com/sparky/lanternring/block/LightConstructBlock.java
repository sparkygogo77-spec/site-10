package com.sparky.lanternring.block;

import com.sparky.lanternring.ClientHooks;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.HeldConstructs;
import com.sparky.lanternring.ReplacedBlocks;
import com.sparky.lanternring.RingTuning;
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
 * Hard light made by a power ring: see-through, finely cracked jade. RIM blocks along a construct's
 * outline glow through their cracks, brighter toward two edges; the blockstate turns each block at
 * random so the lit edges vary. HELD blocks last while the bearer keeps holding the ring's power;
 * the rest fade by themselves after RingTuning.CONSTRUCT_LIFETIME.
 */
public class LightConstructBlock extends TransparentBlock {
	public static final BooleanProperty RIM = BooleanProperty.create("rim");
	public static final BooleanProperty HELD = BooleanProperty.create("held");

	public LightConstructBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(RIM, false).setValue(HELD, false).setValue(Corps.PROPERTY, Corps.GREEN));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(RIM, HELD, Corps.PROPERTY);
	}

	@Override
	protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean movedByPiston) {
		if (!oldState.is(this)) level.scheduleTick(pos, this, state.getValue(HELD) ? HeldConstructs.CHECK_TICKS : RingTuning.CONSTRUCT_LIFETIME.ticks());
	}

	@Override
	protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
		if (state.getValue(HELD) && HeldConstructs.isLive(level, pos)) {
			level.scheduleTick(pos, this, HeldConstructs.CHECK_TICKS);
			return;
		}
		ReplacedBlocks.restore(level, pos);
		if (random.nextInt(4) == 0) {
			level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 0.5f, 1.4f);
		}
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		if (state.getValue(RIM)) ClientHooks.constructAmbient.animate(level, pos, random);
	}
}
