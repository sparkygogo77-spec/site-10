package com.sparky.lanternring.designs;

import java.util.List;
import java.util.Random;
import net.minecraft.core.Direction;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;

/**
 * Builds drawn from code: each generator makes a blueprint for any footprint in its size range,
 * in any palette, with seeded variation (floors, roofs, heights). Front is +z, see Blueprint.
 */
public final class BuildGen {
	/** A generator for a rectangular footprint. */
	public interface Gen {
		Blueprint make(int w, int d, Palette p, Random rng);
	}

	/**
	 * One kind of generated build: its name, which palettes it comes in, the footprint sizes it
	 * works at (the short side), and its depth as a share of its width.
	 */
	public record Kind(String name, List<Palette> palettes, int min, int max, double aspect, Gen gen) {
	}

	public static final List<Kind> KINDS = List.of(
			new Kind("House", Palette.WOOD, 7, 15, 0.8, BuildGen::house),
			new Kind("Manor", Palette.ALL, 13, 25, 0.7, BuildGen::manor),
			new Kind("Tower", Palette.MASONRY, 5, 17, 1, (w, d, p, r) -> tower(w, p, r, false)),
			new Kind("Spire Tower", Palette.ALL, 7, 19, 1, (w, d, p, r) -> tower(w, p, r, true)),
			new Kind("Castle", Palette.MASONRY, 17, 64, 1, BuildGen::castle),
			new Kind("Lighthouse", List.of(Palette.WHITE, Palette.QUARTZ, Palette.LANTERN, Palette.STONE, Palette.SANDSTONE), 7, 15, 1, BuildGen::lighthouse),
			new Kind("Temple", Palette.MASONRY, 9, 33, 1.3, BuildGen::temple),
			new Kind("Pyramid", List.of(Palette.SANDSTONE, Palette.RED_SANDSTONE, Palette.STONE, Palette.BLACKSTONE, Palette.PRISMARINE, Palette.MANGROVE, Palette.QUARTZ), 9, 64, 1, BuildGen::pyramid),
			new Kind("Skyscraper", Palette.MODERN, 9, 40, 1, BuildGen::skyscraper),
			new Kind("Glass Dome", Palette.ALL, 9, 64, 1, BuildGen::dome),
			new Kind("Obelisk", Palette.MASONRY, 5, 15, 1, BuildGen::obelisk),
			new Kind("Gazebo", Palette.WOOD, 5, 13, 1, BuildGen::gazebo),
			new Kind("Power Battery", List.of(Palette.LANTERN, Palette.QUARTZ, Palette.DEEPSLATE, Palette.BLACKSTONE), 7, 25, 1, BuildGen::battery),
			new Kind("Arena", Palette.MASONRY, 17, 64, 1, BuildGen::arena));

	private BuildGen() {
	}

	// ---- helpers ------------------------------------------------------------------------------

	static BlockState with(BlockState s, Direction facing) {
		return s.hasProperty(BlockStateProperties.HORIZONTAL_FACING) ? s.setValue(BlockStateProperties.HORIZONTAL_FACING, facing) : s;
	}

	static BlockState hanging(BlockState light) {
		return light.hasProperty(BlockStateProperties.HANGING) ? light.setValue(BlockStateProperties.HANGING, true) : light;
	}

	/** A full block that gives light, for floors and ceilings. */
	static BlockState lamp(Palette p) {
		BlockState l = p.light();
		return l.isCollisionShapeFullBlock(net.minecraft.world.level.EmptyBlockGetter.INSTANCE, net.minecraft.core.BlockPos.ZERO)
				? l : Blocks.GLOWSTONE.defaultBlockState();
	}

	static boolean inCircle(double x, double z, double cx, double cz, double r) {
		double dx = x - cx, dz = z - cz;
		return dx * dx + dz * dz <= (r + 0.35) * (r + 0.35);
	}

	/**
	 * A gable roof over x0..x1, z0..z1 starting at height y, ridge running along x, overhanging by
	 * {@code over}; its two ends are closed with wall.
	 */
	static int gable(Blueprint b, int x0, int x1, int z0, int z1, int y, int over, Palette p, BlockState gableWall) {
		int k = 0;
		for (int zn = z0 - over, zs = z1 + over; zn <= zs; zn++, zs--, k++) {
			for (int x = x0 - over; x <= x1 + over; x++) {
				if (zn == zs) {
					b.set(x, y + k, zn, p.slab(false));
				} else {
					b.set(x, y + k, zn, p.stairs(Direction.SOUTH));
					b.set(x, y + k, zs, p.stairs(Direction.NORTH));
				}
			}
			for (int z = zn + 1; z < zs; z++) {
				b.set(x0, y + k, z, gableWall);
				b.set(x1, y + k, z, gableWall);
				for (int x = x0 + 1; x < x1; x++) b.clear(x, y + k, z);
			}
		}
		return y + k;
	}

	static void windowsAround(Blueprint b, int x0, int z0, int x1, int z1, int y, int every, BlockState window, int skipX, int skipZ) {
		for (int x = x0 + 2; x <= x1 - 2; x += every) {
			if (x != skipX) b.set(x, y, z1, window);
			b.set(x, y, z0, window);
		}
		for (int z = z0 + 2; z <= z1 - 2; z += every) {
			b.set(x0, y, z, window);
			if (z != skipZ) b.set(x1, y, z, window);
		}
	}

	// ---- houses -------------------------------------------------------------------------------

	public static Blueprint house(int w, int d, Palette p, Random r) {
		Blueprint b = new Blueprint(w, d);
		int x0 = 1, x1 = w - 2, z0 = 1, z1 = d - 2;
		int floors = w >= 9 && d >= 8 && r.nextBoolean() ? 2 : 1;
		int storey = 4;
		int top = storey * floors;
		b.fill(x0, 0, z0, x1, 0, z1, p.base());
		b.fill(x0 + 1, 0, z0 + 1, x1 - 1, 0, z1 - 1, p.floor());
		b.walls(x0, z0, x1, z1, 1, top, p.wall());
		b.fill(x0 + 1, 1, z0 + 1, x1 - 1, top, z1 - 1, Blocks.AIR.defaultBlockState());
		for (int y = 1; y <= top; y++) {
			b.set(x0, y, z0, p.frame());
			b.set(x1, y, z0, p.frame());
			b.set(x0, y, z1, p.frame());
			b.set(x1, y, z1, p.frame());
		}
		int doorX = w / 2;
		for (int f = 0; f < floors; f++) {
			int y = f * storey + 2;
			windowsAround(b, x0, z0, x1, z1, y, 2 + r.nextInt(2), p.window(), doorX, -1);
		}
		// Re-do windows at the same columns on the second row so they're two tall.
		for (int f = 0; f < floors; f++) {
			int y = f * storey + 2;
			for (int x = x0 + 1; x < x1; x++) {
				if (b.get(x, y, z0) == p.window()) b.set(x, y + 1, z0, p.window());
				if (b.get(x, y, z1) == p.window()) b.set(x, y + 1, z1, p.window());
			}
			for (int z = z0 + 1; z < z1; z++) {
				if (b.get(x0, y, z) == p.window()) b.set(x0, y + 1, z, p.window());
				if (b.get(x1, y, z) == p.window()) b.set(x1, y + 1, z, p.window());
			}
		}
		if (floors == 2) {
			b.fill(x0 + 1, storey, z0 + 1, x1 - 1, storey, z1 - 1, p.floor());
			BlockState ladder = with(Blocks.LADDER.defaultBlockState(), Direction.SOUTH);
			for (int y = 1; y <= storey; y++) b.set(x1 - 1, y, z0 + 1, ladder);
		}
		b.door(doorX, 1, z1, p.door(), Direction.NORTH);
		b.set(doorX, 0, z1 + 1, p.slab(false));
		b.set(x0 + 1, 1, z1 - 1, p.light());
		b.set(x1 - 1, 1, z1 - 1, Blocks.CRAFTING_TABLE.defaultBlockState());
		if (floors == 1 || r.nextBoolean()) b.set(x0 + 1, 1, z0 + 1, with(Blocks.CHEST.defaultBlockState(), Direction.SOUTH));
		gable(b, x0, x1, z0, z1, top + 1, 1, p, p.wall());
		if (r.nextInt(3) == 0) {
			// A chimney.
			int cx = x0 + 1, cz = z0 + 1;
			for (int y = top + 1; y < top + 2 + d / 2; y++) b.set(cx, y, cz, p.base());
		}
		return b;
	}

	/** A bigger house: a main hall with a wing, two or three floors and a porch. */
	static Blueprint manor(int w, int d, Palette p, Random r) {
		Blueprint b = new Blueprint(w, d);
		int x0 = 1, x1 = w - 2, z0 = 1, z1 = d - 4;
		int storey = 5;
		int floors = 2 + (w >= 19 && r.nextBoolean() ? 1 : 0);
		int top = storey * floors;
		b.fill(x0, 0, z0, x1, 0, z1, p.base());
		b.fill(x0 + 1, 0, z0 + 1, x1 - 1, 0, z1 - 1, p.floor());
		b.walls(x0, z0, x1, z1, 1, top, p.wall());
		b.fill(x0 + 1, 1, z0 + 1, x1 - 1, top, z1 - 1, Blocks.AIR.defaultBlockState());
		for (int x = x0; x <= x1; x += 4) {
			for (int y = 1; y <= top; y++) {
				b.set(x, y, z0, p.frame());
				b.set(x, y, z1, p.frame());
			}
		}
		b.set(x1, 1, z0, p.frame());
		for (int f = 0; f < floors; f++) {
			int y = f * storey + 2;
			for (int x = x0 + 2; x < x1; x += 4) {
				for (int dy = 0; dy < 2; dy++) {
					b.set(x, y + dy, z0, p.window());
					b.set(x, y + dy, z1, p.window());
				}
			}
			for (int z = z0 + 2; z < z1; z += 3) {
				for (int dy = 0; dy < 2; dy++) {
					b.set(x0, y + dy, z, p.window());
					b.set(x1, y + dy, z, p.window());
				}
			}
			if (f > 0) b.fill(x0 + 1, f * storey, z0 + 1, x1 - 1, f * storey, z1 - 1, p.floor());
			b.set(w / 2, f * storey + storey - 1, (z0 + z1) / 2, hanging(p.light()));
			b.set(w / 2, f * storey + storey, (z0 + z1) / 2, p.floor());
		}
		BlockState ladder = with(Blocks.LADDER.defaultBlockState(), Direction.SOUTH);
		for (int y = 1; y <= top - storey; y++) b.set(x1 - 1, y, z0 + 1, ladder);
		for (int f = 1; f < floors; f++) b.clear(x1 - 1, f * storey, z0 + 1);
		for (int y = storey; y <= top - storey; y += storey) b.set(x1 - 1, y, z0 + 1, ladder);
		int doorX = w / 2;
		b.door(doorX, 1, z1, p.door(), Direction.NORTH);
		b.door(doorX - 1, 1, z1, p.door().setValue(BlockStateProperties.DOOR_HINGE,
				net.minecraft.world.level.block.state.properties.DoorHingeSide.RIGHT), Direction.NORTH);
		// The porch: a floor, posts and a little roof over the door.
		b.fill(doorX - 3, 0, z1 + 1, doorX + 2, 0, z1 + 2, p.floor());
		for (int y = 1; y <= 3; y++) {
			b.set(doorX - 3, y, z1 + 2, p.fence());
			b.set(doorX + 2, y, z1 + 2, p.fence());
		}
		b.fill(doorX - 3, 4, z1 + 1, doorX + 2, 4, z1 + 2, p.slab(false));
		gable(b, x0, x1, z0, z1, top + 1, 1, p, p.wall());
		return b;
	}

	// ---- towers -------------------------------------------------------------------------------

	static Blueprint tower(int s, Palette p, Random r, boolean spire) {
		Blueprint b = new Blueprint(s, s);
		boolean round = spire || r.nextBoolean();
		double c = (s - 1) / 2.0;
		double rad = spire ? c - 1 : c;
		int height = Math.min(72, Math.max(12, s * 3 + r.nextInt(s + 1)));
		boolean[][] in = new boolean[s][s];
		for (int x = 0; x < s; x++) {
			for (int z = 0; z < s; z++) {
				in[x][z] = round ? inCircle(x, z, c, c, rad) : Math.abs(x - c) <= rad && Math.abs(z - c) <= rad;
			}
		}
		int xc = s / 2, zmin = s, zmax = -1;
		for (int z = 0; z < s; z++) {
			if (in[xc][z]) {
				zmin = Math.min(zmin, z);
				zmax = Math.max(zmax, z);
			}
		}
		for (int x = 0; x < s; x++) {
			for (int z = 0; z < s; z++) {
				if (!in[x][z]) continue;
				boolean edge = x == 0 || z == 0 || x == s - 1 || z == s - 1 || !in[x - 1][z] || !in[x + 1][z] || !in[x][z - 1] || !in[x][z + 1];
				b.set(x, 0, z, p.base());
				for (int y = 1; y <= height; y++) {
					if (edge) b.set(x, y, z, (!round && (x == 0 || x == s - 1) && (z == 0 || z == s - 1)) ? p.frame() : p.wall());
					else b.set(x, y, z, y % 6 == 0 || y == height ? p.floor() : Blocks.AIR.defaultBlockState());
				}
				if (edge && !spire && (x + z) % 2 == 0) b.set(x, height + 1, z, p.wall());
			}
		}
		// A ladder up the inside of the back wall, through every floor.
		BlockState ladder = with(Blocks.LADDER.defaultBlockState(), Direction.SOUTH);
		for (int y = 1; y <= height; y++) b.set(xc, y, zmin + 1, ladder);
		for (int y = 3; y < height - 1; y += 6) {
			b.set(xc, y, zmax, p.window());
			b.set(xc, y + 1, zmax, p.window());
			int xmin = 0, xmax = s - 1;
			while (xmin < s && !in[xmin][s / 2]) xmin++;
			while (xmax > 0 && !in[xmax][s / 2]) xmax--;
			b.set(xmin, y, s / 2, p.window());
			b.set(xmax, y, s / 2, p.window());
			b.set(xc, y - 2, s / 2, p.light());
		}
		b.door(xc, 1, zmax, p.door(), Direction.NORTH);
		if (spire) {
			// A cone roof that overhangs by a block, up to a point.
			int y = height + 1;
			for (double rr = rad + 1; rr > 0.3; rr -= 0.75, y++) {
				for (int x = 0; x < s; x++) {
					for (int z = 0; z < s; z++) {
						double dist = Math.hypot(x - c, z - c);
						if (dist <= rr + 0.35 && dist > rr - 1.2) b.set(x, y, z, p.roof());
					}
				}
			}
			b.set(xc, y, s / 2, p.frame());
			b.set(xc, y + 1, s / 2, p.fence());
			b.set(xc, y + 2, s / 2, p.light());
		}
		return b;
	}

	static Blueprint lighthouse(int w, int d, Palette p, Random r) {
		int s = w;
		Blueprint b = new Blueprint(s, s);
		double c = (s - 1) / 2.0;
		double r0 = c - 1;
		int height = Math.min(64, Math.max(20, (int) (s * 3.5) + r.nextInt(6)));
		BlockState stripe = r.nextBoolean() ? Blocks.CONCRETE.red().defaultBlockState() : p.roof();
		double rTop = Math.max(2, r0 * 0.6);
		for (int y = 0; y <= height; y++) {
			double rr = r0 + (rTop - r0) * y / height;
			for (int x = 0; x < s; x++) {
				for (int z = 0; z < s; z++) {
					double dist = Math.hypot(x - c, z - c);
					if (dist > rr + 0.35) continue;
					if (y == 0) b.set(x, 0, z, p.base());
					else if (dist > rr - 0.8) b.set(x, y, z, (y / 4) % 2 == 0 ? p.wall() : stripe);
					else b.set(x, y, z, y == height ? p.floor() : Blocks.AIR.defaultBlockState());
				}
			}
		}
		int xc = s / 2;
		int zmin = 0, zmax = s - 1;
		while (zmin < s && !b.has(xc, 1, zmin)) zmin++;
		while (zmax > 0 && !b.has(xc, 1, zmax)) zmax--;
		b.door(xc, 1, zmax, p.door(), Direction.NORTH);
		BlockState ladder = with(Blocks.LADDER.defaultBlockState(), Direction.SOUTH);
		for (int y = 1; y <= height; y++) {
			int zl = 0;
			while (zl < s && b.get(xc, y, zl) == null) zl++;
			if (zl < s - 1) b.set(xc, y, zl + 1, ladder);
		}
		// The lamp room: a gallery rail, a glass ring round a big light, and a cap.
		int y = height + 1;
		for (int x = 0; x < s; x++) {
			for (int z = 0; z < s; z++) {
				double dist = Math.hypot(x - c, z - c);
				if (dist <= rTop + 1.35 && dist > rTop + 0.35) {
					b.set(x, height, z, p.floor());
					b.set(x, y, z, p.fence());
				}
				if (dist <= rTop - 0.65 && dist > rTop - 1.65) {
					for (int k = 0; k < 3; k++) b.set(x, y + k, z, p.glass());
				}
				if (dist <= rTop - 0.65) b.set(x, y + 3, z, p.roof());
			}
		}
		b.set(xc, y, s / 2, lamp(p));
		b.set(xc, y + 1, s / 2, Blocks.SEA_LANTERN.defaultBlockState());
		b.set(xc, y + 4, s / 2, p.frame());
		return b;
	}

	// ---- big stone builds -----------------------------------------------------------------------

	static Blueprint castle(int w, int d, Palette p, Random r) {
		int s = w;
		Blueprint b = new Blueprint(s, s);
		int wallH = 6 + s / 12;
		int towerR = s >= 33 ? 3 : 2;
		int in = towerR;
		// Curtain walls, two thick, with a walkway and battlements.
		for (int x = in; x <= s - 1 - in; x++) {
			for (int z = in; z <= s - 1 - in; z++) {
				boolean outer = x == in || z == in || x == s - 1 - in || z == s - 1 - in;
				boolean inner = x == in + 1 || z == in + 1 || x == s - 2 - in || z == s - 2 - in;
				if (!outer && !inner) {
					b.set(x, 0, z, (x + z) % 7 == 0 ? Blocks.COARSE_DIRT.defaultBlockState() : Blocks.GRASS_BLOCK.defaultBlockState());
					continue;
				}
				for (int y = 0; y <= wallH; y++) b.set(x, y, z, p.wall());
				if (outer && (x + z) % 2 == 0) b.set(x, wallH + 1, z, p.wall());
			}
		}
		// The gate in the front wall.
		int g = s / 2;
		for (int x = g - 1; x <= g + 1; x++) {
			for (int y = 1; y <= 4; y++) {
				b.clear(x, y, s - 1 - in);
				b.clear(x, y, s - 2 - in);
			}
		}
		for (int x = g - 2; x <= g + 2; x++) b.set(x, 5, s - 1 - in, p.frame());
		// Round towers on the corners, taller than the walls.
		int towerH = wallH + 5;
		int[][] corners = {{in, in}, {s - 1 - in, in}, {in, s - 1 - in}, {s - 1 - in, s - 1 - in}};
		for (int[] cc : corners) {
			for (int x = cc[0] - towerR; x <= cc[0] + towerR; x++) {
				for (int z = cc[1] - towerR; z <= cc[1] + towerR; z++) {
					if (!inCircle(x, z, cc[0], cc[1], towerR)) continue;
					boolean edge = !inCircle(x + 1, z, cc[0], cc[1], towerR) || !inCircle(x - 1, z, cc[0], cc[1], towerR)
							|| !inCircle(x, z + 1, cc[0], cc[1], towerR) || !inCircle(x, z - 1, cc[0], cc[1], towerR);
					for (int y = 0; y <= towerH; y++) b.set(x, y, z, edge || y == 0 || y == towerH ? p.wall() : Blocks.AIR.defaultBlockState());
					if (edge && (x + z) % 2 == 0) b.set(x, towerH + 1, z, p.wall());
				}
			}
			b.set(cc[0], towerH + 1, cc[1], p.light());
		}
		// The keep in the middle.
		int k = Math.max(5, s / 3);
		int k0 = (s - k) / 2, k1 = k0 + k - 1;
		int keepH = wallH + 6 + r.nextInt(5);
		b.fill(k0, 0, k0, k1, 0, k1, p.floor());
		b.walls(k0, k0, k1, k1, 1, keepH, p.wall());
		b.fill(k0 + 1, 1, k0 + 1, k1 - 1, keepH - 1, k1 - 1, Blocks.AIR.defaultBlockState());
		b.fill(k0, keepH, k0, k1, keepH, k1, p.floor());
		for (int x = k0; x <= k1; x += 2) {
			b.set(x, keepH + 1, k0, p.wall());
			b.set(x, keepH + 1, k1, p.wall());
		}
		for (int z = k0; z <= k1; z += 2) {
			b.set(k0, keepH + 1, z, p.wall());
			b.set(k1, keepH + 1, z, p.wall());
		}
		for (int y = 1; y <= keepH; y++) {
			b.set(k0, y, k0, p.frame());
			b.set(k1, y, k0, p.frame());
			b.set(k0, y, k1, p.frame());
			b.set(k1, y, k1, p.frame());
		}
		for (int y = 4; y < keepH - 1; y += 4) windowsAround(b, k0, k0, k1, k1, y, 3, p.window(), -1, -1);
		b.door(s / 2, 1, k1, p.door(), Direction.NORTH);
		BlockState ladder = with(Blocks.LADDER.defaultBlockState(), Direction.SOUTH);
		for (int y = 1; y <= keepH; y++) b.set(k0 + 1, y, k0 + 1, ladder);
		b.set(s / 2, keepH - 1, s / 2, hanging(p.light()));
		// Steps up to the wall walk on each side of the gate.
		for (int i = 0; i < wallH; i++) {
			b.set(g - 3 - i, 1 + i, s - 3 - in, with(p.roofStairs().defaultBlockState(), Direction.WEST));
			for (int y = 1; y <= i; y++) b.set(g - 3 - i, y, s - 3 - in, p.wall());
		}
		return b;
	}

	static Blueprint temple(int w, int d, Palette p, Random r) {
		Blueprint b = new Blueprint(w, d);
		b.fill(0, 0, 0, w - 1, 0, d - 1, p.base());
		b.fill(1, 1, 1, w - 2, 1, d - 2, p.floor());
		// Front steps.
		for (int x = 1; x < w - 1; x++) b.set(x, 1, d - 1, with(p.roofStairs().defaultBlockState(), Direction.NORTH));
		int colH = Math.max(4, Math.min(w, d) / 3 + r.nextInt(2));
		int y0 = 2, top = y0 + colH;
		for (int x = 2; x <= w - 3; x += 2) {
			for (int y = y0; y < top; y++) {
				b.set(x, y, 2, p.frame());
				b.set(x, y, d - 3, p.frame());
			}
		}
		for (int z = 2; z <= d - 3; z += 2) {
			for (int y = y0; y < top; y++) {
				b.set(2, y, z, p.frame());
				b.set(w - 3, y, z, p.frame());
			}
		}
		b.fill(1, top, 1, w - 2, top, d - 2, p.wall());
		if (w >= 13 && d >= 13) {
			// The inner hall, with its own door.
			b.walls(4, 4, w - 5, d - 5, y0, top - 1, p.wall());
			b.door(w / 2, y0, d - 5, p.door(), Direction.NORTH);
			b.set(w / 2, y0, (d - 1) / 2, lamp(p));
		}
		// The pediment: a low gable front to back.
		int k = 0;
		for (; k < 6 && 1 + k <= w - 2 - k; k++) {
			for (int x = 1 + k; x <= w - 2 - k; x++) {
				for (int z = 1; z <= d - 2; z++) {
					boolean rim = x == 1 + k || x == w - 2 - k;
					b.set(x, top + 1 + k, z, rim ? with(p.roofStairs().defaultBlockState(), x == 1 + k ? Direction.EAST : Direction.WEST) : p.roof());
				}
			}
		}
		return b;
	}

	static Blueprint pyramid(int w, int d, Palette p, Random r) {
		int s = w;
		Blueprint b = new Blueprint(s, s);
		int k = 0;
		for (; k <= (s - 1) / 2; k++) {
			for (int x = k; x <= s - 1 - k; x++) {
				for (int z = k; z <= s - 1 - k; z++) {
					boolean edge = x == k || z == k || x == s - 1 - k || z == s - 1 - k;
					if (k == 0) b.set(x, 0, z, edge ? p.base() : p.floor());
					else if (edge) b.set(x, k, z, p.wall());
					else if (k > 1) b.clear(x, k - 1, z);
				}
			}
		}
		b.set(s / 2, k, s / 2, Blocks.GOLD_BLOCK.defaultBlockState());
		// A tunnel in from the front, and a light in the chamber.
		for (int z = s - 1; z > s / 2; z--) {
			b.clear(s / 2, 1, z);
			b.clear(s / 2, 2, z);
		}
		b.set(s / 2, 1, s / 2, lamp(p));
		return b;
	}

	static Blueprint skyscraper(int w, int d, Palette p, Random r) {
		Blueprint b = new Blueprint(w, d);
		int floorH = 4;
		int floors = Math.max(4, Math.min(24, (w * 2 + r.nextInt(w + 1)) / floorH));
		int height = floors * floorH;
		int rib = 3 + r.nextInt(2);
		BlockState glass = p.glass();
		for (int x = 0; x < w; x++) {
			for (int z = 0; z < d; z++) {
				boolean edge = x == 0 || z == 0 || x == w - 1 || z == d - 1;
				b.set(x, 0, z, p.floor());
				for (int y = 1; y <= height; y++) {
					if (y % floorH == 0) {
						b.set(x, y, z, edge ? p.wall() : p.floor());
					} else if (edge) {
						boolean ribHere = (x % rib == 0 && (z == 0 || z == d - 1)) || (z % rib == 0 && (x == 0 || x == w - 1))
								|| ((x == 0 || x == w - 1) && (z == 0 || z == d - 1));
						b.set(x, y, z, ribHere ? p.frame() : glass);
					} else {
						b.clear(x, y, z);
					}
				}
			}
		}
		for (int f = 1; f <= floors; f++) b.set(w / 2, f * floorH, d / 2, lamp(p));
		// A parapet and a mast on the roof.
		for (int x = 0; x < w; x++) {
			b.set(x, height + 1, 0, p.wall());
			b.set(x, height + 1, d - 1, p.wall());
		}
		for (int z = 0; z < d; z++) {
			b.set(0, height + 1, z, p.wall());
			b.set(w - 1, height + 1, z, p.wall());
		}
		int mast = 3 + r.nextInt(6);
		for (int y = height + 1; y <= height + mast; y++) b.set(w / 2, y, d / 2, p.frame());
		b.set(w / 2, height + mast + 1, d / 2, lamp(p));
		// A lobby entrance and a ladder up the core.
		b.door(w / 2, 1, d - 1, p.door(), Direction.NORTH);
		b.door(w / 2 - 1, 1, d - 1, p.door().setValue(BlockStateProperties.DOOR_HINGE,
				net.minecraft.world.level.block.state.properties.DoorHingeSide.RIGHT), Direction.NORTH);
		BlockState ladder = with(Blocks.LADDER.defaultBlockState(), Direction.SOUTH);
		for (int y = 1; y <= height; y++) b.set(w / 2, y, 1, ladder);
		return b;
	}

	static Blueprint dome(int w, int d, Palette p, Random r) {
		int s = w;
		Blueprint b = new Blueprint(s, s);
		double c = (s - 1) / 2.0;
		double rad = c;
		int ribs = r.nextInt(3);
		for (int x = 0; x < s; x++) {
			for (int z = 0; z < s; z++) {
				double flat = Math.hypot(x - c, z - c);
				if (flat > rad + 0.35) continue;
				b.set(x, 0, z, p.floor());
				for (int y = 1; y <= rad + 1; y++) {
					double dist = Math.sqrt(flat * flat + y * y);
					if (dist <= rad + 0.35 && dist > rad - 0.9) {
						boolean rib = ribs > 0 && (Math.abs(x - c) < 0.6 || Math.abs(z - c) < 0.6 || (ribs == 2 && Math.abs(Math.abs(x - c) - Math.abs(z - c)) < 0.6));
						b.set(x, y, z, rib || y <= 1 ? p.frame() : p.glass());
					}
				}
			}
		}
		int zmax = s - 1;
		while (zmax > 0 && !b.has(s / 2, 1, zmax)) zmax--;
		b.door(s / 2, 1, zmax, p.door(), Direction.NORTH);
		b.set(s / 2, 0, s / 2, lamp(p));
		return b;
	}

	static Blueprint obelisk(int w, int d, Palette p, Random r) {
		int s = w;
		Blueprint b = new Blueprint(s, s);
		int steps = Math.min(3, s / 3);
		for (int k = 0; k < steps; k++) b.fill(k, k, k, s - 1 - k, k, s - 1 - k, k == 0 ? p.base() : p.wall());
		int half = Math.max(0, (s - 2 * steps) / 4);
		int c = s / 2;
		int height = Math.max(8, s * 3 + r.nextInt(s));
		for (int y = steps; y < steps + height; y++) b.fill(c - half, y, c - half, c + half, y, c + half, p.frame());
		int y = steps + height;
		for (int h = half; h >= 0; h--, y++) b.fill(c - h, y, c - h, c + h, y, c + h, p.wall());
		b.set(c, y, c, lamp(p));
		return b;
	}

	static Blueprint gazebo(int w, int d, Palette p, Random r) {
		int s = w;
		Blueprint b = new Blueprint(s, s);
		double c = (s - 1) / 2.0;
		double rad = c;
		for (int x = 0; x < s; x++) {
			for (int z = 0; z < s; z++) {
				if (inCircle(x, z, c, c, rad)) b.set(x, 0, z, p.floor());
			}
		}
		int postH = 3 + (s > 9 ? 1 : 0);
		for (int a = 0; a < 8; a++) {
			double ang = a * Math.PI / 4 + Math.PI / 8;
			int x = (int) Math.round(c + Math.cos(ang) * (rad - 0.6)), z = (int) Math.round(c + Math.sin(ang) * (rad - 0.6));
			for (int y = 1; y <= postH; y++) b.set(x, y, z, p.fence());
		}
		int y = postH + 1;
		for (double rr = rad + 0.5; rr > 0.4; rr -= 1, y++) {
			for (int x = 0; x < s; x++) {
				for (int z = 0; z < s; z++) {
					double dist = Math.hypot(x - c, z - c);
					if (dist <= rr + 0.35 && dist > rr - 1.1) b.set(x, y, z, p.slab(false));
					if (dist <= rr - 1.1 + 0.35 && dist > rr - 1.6) b.set(x, y, z, p.roof());
				}
			}
		}
		b.set(s / 2, y, s / 2, p.roof());
		b.set(s / 2, postH, s / 2, hanging(p.light()));
		b.set(s / 2, postH + 1, s / 2, p.roof());
		return b;
	}

	/** A giant lantern like the one the ring charges from. */
	static Blueprint battery(int w, int d, Palette p, Random r) {
		int s = w;
		Blueprint b = new Blueprint(s, s);
		double c = (s - 1) / 2.0;
		double rad = c;
		int baseH = Math.max(2, s / 5);
		int bodyH = (int) (s * 1.1);
		BlockState core = Blocks.STAINED_GLASS.lime().defaultBlockState();
		for (int x = 0; x < s; x++) {
			for (int z = 0; z < s; z++) {
				double dist = Math.hypot(x - c, z - c);
				// A wide stepped base.
				for (int y = 0; y < baseH; y++) {
					if (dist <= rad - y * 0.5 + 0.35) b.set(x, y, z, y == 0 ? p.base() : p.roof());
				}
				// The cage: frame posts at the edge with green glass in between, a bright core.
				double cage = rad - 1.5;
				for (int y = baseH; y < baseH + bodyH; y++) {
					if (dist <= cage + 0.35 && dist > cage - 0.8) {
						boolean post = Math.abs(x - c) < 0.6 || Math.abs(z - c) < 0.6 || Math.abs(Math.abs(x - c) - Math.abs(z - c)) < 0.6;
						b.set(x, y, z, post ? p.frame() : core);
					} else if (dist <= cage - 0.8) {
						b.set(x, y, z, dist < cage * 0.45 ? Blocks.SEA_LANTERN.defaultBlockState() : Blocks.AIR.defaultBlockState());
					}
				}
				// The cap, narrowing to a handle.
				int y = baseH + bodyH;
				for (int k = 0; k < 3; k++) {
					if (dist <= rad - 1 - k * 1.5 + 0.35) b.set(x, y + k, z, k == 0 ? p.frame() : p.roof());
				}
			}
		}
		int top = baseH + bodyH + 3;
		int xc = s / 2;
		for (int k = -2; k <= 2; k++) {
			b.set(xc + k, top + 2, s / 2, p.frame());
		}
		for (int y = top; y <= top + 1; y++) {
			b.set(xc - 2, y, s / 2, p.frame());
			b.set(xc + 2, y, s / 2, p.frame());
		}
		return b;
	}

	static Blueprint arena(int w, int d, Palette p, Random r) {
		int s = w;
		Blueprint b = new Blueprint(s, s);
		double c = (s - 1) / 2.0;
		double rad = c;
		int tiers = Math.max(2, Math.min(7, s / 7));
		for (int x = 0; x < s; x++) {
			for (int z = 0; z < s; z++) {
				double dist = Math.hypot(x - c, z - c);
				if (dist > rad + 0.35) continue;
				double fromEdge = rad - dist;
				if (fromEdge < 1) {
					// The outer wall.
					for (int y = 0; y <= tiers + 2; y++) b.set(x, y, z, p.wall());
					if ((x + z) % 2 == 0) b.set(x, tiers + 3, z, p.wall());
				} else if (fromEdge < 1 + tiers) {
					int tier = tiers - (int) (fromEdge - 1);
					for (int y = 0; y < tier; y++) b.set(x, y, z, p.wall());
					Direction out = Math.abs(x - c) > Math.abs(z - c) ? (x > c ? Direction.EAST : Direction.WEST) : (z > c ? Direction.SOUTH : Direction.NORTH);
					b.set(x, tier, z, with(p.roofStairs().defaultBlockState(), out));
				} else {
					b.set(x, 0, z, Blocks.SAND.defaultBlockState());
				}
			}
		}
		// The gate through the front.
		for (int z = s - 1; z > s - 3 - tiers; z--) {
			for (int x = s / 2 - 1; x <= s / 2 + 1; x++) {
				for (int y = 1; y <= Math.min(3, tiers + 2); y++) b.clear(x, y, z);
				b.set(x, 0, z, p.floor());
			}
		}
		for (int a = 0; a < 8; a++) {
			double ang = a * Math.PI / 4;
			int x = (int) Math.round(c + Math.cos(ang) * (rad - 0.5)), z = (int) Math.round(c + Math.sin(ang) * (rad - 0.5));
			b.set(x, tiers + 4, z, p.light());
		}
		return b;
	}

	/** Small trees and flowers for gardens. */
	static void tree(Blueprint b, int x, int y, int z, Block log, Block leaves, Random r) {
		int h = 4 + r.nextInt(2);
		BlockState leaf = leaves.defaultBlockState();
		if (leaf.hasProperty(BlockStateProperties.PERSISTENT)) leaf = leaf.setValue(BlockStateProperties.PERSISTENT, true);
		for (int dy = h - 2; dy <= h + 1; dy++) {
			int rr = dy >= h ? 1 : 2;
			for (int dx = -rr; dx <= rr; dx++) {
				for (int dz = -rr; dz <= rr; dz++) {
					if (Math.abs(dx) == rr && Math.abs(dz) == rr && (dy == h + 1 || r.nextBoolean())) continue;
					b.set(x + dx, y + dy, z + dz, leaf);
				}
			}
		}
		for (int dy = 0; dy < h; dy++) b.set(x, y + dy, z, log.defaultBlockState());
	}
}
