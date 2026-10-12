package com.sparky.lanternring.block;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.RingTuning;
import java.util.function.IntSupplier;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.AirBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.RenderShape;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.IntegerProperty;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.material.Fluids;

/**
 * Invisible light left in a Blast tunnel so the glowing scar lights up its walls. It behaves like
 * air (no shape, replaceable), stays for RingTuning.BLAST_AFTERGLOW, then dims over one second and
 * removes itself. Removal is a scheduled tick, so it is saved with the world and never gets stuck.
 * The Beam leaves the same light for a moment along its path (ModRegistry.BEAM_GLOW).
 *
 * <p>It renders a speck of fully clear geometry: nothing shows, but shader packs with voxel colored
 * lighting (Complementary) only see lights that have geometry. Its corps blockstate (set from the
 * ring that made it) picks the light colour; see ShaderPackIds.
 *
 * <p>Underwater it is WATERLOGGED: it holds a water source, so the sea closes over it instead of
 * leaving a dry gap, and turns back into plain water when it goes out.
 */
public class BlastGlowBlock extends AirBlock {
	public static final IntegerProperty LEVEL = IntegerProperty.create("level", 0, 15);
	public static final BooleanProperty WATERLOGGED = BlockStateProperties.WATERLOGGED;
	public static final int START_LEVEL = 15;
	private static final int FADE_STEP = 3;
	private static final int FADE_TICKS = 5;

	/** How long the light stays at full strength plus its fade, in ticks. */
	private final IntSupplier lifetime;

	public BlastGlowBlock(Properties properties) {
		this(properties, RingTuning.BLAST_AFTERGLOW::ticks);
	}

	public BlastGlowBlock(Properties properties, IntSupplier lifetime) {
		super(properties);
		this.lifetime = lifetime;
		registerDefaultState(stateDefinition.any().setValue(LEVEL, START_LEVEL).setValue(WATERLOGGED, false).setValue(Corps.PROPERTY, Corps.GREEN));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(LEVEL, WATERLOGGED, Corps.PROPERTY);
	}

	@Override
	protected RenderShape getRenderShape(BlockState state) {
		return RenderShape.MODEL;
	}

	@Override
	protected FluidState getFluidState(BlockState state) {
		return state.getValue(WATERLOGGED) ? Fluids.WATER.getSource(false) : super.getFluidState(state);
	}

	@Override
	protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean movedByPiston) {
		if (oldState.is(this)) return;
		int fade = (START_LEVEL / FADE_STEP + 1) * FADE_TICKS;
		level.scheduleTick(pos, this, Math.max(1, lifetime.getAsInt() - fade));
	}

	@Override
	protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
		int next = state.getValue(LEVEL) - FADE_STEP;
		if (next <= 0) {
			if (state.getValue(WATERLOGGED)) level.setBlock(pos, Blocks.WATER.defaultBlockState(), 3);
			else level.removeBlock(pos, false);
			return;
		}
		level.setBlock(pos, state.setValue(LEVEL, next), 3);
		level.scheduleTick(pos, this, FADE_TICKS);
	}
}
