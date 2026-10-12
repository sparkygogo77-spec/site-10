package com.sparky.lanternring.client.ally;

import com.mojang.blaze3d.platform.NativeImage;
import com.mojang.blaze3d.vertex.PoseStack;
import com.sparky.lanternring.LanternRing;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.texture.DynamicTexture;
import net.minecraft.resources.Identifier;

/**
 * Hard-light skins for the Army constructs, made when one is first drawn. Every face of every
 * cube in the vanilla model gets the cracked jade of the block constructs (construct_inner.png),
 * with a bright edge round it like the bricks' rims, so the warden, dragon or guardian shape reads
 * as built from glowing panes. The vanilla texture only shades it a little, so its face and
 * markings still show through. The faces are painted bright and nearly solid rather than faint
 * (a faint layer just looks dim; see the Blockbench glow note).
 */
public final class ConstructSkins {
	private static final Identifier JADE = LanternRing.id("textures/block/construct_inner.png");
	/** The jade frame is 128 px per block; model textures have 16 texels per block. */
	private static final int JADE_PER_TEXEL = 8;
	private static final Map<Identifier, Identifier> MADE = new HashMap<>();

	private ConstructSkins() {
	}

	/**
	 * The construct skin for a model: {@code vanilla} is the mob's own texture (for its size and
	 * shading), {@code scale} how many pixels each of its texels gets.
	 */
	public static Identifier get(String name, ModelPart root, Identifier vanilla, int scale) {
		Identifier id = LanternRing.id("dynamic/construct_" + name);
		if (MADE.containsKey(id)) return id;
		MADE.put(id, id);
		try {
			NativeImage image = paint(root, vanilla, scale);
			Minecraft.getInstance().getTextureManager().register(id, new DynamicTexture(() -> "lanternring construct " + name, image));
		} catch (Exception e) {
			LanternRing.LOGGER.warn("Couldn't make the {} construct skin", name, e);
			return vanilla;
		}
		return id;
	}

	private static NativeImage read(Identifier id) throws Exception {
		try (InputStream in = Minecraft.getInstance().getResourceManager().open(id)) {
			return NativeImage.read(in);
		}
	}

	private static NativeImage paint(ModelPart root, Identifier vanillaId, int scale) throws Exception {
		NativeImage jade = read(JADE);
		NativeImage vanilla = read(vanillaId);
		int tw = vanilla.getWidth(), th = vanilla.getHeight();
		int w = tw * scale, h = th * scale;
		NativeImage out = new NativeImage(w, h, true);
		int jadeSize = jade.getWidth();
		int step = Math.max(1, JADE_PER_TEXEL / scale);
		int edge = Math.max(1, scale / 2);
		root.visit(new PoseStack(), (pose, path, index, cube) -> {
			for (ModelPart.Polygon face : cube.polygons) {
				float u0 = 1, v0 = 1, u1 = 0, v1 = 0;
				for (ModelPart.Vertex v : face.vertices()) {
					u0 = Math.min(u0, v.u());
					v0 = Math.min(v0, v.v());
					u1 = Math.max(u1, v.u());
					v1 = Math.max(v1, v.v());
				}
				int x0 = Math.round(u0 * w), y0 = Math.round(v0 * h), x1 = Math.round(u1 * w), y1 = Math.round(v1 * h);
				for (int y = Math.max(0, y0); y < Math.min(h, y1); y++) {
					for (int x = Math.max(0, x0); x < Math.min(w, x1); x++) {
						boolean rim = x - x0 < edge || x1 - 1 - x < edge || y - y0 < edge || y1 - 1 - y < edge;
						out.setPixel(x, y, shade(jade, jadeSize, vanilla, x, y, scale, step, rim));
					}
				}
			}
		});
		jade.close();
		vanilla.close();
		return out;
	}

	/** One pixel: jade from the block texture, lit by the mob's own shading, or the bright rim. */
	private static int shade(NativeImage jade, int jadeSize, NativeImage vanilla, int x, int y, int scale, int step, boolean rim) {
		int j = jade.getPixel((x * step) % jadeSize, (y * step) % jadeSize);
		float r = (j >> 16 & 0xFF) / 255f, g = (j >> 8 & 0xFF) / 255f, b = (j & 0xFF) / 255f;
		int v = vanilla.getPixel(Math.min(vanilla.getWidth() - 1, x / scale), Math.min(vanilla.getHeight() - 1, y / scale));
		float lum = (0.3f * (v >> 16 & 0xFF) + 0.59f * (v >> 8 & 0xFF) + 0.11f * (v & 0xFF)) / 255f;
		if ((v >>> 24) < 16) lum = 0.5f;
		float light = 0.8f + 0.55f * lum;
		int alpha = 215;
		if (rim) {
			// The bright edge: near-white mint, fully solid.
			r = 0.72f;
			g = 1f;
			b = 0.8f;
			light = 1f;
			alpha = 255;
		}
		int ri = Math.min(255, Math.round(r * light * 255));
		int gi = Math.min(255, Math.round(g * light * 255));
		int bi = Math.min(255, Math.round(b * light * 255));
		return alpha << 24 | ri << 16 | gi << 8 | bi;
	}
}
