package com.sparky.lanternring.city;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CropBlock;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BedPart;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.Half;
import net.minecraft.world.level.block.state.properties.SlabType;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The Blue Lantern sky city: a vertical city for builders who fly, so its levels are joined by
 * Sky Light bridges and lift tubes rather than stairs. Everything is placed relative to the
 * anchor, the top middle of the foundation disc. Pieces are built in {@link Piece} order, one per
 * U-formation burst of energy; which ones stand is read from the world, so building carries on
 * after a restart. See /mnt/project-files/plans/blue-city.md.
 */
public final class BlueCity {
	/** Foundation disc radius, spire half-width and height, and where the dwelling towers float. */
	static final int DISC_R = 15, SPIRE_HALF = 4, SPIRE_TOP = 44, TOWER_RING = 24, PLATFORM_R = 5, PORT_Y = 36;
	/** Floors inside the spire, every 9 blocks; the ports come off the top one. */
	static final int FLOOR_EVERY = 9;
	/** Each dwelling tower's floor height over the disc; never level with a spire floor, so the doorways miss them. */
	private static final int[] TOWER_Y = {2, 5, 11, 14, 20, 23};
	/** Above the disc: room the city needs for its spire and crown. */
	public static final int HEIGHT = 60;

	public enum Piece {
		FOUNDATION, SPIRE, LIFTS, TOWER_1, TOWER_2, TOWER_3, TOWER_4, TOWER_5, TOWER_6, GARDEN_EAST, GARDEN_WEST, PORTS, CROWN
	}

	// ---- for the villagers ---------------------------------------------------------------------

	/** Where a village's sky city floats: well over the village and anything round it. */
	public static BlockPos site(ServerLevel level, BlockPos villageCentre) {
		int max = villageCentre.getY();
		int r = TOWER_RING + PLATFORM_R;
		for (int dx = -r; dx <= r; dx += 4) {
			for (int dz = -r; dz <= r; dz += 4) {
				max = Math.max(max, level.getHeight(Heightmap.Types.MOTION_BLOCKING, villageCentre.getX() + dx, villageCentre.getZ() + dz));
			}
		}
		// The underside hangs ~15 below the disc, so leave clear air under that.
		int y = Math.min(max + 30, level.getMaxY() - HEIGHT - 4);
		return new BlockPos(villageCentre.getX(), y, villageCentre.getZ());
	}

	/**
	 * The sky city that belongs to a village, founding one (saved with the world) if there isn't one
	 * within 64 blocks yet.
	 */
	public static CityData.City cityFor(ServerLevel level, BlockPos villageCentre) {
		CityData data = CityData.get(level);
		CityData.City city = data.near(villageCentre, 64);
		return city != null ? city : data.add(site(level, villageCentre), villageCentre);
	}

	/**
	 * Called when a U team fires its energy. Carries on the piece the city is building (from the
	 * block it stopped at) with these builders, or lets {@link CityPlanner} pick the next one.
	 * Returns the job (its builders draw the energy beams), or null if the city is complete.
	 */
	public static CityBuilds.@Nullable Job buildNext(ServerLevel level, CityData.City city, List<? extends Entity> builders) {
		CityBuilds.Job job = CityBuilds.find(level, city);
		if (job == null) {
			Piece p = city.active();
			if (p == null) {
				p = CityPlanner.choose(level, city);
				if (p == null) return null;
				city.active = p.ordinal();
				city.formed = city.set = 0;
				city.bursts++;
				CityData.get(level).setDirty();
			}
			job = CityBuilds.start(level, city, p, blocks(city.anchor, p), com.sparky.lanternring.RingTuning.CITY_PIECE.ticks(), focus(city.anchor, p));
		}
		job.attach(builders);
		return job;
	}

	/** Builds the whole city at once, already set, and marks it built (for tests). */
	public static void buildAll(ServerLevel level, CityData.City city) {
		for (Piece p : Piece.values()) {
			CityBuilds.instant(level, blocks(city.anchor, p));
			city.mark(p, true);
		}
		CityData.get(level).setDirty();
	}

	static boolean isTower(Piece p) {
		return p.ordinal() >= Piece.TOWER_1.ordinal() && p.ordinal() <= Piece.TOWER_6.ordinal();
	}

	static int towerIndex(Piece p) {
		return p.ordinal() - Piece.TOWER_1.ordinal();
	}

	static Piece tower(int i) {
		return Piece.values()[Piece.TOWER_1.ordinal() + i];
	}

	/** The four flier landing pads on the top level (the middle of each pad's top surface). */
	public static List<BlockPos> ports(BlockPos anchor) {
		List<BlockPos> out = new ArrayList<>();
		for (Direction d : Direction.Plane.HORIZONTAL) out.add(anchor.offset(d.getStepX() * 16, PORT_Y - 1, d.getStepZ() * 16));
		return out;
	}

	/** Where a U team gathers to build a piece: the middle of it. */
	public static Vec3 focus(BlockPos anchor, Piece p) {
		Vec3 a = Vec3.atBottomCenterOf(anchor);
		return switch (p) {
			case FOUNDATION -> a.add(0, -3, 0);
			case SPIRE -> a.add(0, 10, 0);
			case LIFTS -> a.add(0, 18, 0);
			case GARDEN_EAST -> a.add(polar(60, 10, 0)).add(0, 1, 0);
			case GARDEN_WEST -> a.add(polar(240, 10, 0)).add(0, 1, 0);
			case PORTS -> a.add(0, PORT_Y, 0);
			case CROWN -> a.add(0, SPIRE_TOP + 6, 0);
			default -> {
				int i = p.ordinal() - Piece.TOWER_1.ordinal();
				yield a.add(towerCentre(i)).add(0, 5, 0);
			}
		};
	}

	// ---- progress ------------------------------------------------------------------------------

	/**
	 * Whether a piece stands: its keystone (its highest Skystone or lamp block) has set. Null if
	 * the keystone's chunk isn't loaded, so nothing is decided about it.
	 */
	@Nullable
	static Boolean stands(ServerLevel level, BlockPos anchor, Piece p) {
		BlockPos key = null;
		BlockState keyState = null;
		for (Map.Entry<BlockPos, BlockState> e : blocks(anchor, p).entrySet()) {
			BlockState s = e.getValue();
			if (s.is(CityBlocks.SKY_LIGHT) || !CityBlocks.isCity(s)) continue;
			if (key == null || e.getKey().getY() > key.getY()) {
				key = e.getKey();
				keyState = s;
			}
		}
		if (key == null) return true;
		if (!level.isLoaded(key)) return null;
		return level.getBlockState(key).is(keyState.getBlock());
	}

	// ---- the pieces ----------------------------------------------------------------------------

	static Map<BlockPos, BlockState> blocks(BlockPos anchor, Piece p) {
		Shape s = new Shape(anchor, RandomSource.create(anchor.asLong() * 31 + p.ordinal()));
		switch (p) {
			case FOUNDATION -> foundation(s);
			case SPIRE -> spire(s);
			case LIFTS -> lifts(s);
			case GARDEN_EAST -> garden(s, 60);
			case GARDEN_WEST -> garden(s, 240);
			case PORTS -> ports(s);
			case CROWN -> crown(s);
			default -> tower(s, p.ordinal() - Piece.TOWER_1.ordinal());
		}
		return s.out;
	}

	/** The building kit: positions relative to the anchor. */
	static final class Shape {
		final BlockPos anchor;
		final RandomSource rng;
		final Map<BlockPos, BlockState> out = new LinkedHashMap<>();

		Shape(BlockPos anchor, RandomSource rng) {
			this.anchor = anchor;
			this.rng = rng;
		}

		void put(int x, int y, int z, BlockState s) {
			out.put(anchor.offset(x, y, z), s);
		}

		void putIfFree(int x, int y, int z, BlockState s) {
			out.putIfAbsent(anchor.offset(x, y, z), s);
		}

		void air(int x, int y, int z) {
			out.put(anchor.offset(x, y, z), Blocks.AIR.defaultBlockState());
		}
	}

	private static final BlockState BRICKS = CityBlocks.SKYSTONE_BRICKS.defaultBlockState();
	private static final BlockState TILES = CityBlocks.SKYSTONE_TILES.defaultBlockState();
	private static final BlockState PILLAR = CityBlocks.SKYSTONE_PILLAR.defaultBlockState();
	private static final BlockState LAMP = CityBlocks.HOPE_LAMP.defaultBlockState();
	private static final BlockState LIGHT = CityBlocks.SKY_LIGHT.defaultBlockState();
	private static final BlockState SLAB = CityBlocks.SKYSTONE_SLAB.defaultBlockState();

	private static BlockState stairs(Direction facing, boolean upsideDown) {
		return CityBlocks.SKYSTONE_STAIRS.defaultBlockState().setValue(StairBlock.FACING, facing)
				.setValue(StairBlock.HALF, upsideDown ? Half.TOP : Half.BOTTOM);
	}

	private static Vec3 polar(double deg, double r, double y) {
		double a = Math.toRadians(deg);
		return new Vec3(Math.cos(a) * r, y, Math.sin(a) * r);
	}

	/** Which way a point at (x, z) faces outward, by its larger axis. */
	private static Direction outward(int x, int z) {
		if (Math.abs(x) >= Math.abs(z)) return x >= 0 ? Direction.EAST : Direction.WEST;
		return z >= 0 ? Direction.SOUTH : Direction.NORTH;
	}

	private static double towerAngle(int i) {
		return 30 + i * 60;
	}

	private static Vec3 towerCentre(int i) {
		Vec3 c = polar(towerAngle(i), TOWER_RING, TOWER_Y[i]);
		return new Vec3(Math.round(c.x), c.y, Math.round(c.z));
	}

	/** A floating platform: a disc whose top is at y, hanging to a rough point below like an End island turned to stone. */
	private static void platform(Shape s, int cx, int y, int cz, double r, double depthScale, boolean lit) {
		int ir = Mth.ceil(r) + 1;
		for (int dx = -ir; dx <= ir; dx++) {
			for (int dz = -ir; dz <= ir; dz++) {
				double d = Math.sqrt(dx * dx + dz * dz);
				if (d > r) continue;
				boolean rim = d > r - 1;
				s.put(cx + dx, y, cz + dz, rim ? BRICKS : TILES);
				int depth = 1 + (int) ((r - d) * depthScale);
				for (int k = 1; k <= depth; k++) {
					boolean tip = k == depth && depth > 3;
					s.put(cx + dx, y - k, cz + dz, tip && lit && (dx + dz) % 3 == 0 ? LAMP : BRICKS);
				}
			}
		}
	}

	/** A hard-light rail round a circle's edge at height y, with gaps at the given angles (degrees). */
	private static void rail(Shape s, int cx, int y, int cz, double r, double... gaps) {
		int ir = Mth.ceil(r) + 1;
		for (int dx = -ir; dx <= ir; dx++) {
			for (int dz = -ir; dz <= ir; dz++) {
				double d = Math.sqrt(dx * dx + dz * dz);
				if (d > r || d <= r - 1) continue;
				double a = Math.toDegrees(Math.atan2(dz, dx));
				boolean gap = false;
				for (double g : gaps) {
					if (Math.abs(Mth.wrapDegrees(a - g)) < 9) gap = true;
				}
				if (!gap) s.putIfFree(cx + dx, y, cz + dz, LIGHT);
			}
		}
	}

	private static void foundation(Shape s) {
		platform(s, 0, 0, 0, DISC_R, 0.95, true);
		// Lamps round the rim and a ring of light under the edge, so it glows from the ground.
		for (int i = 0; i < 12; i++) {
			Vec3 p = polar(i * 30 + 15, DISC_R - 0.5, 0);
			s.put((int) Math.round(p.x), 0, (int) Math.round(p.z), LAMP);
		}
		double[] gaps = new double[TOWER_Y.length + 2];
		for (int i = 0; i < TOWER_Y.length; i++) gaps[i] = towerAngle(i);
		gaps[TOWER_Y.length] = 0;
		gaps[TOWER_Y.length + 1] = 180;
		rail(s, 0, 1, 0, DISC_R, gaps);
		// A centre emblem: a lit ring of tiles round the spire's foot.
		for (int dx = -6; dx <= 6; dx++) {
			for (int dz = -6; dz <= 6; dz++) {
				double d = Math.sqrt(dx * dx + dz * dz);
				if (d > 5.5 && d <= 6.5) s.put(dx, 0, dz, LIGHT);
			}
		}
	}

	/** The core spire: square walls with pillar corners, wide End-city caps every floor, window bands of hard light. */
	private static void spire(Shape s) {
		int h = SPIRE_HALF;
		for (int y = 1; y <= SPIRE_TOP; y++) {
			int seg = (y - 1) % FLOOR_EVERY;
			for (int x = -h; x <= h; x++) {
				for (int z = -h; z <= h; z++) {
					boolean edgeX = Math.abs(x) == h, edgeZ = Math.abs(z) == h;
					if (!edgeX && !edgeZ) {
						// Floors with a lift hole in the middle; air elsewhere inside.
						if (y % FLOOR_EVERY == 0 && (Math.abs(x) > 1 || Math.abs(z) > 1)) s.put(x, y, z, TILES);
						else s.air(x, y, z);
						continue;
					}
					if (edgeX && edgeZ) {
						s.put(x, y, z, PILLAR);
						continue;
					}
					int along = edgeX ? z : x;
					boolean window = Math.abs(along) <= 1 && seg >= 2 && seg <= 5;
					boolean slit = Math.abs(along) == 3 && seg >= 1 && seg <= 6;
					s.put(x, y, z, window || slit ? LIGHT : BRICKS);
				}
			}
			if (y % FLOOR_EVERY == 0) cap(s, y, h + 2);
		}
		// Roof.
		for (int x = -h; x <= h; x++) {
			for (int z = -h; z <= h; z++) s.put(x, SPIRE_TOP, z, Math.abs(x) <= 1 && Math.abs(z) <= 1 ? LIGHT : TILES);
		}
		// Glowing lift core down the middle hole: a lamp at the foot.
		s.put(0, 0, 0, LAMP);
	}

	/** An End-city cap: a flared ledge of half-width w round the tower at y, upside-down stairs underneath, lamps hung at the corners. */
	private static void cap(Shape s, int y, int w) {
		for (int x = -w; x <= w; x++) {
			for (int z = -w; z <= w; z++) {
				int m = Math.max(Math.abs(x), Math.abs(z));
				if (m <= SPIRE_HALF) continue;
				s.put(x, y, z, m == w ? BRICKS : TILES);
				if (m == w) {
					s.put(x, y + 1, z, Math.abs(x) == w && Math.abs(z) == w ? LAMP : SLAB);
				} else if (m == SPIRE_HALF + 1) {
					s.putIfFree(x, y - 1, z, stairs(outward(x, z).getOpposite(), true));
				}
			}
		}
		for (int sx = -1; sx <= 1; sx += 2) {
			for (int sz = -1; sz <= 1; sz += 2) s.put(sx * w, y - 1, sz * w, LAMP);
		}
	}

	/** Two lift tubes from the disc to the port level: hollow hard light, open at the ends. */
	private static void lifts(Shape s) {
		for (int side = -1; side <= 1; side += 2) {
			int cx = side * 11;
			for (int y = 1; y <= PORT_Y - 2; y++) {
				for (int dx = -2; dx <= 2; dx++) {
					for (int dz = -2; dz <= 2; dz++) {
						int m = Math.max(Math.abs(dx), Math.abs(dz));
						if (m == 2) {
							boolean corner = Math.abs(dx) == 2 && Math.abs(dz) == 2;
							boolean door = y <= 3 && dx == -side * 2 && Math.abs(dz) <= 0 || y <= 3 && dx == side * 2 && dz == 0;
							if (door) s.air(cx + dx, y, dz);
							else s.put(cx + dx, y, dz, corner ? PILLAR : LIGHT);
						} else {
							s.air(cx + dx, y, dz);
						}
					}
				}
				if (y % 6 == 0) {
					for (int dx = -2; dx <= 2; dx++) {
						for (int dz = -2; dz <= 2; dz++) {
							if (Math.max(Math.abs(dx), Math.abs(dz)) == 2) s.put(cx + dx, y, dz, BRICKS);
						}
					}
				}
			}
		}
	}

	/** A dwelling tower on its own floating platform, joined to the spire by a hard-light bridge. */
	private static void tower(Shape s, int i) {
		Vec3 c = towerCentre(i);
		int cx = (int) c.x, cz = (int) c.z, y0 = TOWER_Y[i];
		platform(s, cx, y0 - 1, cz, PLATFORM_R + 0.5, 1.1, true);
		rail(s, cx, y0, cz, PLATFORM_R + 0.5, towerAngle(i) + 180);
		// Which wall faces the spire: the door goes there.
		Direction toSpire = outward(-cx, -cz);
		int h = 2, top = y0 + 9;
		for (int y = y0; y <= top; y++) {
			for (int x = -h; x <= h; x++) {
				for (int z = -h; z <= h; z++) {
					int wx = cx + x, wz = cz + z;
					boolean edgeX = Math.abs(x) == h, edgeZ = Math.abs(z) == h;
					if (!edgeX && !edgeZ) {
						if (y == y0 + 5 && !(x == 1 && z == 1)) s.put(wx, y, wz, TILES);
						else s.air(wx, y, wz);
						continue;
					}
					if (edgeX && edgeZ) {
						s.put(wx, y, wz, PILLAR);
						continue;
					}
					int along = edgeX ? z : x;
					Direction face = edgeX ? (x > 0 ? Direction.EAST : Direction.WEST) : (z > 0 ? Direction.SOUTH : Direction.NORTH);
					int ly = y - y0;
					boolean door = face == toSpire && along == 0 && ly <= 1;
					boolean window = along == 0 && (ly == 2 || ly == 3 || ly == 7 || ly == 8) && face != toSpire || along == 0 && ly >= 7 && ly <= 8;
					if (door) s.air(wx, y, wz);
					else s.put(wx, y, wz, window ? LIGHT : BRICKS);
				}
			}
		}
		// Rooms: a bed on each floor, a lamp in each ceiling.
		Direction bedDir = toSpire.getClockWise();
		for (int floor = 0; floor < 2; floor++) {
			int fy = y0 + floor * 6;
			int bx = cx - bedDir.getStepX() / 2 + toSpire.getOpposite().getStepX(), bz = cz - bedDir.getStepZ() / 2 + toSpire.getOpposite().getStepZ();
			BlockState bed = Blocks.BED.lightBlue().defaultBlockState().setValue(BlockStateProperties.HORIZONTAL_FACING, bedDir);
			s.put(bx - cxOff(bedDir), fy, bz - czOff(bedDir), bed.setValue(BlockStateProperties.BED_PART, BedPart.FOOT));
			s.put(bx, fy, bz, bed.setValue(BlockStateProperties.BED_PART, BedPart.HEAD));
			s.put(cx, y0 + (floor == 0 ? 4 : 9), cz, LAMP);
		}
		// A flared End-city roof: a wide ledge, upside-down stairs under it, then a stepped crown and a lamp.
		for (int x = -3; x <= 3; x++) {
			for (int z = -3; z <= 3; z++) {
				int m = Math.max(Math.abs(x), Math.abs(z));
				if (m == 3) {
					s.put(cx + x, top + 1, cz + z, Math.abs(x) == 3 && Math.abs(z) == 3 ? LAMP : SLAB);
					s.put(cx + x, top, cz + z, stairs(outward(x, z).getOpposite(), true));
				} else {
					s.put(cx + x, top + 1, cz + z, m == 2 ? BRICKS : TILES);
				}
			}
		}
		for (int x = -1; x <= 1; x++) {
			for (int z = -1; z <= 1; z++) {
				s.put(cx + x, top + 2, cz + z, x == 0 && z == 0 ? PILLAR : stairs(outward(x, z).getOpposite(), false));
			}
		}
		s.put(cx, top + 3, cz, PILLAR);
		s.put(cx, top + 4, cz, LAMP);
		bridge(s, cx, y0 - 1, cz);
	}

	private static int cxOff(Direction d) {
		return d.getStepX();
	}

	private static int czOff(Direction d) {
		return d.getStepZ();
	}

	/** A three-wide hard-light bridge at height y from (fx, fz) to the spire's lift hole, carving a doorway through the spire wall. */
	private static void bridge(Shape s, int fx, int y, int fz) {
		double len = Math.sqrt(fx * fx + fz * fz);
		double ux = -fx / len, uz = -fz / len;
		for (double t = PLATFORM_R - 1; t <= len - 2; t += 0.4) {
			double px = fx + ux * t, pz = fz + uz * t;
			for (double w = -1.2; w <= 1.2; w += 0.4) {
				int x = (int) Math.round(px - uz * w), z = (int) Math.round(pz + ux * w);
				boolean inSpire = Math.abs(x) <= SPIRE_HALF && Math.abs(z) <= SPIRE_HALF;
				if (Math.abs(x) <= 1 && Math.abs(z) <= 1) continue;
				s.put(x, y, z, inSpire ? TILES : LIGHT);
				for (int k = 1; k <= 3; k++) {
					if (inSpire || Math.abs(x) <= SPIRE_HALF + 2 && Math.abs(z) <= SPIRE_HALF + 2) s.air(x, y + k, z);
				}
				if (Math.abs(w) > 1.1 && !inSpire && t > PLATFORM_R + 0.5) s.putIfFree(x, y + 1, z, LIGHT);
			}
		}
	}

	/** A hanging garden on the disc: raised beds of crops round a water channel, between two bridges. */
	private static void garden(Shape s, double angle) {
		BlockState farmland = Blocks.FARMLAND.defaultBlockState().setValue(BlockStateProperties.MOISTURE, 7);
		Block[] crops = {Blocks.WHEAT, Blocks.CARROTS, Blocks.POTATOES, Blocks.BEETROOTS};
		for (int dx = -DISC_R; dx <= DISC_R; dx++) {
			for (int dz = -DISC_R; dz <= DISC_R; dz++) {
				double d = Math.sqrt(dx * dx + dz * dz);
				double a = Math.toDegrees(Math.atan2(dz, dx));
				double off = Mth.wrapDegrees(a - angle);
				if (d < 6.5 || d > 13.5 || Math.abs(off) > 19) continue;
				boolean edge = d > 12.5 || d < 7.5 || Math.abs(off) > 16;
				if (edge) {
					s.put(dx, 1, dz, BRICKS);
					if (Math.abs(off) > 16 && d > 12.5) s.put(dx, 2, dz, LAMP);
					continue;
				}
				if (Math.abs(d - 10) < 0.6) {
					s.put(dx, 1, dz, Blocks.WATER.defaultBlockState());
					continue;
				}
				s.put(dx, 1, dz, farmland);
				Block crop = crops[(int) ((off + 16) / 8) % crops.length];
				s.put(dx, 2, dz, ((CropBlock) crop).getStateForAge(((CropBlock) crop).getMaxAge()));
			}
		}
	}

	/** Four arms off the top cap, each ending in a lit landing pad for fliers. */
	private static void ports(Shape s) {
		int y = PORT_Y - 1;
		for (Direction d : Direction.Plane.HORIZONTAL) {
			int sx = d.getStepX(), sz = d.getStepZ();
			for (int t = SPIRE_HALF + 3; t <= 18; t++) {
				for (int w = -2; w <= 2; w++) {
					int x = sx * t + (sz != 0 ? w : 0), z = sz * t + (sx != 0 ? w : 0);
					boolean pad = t >= 14;
					if (!pad && Math.abs(w) == 2) continue;
					boolean padEdge = pad && (t == 14 || t == 18 || Math.abs(w) == 2);
					boolean padCorner = pad && (t == 14 || t == 18) && Math.abs(w) == 2;
					s.put(x, y, z, padCorner ? LAMP : padEdge ? BRICKS : pad ? TILES : LIGHT);
					// Underneath: a keel of stairs, thinner toward the pad.
					if (!pad && w == 0) s.put(x, y - 1, z, BRICKS);
					if (pad && !padEdge && (t + w) % 2 == 0 && t == 16) s.put(x, y, z, LIGHT);
				}
			}
			// A hard-light beacon post on each pad's far edge, for fliers to aim at.
			for (int k = 1; k <= 3; k++) s.put(sx * 18, y + k, sz * 18, k == 3 ? LAMP : PILLAR.setValue(RotatedPillarBlock.AXIS, Direction.Axis.Y));
		}
	}

	/** The crown vault on top of the spire: a lit chamber with the city's treasure, a stepped roof and a tall light. */
	private static void crown(Shape s) {
		int y0 = SPIRE_TOP + 1, h = 3;
		for (int y = y0; y <= y0 + 5; y++) {
			for (int x = -h; x <= h; x++) {
				for (int z = -h; z <= h; z++) {
					boolean edgeX = Math.abs(x) == h, edgeZ = Math.abs(z) == h;
					if (!edgeX && !edgeZ) {
						s.air(x, y, z);
						continue;
					}
					if (edgeX && edgeZ) {
						s.put(x, y, z, PILLAR);
						continue;
					}
					int along = edgeX ? z : x;
					s.put(x, y, z, Math.abs(along) <= 1 && y >= y0 + 1 && y <= y0 + 3 ? LIGHT : BRICKS);
				}
			}
		}
		s.put(0, y0, 0, Blocks.CHEST.defaultBlockState().setValue(BlockStateProperties.HORIZONTAL_FACING, Direction.SOUTH));
		s.put(-2, y0, -2, LAMP);
		s.put(2, y0, -2, LAMP);
		s.put(-2, y0, 2, LAMP);
		s.put(2, y0, 2, LAMP);
		// Stepped roof.
		int ry = y0 + 6;
		for (int x = -4; x <= 4; x++) {
			for (int z = -4; z <= 4; z++) {
				int m = Math.max(Math.abs(x), Math.abs(z));
				if (m == 4) {
					s.put(x, ry, z, Math.abs(x) == 4 && Math.abs(z) == 4 ? LAMP : SLAB.setValue(BlockStateProperties.SLAB_TYPE, SlabType.BOTTOM));
					s.put(x, ry - 1, z, stairs(outward(x, z).getOpposite(), true));
				} else {
					s.put(x, ry, z, TILES);
				}
			}
		}
		for (int step = 1; step <= 2; step++) {
			int w = 3 - step;
			for (int x = -w; x <= w; x++) {
				for (int z = -w; z <= w; z++) {
					boolean ring = Math.max(Math.abs(x), Math.abs(z)) == w;
					if (ring) s.put(x, ry + step, z, w == 0 ? PILLAR : stairs(outward(x, z).getOpposite(), false));
					else s.put(x, ry + step, z, BRICKS);
				}
			}
		}
		for (int k = 3; k <= 7; k++) s.put(0, ry + k, 0, k == 7 ? LAMP : k % 2 == 0 ? LIGHT : PILLAR);
	}

	private BlueCity() {
	}
}
