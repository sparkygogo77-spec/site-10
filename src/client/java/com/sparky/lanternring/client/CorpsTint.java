package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import net.minecraft.resources.Identifier;

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

	private static float mix(float a, float b, float t) {
		return a + (b - a) * t;
	}
}
