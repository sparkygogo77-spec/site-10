package com.sparky.lanternring.warren;

import net.minecraft.util.RandomSource;

/**
 * Where the Dread Warrens are. Nothing is placed for a Warren itself yet (J said "Not yet" to the lair, 2026-10-19):
 * a site is only a point the world seed picks, and mineshafts round it may carry an entrance down
 * ({@link WarrenEntrance}). Sites are spread like a ravine or a mountain: one chance per region, at a random spot in
 * it, so nothing on the surface lines up with them (J, v2.0113 W1a5a: "it should be random though").
 */
public final class WarrenSites {
	/** One chance of a Warren per square region this many blocks across. */
	static final int REGION = 512;
	/** The chance a region has one. */
	static final float CHANCE = 0.5f;
	/** Mineshaft dead ends this close to a site (horizontally) can lead into it: J's "200 blocks wide". */
	public static final int RADIUS = 100;
	/** Sites keep this far from their region's edge, so two never crowd each other. */
	private static final int MARGIN = RADIUS + 28;
	/** Set by tests: every region has a site at every mineshaft. */
	public static volatile boolean everywhereForTests;

	private WarrenSites() {
	}

	/** The site in region (rx, rz) as {x, z}, or null if that region has none. */
	static int[] site(long seed, int rx, int rz) {
		RandomSource r = RandomSource.create(seed ^ (rx * 341873128712L + rz * 132897987541L) ^ 0x5741_7272_656EL);
		if (r.nextFloat() >= CHANCE) return null;
		int span = REGION - 2 * MARGIN;
		return new int[] {rx * REGION + MARGIN + r.nextInt(span), rz * REGION + MARGIN + r.nextInt(span)};
	}

	/** True if (x, z) lies within {@link #RADIUS} of a Warren site. */
	public static boolean near(long seed, int x, int z) {
		if (everywhereForTests) return true;
		int rx = Math.floorDiv(x, REGION), rz = Math.floorDiv(z, REGION);
		// MARGIN > RADIUS, so only the region (x, z) is in can hold a site that reaches it.
		int[] s = site(seed, rx, rz);
		if (s == null) return false;
		long dx = x - s[0], dz = z - s[1];
		return dx * dx + dz * dz <= (long) RADIUS * RADIUS;
	}
}
