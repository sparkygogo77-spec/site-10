package com.sparky.lanternring.client;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModRegistry;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.data.AtlasIds;
import net.minecraft.util.Mth;
import net.minecraft.world.level.block.state.BlockState;

/**
 * The Nebula lantern's light wrapped in the corps' construct look strip (Blender pass 430, J:
 * "wrap our textures around the light source"; Ring Lab "Nebula light"). Each take in
 * bbmodel/nebula_light_profiles.json is a lathe: [y, radius] profiles in nebula_lantern.bbmodel
 * pixels turned round its axis. One strip frame wraps once round (u), and v runs down the profile
 * with square texels at the widest ring. The strip is the block-atlas sprite the corps' light
 * constructs use, so it animates by itself and the light needs no texture of its own.
 *
 * <p>Drawn in the same space as a BbModel (Blockbench pixels / 16), in two passes: a dim solid pass
 * a hair inside, so the strip's see-through texels read as its dark body, then the strip itself,
 * full-bright and tinted by {@code glow}.
 */
final class NebulaStripLight {
	private static final int FULL_BRIGHT = 0xF000F0;
	/** How bright the solid inner pass is: the strip's own tones, darkened. */
	private static final float CORE = 0.22f;

	private record Part(int segments, int every, float[][] profile, float[] v) {
	}

	private static Map<String, List<Part>> takes;

	private NebulaStripLight() {
	}

	/** Draws the take's light for the corps; false if the take or the corps' strip is missing (draw the classic light). */
	static boolean draw(PoseStack poseStack, SubmitNodeCollector collector, String take, Corps corps, float glow) {
		List<Part> parts = load().get(take);
		TextureAtlasSprite sprite = sprite(corps);
		if (parts == null || sprite == null) return false;
		float g = Mth.clamp(glow, 0f, 1f);
		collector.submitCustomGeometry(poseStack, RenderTypes.entitySolid(TextureAtlas.LOCATION_BLOCKS),
				(pose, vc) -> quads(pose, vc, parts, sprite, 0.97f, CORE, FULL_BRIGHT));
		collector.submitCustomGeometry(poseStack, RenderTypes.entityTranslucentEmissive(TextureAtlas.LOCATION_BLOCKS),
				(pose, vc) -> quads(pose, vc, parts, sprite, 1f, g, ShaderGlow.light()));
		return true;
	}

	/** The corps' light-construct strip (W1 neon for green when its pick has none), or null for a corps without one. */
	private static TextureAtlasSprite sprite(Corps corps) {
		BlockState state = ModRegistry.LIGHT_CONSTRUCT.defaultBlockState();
		if (state.hasProperty(Corps.PROPERTY)) state = state.setValue(Corps.PROPERTY, corps);
		TextureAtlasSprite s = ConstructLooks.sprite(state);
		if (s != null || corps != Corps.GREEN) return s;
		TextureAtlas atlas = Minecraft.getInstance().getAtlasManager().getAtlasOrThrow(AtlasIds.BLOCKS);
		TextureAtlasSprite w1 = atlas.getSprite(LanternRing.id("block/construct_ripples_w1_neon"));
		return w1 == atlas.missingSprite() ? null : w1;
	}

	private static void quads(PoseStack.Pose pose, VertexConsumer vc, List<Part> parts, TextureAtlasSprite s, float shrink, float c, int light) {
		for (Part part : parts) {
			float[][] prof = part.profile;
			for (int k = 0; k < part.segments; k += part.every) {
				float a0 = Mth.TWO_PI * k / part.segments, a1 = Mth.TWO_PI * (k + 1) / part.segments;
				// u runs left to right seen from outside
				float u0 = Mth.lerp(1f - (float) k / part.segments, s.getU0(), s.getU1());
				float u1 = Mth.lerp(1f - (float) (k + 1) / part.segments, s.getU0(), s.getU1());
				float am = (a0 + a1) / 2;
				float nx = Mth.sin(am), nz = -Mth.cos(am);
				for (int j = 0; j + 1 < prof.length; j++) {
					float y0 = prof[j][0], r0 = prof[j][1] * shrink, y1 = prof[j + 1][0], r1 = prof[j + 1][1] * shrink;
					float v0 = Mth.lerp(Math.min(1f, part.v[j]), s.getV0(), s.getV1());
					float v1 = Mth.lerp(Math.min(1f, part.v[j + 1]), s.getV0(), s.getV1());
					float[][] q = {
							{r0 * Mth.sin(a0), y0, -r0 * Mth.cos(a0), u0, v0},
							{r1 * Mth.sin(a0), y1, -r1 * Mth.cos(a0), u0, v1},
							{r1 * Mth.sin(a1), y1, -r1 * Mth.cos(a1), u1, v1},
							{r0 * Mth.sin(a1), y0, -r0 * Mth.cos(a1), u1, v0}};
					for (int side = 0; side < 2; side++) {
						float n = side == 0 ? 1 : -1;
						for (int i = 0; i < 4; i++) {
							float[] p = q[side == 0 ? i : 3 - i];
							vc.addVertex(pose, p[0] / 16f, p[1] / 16f, p[2] / 16f)
									.setColor(c, c, c, 1f)
									.setUv(p[3], p[4])
									.setOverlay(OverlayTexture.NO_OVERLAY)
									.setLight(light)
									.setNormal(pose, nx * n, 0, nz * n);
						}
					}
				}
			}
		}
	}

	private static Map<String, List<Part>> load() {
		if (takes != null) return takes;
		takes = new HashMap<>();
		String path = "/assets/" + LanternRing.MOD_ID + "/bbmodel/nebula_light_profiles.json";
		try (InputStream in = NebulaStripLight.class.getResourceAsStream(path)) {
			if (in == null) return takes;
			JsonObject all = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonObject("takes");
			for (Map.Entry<String, JsonElement> take : all.entrySet()) {
				List<Part> parts = new ArrayList<>();
				for (JsonElement e : take.getValue().getAsJsonObject().getAsJsonArray("parts")) {
					JsonObject p = e.getAsJsonObject();
					var arr = p.getAsJsonArray("profile");
					float[][] prof = new float[arr.size()][];
					float rmax = 0;
					for (int i = 0; i < prof.length; i++) {
						var pt = arr.get(i).getAsJsonArray();
						prof[i] = new float[] {pt.get(0).getAsFloat(), pt.get(1).getAsFloat()};
						rmax = Math.max(rmax, prof[i][1]);
					}
					// v: arc length down the profile over the widest ring's circumference
					float[] v = new float[prof.length];
					for (int i = 1; i < prof.length; i++) {
						v[i] = v[i - 1] + (float) Math.hypot(prof[i][0] - prof[i - 1][0], prof[i][1] - prof[i - 1][1]) / (Mth.TWO_PI * rmax);
					}
					parts.add(new Part(p.get("segments").getAsInt(), p.has("every") ? p.get("every").getAsInt() : 1, prof, v));
				}
				takes.put(take.getKey(), parts);
			}
		} catch (Exception e) {
			LanternRing.LOGGER.warn("Couldn't read {}", path, e);
		}
		return takes;
	}
}
