package com.sparky.lanternring.client;

import net.minecraft.util.Mth;

/**
 * Real glow under the Lantern Ring copy of a Complementary pack ({@link ShaderPackPatcher}).
 *
 * <p>Shader packs light entities, the hand and particles by their lightmap, and only blocks and
 * items they know by ID give off light and bloom. The ring, its charge and its particles are none
 * of those, so under a pack they were merely lit, a flat green with no glow round it. The patched
 * pack treats anything drawn with sky light above vanilla's maximum (15, stored as 240) as the
 * mod's glow: it adds emission there, which the pack's bloom then spreads into a soft halo. The
 * block light carries how strong the glow is. With no shader pack, or another pack, this is the
 * usual full-bright light.
 */
public final class ShaderGlow {
	private static final int FULL_BRIGHT = 0xF000F0;
	/** Sky light 255: past anything vanilla stores, so the patched pack can tell it apart. */
	private static final int MARKER = 0xFF << 16;

	private static java.lang.reflect.Method packName;
	private static boolean failed;
	private static long checkedAt = Long.MIN_VALUE;
	private static boolean patched;

	private ShaderGlow() {
	}

	/** Full-strength glow light. */
	public static int light() {
		return light(1f);
	}

	/** The light for something glowing at {@code strength} (0..1, kept above 0.5 so other packs still see it lit). */
	public static int light(float strength) {
		if (!patchedPackOn()) return FULL_BRIGHT;
		return MARKER | Mth.clamp(Math.round(strength * 240), 120, 240);
	}

	/** Whether the shader pack in use is a Lantern Ring copy (checked once a second). */
	public static boolean patchedPackOn() {
		if (!SoulSight.shaderPackOn()) return false;
		long now = System.nanoTime();
		if (now - checkedAt < 1_000_000_000L) return patched;
		checkedAt = now;
		patched = currentPackName().contains("Lantern Ring");
		return patched;
	}

	/** Iris's current pack name, or a Lantern Ring one when Iris can't be asked (the marker is harmless elsewhere). */
	private static String currentPackName() {
		if (failed) return "Lantern Ring";
		try {
			if (packName == null) packName = Class.forName("net.irisshaders.iris.Iris").getMethod("getCurrentPackName");
			Object name = packName.invoke(null);
			return name == null ? "" : name.toString();
		} catch (ReflectiveOperationException | RuntimeException | LinkageError e) {
			failed = true;
			return "Lantern Ring";
		}
	}
}
