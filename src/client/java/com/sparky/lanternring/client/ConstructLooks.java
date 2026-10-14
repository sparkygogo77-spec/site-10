package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.ModRegistry;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.data.AtlasIds;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

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
			barrierPixels(mc);
		});
	}

	private static String signature() {
		LabSettings s = LabSettings.get();
		return s.barrierSurface + "/" + s.constructLook + "/" + s.wallLook + "/" + s.blueLook + "/" + s.yellowLook + "/" + s.redLook + "/" + s.violetLook + "/" + s.constructOpacity;
	}

	/** The strip's name (after construct_ripples_) this construct block shows, or null for its own model. */
	static String strip(BlockState state) {
		boolean brick = state.is(ModRegistry.CONSTRUCT_BRICK);
		if (!brick && !state.is(ModRegistry.LIGHT_CONSTRUCT)) return null;
		Corps corps = state.hasProperty(Corps.PROPERTY) ? state.getValue(Corps.PROPERTY) : Corps.GREEN;
		LabSettings s = LabSettings.get();
		return switch (corps) {
			case GREEN -> s.barrierSurface.strip != null ? s.barrierSurface.strip : brick ? s.wallLook.strip : s.constructLook.strip;
			case BLUE -> s.blueLook == LabSettings.BlueLook.H1 && brick ? "br1_blue" : s.blueLook.strip;
			case YELLOW -> s.yellowLook.strip;
			case RED -> s.redLook.strip;
			case VIOLET -> s.violetLook.strip;
			default -> null;
		};
	}

	/**
	 * With a barrier surface picked, construct pixels drift slowly off the outside faces of green constructs
	 * near you, a few per block, as on J's Blender barriers (the strip's twinkles stand in for them further off).
	 */
	private static void barrierPixels(Minecraft mc) {
		if (LabSettings.get().barrierSurface.strip == null || mc.level == null || mc.player == null || mc.isPaused()) return;
		RandomSource r = mc.level.getRandom();
		BlockPos centre = mc.player.blockPosition();
		Corps before = CorpsTint.enter(Corps.GREEN);
		try {
			for (int i = 0; i < 160; i++) {
				BlockPos pos = centre.offset(r.nextInt(25) - 12, r.nextInt(17) - 8, r.nextInt(25) - 12);
				BlockState state = mc.level.getBlockState(pos);
				if (!state.is(ModRegistry.CONSTRUCT_BRICK) && !state.is(ModRegistry.LIGHT_CONSTRUCT)) continue;
				if (state.hasProperty(Corps.PROPERTY) && state.getValue(Corps.PROPERTY) != Corps.GREEN) continue;
				Direction side = Direction.getRandom(r);
				BlockState next = mc.level.getBlockState(pos.relative(side));
				if (next.is(ModRegistry.CONSTRUCT_BRICK) || next.is(ModRegistry.LIGHT_CONSTRUCT) || next.isSolidRender()) continue;
				Vec3 normal = Vec3.atLowerCornerOf(side.getUnitVec3i());
				Vec3 at = Vec3.atCenterOf(pos).add(normal.scale(0.52))
						.add((r.nextDouble() - 0.5) * (1 - Math.abs(normal.x)), (r.nextDouble() - 0.5) * (1 - Math.abs(normal.y)), (r.nextDouble() - 0.5) * (1 - Math.abs(normal.z)));
				Vec3 drift = normal.scale(0.004).add((r.nextDouble() - 0.5) * 0.01, (r.nextDouble() - 0.5) * 0.01, (r.nextDouble() - 0.5) * 0.01);
				ConstructParticle p = LabFx.spawn(ModParticles.MOTE, at, drift, 0.35f);
				if (p != null) p.lasting(40 + r.nextInt(40));
			}
		} finally {
			CorpsTint.restore(before);
		}
	}

	/** Whether this construct block shows a glass look: drawn cutout at full alpha, no blending. */
	static boolean glass(BlockState state) {
		if (!state.is(ModRegistry.LIGHT_CONSTRUCT)) return false;
		Corps corps = state.hasProperty(Corps.PROPERTY) ? state.getValue(Corps.PROPERTY) : Corps.GREEN;
		return corps == Corps.GREEN && LabSettings.get().constructLook.glass;
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
