package com.sparky.lanternring.designs;

import com.sparky.lanternring.city.CityBlocks;
import java.util.Random;
import net.minecraft.core.Direction;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BedPart;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.Half;

/**
 * The Blue Lantern bearers' own buildings (J, 2026-10-12: "unique blue constructed", nothing copied
 * from vanilla). Each is shaped like hard light: round, faceted or arched shells of Hope Quartz with
 * see-through blue Hope Crystal and glowing Hope Inlay seams, and a ring of light floating over the
 * top like the Blue Lantern's emblem. They form as blue hard light and set into the quartz (see
 * city.HardLightSet).
 * <ul>
 * <li><b>Rotunda</b>: a round hall ringed by quartz ribs, a crystal window band and a crystal dome
 * with a spire, a halo of inlay floating over it.</li>
 * <li><b>Prism</b>: a hall whose walls flare out into a wide quartz brim, under a stepped crystal
 * prism roof.</li>
 * <li><b>Arch</b>: a pointed shell of quartz ribs with crystal between, like a wing folded over,
 * glowing end walls with a fan window.</li>
 * </ul>
 * Blueprint coordinates: the door (an open arch) is on the +z side, layer y = 0 is the floor.
 * Every house has a bed and a Hope Lamp.
 */
public final class HopeArchitecture {
	private static final BlockState QUARTZ = CityBlocks.HOPE_QUARTZ.defaultBlockState();
	private static final BlockState BRICKS = CityBlocks.HOPE_QUARTZ_BRICKS.defaultBlockState();
	private static final BlockState PILLAR = CityBlocks.HOPE_QUARTZ_PILLAR.defaultBlockState();
	private static final BlockState INLAY = CityBlocks.HOPE_INLAY.defaultBlockState();
	private static final BlockState CRYSTAL = CityBlocks.HOPE_CRYSTAL.defaultBlockState();
	private static final BlockState LAMP = CityBlocks.HOPE_LAMP.defaultBlockState();
	private static final BlockState AIR = Blocks.AIR.defaultBlockState();

	private HopeArchitecture() {
	}

	/** One of the designs, no wider or deeper than {@code maxSide} (7 at the least). */
	public static Blueprint house(int maxSide, Random r) {
		int s = Math.max(7, Math.min(maxSide, 7 + r.nextInt(4) * 2));
		if (s % 2 == 0) s--;
		return switch (r.nextInt(3)) {
			case 0 -> rotunda(s, r);
			case 1 -> prism(s, r);
			default -> arch(s, r);
		};
	}

	// ---- Rotunda ----------------------------------------------------------------------------------

	public static Blueprint rotunda(int s, Random r) {
		Blueprint b = new Blueprint(s, s);
		double c = (s - 1) / 2.0, R = c + 0.5;
		int wall = s >= 11 ? 5 : 4;
		for (int x = 0; x < s; x++) {
			for (int z = 0; z < s; z++) {
				double d = Math.hypot(x - c, z - c);
				if (d > R) continue;
				boolean edge = d > R - 1.2;
				b.set(x, 0, z, edge ? INLAY : d < 1.2 ? INLAY : BRICKS);
				if (!edge) {
					for (int y = 1; y <= wall; y++) b.clear(x, y, z);
					continue;
				}
				double a = Math.atan2(z - c, x - c);
				// Eight ribs round the ring; between them a crystal band.
				boolean rib = Math.abs(Math.sin(a * 4)) < 0.38;
				for (int y = 1; y <= wall; y++) {
					BlockState st;
					if (y == wall) st = INLAY;
					else if (rib) st = PILLAR;
					else if (y == 1) st = BRICKS;
					else st = CRYSTAL;
					b.set(x, y, z, st);
				}
			}
		}
		// Crystal dome: a shell over the hall, a quartz cap at the top.
		int top = wall;
		for (int k = 1; k <= (int) R; k++) {
			double rr = Math.sqrt(Math.max(0, R * R - k * k * 1.2));
			if (rr < 0.6) break;
			top = wall + k;
			for (int x = 0; x < s; x++) {
				for (int z = 0; z < s; z++) {
					double d = Math.hypot(x - c, z - c);
					if (d <= rr && d > rr - 1.3) b.set(x, wall + k, z, rr < 1.5 ? QUARTZ : CRYSTAL);
					else if (d <= rr - 1.3) b.clear(x, wall + k, z);
				}
			}
		}
		int cx = (int) Math.round(c);
		b.set(cx, top + 1, cx, PILLAR);
		b.set(cx, top + 2, cx, INLAY);
		halo(b, cx, top + 4, cx, s >= 9 ? 2 : 1.5);
		// The lamp hangs from the dome's crown.
		b.set(cx, wall, cx, LAMP);
		door(b, cx, (int) Math.round(c + R - 1), 2);
		bed(b, cx - 1, 1, (int) Math.round(c - R + 3));
		return b;
	}

	// ---- Prism ------------------------------------------------------------------------------------

	public static Blueprint prism(int s, Random r) {
		int w = s, d = Math.max(7, s - 2);
		Blueprint b = new Blueprint(w, d);
		int x0 = 1, x1 = w - 2, z0 = 1, z1 = d - 2;
		int wall = 4;
		// The floor, inlay round it.
		b.fill(x0, 0, z0, x1, 0, z1, QUARTZ);
		b.walls(x0, z0, x1, z1, 0, 0, INLAY);
		for (int y = 1; y <= wall; y++) {
			for (int x = x0; x <= x1; x++) {
				for (int z = z0; z <= z1; z++) {
					boolean onX = x == x0 || x == x1, onZ = z == z0 || z == z1;
					if (onX && onZ) {
						// Chamfered corners: the corner itself stays open, a rib just inside closes it.
						b.set(x == x0 ? x + 1 : x - 1, y, z == z0 ? z + 1 : z - 1, y == wall ? INLAY : PILLAR);
						continue;
					}
					if (!onX && !onZ) {
						if (b.get(x, y, z) == null) b.clear(x, y, z);
						continue;
					}
					boolean nextToCorner = (onX && (z == z0 + 1 || z == z1 - 1)) || (onZ && (x == x0 + 1 || x == x1 - 1));
					BlockState st = nextToCorner ? PILLAR : y == 1 ? BRICKS : y == wall ? INLAY : CRYSTAL;
					b.set(x, y, z, st);
				}
			}
		}
		// The brim: the walls flare out a block all round in upside-down quartz stairs, then a ring of inlay.
		int brim = wall + 1;
		for (int x = 0; x < w; x++) {
			for (int z = 0; z < d; z++) {
				boolean outer = x == 0 || z == 0 || x == w - 1 || z == d - 1;
				if (outer) {
					if ((x == 0 || x == w - 1) && (z == 0 || z == d - 1)) {
						b.set(x, brim, z, INLAY);
						continue;
					}
					Direction out = x == 0 ? Direction.WEST : x == w - 1 ? Direction.EAST : z == 0 ? Direction.NORTH : Direction.SOUTH;
					b.set(x, wall, z, stair(out.getOpposite(), true));
					b.set(x, brim, z, BRICKS);
				} else {
					b.set(x, brim, z, (x == 1 || z == 1 || x == w - 2 || z == d - 2) ? INLAY : QUARTZ);
				}
			}
		}
		// A stepped crystal prism, ridged in quartz along its middle.
		int y = brim + 1;
		int ax = 2, az = 2, bx = w - 3, bz = d - 3;
		while (ax <= bx && az <= bz) {
			for (int x = ax; x <= bx; x++) {
				for (int z = az; z <= bz; z++) {
					boolean rim = x == ax || x == bx || z == az || z == bz;
					if (rim) b.set(x, y, z, x == w / 2 || z == d / 2 ? PILLAR : CRYSTAL);
				}
			}
			ax++;
			az++;
			bx--;
			bz--;
			y++;
		}
		b.set(w / 2, y, d / 2, INLAY);
		halo(b, w / 2, y + 2, d / 2, 1.5);
		b.set(w / 2, brim, d / 2, LAMP);
		door(b, w / 2, z1, 1);
		bed(b, x0 + 2, 1, z0 + 2);
		return b;
	}

	// ---- Arch -------------------------------------------------------------------------------------

	public static Blueprint arch(int s, Random r) {
		int w = s, d = s;
		Blueprint b = new Blueprint(w, d);
		double c = (w - 1) / 2.0;
		int height = (int) Math.round(c + 3);
		int z0 = 0, z1 = d - 1;
		// The shell's height over each column: a pointed arch, steep at the sides.
		int[] roof = new int[w];
		for (int x = 0; x < w; x++) {
			double u = Math.abs(x - c) / (c + 0.5);
			roof[x] = (int) Math.round(height * (1 - u * u * u * 0.95 - u * 0.05));
		}
		for (int z = z0; z <= z1; z++) {
			boolean end = z == z0 || z == z1;
			boolean rib = end || (z - z0) % 3 == 0;
			for (int x = 0; x < w; x++) {
				b.set(x, 0, z, x == 0 || x == w - 1 || end ? INLAY : QUARTZ);
				// The shell: from this column's top down to its lower neighbour's, so steep sides close up.
				int lo = Math.min(x > 0 ? roof[x - 1] : 0, x < w - 1 ? roof[x + 1] : 0) + 1;
				lo = Math.min(lo, roof[x]);
				for (int y = 1; y <= roof[x]; y++) {
					boolean shell = y >= lo;
					if (shell) {
						boolean crest = y == height;
						b.set(x, y, z, crest ? INLAY : rib ? PILLAR : y > 1 ? CRYSTAL : BRICKS);
					} else if (end) {
						// The end walls: quartz, with a fan of crystal radiating from the middle.
						double a = Math.atan2(y, x - c);
						boolean fan = y >= 2 && Math.abs(Math.sin(a * 5)) < 0.3;
						b.set(x, y, z, fan ? CRYSTAL : BRICKS);
					} else {
						b.clear(x, y, z);
					}
				}
			}
		}
		int mx = w / 2;
		halo(b, mx, height + 2, d / 2, s >= 9 ? 2 : 1.5);
		b.set(mx, height - 1, d / 2, LAMP);
		door(b, mx, z1, 3);
		bed(b, 2, 1, 2);
		return b;
	}

	// ---- parts ------------------------------------------------------------------------------------

	/** A ring of inlay floating in the air over the roof: the Blue Lantern's halo of hope. */
	private static void halo(Blueprint b, int cx, int y, int cz, double radius) {
		for (int x = cx - 3; x <= cx + 3; x++) {
			for (int z = cz - 3; z <= cz + 3; z++) {
				double d = Math.hypot(x - cx, z - cz);
				if (Math.abs(d - radius) < 0.6) b.set(x, y, z, INLAY);
			}
		}
	}

	/** An open arch two blocks high at (x, 1, z), with an inlay lintel; it cuts through {@code depth} wall layers inward. */
	private static void door(Blueprint b, int x, int z, int depth) {
		for (int k = 0; k < depth; k++) {
			b.clear(x, 1, z - k);
			b.clear(x, 2, z - k);
		}
		if (b.has(x, 3, z)) b.set(x, 3, z, INLAY);
		// A step of quartz out front.
		if (z + 1 < b.d) b.set(x, 0, z + 1, QUARTZ);
	}

	/** A light blue bed with its head to the north, foot at (x, y, z). */
	private static void bed(Blueprint b, int x, int y, int z) {
		BlockState foot = Blocks.BED.lightBlue().defaultBlockState().setValue(BlockStateProperties.HORIZONTAL_FACING, Direction.NORTH);
		if (b.has(x, y, z) || b.has(x, y, z - 1)) return;
		b.set(x, y, z, foot.setValue(BlockStateProperties.BED_PART, BedPart.FOOT));
		b.set(x, y, z - 1, foot.setValue(BlockStateProperties.BED_PART, BedPart.HEAD));
	}

	private static BlockState stair(Direction facing, boolean upsideDown) {
		return CityBlocks.HOPE_QUARTZ_STAIRS.defaultBlockState().setValue(StairBlock.FACING, facing)
				.setValue(StairBlock.HALF, upsideDown ? Half.TOP : Half.BOTTOM);
	}
}
