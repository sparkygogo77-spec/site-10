package com.sparky.lanternring.client;

import com.mojang.blaze3d.platform.NativeImage;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.texture.DynamicTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;

/**
 * Draws the ring's effects in its corps' colour. The effects were made green; {@link #apply}
 * turns any of their greens into the same shade of the corps' colour (keeping how pale or deep it
 * is), so every effect works for every corps without a colour of its own.
 *
 * <p>{@link #current} is the corps whose effect is being started right now: LabFx sets it while it
 * handles a server effect (from the payload's corps), a ring's glow, or a glowing block, and
 * particles and beams made meanwhile keep it.
 */
public final class CorpsTint {
	private static Corps current = Corps.GREEN;

	private CorpsTint() {
	}

	public static Corps current() {
		return current;
	}

	/** Makes {@code corps} current; hand the result back to {@link #restore}. */
	public static Corps enter(Corps corps) {
		Corps before = current;
		current = corps == null ? Corps.GREEN : corps;
		return before;
	}

	public static void restore(Corps before) {
		current = before;
	}

	/** {r, g, b} of a green effect colour, in {@code corps}' colour instead. */
	public static float[] apply(Corps corps, float r, float g, float b) {
		if (corps == Corps.GREEN) return new float[] {r, g, b};
		float v = Math.max(r, Math.max(g, b));
		if (v <= 0f) return new float[] {0, 0, 0};
		// How pale it is: a white-green core stays a white-red core.
		float pale = Math.min(r, Math.min(g, b)) / v * 0.6f;
		return new float[] {
				mix(corps.red() * v, v, pale),
				mix(corps.green() * v, v, pale),
				mix(corps.blue() * v, v, pale)};
	}

	public static int apply(Corps corps, int argb) {
		if (corps == Corps.GREEN) return argb;
		float[] c = apply(corps, (argb >> 16 & 0xFF) / 255f, (argb >> 8 & 0xFF) / 255f, (argb & 0xFF) / 255f);
		return argb & 0xFF000000 | Math.round(c[0] * 255) << 16 | Math.round(c[1] * 255) << 8 | Math.round(c[2] * 255);
	}

	/** A texture's version for the corps: textures/x.png becomes textures/x_red.png (see tools/corps_textures.py). */
	public static Identifier texture(Identifier green, Corps corps) {
		if (corps == Corps.GREEN) return green;
		String path = green.getPath();
		return green.withPath(path.substring(0, path.length() - 4) + "_" + corps.getSerializedName() + ".png");
	}

	/** Textures recoloured at run time by {@link #textureOrMade}, by green texture and corps. */
	private static final Map<String, Identifier> MADE = new HashMap<>();

	/**
	 * The corps' version of a green texture: the jar's own {@code _<corps>} file when there is one,
	 * otherwise one recoloured now the way tools/corps_textures.py does it (only the green and jade
	 * pixels turn to the corps' hue, so gold bands stay gold). The square, crown and round-face rings
	 * ship green only, so a Yellow ring used to show a green gem.
	 */
	public static Identifier textureOrMade(Identifier green, Corps corps) {
		if (corps == Corps.GREEN) return green;
		Identifier file = texture(green, corps);
		Minecraft mc = Minecraft.getInstance();
		if (mc.getResourceManager().getResource(file).isPresent()) return file;
		return MADE.computeIfAbsent(green + "/" + corps, k -> {
			String path = green.getPath();
			Identifier id = LanternRing.id("dynamic/" + path.substring(path.lastIndexOf('/') + 1, path.length() - 4) + "_" + corps.getSerializedName());
			try (InputStream in = mc.getResourceManager().open(green)) {
				NativeImage image = NativeImage.read(in);
				recolour(image, corps);
				mc.getTextureManager().register(id, new DynamicTexture(id::toString, image));
				return id;
			} catch (Exception e) {
				LanternRing.LOGGER.warn("Couldn't recolour {} for {}", green, corps, e);
				return green;
			}
		});
	}

	/** Target hue (degrees), saturation boost and brightness scale per corps, as in tools/corps_textures.py. */
	private static float[] style(Corps corps) {
		return switch (corps) {
			case RED -> new float[] {358f, 1.15f, 0.95f};
			case YELLOW -> new float[] {50f, 1.1f, 1.05f};
			case VIOLET -> new float[] {282f, 1.05f, 1f};
			case BLUE -> new float[] {205f, 1f, 1f};
			case ORANGE -> new float[] {25f, 1.15f, 1f};
			default -> null;
		};
	}

	/** Turns the image's greens (hue 70..190, not grey) to the corps' hue, keeping a little of their spread. */
	static void recolour(NativeImage image, Corps corps) {
		float[] st = style(corps);
		if (st == null) return;
		for (int y = 0; y < image.getHeight(); y++) {
			for (int x = 0; x < image.getWidth(); x++) {
				int argb = image.getPixel(x, y);
				if ((argb >>> 24) == 0) continue;
				int out = recolourPixel(argb, st);
				if (out != argb) image.setPixel(x, y, out);
			}
		}
	}

	static int recolourPixel(int argb, float[] st) {
		float r = (argb >> 16 & 0xFF) / 255f, g = (argb >> 8 & 0xFF) / 255f, b = (argb & 0xFF) / 255f;
		float max = Math.max(r, Math.max(g, b)), min = Math.min(r, Math.min(g, b));
		float d = max - min;
		float s = max <= 0f ? 0f : d / max;
		if (s < 0.18f || d <= 0f) return argb;
		float deg;
		if (max == r) deg = 60f * (((g - b) / d) % 6f);
		else if (max == g) deg = 60f * ((b - r) / d + 2f);
		else deg = 60f * ((r - g) / d + 4f);
		if (deg < 0f) deg += 360f;
		if (deg < 70f || deg > 190f) return argb;
		float hue = Mth.positiveModulo(st[0] + (deg - 140f) * 0.25f, 360f) / 360f;
		int rgb = Mth.hsvToRgb(hue, Math.min(1f, s * st[1]), Math.min(1f, max * st[2]));
		return argb & 0xFF000000 | rgb & 0xFFFFFF;
	}

	private static float mix(float a, float b, float t) {
		return a + (b - a) * t;
	}
}
