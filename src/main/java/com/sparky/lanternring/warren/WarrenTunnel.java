package com.sparky.lanternring.warren;

import com.sparky.lanternring.LanternRing;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceSerializationContext;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePieceType;

/**
 * The narrow way on from a Warren entrance's first cave to the lair: a round tunnel, lined in dread stone, winding
 * from the cave to the lair's rim. One piece per stretch of {@link #STRETCH} steps (so each has a small box); all
 * stretches of one tunnel share its ends and wobble, so they join up.
 */
public final class WarrenTunnel extends StructurePiece {
	public static final StructurePieceType.ContextlessType TYPE = WarrenTunnel::new;
	static final int STRETCH = 20;
	private static final double R = 1.7, LINE = 2.9, SWAY = 5;

	private final int ax, ay, az, bx, by, bz, from, to;
	private final long seed;

	WarrenTunnel(BlockPos a, BlockPos b, long seed, int from, int to) {
		super(TYPE, 0, box(a, b, seed, from, to));
		this.ax = a.getX();
		this.ay = a.getY();
		this.az = a.getZ();
		this.bx = b.getX();
		this.by = b.getY();
		this.bz = b.getZ();
		this.seed = seed;
		this.from = from;
		this.to = to;
	}

	public WarrenTunnel(CompoundTag tag) {
		super(TYPE, tag);
		ax = tag.getIntOr("AX", 0);
		ay = tag.getIntOr("AY", 0);
		az = tag.getIntOr("AZ", 0);
		bx = tag.getIntOr("BX", 0);
		by = tag.getIntOr("BY", 0);
		bz = tag.getIntOr("BZ", 0);
		from = tag.getIntOr("From", 0);
		to = tag.getIntOr("To", 0);
		seed = tag.getLongOr("Seed", 0L);
	}

	public static void register() {
		Registry.register(BuiltInRegistries.STRUCTURE_PIECE, LanternRing.id("warren_tunnel"), TYPE);
	}

	@Override
	protected void addAdditionalSaveData(StructurePieceSerializationContext ctx, CompoundTag tag) {
		tag.putInt("AX", ax);
		tag.putInt("AY", ay);
		tag.putInt("AZ", az);
		tag.putInt("BX", bx);
		tag.putInt("BY", by);
		tag.putInt("BZ", bz);
		tag.putInt("From", from);
		tag.putInt("To", to);
		tag.putLong("Seed", seed);
	}

	/** The pieces of one whole tunnel from {@code a} to {@code b}. */
	static java.util.List<WarrenTunnel> between(BlockPos a, BlockPos b, long seed) {
		int n = steps(a, b);
		java.util.List<WarrenTunnel> out = new java.util.ArrayList<>();
		for (int i = 0; i < n; i += STRETCH) out.add(new WarrenTunnel(a, b, seed, i, Math.min(n, i + STRETCH + 1)));
		return out;
	}

	private static int steps(BlockPos a, BlockPos b) {
		return Math.max(1, Mth.ceil(Math.sqrt(a.distSqr(b))));
	}

	/** Step {@code i} of {@code n} along the tunnel: a straight line bent by two slow sways, still at both ends. */
	private static double[] point(BlockPos a, BlockPos b, long seed, int i, int n) {
		RandomSource r = RandomSource.create(seed);
		double p1 = r.nextDouble() * Mth.TWO_PI, p2 = r.nextDouble() * Mth.TWO_PI;
		double t = i / (double) n;
		double dx = b.getX() - a.getX(), dz = b.getZ() - a.getZ(), len = Math.max(1, Math.hypot(dx, dz));
		double px = -dz / len, pz = dx / len;
		double env = Math.sin(Math.PI * t);
		double side = SWAY * env * Math.sin(p1 + t * 9), up = 1.5 * env * Math.sin(p2 + t * 7);
		return new double[] {a.getX() + dx * t + px * side + 0.5, a.getY() + (b.getY() - a.getY()) * t + up + 1,
				a.getZ() + dz * t + pz * side + 0.5};
	}

	private static BoundingBox box(BlockPos a, BlockPos b, long seed, int from, int to) {
		int n = steps(a, b);
		double lx = Double.MAX_VALUE, ly = lx, lz = lx, hx = -lx, hy = hx, hz = hx;
		for (int i = from; i <= to && i <= n; i++) {
			double[] p = point(a, b, seed, i, n);
			lx = Math.min(lx, p[0]);
			ly = Math.min(ly, p[1]);
			lz = Math.min(lz, p[2]);
			hx = Math.max(hx, p[0]);
			hy = Math.max(hy, p[1]);
			hz = Math.max(hz, p[2]);
		}
		int g = Mth.ceil(LINE) + 1;
		return new BoundingBox(Mth.floor(lx) - g, Mth.floor(ly) - g, Mth.floor(lz) - g, Mth.ceil(hx) + g, Mth.ceil(hy) + g, Mth.ceil(hz) + g);
	}

	@Override
	public void postProcess(WorldGenLevel level, StructureManager structures, ChunkGenerator generator, RandomSource random,
			BoundingBox chunkBox, ChunkPos chunkPos, BlockPos pivot) {
		BlockPos a = new BlockPos(ax, ay, az), b = new BlockPos(bx, by, bz);
		int n = steps(a, b);
		double[][] pts = new double[to - from + 1][];
		for (int i = from; i <= to; i++) pts[i - from] = point(a, b, seed, Math.min(i, n), n);
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		int x0 = Math.max(boundingBox.minX(), chunkBox.minX()), x1 = Math.min(boundingBox.maxX(), chunkBox.maxX());
		int y0 = Math.max(boundingBox.minY(), chunkBox.minY()), y1 = Math.min(boundingBox.maxY(), chunkBox.maxY());
		int z0 = Math.max(boundingBox.minZ(), chunkBox.minZ()), z1 = Math.min(boundingBox.maxZ(), chunkBox.maxZ());
		for (int x = x0; x <= x1; x++) {
			for (int z = z0; z <= z1; z++) {
				for (int y = y0; y <= y1; y++) {
					double best = Double.MAX_VALUE;
					for (double[] p : pts) {
						double dx = x + 0.5 - p[0], dy = y + 0.5 - p[1], dz = z + 0.5 - p[2];
						best = Math.min(best, dx * dx + dy * dy + dz * dz);
					}
					if (best >= LINE * LINE) continue;
					pos.set(x, y, z);
					BlockState here = level.getBlockState(pos);
					if (here.is(BlockTags.FEATURES_CANNOT_REPLACE) || !here.getFluidState().isEmpty()) continue;
					if (best < R * R) {
						if (here.isAir()) continue;
						boolean wet = false;
						for (Direction d : Direction.values()) wet |= !level.getFluidState(pos.relative(d)).isEmpty();
						level.setBlock(pos, wet ? lining(x, y, z) : Blocks.CAVE_AIR.defaultBlockState(), 2);
					} else if (WarrenLair.isRock(here)) {
						level.setBlock(pos, lining(x, y, z), 2);
					}
				}
			}
		}
	}

	private BlockState lining(int x, int y, int z) {
		long h = seed ^ (x * 3129871L) ^ (z * 116129781L) ^ (long) y * 0x2545F4914F6CDD1DL;
		h = (h ^ (h >>> 33)) * 0xff51afd7ed558ccdL;
		int k = (int) (((h ^ (h >>> 29)) & Long.MAX_VALUE) % 100);
		if (k < 38) return Blocks.COBBLED_DEEPSLATE.defaultBlockState();
		if (k < 66) return Blocks.DEEPSLATE.defaultBlockState();
		if (k < 88) return Blocks.BLACKSTONE.defaultBlockState();
		if (k < 99) return Blocks.TUFF.defaultBlockState();
		return Blocks.GILDED_BLACKSTONE.defaultBlockState();
	}
}
