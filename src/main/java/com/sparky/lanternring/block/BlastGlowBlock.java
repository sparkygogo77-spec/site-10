package com.sparky.lanternring.block;

import com.sparky.lanternring.RingTuning;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.AirBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.IntegerProperty;

/**
 * Invisible light left in a Blast tunnel so the glowing scar lights up its walls. It behaves like
 * air (no shape, replaceable), stays for RingTuning.BLAST_AFTERGLOW, then dims over one second and
 * removes itself. Removal is a scheduled tick, so it is saved with the world and never gets stuck.
 *
 * <p>It renders a speck of fully clear geometry: nothing shows, but shader packs with voxel colored
 * lighting (Complementary) only see lights that have geometry. See IrisGreenLight for the colour.
 */
public class BlastGlowBlock extends AirBlock {
	public static final IntegerProperty LEVEL = IntegerProperty.create("level", 0, 15);
	public static final int START_LEVEL = 11;
	private static final int FADE_STEP = 3;
	private static final int FADE_TICKS = 5;

	public BlastGlowBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(LEVEL, START_LEVEL));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(LEVEL);
	}

	@Override
	protected RenderShape getRenderShape(BlockState state) {
		return RenderShape.MODEL;
	}

	@Override
	protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean movedByPiston) {
		if (oldState.is(this)) return;
		int fade = (START_LEVEL / FADE_STEP + 1) * FADE_TICKS;
		level.scheduleTick(pos, this, Math.max(1, RingTuning.BLAST_AFTERGLOW.ticks() - fade));
	}

	@Override
	protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
		int next = state.getValue(LEVEL) - FADE_STEP;
		if (next <= 0) {
			level.removeBlock(pos, false);
			return;
		}
		level.setBlock(pos, state.setValue(LEVEL, next), 3);
		level.scheduleTick(pos, this, FADE_TICKS);
	}
}
