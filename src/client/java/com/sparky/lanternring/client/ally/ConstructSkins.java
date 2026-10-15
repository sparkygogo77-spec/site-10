package com.sparky.lanternring.client.ally;

import com.mojang.blaze3d.platform.NativeImage;
import com.mojang.blaze3d.vertex.PoseStack;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.client.CorpsTint;
import com.sparky.lanternring.client.LabSettings;
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
 * layer just looks dim; see the Blockbench glow note). Red constructs wear J's Red construct look
 * instead (Ring Lab "Red constructs", R1 magma or R2 bloodfire), stepping through its frames.
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
	/** Frames of the Red look's strip a skin steps through, and the ticks each one shows. */
	private static final int RED_FRAMES = 8;
	private static final int RED_FRAME_TICKS = 6;

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
		String strip = corps == Corps.RED ? LabSettings.get().redLook.strip : null;
		if (strip != null) return red(name, root, vanilla, scale, strip);
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

	/**
	 * The Red look skin (J's pick, 2026-10-14): the mob's shading over the picked Red construct strip
	 * (construct_ripples_red_r1/r2) instead of tinted jade, with the same bright rim, stepping through
	 * RED_FRAMES of the strip as the game runs, like the Wall does.
	 */
	private static Identifier red(String name, ModelPart root, Identifier vanilla, int scale, String strip) {
		Minecraft mc = Minecraft.getInstance();
		long time = mc.level == null ? 0 : mc.level.getGameTime();
		int frame = (int) (time / RED_FRAME_TICKS % RED_FRAMES);
		Identifier id = LanternRing.id("dynamic/construct_" + name + "_" + strip + "_" + frame);
		if (MADE.containsKey(id)) return id;
		MADE.put(id, id);
		try {
			NativeImage pattern = read(LanternRing.id("textures/block/construct_ripples_" + strip + ".png"));
			NativeImage image = paintRed(root, vanilla, scale, pattern, frame);
			pattern.close();
			mc.getTextureManager().register(id, new DynamicTexture(() -> "lanternring construct " + name + " " + strip, image));
		} catch (Exception e) {
			LanternRing.LOGGER.warn("Couldn't make the {} {} construct skin", name, strip, e);
			MADE.remove(id);
			return get(name, root, vanilla, scale, Corps.GREEN);
		}
		return id;
	}

	private static NativeImage paintRed(ModelPart root, Identifier vanillaId, int scale, NativeImage pattern, int frame) throws Exception {
		NativeImage vanilla = read(vanillaId);
		int tw = vanilla.getWidth(), th = vanilla.getHeight();
		int w = tw * scale, h = th * scale;
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
		int size = pattern.getWidth();
		int frames = Math.max(1, pattern.getHeight() / size);
		int top = frame * frames / RED_FRAMES * size;
		// A strip spans 4 blocks (64 model texels) at whatever resolution it has (R2 is 256 px).
		float step = size / 64f / scale;
		NativeImage out = new NativeImage(w, h, true);
		for (int y = 0; y < h; y++) {
			for (int x = 0; x < w; x++) {
				int v = vanilla.getPixel(x / scale, y / scale);
				int a = v >>> 24;
				if (a < 16) continue;
				float t = Math.max(0f, Math.min(1f, (luminance(v) - lo) / range));
				int p = pattern.getPixel(Math.floorMod((int) (x * step), size), top + Math.floorMod((int) (y * step), size));
				// The strip's own colour, lit by the mob's shading so its face and muscles still read.
				// J (2026-10-14): brighter, so the bull reads from a distance: the strip lifted and a red glow under it.
				float k = 1.7f + 1.2f * t;
				int rgb = rgb(0.16f + (p >> 16 & 0xFF) / 255f * k, 0.02f + (p >> 8 & 0xFF) / 255f * k, 0.01f + (p & 0xFF) / 255f * k);
				out.setPixel(x, y, Math.min(a, Math.max(200, Math.min(240, p >>> 24))) << 24 | rgb);
			}
		}
		rim(root, out, w, h, scale, 0xFF7A4A);
		vanilla.close();
		return out;
	}

	/** How opaque a stretched construct texture is (Blender pass 828: 88%). */
	private static final int STRETCHED_ALPHA = 224;

	/**
	 * Blender pass 828's construct animals: only the construct texture, 88% opaque and stretched across each face of each
	 * cube of the model (no mob shading under it), stepping through RED_FRAMES of the strip like the Red look. One frame
	 * of {@code strip} (textures/block/construct_ripples_&lt;strip&gt;) covers a cube's longest edge rounded up to 4, 8 or
	 * 16 texels, as the Blender boxes tile it (a pig's body one frame per block, head and legs per half, snout per
	 * quarter). {@code texW} x {@code texH} is the model's texture size and {@code scale} the pixels per texel;
	 * {@code eyes} lists texels (x, y pairs) painted solid in the rim colour.
	 */
	public static Identifier stretched(String name, ModelPart root, int texW, int texH, int scale, String strip, Corps corps, int... eyes) {
		Minecraft mc = Minecraft.getInstance();
		long time = mc.level == null ? 0 : mc.level.getGameTime();
		int frame = (int) (time / RED_FRAME_TICKS % RED_FRAMES);
		Identifier id = LanternRing.id("dynamic/construct_" + name + "_" + strip + "_" + corps.getSerializedName() + "_" + frame);
		if (MADE.containsKey(id)) return id;
		MADE.put(id, id);
		try {
			NativeImage pattern = read(LanternRing.id("textures/block/construct_ripples_" + strip + ".png"));
			NativeImage image = paintStretched(root, texW * scale, texH * scale, scale, pattern, frame);
			pattern.close();
			for (int i = 0; i + 1 < eyes.length; i += 2) {
				for (int y = 0; y < scale; y++) {
					for (int x = 0; x < scale; x++) image.setPixel(eyes[i] * scale + x, eyes[i + 1] * scale + y, 0xFF << 24 | 0xB8FFCC);
				}
			}
			tint(image, corps);
			mc.getTextureManager().register(id, new DynamicTexture(() -> "lanternring construct " + name + " " + strip, image));
		} catch (Exception e) {
			LanternRing.LOGGER.warn("Couldn't make the {} {} construct skin", name, strip, e);
			return LanternRing.id("textures/block/construct_ripples_" + strip + ".png");
		}
		return id;
	}

	private static NativeImage paintStretched(ModelPart root, int w, int h, int scale, NativeImage pattern, int frame) {
		int size = pattern.getWidth();
		int frames = Math.max(1, pattern.getHeight() / size);
		int top = frame * frames / RED_FRAMES * size;
		NativeImage out = new NativeImage(w, h, true);
		root.visit(new PoseStack(), (pose, path, index, cube) -> {
			// The cube's longest edge in texels, rounded up to 4, 8 or 16: how much one frame of the strip covers.
			float longest = 0;
			for (ModelPart.Polygon face : cube.polygons) {
				float u0 = 1, v0 = 1, u1 = 0, v1 = 0;
				for (ModelPart.Vertex v : face.vertices()) {
					u0 = Math.min(u0, v.u());
					v0 = Math.min(v0, v.v());
					u1 = Math.max(u1, v.u());
					v1 = Math.max(v1, v.v());
				}
				longest = Math.max(longest, Math.max((u1 - u0) * w, (v1 - v0) * h) / scale);
			}
			int tile = longest > 8.01f ? 16 : longest > 4.01f ? 8 : 4;
			float step = size / (float) (tile * scale);
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
						int p = pattern.getPixel(Math.floorMod((int) ((x - x0) * step), size), top + Math.floorMod((int) ((y - y0) * step), size));
						// The strip's own colour; its clear texels stay faintly lit so the shape still reads.
						int a = p >>> 24;
						int rgb = a < 16 ? 0x0E3A1C : p & 0xFFFFFF;
						out.setPixel(x, y, STRETCHED_ALPHA << 24 | rgb);
					}
				}
			}
		});
		return out;
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
		rim(root, out, w, h, scale, 0xB8FFCC);
		jade.close();
		vanilla.close();
		return out;
	}

	/** The thin bright line round each face of each cube, in {@code colour}. */
	private static void rim(ModelPart root, NativeImage out, int w, int h, int scale, int colour) {
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
						out.setPixel(x, y, 0xFF << 24 | mix(p, colour, 0.65f));
					}
				}
			}
		});
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
