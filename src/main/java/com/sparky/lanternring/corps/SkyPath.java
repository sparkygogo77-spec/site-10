package com.sparky.lanternring.corps;

import java.util.ArrayDeque;
import java.util.Deque;
import net.minecraft.util.Mth;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

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
}
