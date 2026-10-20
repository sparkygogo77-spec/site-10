package com.sparky.lanternring.warren;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.PointedDripstoneBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.SpeleothemThickness;

/**
 * The Dread Warren's lair: J's W1 cave from the giant-spider rounds (docs/handoff/2026-10-19-spider-lair, kept in
 * `tools/trials/spider_cave_wild.py`), carved at every Warren site, different every time ("I always need it in a
 * differently generated"). About 200-250 long, 130-160 wide and 56 high, floor about y -30 (so the ring and dens stay above the lava at y -54): a long natural cavern
 * from 3D noise, leaning one way, with side lobes (corners), hourglass columns, dripstone hanging from the roof, a
 * ring tunnel under its rim, 5 den rooms (about 30 x 24 x 14) in the rock round it with burrows up through the lair's
 * floor and walls and links to the other dens. Lined in the quiet dread stone of the entrances.
 * <p>
 * Everything is a pure function of the world seed and the site, so each chunk carves its own part when it's decorated
 * ({@link #carve}) and the pieces meet up. Not yet here (they need the spiders): cave 1 and the collapse funnel above,
 * the hard-light spike tips, webs (danger only, never across a walkway).
 */
public final class WarrenLair {
	public static final int FLOOR_Y = -30;
	static final double H = 56, DEPTH = 14, SCALE = 1.6;
	/** Ring tunnel radius, burrow radius (9 wide), den half sizes along the ring, across it and up. */
	static final double RING_R = 5.5, BURROW_R = 4.5, DEN_T = 15, DEN_R = 12, DEN_Y = 7;
	private static final int DENS = 5, BIG_SPIKES = 90;

	/** Chunks that carved part of a lair since start-up (for tests). */
	public static final java.util.concurrent.atomic.AtomicLong CHUNKS = new java.util.concurrent.atomic.AtomicLong();

	private static final Map<Long, WarrenLair> CACHE = new ConcurrentHashMap<>();

	public final int cx, cz;
	final long seed;
	final double A, C, yc, tilt, cos, sin, cell1, cell2;
	private final List<double[]> lobes = new ArrayList<>();   // lx, lz, la, lc, lh, ly
	private final List<double[]> cols = new ArrayList<>();    // pu, pv, r0
	private final List<Tube> tubes = new ArrayList<>();
	private final List<double[]> dens = new ArrayList<>();    // x, y, z, angle
	private final List<double[]> spikes = new ArrayList<>();  // x, z, ceiling y, length, radius
	final int minX, maxX, minZ, maxZ, minY, maxY;

	/** The lair at a site (cached). */
	public static WarrenLair get(long seed, int[] site) {
		long key = seed * 961 + (((long) site[0]) << 32 ^ (site[1] & 0xffffffffL));
		if (CACHE.size() > 64) CACHE.clear();
		return CACHE.computeIfAbsent(key, k -> new WarrenLair(seed, site[0], site[1]));
	}

	private WarrenLair(long worldSeed, int cx, int cz) {
		this.cx = cx;
		this.cz = cz;
		this.seed = worldSeed ^ (cx * 73856093L) ^ (cz * 19349663L) ^ 0x4C61_6972L;
		RandomSource r = RandomSource.create(seed);
		A = Mth.nextDouble(r, 62, 78) * SCALE;
		C = Mth.nextDouble(r, 38, 48) * SCALE;
		yc = FLOOR_Y + H * 0.32;
		tilt = Mth.nextDouble(r, -0.18, 0.18);
		double yaw = r.nextDouble() * Math.PI;
		cos = Math.cos(yaw);
		sin = Math.sin(yaw);
		cell1 = 28 * Math.pow(SCALE, 0.7);
		cell2 = 11 * Math.pow(SCALE, 0.4);
		int nl = (int) Math.round((2 + r.nextInt(2)) * Math.pow(SCALE, 0.8));
		double reach = A * 1.25;
		for (int i = 0; i < nl; i++) {
			double a = r.nextDouble() * Mth.TWO_PI, s8 = Math.pow(SCALE, 0.8);
			double[] l = {Math.cos(a) * A * 0.85, Math.sin(a) * C * 0.85, Mth.nextDouble(r, 22, 34) * s8,
					Mth.nextDouble(r, 16, 26) * s8, Mth.nextDouble(r, 14, 24) * Math.pow(Math.min(SCALE, H / 45), 0.8),
					Mth.nextDouble(r, -2, 8)};
			lobes.add(l);
			reach = Math.max(reach, Math.hypot(l[0], l[1]) + Math.max(l[2], l[3]) * 1.2);
		}
		int nc = (int) Math.round((4 + r.nextInt(4)) * Math.pow(SCALE, 1.2));
		for (int i = 0; i < nc; i++) {
			double pu = 0, pv = 0;
			for (int t = 0; t < 20; t++) {
				pu = Mth.nextDouble(r, -0.7, 0.7) * A;
				pv = Mth.nextDouble(r, -0.6, 0.6) * C;
				boolean apart = true;
				for (double[] q : cols) apart &= Math.hypot(pu - q[0], pv - q[1]) > 22 * Math.pow(SCALE, 0.6);
				if (apart) break;
			}
			cols.add(new double[] {pu, pv, Mth.nextDouble(r, 2.5, 5.5) * Math.pow(SCALE, 0.6)});
		}
		// The ring tunnel just outside the rim, under the floor, gently rising and falling.
		double ra = A * 1.12 + RING_R * 1.6, rc = C * 1.2 + RING_R * 1.6;
		double[][] ring = new double[72][];
		for (int i = 0; i < 72; i++) {
			double a = i * Mth.TWO_PI / 72;
			ring[i] = world(Math.cos(a) * ra, FLOOR_Y - DEPTH + 1.5 * Math.sin(3 * a), Math.sin(a) * rc);
		}
		for (int i = 0; i < 72; i++) tubes.add(new Tube(ring[i], ring[(i + 1) % 72], RING_R));
		reach = Math.max(reach, Math.max(ra, rc) + RING_R + DEN_T + 4);
		// One cut-through under the long axis.
		double[] deep = world(0, FLOOR_Y - DEPTH - 2, 0);
		tubes.add(new Tube(ring[0], deep, RING_R - 0.5));
		tubes.add(new Tube(deep, ring[36], RING_R - 0.5));
		// Five dens round the ring; each has a burrow up through the lair's floor and one out of its wall.
		double start = r.nextDouble();
		for (int k = 0; k < DENS; k++) {
			double a = (start + k / (double) DENS + Mth.nextDouble(r, -0.03, 0.03)) * Mth.TWO_PI;
			double[] d = world(Math.cos(a) * ra, FLOOR_Y - DEPTH + 3, Math.sin(a) * rc);
			dens.add(new double[] {d[0], d[1], d[2], a});
			double[] hole = world(Math.cos(a) * A * 0.6, 0, Math.sin(a) * C * 0.6);
			int fl = firstAir((int) hole[0], (int) hole[2], FLOOR_Y);
			burrow(new double[] {hole[0], fl + 2, hole[2]}, new double[] {hole[0], fl - 9, hole[2]}, d);
			double[] wall = world(Math.cos(a + 0.35) * A * 0.92, 0, Math.sin(a + 0.35) * C * 0.92);
			int fw = firstAir((int) wall[0], (int) wall[2], Integer.MIN_VALUE);
			if (fw != Integer.MIN_VALUE) {
				double[] w = {wall[0], fw + BURROW_R, wall[2]};
				burrow(w, new double[] {(w[0] + d[0]) / 2, (w[1] + d[1]) / 2, (w[2] + d[2]) / 2}, d);
			}
		}
		// Every den links to the two it isn't beside on the ring, dipping under the lair on the way.
		for (int k = 0; k < DENS; k++) {
			double[] a = dens.get(k), b = dens.get((k + 2) % DENS);
			double[] mid = {(a[0] + b[0]) / 2, FLOOR_Y - DEPTH - 3, (a[2] + b[2]) / 2};
			burrow(a, mid, b);
		}
		// Big dripstone spikes hanging from the roof (J: "driplets ... they will hang from the ceiling").
		for (int i = 0; i < BIG_SPIKES; i++) {
			double u = Mth.nextDouble(r, -0.85, 0.85) * A, v = Mth.nextDouble(r, -0.8, 0.8) * C;
			double len = Mth.nextDouble(r, 8, 29);
			double[] p = world(u, 0, v);
			int x = Mth.floor(p[0]), z = Mth.floor(p[2]);
			int ceil = ceiling(x, z), floor = firstAir(x, z, Integer.MIN_VALUE);
			if (ceil == Integer.MIN_VALUE || floor == Integer.MIN_VALUE) continue;
			len = Math.min(len, ceil - floor - 5);
			if (len < 6) continue;
			spikes.add(new double[] {x + 0.5, z + 0.5, ceil, len, 1 + len / 7});
		}
		int rb = Mth.ceil(reach + 8);
		minX = cx - rb;
		maxX = cx + rb;
		minZ = cz - rb;
		maxZ = cz + rb;
		minY = (int) (FLOOR_Y - DEPTH - 6 - BURROW_R - 4);
		maxY = Mth.ceil(yc + H * 0.68 * 1.3 + 6);
	}

	private void burrow(double[]... pts) {
		for (int i = 0; i + 1 < pts.length; i++) tubes.add(new Tube(pts[i], pts[i + 1], BURROW_R));
	}

	/** Lair (u across its length, y, v across its width) to world {x, y, z}. */
	private double[] world(double u, double y, double v) {
		return new double[] {cx + u * cos - v * sin, y, cz + u * sin + v * cos};
	}

	/**
	 * Where a tunnel from (x, z) should come into the lair: two thirds of the way out from the middle toward (x, z),
	 * on the floor. Null if (x, z) is already that close in.
	 */
	public BlockPos rimToward(int x, int z) {
		double dx = x - cx, dz = z - cz;
		double u = dx * cos + dz * sin, v = -dx * sin + dz * cos;
		double e = Math.sqrt((u / A) * (u / A) + (v / C) * (v / C));
		if (e < 0.7) return null;
		double[] p = world(u / e * 0.66, 0, v / e * 0.66);
		int px = Mth.floor(p[0]), pz = Mth.floor(p[2]);
		return new BlockPos(px, firstAir(px, pz, FLOOR_Y), pz);
	}

	/** A spot on the floor at (fu of the half-length, fv of the half-width) from the middle, {@code up} blocks over it. */
	public BlockPos standAt(double fu, double fv, int up) {
		double[] p = world(fu * A, 0, fv * C);
		int x = Mth.floor(p[0]), z = Mth.floor(p[2]);
		return new BlockPos(x, firstAir(x, z, FLOOR_Y) + up, z);
	}

	/** Where to stand: the middle of the floor, and the yaw (Minecraft degrees) looking down the long axis. */
	public BlockPos middle() {
		return new BlockPos(cx, firstAir(cx, cz, FLOOR_Y) + 2, cz);
	}

	public float lengthYaw() {
		return (float) Math.toDegrees(Math.atan2(-cos, sin));
	}

	public List<BlockPos> denCentres() {
		List<BlockPos> out = new ArrayList<>();
		for (double[] d : dens) out.add(BlockPos.containing(d[0], d[1] - 2, d[2]));
		return out;
	}

	// ---- the shape --------------------------------------------------------------------------------------

	/** The main cavern's density: above 0 is cave (before the floor cut and the columns). */
	double density(int x, int y, int z) {
		double dx = x - cx, dz = z - cz;
		double u = dx * cos + dz * sin, v = -dx * sin + dz * cos;
		double ysl = (y - yc) - tilt * u;
		double best = -1;
		double vy = ysl > 0 ? ysl / (H * 0.68) : ysl / (H * 0.32);
		double base = (u / A) * (u / A) + vy * vy + (v / C) * (v / C);
		if (base < 1.5) best = 1 - base + 0.32 * noise(x, y, z, cell1, 1) + 0.12 * noise(x, y, z, cell2, 2);
		for (int i = 0; i < lobes.size(); i++) {
			double[] l = lobes.get(i);
			double hu = (u - l[0]) / l[2], hv = (v - l[1]) / l[3];
			if (hu * hu + hv * hv > 1.2) continue;
			double vl = (ysl - l[5]) / l[4];
			if (vl < 0) vl *= 2.2;
			best = Math.max(best, 1 - (hu * hu + vl * vl + hv * hv) + 0.15 * noise(x, y, z, 9, 3 + i));
		}
		return best;
	}

	private boolean inColumn(int x, int y, int z) {
		double dx = x - cx, dz = z - cz;
		double u = dx * cos + dz * sin, v = -dx * sin + dz * cos;
		double k = ((y - yc) - H * 0.25) / (H * 0.6);
		for (double[] c : cols) {
			double rad = c[2] * (1 + 0.9 * k * k);
			double du = u - c[0], dv = v - c[1];
			if (du * du + dv * dv < rad * rad) return true;
		}
		return false;
	}

	/** True if the main cavern is open air here. */
	public boolean caveAir(int x, int y, int z) {
		return y >= FLOOR_Y - 12 && density(x, y, z) > 0 && !inColumn(x, y, z);
	}

	/** The lowest cave air in a column (between y -48 and the top), or {@code dflt}. */
	int firstAir(int x, int z, int dflt) {
		for (int y = FLOOR_Y - 12; y < maxYGuess(); y++) if (caveAir(x, y, z)) return y;
		return dflt;
	}

	/** The highest cave air in a column (just under the roof), or MIN_VALUE. */
	int ceiling(int x, int z) {
		for (int y = maxYGuess(); y >= FLOOR_Y - 12; y--) if (caveAir(x, y, z)) return y;
		return Integer.MIN_VALUE;
	}

	private int maxYGuess() {
		return Mth.ceil(yc + H * 0.68 * 1.3 + 4);
	}

	/** 0 = leave, 1 = air, 2 = lining. */
	private int classify(int x, int y, int z, List<Tube> ts, List<double[]> ds) {
		double wob = 1 + 0.1 * noise(x, y, z, 5, 9);
		double d = density(x, y, z);
		boolean col = inColumn(x, y, z);
		if (d > 0 && y >= FLOOR_Y - 12 && !col) return 1;
		double near = Double.MAX_VALUE;
		for (Tube t : ts) {
			double q = t.dist2(x, y, z) / (t.r * t.r);
			if (q < 1 * wob) return 1;
			near = Math.min(near, Math.sqrt(t.dist2(x, y, z)) - t.r);
		}
		for (double[] den : ds) {
			double q = denQ(den, x, y, z, 0);
			if (q < wob && y >= den[1] - DEN_Y * 0.55) return 1;   // a flat floor
			if (denQ(den, x, y, z, 2.5) < wob) return 2;
		}
		if (near < 2.4) return 2;
		if (d > 0 && (col || y >= FLOOR_Y - 15)) return 2;   // the columns and the floor under the cut
		if (d > -0.06 && y >= FLOOR_Y - 15) return 2;
		return 0;
	}

	private static double denQ(double[] den, int x, int y, int z, double grow) {
		double dx = x - den[0], dz = z - den[2], dy = y - den[1];
		double ct = -Math.sin(den[3]), st = Math.cos(den[3]);   // along the ring, then across it
		double t = (dx * ct + dz * st) / (DEN_T + grow), r = (-dx * st + dz * ct) / (DEN_R + grow), h = dy / (DEN_Y + grow);
		return t * t + r * r + h * h;
	}

	// ---- carving one chunk ------------------------------------------------------------------------------

	/** Carves this lair's part of one chunk (called as the chunk is decorated). */
	public void carve(WorldGenLevel level, ChunkPos chunk) {
		int x0 = chunk.getMinBlockX(), z0 = chunk.getMinBlockZ();
		if (x0 + 15 < minX || x0 > maxX || z0 + 15 < minZ || z0 > maxZ) return;
		List<Tube> ts = new ArrayList<>();
		for (Tube t : tubes) if (t.near(x0, z0, 4)) ts.add(t);
		List<double[]> ds = new ArrayList<>();
		for (double[] d : dens) {
			if (d[0] + DEN_T + 4 >= x0 && d[0] - DEN_T - 4 <= x0 + 15 && d[2] + DEN_T + 4 >= z0 && d[2] - DEN_T - 4 <= z0 + 15) ds.add(d);
		}
		int lo = Math.max(minY, level.getMinY() + 2), hi = maxY, ny = hi - lo + 1;
		byte[] cls = new byte[16 * 16 * ny];
		boolean any = false;
		for (int i = 0; i < 16; i++) {
			for (int k = 0; k < 16; k++) {
				if (!columnNear(x0 + i, z0 + k, ts, ds)) continue;
				for (int y = lo; y <= hi; y++) {
					int c = classify(x0 + i, y, z0 + k, ts, ds);
					cls[(i * 16 + k) * ny + (y - lo)] = (byte) c;
					any |= c != 0;
				}
			}
		}
		if (!any) return;
		CHUNKS.incrementAndGet();
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		BlockState air = Blocks.CAVE_AIR.defaultBlockState();
		for (int i = 0; i < 16; i++) {
			for (int k = 0; k < 16; k++) {
				for (int y = lo; y <= hi; y++) {
					int c = cls[(i * 16 + k) * ny + (y - lo)];
					if (c == 0) continue;
					int x = x0 + i, z = z0 + k;
					pos.set(x, y, z);
					BlockState here = level.getBlockState(pos);
					if (here.is(BlockTags.FEATURES_CANNOT_REPLACE)) continue;
					boolean fluid = !here.getFluidState().isEmpty();
					if (c == 1) {
						level.setBlock(pos, sealsFluid(level, pos, ts, ds) ? lining(x, y, z) : air, 2);
					} else if (fluid || isRock(here)) {
						level.setBlock(pos, lining(x, y, z), 2);
					}
				}
			}
		}
		decorate(level, x0, z0, lo, ny, cls, pos);
	}

	/** False if nothing of the lair can reach this column (a quick skip for the corners of its square). */
	private boolean columnNear(int x, int z, List<Tube> ts, List<double[]> ds) {
		double dx = x - cx, dz = z - cz;
		double u = dx * cos + dz * sin, v = -dx * sin + dz * cos;
		// The tilt shifts the floor, not the outline; noise can push the wall out by about a fifth.
		if ((u / A) * (u / A) + (v / C) * (v / C) < 1.6) return true;
		for (double[] l : lobes) {
			double hu = (u - l[0]) / l[2], hv = (v - l[1]) / l[3];
			if (hu * hu + hv * hv < 1.3) return true;
		}
		for (Tube t : ts) if (t.dist2xz(x, z) < (t.r + 3) * (t.r + 3)) return true;
		for (double[] d : ds) if (Math.hypot(x - d[0], z - d[2]) < DEN_T + 4) return true;
		return false;
	}

	/** True if an air block here would touch water or lava that stays (outside everything we carve). */
	private boolean sealsFluid(WorldGenLevel level, BlockPos pos, List<Tube> ts, List<double[]> ds) {
		for (Direction d : Direction.values()) {
			BlockPos n = pos.relative(d);
			if (level.getFluidState(n).isEmpty()) continue;
			if (classify(n.getX(), n.getY(), n.getZ(), ts, ds) == 0) return true;
		}
		return false;
	}

	/** Dripstone from roof and floor, the big hanging spikes, and a few old bones on the floor. */
	private void decorate(WorldGenLevel level, int x0, int z0, int lo, int ny, byte[] cls, BlockPos.MutableBlockPos pos) {
		for (int i = 0; i < 16; i++) {
			for (int k = 0; k < 16; k++) {
				int x = x0 + i, z = z0 + k, base = (i * 16 + k) * ny;
				for (int j = 1; j < ny - 1; j++) {
					if (cls[base + j] != 1) continue;
					int y = lo + j;
					long h = hash(x, y, z);
					if (cls[base + j + 1] == 2 && (h & 1023) < 70) {        // a roof: small dripstone
						hang(level, pos, x, y, z, 1 + (int) ((h >>> 10) % 3), Direction.DOWN, cls, base, j, ny);
					} else if (cls[base + j - 1] == 2) {                      // a floor
						if ((h & 1023) < 22) hang(level, pos, x, y, z, 1 + (int) ((h >>> 10) % 2), Direction.UP, cls, base, j, ny);
						else if ((h & 1023) < 28) level.setBlock(pos.set(x, y - 1, z), Blocks.BONE_BLOCK.defaultBlockState(), 2);
					}
				}
			}
		}
		for (double[] s : spikes) {
			double r = s[4];
			if (s[0] + r < x0 || s[0] - r > x0 + 16 || s[1] + r < z0 || s[1] - r > z0 + 16) continue;
			int ceil = (int) s[2], len = (int) s[3];
			for (int y = ceil; y > ceil - len; y--) {
				double rad = r * (1 - (ceil - y) / (double) len);
				for (int i = 0; i < 16; i++) {
					for (int k = 0; k < 16; k++) {
						double dx = x0 + i + 0.5 - s[0], dz = z0 + k + 0.5 - s[1];
						int j = y - lo;
						if (j < 0 || j >= ny || cls[(i * 16 + k) * ny + j] != 1) continue;
						double d2 = dx * dx + dz * dz;
						if (d2 > rad * rad && !(d2 < 0.3 && ceil - y < len)) continue;
						BlockState st = Blocks.DRIPSTONE_BLOCK.defaultBlockState();
						if (rad < 1.0) st = speleothem(Direction.DOWN, ceil - y >= len - 1 ? SpeleothemThickness.TIP : SpeleothemThickness.FRUSTUM);
						level.setBlock(pos.set(x0 + i, y, z0 + k), st, 2);
					}
				}
			}
		}
	}

	/** A small dripstone of {@code n} blocks from (x, y, z) pointing {@code dir}, as far as the air goes. */
	private void hang(WorldGenLevel level, BlockPos.MutableBlockPos pos, int x, int y, int z, int n, Direction dir,
			byte[] cls, int base, int j, int ny) {
		int step = dir == Direction.DOWN ? -1 : 1;
		int len = 0;
		while (len < n && j + step * len > 0 && j + step * len < ny - 1 && cls[base + j + step * len] == 1) len++;
		// Leave the block before the next floor/roof as air so a spike never seals a gap.
		int past = j + step * len;
		if (len > 1 && past > 0 && past < ny - 1 && cls[base + past] != 1) len--;
		for (int m = 0; m < len; m++) {
			SpeleothemThickness t = m == len - 1 ? SpeleothemThickness.TIP
					: m == 0 && len >= 3 ? SpeleothemThickness.BASE : SpeleothemThickness.FRUSTUM;
			level.setBlock(pos.set(x, y + step * m, z), speleothem(dir, t), 2);
		}
	}

	private static BlockState speleothem(Direction dir, SpeleothemThickness t) {
		return Blocks.POINTED_DRIPSTONE.defaultBlockState().setValue(PointedDripstoneBlock.TIP_DIRECTION, dir)
				.setValue(PointedDripstoneBlock.THICKNESS, t);
	}

	/** The quiet dread-stone lining (the entrance's mix): dark natural blocks, a rare gilded fleck the only gold. */
	BlockState lining(int x, int y, int z) {
		int h = (int) ((hash(x, y, z) >>> 8) % 100);
		if (h < 38) return Blocks.COBBLED_DEEPSLATE.defaultBlockState();
		if (h < 66) return Blocks.DEEPSLATE.defaultBlockState();
		if (h < 88) return Blocks.BLACKSTONE.defaultBlockState();
		if (h < 99) return Blocks.TUFF.defaultBlockState();
		return Blocks.GILDED_BLACKSTONE.defaultBlockState();
	}

	static boolean isRock(BlockState s) {
		return s.is(BlockTags.BASE_STONE_OVERWORLD) || s.is(BlockTags.DIRT) || s.is(Blocks.GRAVEL)
				|| BuiltInRegistries.BLOCK.getKey(s.getBlock()).getPath().endsWith("_ore");
	}

	// ---- noise ------------------------------------------------------------------------------------------

	/** Smooth value noise in -1..1 with lattice cells {@code cell} blocks across (the script's upsampled grid). */
	double noise(double x, double y, double z, double cell, int salt) {
		x /= cell;
		y /= cell;
		z /= cell;
		int ix = Mth.floor(x), iy = Mth.floor(y), iz = Mth.floor(z);
		double fx = smooth(x - ix), fy = smooth(y - iy), fz = smooth(z - iz);
		double v = 0;
		for (int c = 0; c < 8; c++) {
			int ox = c & 1, oy = (c >> 1) & 1, oz = (c >> 2) & 1;
			double w = (ox == 1 ? fx : 1 - fx) * (oy == 1 ? fy : 1 - fy) * (oz == 1 ? fz : 1 - fz);
			v += w * lattice(ix + ox, iy + oy, iz + oz, salt);
		}
		return v;
	}

	private static double smooth(double t) {
		return t * t * (3 - 2 * t);
	}

	private double lattice(int x, int y, int z, int salt) {
		return (hash(x * 7 + salt, y, z * 13 - salt) >>> 11) / (double) (1L << 52) * 2 - 1;
	}

	long hash(int x, int y, int z) {
		long h = seed ^ (x * 3129871L) ^ (z * 116129781L) ^ (long) y * 0x2545F4914F6CDD1DL;
		h = (h ^ (h >>> 33)) * 0xff51afd7ed558ccdL;
		h = (h ^ (h >>> 33)) * 0xc4ceb9fe1a85ec53L;
		return (h ^ (h >>> 33)) & Long.MAX_VALUE;
	}

	/** A straight stretch of round tunnel. */
	static final class Tube {
		final double ax, ay, az, bx, by, bz, r;
		final double loX, hiX, loZ, hiZ;

		Tube(double[] a, double[] b, double r) {
			ax = a[0];
			ay = a[1];
			az = a[2];
			bx = b[0];
			by = b[1];
			bz = b[2];
			this.r = r;
			loX = Math.min(ax, bx) - r;
			hiX = Math.max(ax, bx) + r;
			loZ = Math.min(az, bz) - r;
			hiZ = Math.max(az, bz) + r;
		}

		boolean near(int x0, int z0, double pad) {
			return hiX + pad >= x0 && loX - pad <= x0 + 15 && hiZ + pad >= z0 && loZ - pad <= z0 + 15;
		}

		double dist2xz(double x, double z) {
			double ux = bx - ax, uz = bz - az;
			double l2 = ux * ux + uz * uz;
			double t = l2 == 0 ? 0 : Mth.clamp(((x - ax) * ux + (z - az) * uz) / l2, 0, 1);
			double dx = x - (ax + ux * t), dz = z - (az + uz * t);
			return dx * dx + dz * dz;
		}

		double dist2(double x, double y, double z) {
			double ux = bx - ax, uy = by - ay, uz = bz - az;
			double l2 = ux * ux + uy * uy + uz * uz;
			double t = l2 == 0 ? 0 : Mth.clamp(((x - ax) * ux + (y - ay) * uy + (z - az) * uz) / l2, 0, 1);
			double dx = x - (ax + ux * t), dy = y - (ay + uy * t), dz = z - (az + uz * t);
			return dx * dx + dy * dy + dz * dz;
		}
	}
}
