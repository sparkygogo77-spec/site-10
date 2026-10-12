package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModRegistry;
import it.unimi.dsi.fastutil.objects.Object2IntMap;
import java.util.List;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.client.Minecraft;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Makes the ring's light green under shader packs with colored lighting, like Complementary.
 * Those packs give each block a material ID from their block.properties and pick a light colour per
 * ID; our blocks aren't listed, so they would get the pack's default warm light. When Iris loads a
 * pack, this files every ring light block under the same ID as a verdant froglight (green light).
 *
 * <p>Iris has no public API for this, so it is done by reflection and does nothing if Iris is
 * missing or its internals change. Without colored lighting turned on in the pack, block light is
 * one colour for everything and there is nothing a mod can tint.
 */
final class IrisGreenLight {
	private static final String SETTINGS = "net.irisshaders.iris.shaderpack.materialmap.WorldRenderingSettings";
	private static final boolean IRIS = FabricLoader.getInstance().isModLoaded("iris");
	private static Object patched;
	private static boolean failed;
	private static int tick;

	private IrisGreenLight() {
	}

	static void tick(Minecraft mc) {
		if (!IRIS || failed || mc.level == null || ++tick % 20 != 0) return;
		try {
			Class<?> settings = Class.forName(SETTINGS);
			Object instance = settings.getField("INSTANCE").get(null);
			Object ids = settings.getMethod("getBlockStateIds").invoke(instance);
			if (ids == null || ids == patched) return;
			patched = ids;
			@SuppressWarnings("unchecked")
			Object2IntMap<BlockState> map = (Object2IntMap<BlockState>) ids;
			BlockState green = Blocks.VERDANT_FROGLIGHT.defaultBlockState();
			if (!map.containsKey(green)) return;
			int id = map.getInt(green);
			for (Block block : List.of(ModRegistry.BLAST_GLOW, ModRegistry.BEAM_GLOW, ModRegistry.LIGHT_CONSTRUCT, ModRegistry.CONSTRUCT_BRICK, ModRegistry.POWER_BATTERY)) {
				for (BlockState state : block.getStateDefinition().getPossibleStates()) map.put(state, id);
			}
			// Chunks already built carry the old IDs; new ones (like a fresh Blast tunnel) are fine.
			try {
				mc.levelRenderer.getClass().getMethod("allChanged").invoke(mc.levelRenderer);
			} catch (ReflectiveOperationException ignored) {
				// Older chunks pick the colour up next time they rebuild.
			}
			LanternRing.LOGGER.info("Shader pack colored lighting: ring lights set to green (material {})", id);
		} catch (ReflectiveOperationException | RuntimeException e) {
			failed = true;
			LanternRing.LOGGER.info("Couldn't give ring lights a green shader colour ({}); they use the pack's default light colour", e.toString());
		}
	}
}
