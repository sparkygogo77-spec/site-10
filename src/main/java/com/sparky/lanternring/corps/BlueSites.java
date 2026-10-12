package com.sparky.lanternring.corps;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import org.jspecify.annotations.Nullable;

/**
 * Where the Blue Lantern crews build. Instead of taking the first patch that fits, a site picker
 * looks at many candidates and scores each one: flat ground, dry land, a comfortable distance
 * from the village centre (close enough to belong, far enough to leave a street), clear of other
 * crews' sites and of anything already built, and next to the village rather than out in the wilds.
 */
public final class BlueSites {
	private static final int CANDIDATES = 40;
	/** The ring round home that houses go in. */
	private static final double NEAR = 8, FAR = 26, IDEAL = 14;

	private BlueSites() {
	}

	/** The best low corner (at ground level) for a w by d footprint round {@code home}, or null if nowhere fits. */
	@Nullable
	public static BlockPos ground(ServerLevel level, BlockPos home, int w, int d, RandomSource rng) {
		BlockPos best = null;
		double bestScore = Double.MAX_VALUE;
		for (int i = 0; i < CANDIDATES; i++) {
			double a = rng.nextDouble() * Math.PI * 2;
			double dist = NEAR + rng.nextDouble() * (FAR - NEAR) + Math.max(w, d) * 0.5;
			int x = home.getX() + (int) Math.round(Math.cos(a) * dist) - w / 2;
			int z = home.getZ() + (int) Math.round(Math.sin(a) * dist) - d / 2;
			Double score = score(level, x, z, w, d, dist);
			if (score == null || score >= bestScore) continue;
			bestScore = score;
			int y = (int) Math.round(meanHeight(level, x, z, w, d));
			best = new BlockPos(x, y, z);
		}
		return best;
	}

	/** Lower is better; null rules the spot out. */
	@Nullable
	private static Double score(ServerLevel level, int x, int z, int w, int d, double dist) {
		int lo = Integer.MAX_VALUE, hi = Integer.MIN_VALUE;
		int built = 0;
		for (int dx = 0; dx < w; dx++) {
			for (int dz = 0; dz < d; dz++) {
				int top = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x + dx, z + dz) - 1;
				BlockPos p = new BlockPos(x + dx, top, z + dz);
				if (!level.isLoaded(p)) return null;
				if (!level.getFluidState(p).isEmpty() || !level.getFluidState(p.above()).isEmpty()) return null;
				BlockState s = level.getBlockState(p);
				if (!natural(s)) built++;
				lo = Math.min(lo, top);
				hi = Math.max(hi, top);
			}
		}
		// Someone's house, a road or a farm under it: never build over more than a corner of it.
		if (built > (w * d) / 8) return null;
		int y = (lo + hi) / 2;
		AABB box = new AABB(x, y - 2, z, x + w, y + 16, z + d);
		if (!BlueCrew.Claims.free(level, box, 2)) return null;
		int bumps = hi - lo;
		if (bumps > 4) return null;
		return bumps * 3.0 + built * 2.0 + Math.abs(dist - IDEAL) * 0.4;
	}

	private static double meanHeight(ServerLevel level, int x, int z, int w, int d) {
		double sum = 0;
		for (int dx = 0; dx < w; dx++) {
			for (int dz = 0; dz < d; dz++) sum += level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x + dx, z + dz) - 1;
		}
		return sum / (w * d);
	}

	private static boolean natural(BlockState s) {
		return s.is(BlockTags.DIRT) || s.is(BlockTags.SAND) || s.is(BlockTags.BASE_STONE_OVERWORLD) || s.is(Blocks.GRAVEL)
				|| s.is(Blocks.SNOW_BLOCK) || s.is(Blocks.SNOW);
	}
}
