package com.sparky.lanternring.corps;

import java.util.ArrayDeque;
import java.util.Deque;
import net.minecraft.util.Mth;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * Levitation routes for ring-flying villagers. A short hop goes straight there; a longer flight
 * lifts off to a cruising height that clears every tree, roof and hill under the line (sampled
 * along it), crosses at that height, and comes down over the destination, the way a ring
 * bearer flies rather than a mob pathing on foot. Anything missed on the way is climbed over
 * (see CorpsVillager.flyStep).
 */
public final class SkyPath {
	/** Blocks over the highest thing below the route. */
	private static final int CLEARANCE = 3;
	/** Shorter flights than this (horizontally) go straight. */
	private static final double DIRECT = 6;

	private SkyPath() {
	}

	/** The waypoints from {@code from} to {@code to}, ending at {@code to}. */
	public static Deque<Vec3> plan(Level level, Vec3 from, Vec3 to) {
		Deque<Vec3> out = new ArrayDeque<>();
		// Under a roof or an eave: first slip out sideways to open sky, or it would fly up into the
		// ceiling and hang there (J's founder never reached its island, 2026-10-12).
		Vec3 out0 = openSky(level, from);
		if (out0 != null) {
			out.add(out0);
			from = out0;
		}
		double dx = to.x - from.x, dz = to.z - from.z;
		double horizontal = Math.sqrt(dx * dx + dz * dz);
		if (horizontal >= DIRECT) {
			int top = Integer.MIN_VALUE;
			int steps = Mth.ceil(horizontal / 2);
			for (int i = 0; i <= steps; i++) {
				double t = i / (double) steps;
				int x = Mth.floor(from.x + dx * t), z = Mth.floor(from.z + dz * t);
				top = Math.max(top, level.getHeight(Heightmap.Types.MOTION_BLOCKING, x, z));
			}
			double cruise = Math.min(level.getMaxY() - 2, Math.max(top + CLEARANCE, Math.max(from.y, to.y)));
			if (cruise > from.y + 1) out.add(new Vec3(from.x, cruise, from.z));
			if (cruise > to.y + 1) out.add(new Vec3(to.x, cruise, to.z));
		}
		out.add(to);
		return out;
	}

	/** If something is overhead at {@code from}, the nearest spot at the same height with open sky above it. */
	private static @Nullable Vec3 openSky(Level level, Vec3 from) {
		int fx = Mth.floor(from.x), fz = Mth.floor(from.z), fy = Mth.floor(from.y);
		if (level.getHeight(Heightmap.Types.MOTION_BLOCKING, fx, fz) <= fy + 1) return null;
		for (int r = 1; r <= 12; r++) {
			Vec3 best = null;
			double bestD = Double.MAX_VALUE;
			for (int dx = -r; dx <= r; dx++) {
				for (int dz = -r; dz <= r; dz++) {
					if (Math.max(Math.abs(dx), Math.abs(dz)) != r) continue;
					if (level.getHeight(Heightmap.Types.MOTION_BLOCKING, fx + dx, fz + dz) > fy + 1) continue;
					double d = dx * dx + dz * dz;
					if (d < bestD) {
						bestD = d;
						best = new Vec3(fx + dx + 0.5, from.y, fz + dz + 0.5);
					}
				}
			}
			if (best != null) return best;
		}
		return null;
	}
}
