package com.sparky.lanternring;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * What the Anvil mode drops at each of its three levels: the anvil, a mining drill bit falling
 * point first, and a ship's anchor falling crown first. Each is a set of blocks given as offsets
 * from the middle of its bottom: x along its long side (laid across the bearer's view), y up, z
 * front to back.
 *
 * <p>While it falls a shape is drawn as moving block displays. To keep that to a few dozen or a few
 * hundred entities, its blocks are covered with cubes as big as fit (up to {@code maxBody} blocks
 * on a side), and each cube is one scaled display.
 */
public enum AnvilShape {
	ANVIL(1, 1),
	DRILL(3, 3),
	ANCHOR(5, 3);

	/** The level's id, stored on the ring: 1, 3 or 5 (once sizes of the anvil). */
	public final int size;
	/** Every block, as {x, y, z}. */
	public final List<int[]> blocks = new ArrayList<>();
	/** Cubes covering the blocks for the moving display: {x, y, z, edge}, x/y/z the low corner. */
	public final List<int[]> bodies = new ArrayList<>();
	public final int height;
	/** Furthest any block reaches sideways from the middle, along and across. */
	public final int reachAlong;
	public final int reachAcross;

	AnvilShape(int size, int maxBody) {
		this.size = size;
		Set<Long> set = new HashSet<>();
		switch (size) {
			case 1 -> anvil(set);
			case 3 -> drill(set);
			default -> anchor(set);
		}
		int top = 0, along = 0, across = 0;
		for (long key : set) {
			int[] b = unpack(key);
			blocks.add(b);
			top = Math.max(top, b[1]);
			along = Math.max(along, Math.abs(b[0]));
			across = Math.max(across, Math.abs(b[2]));
		}
		blocks.sort(Comparator.<int[]>comparingInt(b -> b[1]).thenComparingInt(b -> b[0]).thenComparingInt(b -> b[2]));
		height = top + 1;
		reachAlong = along;
		reachAcross = across;
		cover(set, maxBody);
	}

	public static AnvilShape of(int size) {
		for (AnvilShape s : values()) if (s.size == size) return s;
		return ANVIL;
	}

	/** The translation key of its name: "Anvil", "Drill" or "Anchor". */
	public String key() {
		return "anvil_shape.lanternring." + name().toLowerCase(java.util.Locale.ROOT);
	}

	// ---- the shapes -----------------------------------------------------------------------

	/** Base 3x3, a 3-long waist two blocks high, then a 5x3 face with a horn on one end. */
	private static void anvil(Set<Long> s) {
		for (int x = -1; x <= 1; x++) for (int z = -1; z <= 1; z++) add(s, x, 0, z);
		for (int y = 1; y <= 2; y++) for (int x = -1; x <= 1; x++) add(s, x, y, 0);
		for (int y = 3; y <= 4; y++) {
			for (int x = -1; x <= 2; x++) for (int z = -1; z <= 1; z++) add(s, x, y, z);
			add(s, -2, y, 0);
		}
		// The horn tapers to a point.
		add(s, -3, 4, 0);
	}

	/**
	 * A big mining drill bit standing on its point: a 12-tall cone with two spiral flutes cut
	 * round it, a wide collar, then a round shank with a cap. 20 tall, 11 across.
	 */
	private static void drill(Set<Long> s) {
		for (int y = 0; y <= 19; y++) {
			for (int x = -6; x <= 6; x++) {
				for (int z = -6; z <= 6; z++) {
					double r = Math.hypot(x, z);
					boolean in;
					if (y <= 11) {
						double edge = 0.6 + y * 0.42;
						in = r <= edge;
						// Two flutes winding up the cone: a groove cut into the outer part.
						if (in && y >= 2 && r > edge - 1.6) {
							double a = Math.atan2(z, x) - y * Math.PI * 2 / 8;
							double d = Math.abs(Math.sin(a));
							in = d > 0.42;
						}
					} else if (y == 12) {
						in = r <= 5.6;
					} else if (y == 13) {
						in = r <= 4.6;
					} else if (y == 19) {
						in = r <= 2.4;
					} else {
						in = r <= 2.9;
					}
					if (in) add(s, x, y, z);
				}
			}
		}
	}

	/**
	 * A ship's anchor hanging crown down: a shank up the middle, curved arms from the crown up to
	 * spade-shaped flukes, a stock across the top (at right angles to the arms) and a ring. 30 tall,
	 * 25 across the arms.
	 */
	private static void anchor(Set<Long> s) {
		// Shank: 3x3 up from the crown.
		for (int y = 1; y <= 24; y++) for (int x = -1; x <= 1; x++) for (int z = -1; z <= 1; z++) add(s, x, y, z);
		// The crown's point.
		add(s, 0, 0, 0);
		// Arms: the lower part of a circle round a point up the shank, 2 thick, 3 deep, curving up
		// to 75 degrees each side.
		double cy = 11, inner = 9.1, outer = 11.3, reach = 75;
		for (int y = 0; y <= 12; y++) {
			for (int x = -13; x <= 13; x++) {
				double d = Math.hypot(x, y + 0.5 - cy);
				double angle = Math.toDegrees(Math.atan2(Math.abs(x), cy - y - 0.5));
				if (d >= inner && d <= outer && angle <= reach) {
					for (int z = -1; z <= 1; z++) add(s, x, y, z);
				}
			}
		}
		// Flukes: an arrowhead on the end of each arm, pointing on along the curve (up and a little
		// out), wider than the arm and a block thinner at its edges.
		double fa = Math.toRadians(reach), mid = (inner + outer) / 2;
		double endX = Math.sin(fa) * mid, endY = cy - Math.cos(fa) * mid;
		for (int side = -1; side <= 1; side += 2) {
			double ux = Math.cos(fa) * side, uy = Math.sin(fa);
			for (int y = 0; y <= 20; y++) {
				for (int x = -15; x <= 15; x++) {
					double px = x + 0.5 - endX * side - 0.5, py = y + 0.5 - endY;
					double along = px * ux + py * uy;
					double across = Math.abs(-px * uy + py * ux);
					if (along < -1 || along > 4.5) continue;
					double width = along < 0 ? 3.2 : 3.2 * (1 - along / 4.5);
					if (across <= width) for (int z = -1; z <= 1; z++) if (z == 0 || across <= width - 1.2) add(s, x, y, z);
				}
			}
		}
		// Stock: a bar across the arms near the top, with knobs on its ends.
		for (int z = -8; z <= 8; z++) {
			for (int y = 20; y <= 21; y++) add(s, 0, y, z);
			if (Math.abs(z) <= 7) {
				add(s, -1, 20, z);
				add(s, 1, 20, z);
			}
		}
		for (int side = -1; side <= 1; side += 2) {
			for (int x = -1; x <= 1; x++) for (int y = 19; y <= 22; y++) add(s, x, y, 9 * side);
		}
		// Ring: through the top of the shank, in the plane of the arms.
		for (int y = 24; y <= 31; y++) {
			for (int x = -5; x <= 5; x++) {
				double d = Math.hypot(x, y - 28);
				if (d >= 2.4 && d <= 3.6) add(s, x, y, 0);
			}
		}
	}

	// ---- helpers --------------------------------------------------------------------------

	private static void add(Set<Long> s, int x, int y, int z) {
		s.add(pack(x, y, z));
	}

	private static long pack(int x, int y, int z) {
		return ((long) (x + 512) << 20) | ((long) (y + 512) << 10) | (z + 512);
	}

	private static int[] unpack(long key) {
		return new int[] {(int) (key >> 20) - 512, (int) ((key >> 10) & 1023) - 512, (int) (key & 1023) - 512};
	}

	/** Covers the blocks with cubes, biggest that fit first, scanning from the bottom low corner. */
	private void cover(Set<Long> set, int maxBody) {
		Set<Long> covered = new HashSet<>();
		for (int edge = maxBody; edge >= 1; edge--) {
			for (int[] b : blocks) {
				if (covered.contains(pack(b[0], b[1], b[2]))) continue;
				if (!fits(set, covered, b, edge)) continue;
				for (int i = 0; i < edge; i++) for (int j = 0; j < edge; j++) for (int k = 0; k < edge; k++) {
					covered.add(pack(b[0] + i, b[1] + j, b[2] + k));
				}
				bodies.add(new int[] {b[0], b[1], b[2], edge});
			}
		}
	}

	private static boolean fits(Set<Long> set, Set<Long> covered, int[] b, int edge) {
		for (int i = 0; i < edge; i++) for (int j = 0; j < edge; j++) for (int k = 0; k < edge; k++) {
			long key = pack(b[0] + i, b[1] + j, b[2] + k);
			if (!set.contains(key) || covered.contains(key)) return false;
		}
		return true;
	}
}
