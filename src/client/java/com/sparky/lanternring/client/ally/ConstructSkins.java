package com.sparky.lanternring.client.ally;

import com.mojang.blaze3d.platform.NativeImage;
import com.mojang.blaze3d.vertex.PoseStack;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.client.CorpsTint;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.texture.DynamicTexture;
import net.minecraft.resources.Identifier;

/**
 * Hard-light skins for the Army constructs, made when one is first drawn from the mob's own
 * texture: every detail of the warden, dragon or guardian kept, recoloured into jade with the
 * R2 K1 dark jade fragments (construct_skin_r2k1.png) over it and a thin bright rim round each
 * cube face (see paint). The faces are painted bright and nearly solid rather than faint (a faint
 * layer just looks dim; see the Blockbench glow note).
 */
public final class ConstructSkins {
	/**
	 * The pattern laid over the skin: J's pick for the bull and the other constructs (2026-10-12), one frame of
	 * the R2 small fragments in K1 dark jade over the cloudy jade, as a brightness map (tools/construct_jade_game.py
	 * makes the ripples; construct_skin_r2k1.png is 4 blocks at 64 px a block).
	 */
	private static final Identifier JADE = LanternRing.id("textures/block/construct_skin_r2k1.png");
	/** The pattern is 64 px per block; model textures have 16 texels per block. */
	private static final int JADE_PER_TEXEL = 4;
	private static final Map<Identifier, Identifier> MADE = new HashMap<>();

	private ConstructSkins() {
	}

	/**
	 * The construct skin for a model: {@code vanilla} is the mob's own texture (for its size and
	 * shading), {@code scale} how many pixels each of its texels gets.
	 */
	public static Identifier get(String name, ModelPart root, Identifier vanilla, int scale) {
		return get(name, root, vanilla, scale, Corps.GREEN);
	}

	/** The same in another corps' colour (the jade turned to it, see CorpsTint). */
	public static Identifier get(String name, ModelPart root, Identifier vanilla, int scale, Corps corps) {
		Identifier id = LanternRing.id("dynamic/construct_" + name + (corps == Corps.GREEN ? "" : "_" + corps.getSerializedName()));
		if (MADE.containsKey(id)) return id;
		MADE.put(id, id);
		try {
			NativeImage image = paint(root, vanilla, scale);
			tint(image, corps);
			Minecraft.getInstance().getTextureManager().register(id, new DynamicTexture(() -> "lanternring construct " + name, image));
		} catch (Exception e) {
			LanternRing.LOGGER.warn("Couldn't make the {} construct skin", name, e);
			return vanilla;
		}
		return id;
	}

	/** Turns a jade image into the corps' colour, keeping how deep or bright each pixel is. */
	private static void tint(NativeImage image, Corps corps) {
		if (corps == Corps.GREEN) return;
		for (int y = 0; y < image.getHeight(); y++) {
			for (int x = 0; x < image.getWidth(); x++) {
				int v = image.getPixel(x, y);
				if ((v >>> 24) == 0) continue;
				image.setPixel(x, y, CorpsTint.apply(corps, v));
			}
		}
	}

	private static NativeImage read(Identifier id) throws Exception {
		try (InputStream in = Minecraft.getInstance().getResourceManager().open(id)) {
			return NativeImage.read(in);
		}
	}

	/**
	 * A glowing layer for a model (the warden's bioluminescent spots and heart, the dragon's eyes):
	 * the vanilla layer's own shapes, recoloured bright mint.
	 */
	public static Identifier glow(String name, Identifier vanilla) {
		return glow(name, vanilla, Corps.GREEN);
	}

	public static Identifier glow(String name, Identifier vanilla, Corps corps) {
		Identifier id = LanternRing.id("dynamic/construct_glow_" + name + (corps == Corps.GREEN ? "" : "_" + corps.getSerializedName()));
		if (MADE.containsKey(id)) return id;
		MADE.put(id, id);
		try {
			NativeImage image = read(vanilla);
			for (int y = 0; y < image.getHeight(); y++) {
				for (int x = 0; x < image.getWidth(); x++) {
					int v = image.getPixel(x, y);
					int a = v >>> 24;
					if (a == 0) continue;
					float lum = Math.max(0.55f, luminance(v));
					image.setPixel(x, y, a << 24 | rgb(0.62f * lum + 0.2f, 1f, 0.72f * lum + 0.15f));
				}
			}
			tint(image, corps);
			Minecraft.getInstance().getTextureManager().register(id, new DynamicTexture(() -> "lanternring construct glow " + name, image));
		} catch (Exception e) {
			LanternRing.LOGGER.warn("Couldn't make the {} construct glow", name, e);
			return vanilla;
		}
		return id;
	}

	/**
	 * The mob's own texture at {@code scale} times the size, every pixel turned to jade by its
	 * brightness (so its face, ribs, scales and markings all stay), with the cracked jade of the
	 * block constructs laid over it and a thin bright line round each face of each cube. Holes in
	 * the vanilla texture (the warden's ribcage, the dragon's wing webs) stay holes.
	 */
	private static NativeImage paint(ModelPart root, Identifier vanillaId, int scale) throws Exception {
		NativeImage jade = read(JADE);
		NativeImage vanilla = read(vanillaId);
		int tw = vanilla.getWidth(), th = vanilla.getHeight();
		int w = tw * scale, h = th * scale;
		// Stretch the mob's brightness range to the full jade ramp, so dark mobs (the warden,
		// the dragon) keep their contrast instead of all turning the same deep green.
		float lo = 1f, hi = 0f;
		for (int y = 0; y < th; y++) {
			for (int x = 0; x < tw; x++) {
				int v = vanilla.getPixel(x, y);
				if ((v >>> 24) < 128) continue;
				float l = luminance(v);
				lo = Math.min(lo, l);
				hi = Math.max(hi, l);
			}
		}
		float range = Math.max(0.05f, hi - lo);
		int jadeSize = jade.getWidth();
		int step = Math.max(1, JADE_PER_TEXEL / scale);
		float jadeAvg = 0;
		for (int i = 0; i < 64; i++) jadeAvg += luminance(jade.getPixel((i * 37) % jadeSize, (i * 53) % jadeSize));
		jadeAvg /= 64;
		NativeImage out = new NativeImage(w, h, true);
		for (int y = 0; y < h; y++) {
			for (int x = 0; x < w; x++) {
				int v = vanilla.getPixel(x / scale, y / scale);
				int a = v >>> 24;
				if (a < 16) continue;
				float t = (luminance(v) - lo) / range;
				float crack = luminance(jade.getPixel((x * step) % jadeSize, (y * step) % jadeSize)) / Math.max(0.05f, jadeAvg);
				float k = 0.45f + 0.55f * crack;  // the dark fragments show clearly, the jade between stays bright
				out.setPixel(x, y, Math.min(a, 240) << 24 | ramp(t, k));
			}
		}
		// The thin bright line round each cube face.
		int edge = Math.max(1, scale / 4);
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
						int p = out.getPixel(x, y);
						if (!rim || (p >>> 24) == 0) continue;
						out.setPixel(x, y, 0xFF << 24 | mix(p, 0xB8FFCC, 0.65f));
					}
				}
			}
		});
		jade.close();
		vanilla.close();
		return out;
	}

	/** Deep jade in the shadows, bright mint in the highlights, scaled by the crackle k. */
	private static int ramp(float t, float k) {
		t = Math.max(0, Math.min(1, t));
		float r, g, b;
		if (t < 0.5f) {
			float u = t / 0.5f;
			r = 0.07f + 0.15f * u;
			g = 0.32f + 0.34f * u;
			b = 0.19f + 0.21f * u;
		} else {
			float u = (t - 0.5f) / 0.5f;
			r = 0.22f + 0.50f * u;
			g = 0.66f + 0.34f * u;
			b = 0.40f + 0.40f * u;
		}
		return rgb(r * k, g * k, b * k);
	}

	private static float luminance(int argb) {
		return (0.3f * (argb >> 16 & 0xFF) + 0.59f * (argb >> 8 & 0xFF) + 0.11f * (argb & 0xFF)) / 255f;
	}

	private static int rgb(float r, float g, float b) {
		return clamp(r) << 16 | clamp(g) << 8 | clamp(b);
	}

	private static int clamp(float c) {
		return Math.max(0, Math.min(255, Math.round(c * 255)));
	}

	private static int mix(int argb, int rgb, float f) {
		int r = Math.round((argb >> 16 & 0xFF) * (1 - f) + (rgb >> 16 & 0xFF) * f);
		int g = Math.round((argb >> 8 & 0xFF) * (1 - f) + (rgb >> 8 & 0xFF) * f);
		int b = Math.round((argb & 0xFF) * (1 - f) + (rgb & 0xFF) * f);
		return r << 16 | g << 8 | b;
	}
}
