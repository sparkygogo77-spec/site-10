package com.sparky.lanternring.warren;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.core.QuartPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.biome.BiomeResolver;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.world.level.LevelHeightAccessor;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.RandomState;

/**
 * Where the Dread Warrens are. Each region has one chance of a Warren at a random spot in it, so they're spread like
 * a ravine or a mountain and nothing on the surface lines up with them (J, v2.0113 W1a5a: "it should be random
 * though"). A site needs land over it: never under an ocean or a river, and enough rock over the lair's roof.
 * <p>
 * The lair itself ({@link WarrenLair}) is carved round the site; mineshafts near it may carry an entrance down
 * ({@link WarrenEntrance}).
 */
public final class WarrenSites {
	/** One chance of a Warren per square region this many blocks across. */
	static final int REGION = 512;
	/** The chance a region has one. */
	static final float CHANCE = 0.7f;
	/** Mineshaft dead ends this close to a site (horizontally) can lead into it: J's "200 blocks wide", widened
	 * to 300 across so a normal mine near one usually reaches it (J on PR #364: "Easier to find"). */
	public static final int RADIUS = 150;
	/** Sites keep this far from their region's edge, so a lair (up to about 185 from its middle) and its entrances
	 * stay inside its own region and two never crowd each other. */
	private static final int MARGIN = 200;
	/** The land over a lair must be at least this high everywhere it's sampled (the roof reaches about y 30). */
	private static final int MIN_GROUND = 60;

	/** Set by tests: every mineshaft counts as near a Warren (its own site is still needed for the lair). */
	public static volatile boolean everywhereForTests;
	/** Set by tests before a world is made: the one Warren, at this {x, z}, land or not. */
	public static volatile int[] testSite;

	private static final Map<Long, Boolean> VALID = new ConcurrentHashMap<>();

	private WarrenSites() {
	}

	/** The site in region (rx, rz) as {x, z}, or null if that region has none (before the land check). */
	static int[] site(long seed, int rx, int rz) {
		int[] t = testSite;
		if (t != null) return Math.floorDiv(t[0], REGION) == rx && Math.floorDiv(t[1], REGION) == rz ? t : null;
		RandomSource r = RandomSource.create(seed ^ (rx * 341873128712L + rz * 132897987541L) ^ 0x5741_7272_656EL);
		if (r.nextFloat() >= CHANCE) return null;
		int span = REGION - 2 * MARGIN;
		return new int[] {rx * REGION + MARGIN + r.nextInt(span), rz * REGION + MARGIN + r.nextInt(span)};
	}

	/** The Warren site whose region holds (x, z), if there is one and it has land over it; else null. */
	public static int[] siteAt(long seed, int x, int z, ChunkGenerator gen, RandomState random, LevelHeightAccessor heights) {
		int rx = Math.floorDiv(x, REGION), rz = Math.floorDiv(z, REGION);
		int[] s = site(seed, rx, rz);
		if (s == null) return null;
		if (testSite != null) return s;
		long key = seed * 31 + (((long) rx) << 32 ^ (rz & 0xffffffffL));
		if (VALID.size() > 4096) VALID.clear();
		boolean ok = VALID.computeIfAbsent(key, k -> hasLand(s, gen, random, heights));
		return ok ? s : null;
	}

	/**
	 * Ocean and river floors are under y 60; hills and plains are over it. And never in the deep dark (the lair
	 * brief). Checked at the middle and 8 points round.
	 */
	private static boolean hasLand(int[] s, ChunkGenerator gen, RandomState random, LevelHeightAccessor heights) {
		BiomeResolver biomes = gen.getBiomeSource().createUncachedResolver(random);
		for (int i = -1; i < 8; i++) {
			double a = i * Math.PI / 4;
			int r = i < 0 ? 0 : 110;
			int x = s[0] + (int) (Math.cos(a) * r), z = s[1] + (int) (Math.sin(a) * r);
			if (gen.getBaseHeight(x, z, Heightmap.Types.OCEAN_FLOOR_WG, heights, random) < MIN_GROUND) return false;
			for (int y = -50; y <= 10; y += 20) {
				if (biomes.getNoiseBiome(QuartPos.fromBlock(x), QuartPos.fromBlock(y), QuartPos.fromBlock(z)).is(Biomes.DEEP_DARK)) return false;
			}
		}
		return true;
	}

	/** True if (x, z) lies within {@link #RADIUS} of a Warren site with land over it. */
	public static boolean near(long seed, int x, int z, ChunkGenerator gen, RandomState random, LevelHeightAccessor heights) {
		if (everywhereForTests) return true;
		// MARGIN > RADIUS, so only the region (x, z) is in can hold a site that reaches it.
		int[] s = siteAt(seed, x, z, gen, random, heights);
		if (s == null) return false;
		long dx = x - s[0], dz = z - s[1];
		return dx * dx + dz * dz <= (long) RADIUS * RADIUS;
	}
}
