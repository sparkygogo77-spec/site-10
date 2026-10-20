package com.sparky.lanternring.warren;

import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.mixin.StructurePiecesBuilderAccessor;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.LevelHeightAccessor;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceSerializationContext;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceType;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePiecesBuilder;
import net.minecraft.world.level.levelgen.structure.structures.MineshaftPieces;

/**
 * Pass v2.0114 · Warren mineshaft entrance (J's W1a7a-c KEEP, 2026-10-20: "natural mineshafts that have the
 * additional portion of ours attached to it"). An ordinary mineshaft generates as usual; near a Dread Warren
 * ({@link WarrenSites}) some of its dead ends carry on as ours: two or three more frames in old dark timber, then
 * the tunnel turns round and narrow, lined in dark stone, and drops into the Warren's first cave.
 * <p>
 * Nothing in the mine itself changes (no signs, light, mobs or webs: "It shouldnt be obvious"), and a ravine cutting
 * a mine cuts ours the same way. Webs come later and only in danger, on walls, never across the walkway.
 * <p>
 * It is a real structure piece of the mineshaft, so it generates chunk by chunk with the rest of the mine and is
 * saved with it. Its shape is worked out from the few numbers saved below, the same in every chunk.
 */
public final class WarrenEntrance extends StructurePiece {
	public static final StructurePieceType.ContextlessType TYPE = WarrenEntrance::new;

	/** The chance one dead end (near a Warren) carries ours (J: "Easier to find"); the rest stay plain dead ends. */
	static final float CHANCE = 0.6f;
	/** No more than this many in one mine. */
	static final int MAX_PER_MINE = 3;
	/** Vanilla corridor sections are 5 long, with a frame 2 blocks into each. */
	private static final int SECTION = 5;
	/** The round tunnel: steps (1 block forward each), air and lining radius, drop per step. */
	private static final int STEPS = 16;
	private static final double TUNNEL_R = 1.3, LINE_R = 2.5, DROP = 0.55, STEEP_DROP = 0.85;
	private static final int STEEP_FROM = 11;
	/** The first cave: half-length forward, half-width, half-height; floor this far under its middle. */
	private static final double CAVE_F = 7, CAVE_S = 6, CAVE_Y = 3.6, CAVE_FLOOR = 2.0, SHELL = 2.0;

	/** Entrances made since start-up, for tests (start of ours and the way it faces). */
	public static final List<BlockPos> MADE = new ArrayList<>();

	private final int sx, sy, sz, frames;
	private final long seed;

	/** Ours starting at {@code start} (the first block past the dead end, its floor level), heading {@code dir}. */
	public WarrenEntrance(BlockPos start, Direction dir, int frames, long seed) {
		super(TYPE, 0, box(start, dir, frames, seed));
		setOrientation(dir);
		this.sx = start.getX();
		this.sy = start.getY();
		this.sz = start.getZ();
		this.frames = frames;
		this.seed = seed;
	}

	public WarrenEntrance(CompoundTag tag) {
		super(TYPE, tag);
		this.sx = tag.getIntOr("SX", 0);
		this.sy = tag.getIntOr("SY", 0);
		this.sz = tag.getIntOr("SZ", 0);
		this.frames = tag.getIntOr("Frames", 2);
		this.seed = tag.getLongOr("Seed", 0L);
	}

	public static void register() {
		Registry.register(BuiltInRegistries.STRUCTURE_PIECE, LanternRing.id("warren_entrance"), TYPE);
	}

	@Override
	protected void addAdditionalSaveData(StructurePieceSerializationContext ctx, CompoundTag tag) {
		tag.putInt("SX", sx);
		tag.putInt("SY", sy);
		tag.putInt("SZ", sz);
		tag.putInt("Frames", frames);
		tag.putLong("Seed", seed);
	}

	// ---- attaching to a mine -------------------------------------------------------------------------------

	/**
	 * Called once a mineshaft's pieces are laid out and moved to their height: adds ours to some of its dead
	 * ends if the mine is near a Warren.
	 */
	public static void attach(StructurePiecesBuilder builder, long worldSeed, LevelHeightAccessor heights) {
		List<StructurePiece> pieces = ((StructurePiecesBuilderAccessor) builder).lanternring$pieces();
		List<WarrenEntrance> added = new ArrayList<>();
		for (StructurePiece p : List.copyOf(pieces)) {
			if (added.size() >= MAX_PER_MINE) break;
			if (!(p instanceof MineshaftPieces.MineShaftCorridor corridor)) continue;
			Direction dir = corridor.getOrientation();
			if (dir == null || dir.getAxis() == Direction.Axis.Y) continue;
			BlockPos start = startPast(corridor.getBoundingBox(), dir);
			if (!WarrenSites.near(worldSeed, start.getX(), start.getZ())) continue;
			RandomSource r = RandomSource.create(worldSeed ^ start.asLong() * 0x9E3779B97F4A7C15L);
			if (!WarrenSites.everywhereForTests && r.nextFloat() >= CHANCE) continue;
			if (!isDeadEnd(pieces, corridor.getBoundingBox(), dir)) continue;
			WarrenEntrance ours = new WarrenEntrance(start, dir, 2 + r.nextInt(2), r.nextLong());
			if (ours.boundingBox.minY() < heights.getMinY() + 4) continue;
			if (StructurePiece.findCollisionPiece(pieces, ours.boundingBox) != null) continue;
			pieces.add(ours);
			added.add(ours);
		}
		synchronized (MADE) {
			for (WarrenEntrance e : added) MADE.add(new BlockPos(e.sx, e.sy, e.sz));
		}
	}

	/** The first block past a corridor's far end, in the middle of its 3-wide floor. */
	public static BlockPos startPast(BoundingBox b, Direction dir) {
		return switch (dir) {
			case NORTH -> new BlockPos(b.minX() + 1, b.minY(), b.minZ() - 1);
			case SOUTH -> new BlockPos(b.minX() + 1, b.minY(), b.maxZ() + 1);
			case WEST -> new BlockPos(b.minX() - 1, b.minY(), b.minZ() + 1);
			default -> new BlockPos(b.maxX() + 1, b.minY(), b.minZ() + 1);
		};
	}

	/** True if nothing of the mine carries on past the corridor's far end (two blocks deep, a block wider). */
	private static boolean isDeadEnd(List<StructurePiece> pieces, BoundingBox b, Direction dir) {
		BoundingBox past = switch (dir) {
			case NORTH -> new BoundingBox(b.minX() - 1, b.minY(), b.minZ() - 2, b.maxX() + 1, b.maxY(), b.minZ() - 1);
			case SOUTH -> new BoundingBox(b.minX() - 1, b.minY(), b.maxZ() + 1, b.maxX() + 1, b.maxY(), b.maxZ() + 2);
			case WEST -> new BoundingBox(b.minX() - 2, b.minY(), b.minZ() - 1, b.minX() - 1, b.maxY(), b.maxZ() + 1);
			default -> new BoundingBox(b.maxX() + 1, b.minY(), b.minZ() - 1, b.maxX() + 2, b.maxY(), b.maxZ() + 1);
		};
		return StructurePiece.findCollisionPiece(pieces, past) == null;
	}

	// ---- the shape, in our own frame: t forward from the dead end, s to the right, y up from the floor --------

	/** The tunnel's middle line, step by step: {t, s, y}. Its end meets the cave. */
	private static double[][] tunnel(int frames, long seed) {
		RandomSource r = RandomSource.create(seed);
		double phase = r.nextDouble() * Mth.TWO_PI, sway = 0.4 + r.nextDouble() * 0.5;
		double[][] pts = new double[STEPS][];
		double y = 1.0;
		int t0 = frames * SECTION - 1;
		for (int i = 0; i < STEPS; i++) {
			pts[i] = new double[] {t0 + i, sway * Math.sin(phase + i * 0.45) - sway * Math.sin(phase), y};
			y -= i >= STEEP_FROM ? STEEP_DROP : DROP;
		}
		return pts;
	}

	/** The cave's middle {t, s, y}: just past the tunnel's end, its floor a block under where the tunnel comes in. */
	private static double[] cave(double[][] tunnel) {
		double[] end = tunnel[tunnel.length - 1];
		return new double[] {end[0] + CAVE_F - 1, end[1], end[2] + CAVE_FLOOR - 1};
	}

	private static BoundingBox box(BlockPos start, Direction dir, int frames, long seed) {
		double[][] tunnel = tunnel(frames, seed);
		double[] c = cave(tunnel);
		int tMax = Mth.ceil(c[0] + CAVE_F + SHELL + 1);
		int sMax = Mth.ceil(CAVE_S + SHELL + 1);
		int yMin = Mth.floor(c[2] - CAVE_FLOOR - SHELL - 1), yMax = 4;
		Direction right = dir.getClockWise();
		BlockPos a = start.offset(right.getStepX() * -sMax, yMin, right.getStepZ() * -sMax);
		BlockPos b = start.offset(dir.getStepX() * tMax + right.getStepX() * sMax, yMax,
				dir.getStepZ() * tMax + right.getStepZ() * sMax);
		return BoundingBox.fromCorners(a, b);
	}

	// ---- placing ------------------------------------------------------------------------------------------

	private static final BlockState PLANKS = Blocks.DARK_OAK_PLANKS.defaultBlockState();
	private static final BlockState FENCE = Blocks.DARK_OAK_FENCE.defaultBlockState();

	@Override
	public void postProcess(WorldGenLevel level, StructureManager structures, ChunkGenerator generator, RandomSource random,
			BoundingBox chunkBox, ChunkPos chunkPos, BlockPos pivot) {
		Direction f = getOrientation();
		Direction rt = f.getClockWise();
		int fx = f.getStepX(), fz = f.getStepZ(), rx = rt.getStepX(), rz = rt.getStepZ();
		double[][] tunnel = tunnel(frames, seed);
		double[] cave = cave(tunnel);
		int timber = frames * SECTION;
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		int x0 = Math.max(boundingBox.minX(), chunkBox.minX()), x1 = Math.min(boundingBox.maxX(), chunkBox.maxX());
		int y0 = Math.max(boundingBox.minY(), chunkBox.minY()), y1 = Math.min(boundingBox.maxY(), chunkBox.maxY());
		int z0 = Math.max(boundingBox.minZ(), chunkBox.minZ()), z1 = Math.min(boundingBox.maxZ(), chunkBox.maxZ());
		for (int x = x0; x <= x1; x++) {
			for (int z = z0; z <= z1; z++) {
				int t = (x - sx) * fx + (z - sz) * fz, s = (x - sx) * rx + (z - sz) * rz;
				for (int y = y0; y <= y1; y++) {
					int ly = y - sy;
					pos.set(x, y, z);
					BlockState here = level.getBlockState(pos);
					if (here.is(BlockTags.FEATURES_CANNOT_REPLACE) || !here.getFluidState().isEmpty()) continue;
					BlockState want = shape(t, s, ly, timber, tunnel, cave, x, y, z);
					if (want == null) continue;
					if (want.isAir()) {
						if (here.isAir()) continue;
						// Never open into water or lava: seal it with the lining instead.
						if (nextToFluid(level, pos)) want = lining(x, y, z);
					} else if (want == PLANKS && ly == -1) {
						if (!here.isAir()) continue;   // the floor plank only bridges a gap, as vanilla's do
					} else if (want != FENCE && want != PLANKS && !isRock(here)) {
						continue;   // the lining only replaces natural stone, never air or anything built
					}
					level.setBlock(pos, want, 2);
				}
			}
		}
	}

	/** What goes at (t, s, y) of ours, or null to leave it. */
	private BlockState shape(int t, int s, int y, int timber, double[][] tunnel, double[] cave, int x, int wy, int z) {
		if (t < 0) return null;
		// The old timber stretch: a vanilla corridor's 3x3 hole, with a frame 2 blocks into each 5-block section.
		if (t < timber && Math.abs(s) <= 1 && y >= -1 && y <= 2) {
			if (y == -1) return PLANKS;
			boolean frame = t % SECTION == 2;
			if (!frame) return Blocks.CAVE_AIR.defaultBlockState();
			long h = hash(x, wy, z);
			if (y == 2) return (h & 7) == 0 ? Blocks.CAVE_AIR.defaultBlockState() : PLANKS;   // the odd plank gone
			// Posts on both sides; the last frame has lost one of them.
			if (s != 0 && !(t / SECTION == frames - 1 && s == ((seed & 1) == 0 ? 1 : -1))) return FENCE;
			return Blocks.CAVE_AIR.defaultBlockState();
		}
		double best = Double.MAX_VALUE;
		for (double[] p : tunnel) {
			double dt = t - p[0], ds = s - p[1], dy = y - p[2];
			best = Math.min(best, dt * dt + ds * ds + dy * dy);
		}
		double wob = 1 + 0.12 * Math.sin(x * 0.71 + seed % 7) * Math.cos(z * 0.63 + wy * 0.9);
		boolean inCave = false, caveShell = false;
		double ct = (t - cave[0]) / CAVE_F, cs = (s - cave[1]) / CAVE_S, cy = (y - cave[2]) / CAVE_Y;
		double q = ct * ct + cs * cs + cy * cy;
		double floor = cave[2] - CAVE_FLOOR;
		if (q < wob) {
			if (y >= floor) inCave = true;
			else caveShell = y >= floor - SHELL;
		} else {
			double ot = (t - cave[0]) / (CAVE_F + SHELL), os = (s - cave[1]) / (CAVE_S + SHELL), oy = (y - cave[2]) / (CAVE_Y + SHELL);
			caveShell = ot * ot + os * os + oy * oy < wob;
		}
		if (inCave || (t >= timber - 1 && best < TUNNEL_R * TUNNEL_R * wob)) return Blocks.CAVE_AIR.defaultBlockState();
		if (caveShell || (t >= timber - 1 && best < LINE_R * LINE_R * wob)) return lining(x, wy, z);
		return null;
	}

	/** The quiet dread-stone lining from natural dark blocks; a rare gilded fleck is the only gold. */
	private BlockState lining(int x, int y, int z) {
		int h = (int) ((hash(x, y, z) >>> 8) % 100);
		if (h < 38) return Blocks.COBBLED_DEEPSLATE.defaultBlockState();
		if (h < 66) return Blocks.DEEPSLATE.defaultBlockState();
		if (h < 88) return Blocks.BLACKSTONE.defaultBlockState();
		if (h < 99) return Blocks.TUFF.defaultBlockState();
		return Blocks.GILDED_BLACKSTONE.defaultBlockState();
	}

	private static boolean isRock(BlockState s) {
		return s.is(BlockTags.BASE_STONE_OVERWORLD) || s.is(BlockTags.DIRT) || s.is(Blocks.GRAVEL)
				|| BuiltInRegistries.BLOCK.getKey(s.getBlock()).getPath().endsWith("_ore");
	}

	private static boolean nextToFluid(WorldGenLevel level, BlockPos pos) {
		for (Direction d : Direction.values()) {
			if (!level.getFluidState(pos.relative(d)).isEmpty()) return true;
		}
		return false;
	}

	private long hash(int x, int y, int z) {
		long h = seed ^ (x * 3129871L) ^ (z * 116129781L) ^ (long) y * 0x2545F4914F6CDD1DL;
		h = (h ^ (h >>> 33)) * 0xff51afd7ed558ccdL;
		return (h ^ (h >>> 29)) & Long.MAX_VALUE;
	}
}
