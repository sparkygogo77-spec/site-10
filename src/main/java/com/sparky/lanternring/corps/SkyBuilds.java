package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingFx;
import com.sparky.lanternring.designs.Blueprint;
import com.sparky.lanternring.designs.BuildDesigns;
import com.sparky.lanternring.net.RingFxPayload;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * What the corps villagers and the Red sky raiders build: floating islands, village houses and
 * watchtowers, raised a few blocks a tick while the builder points its ring at them. Jobs aren't
 * saved; a builder that finds its job gone after a restart simply starts that step again.
 */
public final class SkyBuilds {
	private static final int FLAGS = Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE;

	/** The houses a corps village is made of: plains village houses no wider than an island quarter. */
	static final List<String> HOUSES = List.of("plains_small_house_1", "plains_small_house_2", "plains_small_house_3",
			"plains_small_house_4", "plains_small_house_5", "plains_small_house_6", "plains_small_house_7", "plains_small_house_8",
			"plains_medium_house_1", "plains_medium_house_2", "plains_butcher_shop_1", "plains_tool_smith_1", "plains_library_1",
			"plains_fletcher_house_1", "plains_cartographer_1", "plains_armorer_house_1", "plains_shepherds_house_1",
			"plains_temple_3", "plains_weaponsmith_1", "plains_masons_house_1", "plains_tannery_1", "plains_big_house_1");

	/** One build forming a few blocks a tick. */
	public static final class Job {
		final ServerLevel level;
		final List<BlockPos> order;
		final Map<BlockPos, BlockState> blocks;
		final int perTick;
		final Corps corps;
		/** Whether it may knock out terrain in the way (a house on the ground), or only fill air (an island). */
		final boolean force;
		final @Nullable Entity builder;
		/** Helpers pouring their own light into the build beside the builder (the Blue Lantern's U of three). */
		final List<Entity> crew = new ArrayList<>();
		/** The middle of the build's footprint at its base, and how far it reaches from there. */
		public final Vec3 center;
		public final double radius;
		int index;

		Job(ServerLevel level, Map<BlockPos, BlockState> blocks, int ticks, Corps corps, boolean force, @Nullable Entity builder) {
			this.level = level;
			this.blocks = blocks;
			this.order = new ArrayList<>(blocks.keySet());
			// Bottom up, so floors are there before walls and doors.
			order.sort(Comparator.comparingInt(BlockPos::getY));
			this.perTick = Math.max(1, Mth.ceil(order.size() / (double) Math.max(1, ticks)));
			this.corps = corps;
			this.force = force;
			this.builder = builder;
			int x0 = Integer.MAX_VALUE, z0 = Integer.MAX_VALUE, y0 = Integer.MAX_VALUE, x1 = Integer.MIN_VALUE, z1 = Integer.MIN_VALUE;
			for (BlockPos p : order) {
				x0 = Math.min(x0, p.getX());
				x1 = Math.max(x1, p.getX());
				z0 = Math.min(z0, p.getZ());
				z1 = Math.max(z1, p.getZ());
				y0 = Math.min(y0, p.getY());
			}
			this.center = order.isEmpty() ? Vec3.ZERO : new Vec3((x0 + x1 + 1) / 2.0, y0, (z0 + z1 + 1) / 2.0);
			this.radius = order.isEmpty() ? 0 : Math.max(x1 - x0 + 1, z1 - z0 + 1) / 2.0;
		}

		/** Others who shoot light into this build alongside the builder. */
		public void crew(List<? extends Entity> helpers) {
			crew.clear();
			crew.addAll(helpers);
		}

		public boolean done() {
			return index >= order.size();
		}

		/** The block being raised now (the builder looks at it). */
		public BlockPos current() {
			return order.isEmpty() ? BlockPos.ZERO : order.get(Math.min(index, order.size() - 1));
		}
	}

	private static final List<Job> JOBS = new ArrayList<>();

	public static void register() {
		ServerTickEvents.END_SERVER_TICK.register(server -> tick());
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> JOBS.clear());
	}

	public static Job start(ServerLevel level, Map<BlockPos, BlockState> blocks, int ticks, Corps corps, boolean force, @Nullable Entity builder) {
		Job job = new Job(level, blocks, ticks, corps, force, builder);
		JOBS.add(job);
		return job;
	}

	/** Whether the job is still forming (false for null, finished or forgotten after a restart). */
	public static boolean running(@Nullable Job job) {
		return job != null && JOBS.contains(job);
	}

	private static void tick() {
		for (Iterator<Job> it = JOBS.iterator(); it.hasNext(); ) {
			Job job = it.next();
			if (job.builder != null && job.builder.isRemoved()) {
				it.remove();
				continue;
			}
			int end = Math.min(job.order.size(), job.index + job.perTick);
			for (; job.index < end; job.index++) form(job, job.order.get(job.index));
			if (job.builder != null && !job.done()) {
				// The builder's ring shoots the light that becomes the blocks; its crew take turns between its shots.
				long t = job.level.getGameTime();
				if (t % 6 == 0) shoot(job, job.builder, job.current());
				for (int i = 0; i < job.crew.size(); i++) {
					Entity e = job.crew.get(i);
					if (e.isAlive() && t % 6 == 2 * (i + 1)) shoot(job, e, job.order.get(Math.max(0, job.index - 1 - i * job.perTick)));
				}
			}
			if (job.done()) {
				finish(job);
				if (!job.order.isEmpty()) {
					job.level.playSound(null, job.order.getLast(), SoundEvents.PLAYER_LEVELUP, SoundSource.NEUTRAL, 1f, 1.2f);
				}
				it.remove();
			}
		}
	}

	private static void shoot(Job job, Entity from, BlockPos at) {
		Corps before = Corps.enter(job.corps);
		try {
			RingFx.send(job.level, RingFxPayload.Kind.ALLY_SHOT, from.position().add(0, from.getBbHeight() * 0.6, 0), Vec3.atCenterOf(at));
		} finally {
			Corps.restore(before);
		}
	}

	private static void form(Job job, BlockPos pos) {
		ServerLevel level = job.level;
		if (!level.isLoaded(pos)) return;
		BlockState want = job.blocks.get(pos);
		BlockState current = level.getBlockState(pos);
		if (current.hasBlockEntity() || current.getDestroySpeed(level, pos) < 0) return;
		if (!job.force && !current.canBeReplaced()) return;
		if (want.isAir() && current.isAir()) return;
		level.setBlock(pos, want, FLAGS);
		if (!want.isAir() && level.getRandom().nextInt(10) == 0) {
			level.sendParticles(ModParticles.of(ModParticles.MOTE, job.corps), pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5,
					3, 0.3, 0.3, 0.3, 0.02);
		}
		if (level.getRandom().nextInt(40) == 0) {
			level.playSound(null, pos, want.getSoundType().getPlaceSound(), SoundSource.BLOCKS, 1f, 0.9f);
		}
	}

	/** Once it's all there: let fences, panes and stairs join up with their neighbours. */
	private static void finish(Job job) {
		for (BlockPos pos : job.order) {
			if (!job.level.isLoaded(pos)) continue;
			BlockState s = job.level.getBlockState(pos);
			if (s.isAir()) continue;
			BlockState joined = Block.updateFromNeighbourShapes(s, job.level, pos);
			if (joined != s && !joined.isAir()) job.level.setBlock(pos, joined, FLAGS);
		}
	}

	// ---- floating islands -----------------------------------------------------------------------

	/** The look of a corps' islands. */
	private record IslandLook(BlockState top, BlockState soil, BlockState stone, BlockState accent, BlockState rim, BlockState light) {
	}

	private static IslandLook look(Corps corps) {
		if (corps == Corps.RED) {
			return new IslandLook(Blocks.CRIMSON_NYLIUM.defaultBlockState(), Blocks.NETHERRACK.defaultBlockState(),
					Blocks.BLACKSTONE.defaultBlockState(), Blocks.MAGMA_BLOCK.defaultBlockState(),
					Blocks.STAINED_GLASS_PANE.red().defaultBlockState(), Blocks.SHROOMLIGHT.defaultBlockState());
		}
		BlockState rim = switch (corps.getSerializedName()) {
			case "blue" -> Blocks.STAINED_GLASS_PANE.lightBlue().defaultBlockState();
			case "yellow" -> Blocks.STAINED_GLASS_PANE.yellow().defaultBlockState();
			case "violet" -> Blocks.STAINED_GLASS_PANE.magenta().defaultBlockState();
			case "orange" -> Blocks.STAINED_GLASS_PANE.orange().defaultBlockState();
			default -> Blocks.STAINED_GLASS_PANE.lime().defaultBlockState();
		};
		return new IslandLook(Blocks.GRASS_BLOCK.defaultBlockState(), Blocks.DIRT.defaultBlockState(), Blocks.STONE.defaultBlockState(),
				corps == Corps.GREEN ? Blocks.EMERALD_ORE.defaultBlockState() : Blocks.AMETHYST_BLOCK.defaultBlockState(), rim,
				Blocks.SEA_LANTERN.defaultBlockState());
	}

	/**
	 * A floating island whose grass top is at {@code top}: a rough disc of radius r, soil under the
	 * grass, then rock tapering to a point below, a glass rail round the edge so villagers don't
	 * walk off, and lights set into the rim.
	 */
	public static Map<BlockPos, BlockState> island(BlockPos top, int r, Corps corps, RandomSource rng, boolean lantern) {
		IslandLook look = look(corps);
		Map<BlockPos, BlockState> out = new LinkedHashMap<>();
		double wobbleA = rng.nextDouble() * Math.PI * 2, wobbleB = rng.nextDouble() * Math.PI * 2;
		for (int dx = -r - 1; dx <= r + 1; dx++) {
			for (int dz = -r - 1; dz <= r + 1; dz++) {
				double a = Math.atan2(dz, dx);
				double edge = r + Math.sin(a * 3 + wobbleA) * 0.8 + Math.sin(a * 5 + wobbleB) * 0.5;
				double d = Math.sqrt(dx * dx + dz * dz);
				if (d > edge) continue;
				BlockPos col = top.offset(dx, 0, dz);
				boolean rim = d > edge - 1;
				boolean lamp = rim && Math.abs(Math.sin(a * 4)) < 0.12;
				out.put(col, lamp ? look.light : look.top);
				if (rim && !lamp) out.put(col.above(), look.rim);
				out.put(col.below(), look.soil);
				out.put(col.below(2), look.soil);
				// Deepest in the middle, a point hanging under the island.
				int depth = 2 + (int) ((edge - d) * 0.8) + rng.nextInt(2);
				for (int y = 3; y <= depth; y++) {
					out.put(col.below(y), rng.nextInt(18) == 0 ? look.accent : look.stone);
				}
			}
		}
		if (lantern) {
			out.put(top.above(), ModRegistry.POWER_BATTERY.defaultBlockState().setValue(Corps.PROPERTY, corps));
		}
		return out;
	}

	/** How high over the ground round {@code at} an island floats: well clear of hills and trees. */
	public static BlockPos skySpot(ServerLevel level, BlockPos at, int r, int above) {
		int max = at.getY();
		for (int dx = -r; dx <= r; dx += 3) {
			for (int dz = -r; dz <= r; dz += 3) {
				max = Math.max(max, level.getHeight(Heightmap.Types.MOTION_BLOCKING, at.getX() + dx, at.getZ() + dz));
			}
		}
		int y = Math.min(max + above, level.getMaxY() - 24);
		return new BlockPos(at.getX(), y, at.getZ());
	}

	// ---- houses ---------------------------------------------------------------------------------

	@Nullable
	public static Blueprint structure(ServerLevel level, String id) {
		StructureTemplate t = level.getServer().getStructureTemplateManager().get(Identifier.parse(id)).orElse(null);
		return t == null ? null : BuildDesigns.fromStructure(t);
	}

	@Nullable
	public static Blueprint house(ServerLevel level, RandomSource rng, int maxSide) {
		for (int tries = 0; tries < 8; tries++) {
			Blueprint b = structure(level, "minecraft:village/plains/houses/" + HOUSES.get(rng.nextInt(HOUSES.size())));
			if (b != null && Math.max(b.w, b.d) <= maxSide) return b;
		}
		return null;
	}

	/** Which way to turn a build so its front (+z, the door) faces {@code toward}. */
	public static Rotation facing(Direction toward) {
		return switch (toward) {
			case NORTH -> Rotation.CLOCKWISE_180;
			case WEST -> Rotation.CLOCKWISE_90;
			case EAST -> Rotation.COUNTERCLOCKWISE_90;
			default -> Rotation.NONE;
		};
	}

	public static int footW(Blueprint b, Rotation rot) {
		return rot == Rotation.CLOCKWISE_90 || rot == Rotation.COUNTERCLOCKWISE_90 ? b.d : b.w;
	}

	public static int footD(Blueprint b, Rotation rot) {
		return rot == Rotation.CLOCKWISE_90 || rot == Rotation.COUNTERCLOCKWISE_90 ? b.w : b.d;
	}

	/** The blueprint's blocks in the world with its low corner at (x, groundY, z), turned by rot. */
	public static Map<BlockPos, BlockState> place(Blueprint b, int x, int groundY, int z, Rotation rot) {
		Map<BlockPos, BlockState> out = new LinkedHashMap<>();
		for (Map.Entry<Long, BlockState> e : b.blocks.entrySet()) {
			int lx = BlockPos.getX(e.getKey()), ly = BlockPos.getY(e.getKey()), lz = BlockPos.getZ(e.getKey());
			if (ly == 0 && e.getValue().isAir()) continue;
			int rx, rz;
			switch (rot) {
				case CLOCKWISE_90 -> {
					rx = b.d - 1 - lz;
					rz = lx;
				}
				case CLOCKWISE_180 -> {
					rx = b.w - 1 - lx;
					rz = b.d - 1 - lz;
				}
				case COUNTERCLOCKWISE_90 -> {
					rx = lz;
					rz = b.w - 1 - lx;
				}
				default -> {
					rx = lx;
					rz = lz;
				}
			}
			out.put(new BlockPos(x + rx, groundY + ly, z + rz), e.getValue().rotate(rot));
		}
		return out;
	}

	/**
	 * A flat-enough patch of natural ground for a w by d house somewhere 7 to 24 blocks from home,
	 * as its low corner at ground level (the top block), or null if none turned up.
	 */
	@Nullable
	public static BlockPos groundSpot(ServerLevel level, BlockPos home, int w, int d, RandomSource rng) {
		for (int tries = 0; tries < 30; tries++) {
			double a = rng.nextDouble() * Math.PI * 2;
			double dist = 7 + rng.nextDouble() * 17 + Math.max(w, d) * 0.5;
			int x = home.getX() + (int) Math.round(Math.cos(a) * dist) - w / 2;
			int z = home.getZ() + (int) Math.round(Math.sin(a) * dist) - d / 2;
			int lo = Integer.MAX_VALUE, hi = Integer.MIN_VALUE;
			boolean ok = true;
			for (int dx = 0; dx < w && ok; dx++) {
				for (int dz = 0; dz < d && ok; dz++) {
					int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x + dx, z + dz) - 1;
					BlockPos p = new BlockPos(x + dx, y, z + dz);
					BlockState s = level.getBlockState(p);
					if (!natural(s) || !level.getFluidState(p.above()).isEmpty()) ok = false;
					lo = Math.min(lo, y);
					hi = Math.max(hi, y);
				}
			}
			if (ok && hi - lo <= 2) return new BlockPos(x, (lo + hi + 1) / 2, z);
		}
		return null;
	}

	private static boolean natural(BlockState s) {
		return s.is(BlockTags.DIRT) || s.is(BlockTags.SAND) || s.is(BlockTags.BASE_STONE_OVERWORLD) || s.is(Blocks.GRAVEL)
				|| s.is(Blocks.SNOW_BLOCK) || s.is(Blocks.SNOW) || s.is(Blocks.DIRT_PATH);
	}

	/** A house on the ground: the ground under it filled in, and the air over it cleared. */
	public static Map<BlockPos, BlockState> groundHouse(ServerLevel level, Blueprint b, BlockPos corner, Rotation rot) {
		Map<BlockPos, BlockState> out = new LinkedHashMap<>();
		int w = footW(b, rot), d = footD(b, rot);
		BlockState fill = Blocks.DIRT.defaultBlockState();
		for (int dx = 0; dx < w; dx++) {
			for (int dz = 0; dz < d; dz++) {
				for (int y = 1; y <= 4; y++) {
					BlockPos p = corner.offset(dx, -y, dz);
					if (level.getBlockState(p).canBeReplaced()) out.put(p, fill);
				}
				for (int y = 1; y <= b.h + 2; y++) out.put(corner.offset(dx, y, dz), Blocks.AIR.defaultBlockState());
			}
		}
		out.putAll(place(b, corner.getX(), corner.getY(), corner.getZ(), rot));
		return out;
	}

	private SkyBuilds() {
	}
}
