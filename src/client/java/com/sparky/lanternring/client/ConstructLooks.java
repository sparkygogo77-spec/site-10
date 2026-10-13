package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModRegistry;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.data.AtlasIds;
import net.minecraft.world.level.block.state.BlockState;

/**
 * J's construct texture picks (Blender rounds, 2026-10-13), chosen in the Ring Lab: the animated strip a
 * construct block shows, by its corps and whether it is a Wall brick. FlowConstructModel slices the strip
 * over 4 x 4 blocks by world position (tools/construct_picks.py makes them). Changing a pick rebuilds the
 * chunks so placed constructs take it at once.
 */
public final class ConstructLooks {
	private static String applied;

	private ConstructLooks() {
	}

	public static void register() {
		ClientTickEvents.END_CLIENT_TICK.register(mc -> {
			String now = signature();
			if (applied != null && !applied.equals(now) && mc.level != null) mc.levelRenderer.invalidateCompiledGeometry(mc.level, mc.options, mc.gameRenderer.mainCamera(), mc.getBlockColors());
			applied = now;
		});
	}

	private static String signature() {
		LabSettings s = LabSettings.get();
		return s.constructLook + "/" + s.wallLook + "/" + s.blueLook + "/" + s.yellowLook + "/" + s.constructOpacity;
	}

	/** The strip's name (after construct_ripples_) this construct block shows, or null for its own model. */
	static String strip(BlockState state) {
		boolean brick = state.is(ModRegistry.CONSTRUCT_BRICK);
		if (!brick && !state.is(ModRegistry.LIGHT_CONSTRUCT)) return null;
		Corps corps = state.hasProperty(Corps.PROPERTY) ? state.getValue(Corps.PROPERTY) : Corps.GREEN;
		LabSettings s = LabSettings.get();
		return switch (corps) {
			case GREEN -> brick ? s.wallLook.strip : s.constructLook.strip;
			case BLUE -> s.blueLook == LabSettings.BlueLook.CLASSIC ? null : brick ? "br1_blue" : s.blueLook.strip;
			case YELLOW -> s.yellowLook.strip;
			default -> null;
		};
	}

	/** How opaque constructs are drawn (Ring Lab "Construct opacity"), as a vertex alpha 0..255. */
	static int alpha() {
		return Math.round(LabSettings.get().constructOpacity.alpha * 255);
	}

	/**
	 * The strip a moving construct (a block display, like the falling Anvil) is drawn with: the picked strip,
	 * or R2 K1 from the jade pack for green when that's the pick; null leaves it to the block model.
	 */
	static TextureAtlasSprite displaySprite(BlockState state) {
		TextureAtlasSprite strip = sprite(state);
		if (strip != null || !state.is(ModRegistry.LIGHT_CONSTRUCT)) return strip;
		Corps corps = state.hasProperty(Corps.PROPERTY) ? state.getValue(Corps.PROPERTY) : Corps.GREEN;
		if (corps != Corps.GREEN || LabSettings.get().constructLook != LabSettings.ConstructLook.R2K1) return null;
		TextureAtlas atlas = Minecraft.getInstance().getAtlasManager().getAtlasOrThrow(AtlasIds.BLOCKS);
		TextureAtlasSprite r2k1 = atlas.getSprite(LanternRing.id("block/construct_ripples_r2k1"));
		return r2k1 == atlas.missingSprite() ? null : r2k1;
	}

	/** The strip's sprite on the block atlas, or null if it isn't there. */
	static TextureAtlasSprite sprite(BlockState state) {
		String strip = strip(state);
		if (strip == null) return null;
		TextureAtlas atlas = Minecraft.getInstance().getAtlasManager().getAtlasOrThrow(AtlasIds.BLOCKS);
		TextureAtlasSprite sprite = atlas.getSprite(LanternRing.id("block/construct_ripples_" + strip));
		return sprite == atlas.missingSprite() ? null : sprite;
	}
}
