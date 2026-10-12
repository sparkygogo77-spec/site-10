package com.sparky.lanternring;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * What the Anvil mode drops at each of its four levels: the anvil, a drill tank falling drill
 * first, a ship's anchor falling crown first, and a whole ship falling bow first. Each is a set of blocks given as offsets
 * from the middle of its bottom: x along its long side (laid across the bearer's view), y up, z
 * front to back.
 *
 * <p>While it falls a shape is drawn as moving block displays. To keep that to a few dozen or a few
 * hundred entities, its blocks are covered with boxes as big as fit (up to {@code maxBody} blocks
 * on a side), and each box is one scaled display.
 */
public enum AnvilShape {
	ANVIL(1, 1),
	TANK(3, 3),
	ANCHOR(5, 3),
	SHIP(7, 5);

	/** The level's id, stored on the ring: 1, 3, 5 or 7 (once sizes of the anvil). */
	public final int size;
	/** Every block, as {x, y, z}. */
	public final List<int[]> blocks = new ArrayList<>();
	/** Boxes covering the blocks for the moving display: {x, y, z, width, height, depth}, x/y/z the low corner. */
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
			case 3 -> tank(set);
			case 5 -> anchor(set);
			default -> ship(set);
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

	/** The translation key of its name: "Anvil", "Drill Tank", "Anchor" or "Ship". */
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
	 * A tracked drill tank diving nose first: a 9-tall drill cone with two spiral flutes at the
	 * bottom, a collar and mount, then the hull with a track down each side, a cab on its top face
	 * and two exhaust stacks at the back. 28 tall, 13 across the tracks.
	 */
	private static void tank(Set<Long> s) {
		// The drill: a cone with two flutes winding round it, point down.
		for (int y = 0; y <= 8; y++) {
			for (int x = -5; x <= 5; x++) {
				for (int z = -5; z <= 5; z++) {
					double r = Math.hypot(x, z + 0.5);
					double edge = 0.6 + y * 0.42;
					boolean in = r <= edge;
					if (in && y >= 2 && r > edge - 1.5) {
						double a = Math.atan2(z + 0.5, x) - y * Math.PI * 2 / 7;
						in = Math.abs(Math.sin(a)) > 0.42;
					}
					if (in) add(s, x, y, z);
				}
			}
		}
		// Collar and mount.
		for (int x = -5; x <= 5; x++) for (int z = -5; z <= 4; z++) if (Math.hypot(x, z + 0.5) <= 4.5) add(s, x, 9, z);
		for (int x = -3; x <= 3; x++) for (int z = -3; z <= 2; z++) add(s, x, 10, z);
		// Hull, with the front corners bevelled.
		for (int y = 11; y <= 25; y++) {
			for (int x = -4; x <= 4; x++) {
				for (int z = -3; z <= 2; z++) {
					if (y <= 12 && Math.abs(x) == 4 && (z == -3 || z == 2)) continue;
					add(s, x, y, z);
				}
			}
		}
		// Tracks down both sides, rounded at the ends, with treads cut into the outside.
		for (int side = -1; side <= 1; side += 2) {
			for (int y = 10; y <= 26; y++) {
				boolean end = y == 10 || y == 26;
				for (int z = -4; z <= 2; z++) {
					if (end && (z == -4 || z == 2)) continue;
					for (int w = 5; w <= 6; w++) {
						if (w == 6 && !end && y % 3 == 0 && z > -4 && z < 2) continue;
						add(s, w * side, y, z);
					}
				}
			}
		}
		// Cab on the top face, toward the back, with a hatch.
		for (int y = 16; y <= 23; y++) for (int x = -3; x <= 3; x++) for (int z = 3; z <= 5; z++) add(s, x, y, z);
		for (int y = 18; y <= 21; y++) for (int x = -1; x <= 1; x++) add(s, x, y, 6);
		// Exhaust stacks.
		for (int side = -1; side <= 1; side += 2) for (int y = 26; y <= 28; y++) add(s, 2 * side, y, 0);
	}

	/**
	 * A ship's anchor hanging crown down: a shank up the middle, curved arms from the crown up to
	 * spade-shaped flukes, a stock across the top (in line with the arms) and a ring. 30 tall,
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
		// Stock: a bar near the top in the same plane as the arms, with knobs on its ends.
		for (int x = -8; x <= 8; x++) {
			for (int y = 20; y <= 21; y++) add(s, x, y, 0);
			if (Math.abs(x) <= 7) {
				add(s, x, 20, -1);
				add(s, x, 20, 1);
			}
		}
		for (int side = -1; side <= 1; side += 2) {
			for (int z = -1; z <= 1; z++) for (int y = 19; y <= 22; y++) add(s, 9 * side, y, z);
		}
		// Ring: through the top of the shank, in the plane of the arms.
		for (int y = 24; y <= 31; y++) {
			for (int x = -5; x <= 5; x++) {
				double d = Math.hypot(x, y - 28);
				if (d >= 2.4 && d <= 3.6) add(s, x, y, 0);
			}
		}
	}

	/**
	 * A steel ship diving bow first: a hull 12 wide that comes to a sharp bow at the bottom, a deck
	 * with bulwarks on its top face, two funnels, a bridge and a mast, and a rudder at the stern.
	 * 50 tall.
	 */
	private static void ship(Set<Long> s) {
		int length = 47;
		for (int y = 0; y <= length; y++) {
			// Beam and keel depth: a sharp bow widening over 14 blocks, a slightly narrower stern.
			double grow = y < 14 ? Math.sqrt((y + 0.5) / 14) : 1;
			double w = 6 * grow - (y > 43 ? (y - 43) * 0.45 : 0);
			double d = 5 * grow - (y > 43 ? (y - 43) * 0.5 : 0);
			for (int x = -7; x <= 7; x++) {
				for (int z = -6; z <= 3; z++) {
					boolean in;
					if (z < 0) in = sq(x / w) + sq(z / d) <= 1;
					else if (z <= 2) in = Math.abs(x) <= w;
					// Bulwarks: the deck's raised edge.
					else in = y >= 3 && y <= length - 1 && Math.abs(x) <= w && Math.abs(x) > w - 1;
					if (in) add(s, x, y, z);
				}
			}
		}
		// Two round funnels.
		for (int f : new int[] {16, 24}) {
			for (int y = f - 2; y <= f + 2; y++) {
				for (int x = -3; x <= 3; x++) {
					if (Math.hypot(x, y - f) > 2.4) continue;
					for (int z = 3; z <= 11; z++) add(s, x, y, z);
				}
			}
		}
		// The bridge: a block of decks toward the stern, its top deck a little longer.
		for (int y = 31; y <= 39; y++) for (int x = -4; x <= 4; x++) for (int z = 3; z <= 7; z++) add(s, x, y, z);
		for (int y = 30; y <= 40; y++) for (int x = -5; x <= 5; x++) add(s, x, y, 8);
		// A mast on the bridge, and one near the bow.
		for (int z = 9; z <= 14; z++) add(s, 0, 35, z);
		for (int x = -2; x <= 2; x++) add(s, x, 35, 13);
		for (int z = 3; z <= 10; z++) add(s, 0, 8, z);
		// Rudder below the stern.
		for (int y = length - 3; y <= length + 2; y++) for (int z = -6; z <= -3; z++) add(s, 0, y, z);
	}

	private static double sq(double v) {
		return v * v;
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

	/**
	 * Covers the blocks with boxes, biggest that fit first, scanning from the bottom low corner.
	 * Boxes are at most maxBody on a side and at most twice as long one way as another, so the
	 * texture is never stretched more than 2 to 1.
	 */
	private void cover(Set<Long> set, int maxBody) {
		List<int[]> sizes = new ArrayList<>();
		for (int a = 1; a <= maxBody; a++) for (int b = 1; b <= maxBody; b++) for (int c = 1; c <= maxBody; c++) {
			int lo = Math.min(a, Math.min(b, c)), hi = Math.max(a, Math.max(b, c));
			if (hi <= 2 * lo) sizes.add(new int[] {a, b, c});
		}
		// Biggest first; among equal volumes, the most even.
		sizes.sort(Comparator.<int[]>comparingInt(d -> -d[0] * d[1] * d[2])
				.thenComparingInt(d -> Math.max(d[0], Math.max(d[1], d[2])) - Math.min(d[0], Math.min(d[1], d[2]))));
		Set<Long> covered = new HashSet<>();
		for (int[] d : sizes) {
			for (int[] b : blocks) {
				if (covered.contains(pack(b[0], b[1], b[2]))) continue;
				if (!fits(set, covered, b, d)) continue;
				for (int i = 0; i < d[0]; i++) for (int j = 0; j < d[1]; j++) for (int k = 0; k < d[2]; k++) {
					covered.add(pack(b[0] + i, b[1] + j, b[2] + k));
				}
				bodies.add(new int[] {b[0], b[1], b[2], d[0], d[1], d[2]});
			}
		}
	}

	private static boolean fits(Set<Long> set, Set<Long> covered, int[] b, int[] d) {
		for (int i = 0; i < d[0]; i++) for (int j = 0; j < d[1]; j++) for (int k = 0; k < d[2]; k++) {
			long key = pack(b[0] + i, b[1] + j, b[2] + k);
			if (!set.contains(key) || covered.contains(key)) return false;
		}
		return true;
	}
}
