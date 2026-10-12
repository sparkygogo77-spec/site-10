package com.sparky.lanternring;

import com.sparky.lanternring.block.HardLightLiquidBlock;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.Item;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.LiquidBlock;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.FluidState;
import net.minecraft.world.level.material.LavaFluid;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;
import net.minecraft.world.level.material.WaterFluid;

/**
 * The Deluge's hard-light liquid: water in every way that matters (you swim in it, it puts out
 * fires, it is in the minecraft:water fluid tag so the camera gets underwater fog), but green and
 * short-lived. It can't make new sources or be picked up in a bucket, and it spreads only a few
 * blocks, so when the Deluge drains its sources the rest dries up by itself.
 *
 * <p>Shader packs draw it as water too: ShaderPackIds files it under the pack's water ID, and
 * the green comes from its tint (Complementary colours water by its tint by default).
 */
public final class ModFluids {
	public static final HardLightFluid SOURCE = register("hard_light_liquid", new Source());
	public static final HardLightFluid FLOWING = register("flowing_hard_light_liquid", new Flowing());

	public static final Block BLOCK;

	/** The Red Lantern's Deluge liquid: lava to the game (it burns and slows), red, and short-lived. */
	public static final EmberFluid EMBER_SOURCE = register("ember_liquid", new EmberSource());
	public static final EmberFluid EMBER_FLOWING = register("flowing_ember_liquid", new EmberFlowing());
	public static final Block EMBER_BLOCK;

	static {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, LanternRing.id("hard_light_liquid"));
		BLOCK = Registry.register(BuiltInRegistries.BLOCK, key, new HardLightLiquidBlock(SOURCE, BlockBehaviour.Properties.of()
				.mapColor(MapColor.EMERALD)
				.replaceable()
				.noCollision()
				.strength(100f)
				// It glows: the pool lights up everything around it, the thin runoff a little less.
				.lightLevel(state -> state.getValue(LiquidBlock.LEVEL) == 0 ? 13 : 10)
				.pushReaction(PushReaction.POPPED)
				.noLootTable()
				.liquid()
				.sound(SoundType.EMPTY)
				.setId(key)));
		ResourceKey<Block> emberKey = ResourceKey.create(Registries.BLOCK, LanternRing.id("ember_liquid"));
		EMBER_BLOCK = Registry.register(BuiltInRegistries.BLOCK, emberKey, new HardLightLiquidBlock(EMBER_SOURCE, BlockBehaviour.Properties.of()
				.mapColor(MapColor.FIRE)
				.replaceable()
				.noCollision()
				.strength(100f)
				.lightLevel(state -> 9)
				.pushReaction(PushReaction.POPPED)
				.noLootTable()
				.liquid()
				.sound(SoundType.EMPTY)
				.setId(emberKey)));
	}

	/** Either Deluge liquid, green or red. */
	public static boolean isDelugeLiquid(BlockState state) {
		return state.is(BLOCK) || state.is(EMBER_BLOCK);
	}

	private static <T extends Fluid> T register(String name, T fluid) {
		return Registry.register(BuiltInRegistries.FLUID, LanternRing.id(name), fluid);
	}

	static void init() {
	}

	private ModFluids() {
	}

	/** Both halves of the liquid: water, but green, its own kind, and quick to dry up. */
	public abstract static class HardLightFluid extends WaterFluid {
		@Override
		public Fluid getFlowing() {
			return FLOWING;
		}

		@Override
		public Fluid getSource() {
			return SOURCE;
		}

		@Override
		public Item getBucket() {
			return Items.AIR;
		}

		@Override
		protected boolean canConvertToSource(ServerLevel level) {
			return false;
		}

		@Override
		public boolean isSame(Fluid fluid) {
			return fluid == SOURCE || fluid == FLOWING;
		}

		/** Water loses 1 level a block and runs 7 out; this loses 2, so it runs about 3 past the splash. */
		@Override
		public int getDropOff(LevelReader level) {
			return 2;
		}

		@Override
		public int getSlopeFindDistance(LevelReader level) {
			return 2;
		}

		@Override
		public BlockState createLegacyBlock(FluidState state) {
			return BLOCK.defaultBlockState().setValue(LiquidBlock.LEVEL, getLegacyLevel(state));
		}
	}

	/**
	 * The red liquid: lava (in the minecraft:lava tag, so it sets whatever wades in on fire and
	 * lights the grass around it), but it can't make sources, can't be bucketed, and runs only a few
	 * blocks, so the Deluge can take all of it away again.
	 */
	public abstract static class EmberFluid extends LavaFluid {
		@Override
		public Fluid getFlowing() {
			return EMBER_FLOWING;
		}

		@Override
		public Fluid getSource() {
			return EMBER_SOURCE;
		}

		@Override
		public Item getBucket() {
			return Items.AIR;
		}

		@Override
		protected boolean canConvertToSource(ServerLevel level) {
			return false;
		}

		@Override
		public boolean isSame(Fluid fluid) {
			return fluid == EMBER_SOURCE || fluid == EMBER_FLOWING;
		}

		@Override
		public int getDropOff(LevelReader level) {
			return 2;
		}

		@Override
		public int getSlopeFindDistance(LevelReader level) {
			return 2;
		}

		/** Quicker than overworld lava, which takes 1.5 s a block; this pours like it does in the Nether. */
		@Override
		public int getTickDelay(LevelReader level) {
			return 10;
		}

		/** It looks like blood-red water, so none of lava's sparks and smoke rise off it. */
		@Override
		public void animateTick(Level level, BlockPos pos, FluidState state, RandomSource random) {
		}

		@Override
		public BlockState createLegacyBlock(FluidState state) {
			return EMBER_BLOCK.defaultBlockState().setValue(LiquidBlock.LEVEL, getLegacyLevel(state));
		}
	}

	private static final class EmberSource extends EmberFluid {
		@Override
		public int getAmount(FluidState state) {
			return 8;
		}

		@Override
		public boolean isSource(FluidState state) {
			return true;
		}
	}

	private static final class EmberFlowing extends EmberFluid {
		@Override
		protected void createFluidStateDefinition(StateDefinition.Builder<Fluid, FluidState> builder) {
			super.createFluidStateDefinition(builder);
			builder.add(LEVEL);
		}

		@Override
		public int getAmount(FluidState state) {
			return state.getValue(LEVEL);
		}

		@Override
		public boolean isSource(FluidState state) {
			return false;
		}
	}

	private static final class Source extends HardLightFluid {
		@Override
		public int getAmount(FluidState state) {
			return 8;
		}

		@Override
		public boolean isSource(FluidState state) {
			return true;
		}
	}

	private static final class Flowing extends HardLightFluid {
		@Override
		protected void createFluidStateDefinition(StateDefinition.Builder<Fluid, FluidState> builder) {
			super.createFluidStateDefinition(builder);
			builder.add(LEVEL);
		}

		@Override
		public int getAmount(FluidState state) {
			return state.getValue(LEVEL);
		}

		@Override
		public boolean isSource(FluidState state) {
			return false;
		}
	}
}
