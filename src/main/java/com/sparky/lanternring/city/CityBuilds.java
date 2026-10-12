package com.sparky.lanternring.city;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RingFx;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.city.BlueCity.Piece;
import com.sparky.lanternring.city.CityData.City;
import com.sparky.lanternring.net.RingFxPayload;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.block.BedBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.loot.LootTable;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * One piece of a sky city forming. The builders' energy raises it bottom up as blue Sky Light, a
 * few blocks a tick; {@link RingTuning#CITY_SET} later each block "sets" into what it's meant to be
 * (Skystone, lamps, beds, crops...), so a hardening line climbs the piece behind the glowing one.
 * <p>
 * Progress is written into the city's saved data as it goes. The job waits (never skips) while
 * the block it's on is in an unloaded chunk or no builder is near, and is put away after a while
 * with no builders; the next {@link BlueCity#buildNext} picks it up from the same block.
 */
public final class CityBuilds {
	private static final int FLAGS = Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE;
	/** Builders further than this from the piece don't count as building it. */
	private static final double REACH = 64;
	/** Ticks a job waits with nobody building before it's put away (progress is kept). */
	private static final int IDLE_LIMIT = 200;
	public static final ResourceKey<LootTable> VAULT_LOOT = ResourceKey.create(Registries.LOOT_TABLE, LanternRing.id("chests/sky_city_vault"));

	public static final class Job {
		final ServerLevel level;
		final int cityId;
		final Piece piece;
		final List<BlockPos> order;
		final Map<BlockPos, BlockState> blocks;
		final int perTick, setDelay;
		final List<Entity> builders = new ArrayList<>();
		final Vec3 focus;
		int formed, set, age, idle;

		Job(ServerLevel level, City city, Piece piece, Map<BlockPos, BlockState> blocks, int ticks, Vec3 focus) {
			this.level = level;
			this.cityId = city.id;
			this.piece = piece;
			this.blocks = blocks;
			this.order = new ArrayList<>(blocks.keySet());
			order.sort(Comparator.comparingInt(BlockPos::getY));
			this.perTick = Math.max(1, Mth.ceil(order.size() / (double) Math.max(1, ticks)));
			this.setDelay = RingTuning.CITY_SET.ticks();
			this.focus = focus;
			// Carry on from where it was saved.
			this.formed = Math.min(city.formed, order.size());
			this.set = Math.min(city.set, formed);
			if (formed > 0) age = setDelay;
		}

		public boolean done() {
			return set >= order.size();
		}

		public Piece piece() {
			return piece;
		}

		/** The middle of the piece: where a U team faces and streams its energy. */
		public Vec3 focus() {
			return focus;
		}

		/** The block forming now (the builders' beams point at it). */
		public BlockPos current() {
			return order.isEmpty() ? BlockPos.containing(focus) : order.get(Math.min(formed, order.size() - 1));
		}

		/** How much of the piece has set, 0 to 1. */
		public float progress() {
			return order.isEmpty() ? 1f : set / (float) order.size();
		}

		/** Adds builders to the piece (a new U team taking over, or more joining). */
		public void attach(List<? extends Entity> more) {
			for (Entity e : more) {
				if (!builders.contains(e)) builders.add(e);
			}
		}

		private boolean anyBuilder() {
			builders.removeIf(e -> e.isRemoved() || e.level() != level);
			for (Entity e : builders) {
				if (e.position().distanceToSqr(focus) < REACH * REACH) return true;
			}
			return false;
		}
	}

	private static final List<Job> JOBS = new ArrayList<>();

	public static void register() {
		ServerTickEvents.END_SERVER_TICK.register(server -> tick());
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> JOBS.clear());
	}

	/** The job forming a piece of this city, if one is in memory. */
	@Nullable
	static Job find(ServerLevel level, City city) {
		for (Job j : JOBS) {
			if (j.level == level && j.cityId == city.id) return j;
		}
		return null;
	}

	static Job start(ServerLevel level, City city, Piece piece, Map<BlockPos, BlockState> blocks, int ticks, Vec3 focus) {
		Job job = new Job(level, city, piece, blocks, ticks, focus);
		JOBS.add(job);
		return job;
	}

	/** Whether the piece is still forming (false for null, finished or put away). */
	public static boolean running(@Nullable Job job) {
		return job != null && JOBS.contains(job);
	}

	/** Builds every block at once, set, with no light phase (tests). */
	static void instant(ServerLevel level, Map<BlockPos, BlockState> blocks) {
		List<BlockPos> order = new ArrayList<>(blocks.keySet());
		order.sort(Comparator.comparingInt(BlockPos::getY));
		for (BlockPos pos : order) {
			if (allowed(level, pos)) setFinal(level, pos, blocks.get(pos));
		}
	}

	private static void tick() {
		for (Iterator<Job> it = JOBS.iterator(); it.hasNext(); ) {
			Job job = it.next();
			CityData data = CityData.get(job.level);
			City city = data.byId(job.cityId);
			if (city == null) {
				it.remove();
				continue;
			}
			if (!job.anyBuilder()) {
				if (++job.idle > IDLE_LIMIT) it.remove();
				continue;
			}
			job.idle = 0;
			job.age++;
			step(job);
			beams(job);
			city.formed = job.formed;
			city.set = job.set;
			data.setDirty();
			if (job.done()) {
				city.active = -1;
				city.formed = city.set = 0;
				city.mark(job.piece, true);
				if (!job.order.isEmpty()) {
					job.level.playSound(null, BlockPos.containing(job.focus), SoundEvents.BEACON_POWER_SELECT, SoundSource.BLOCKS, 2f, 1.3f);
				}
				it.remove();
			}
		}
	}

	/** Forms and sets up to perTick blocks each, stopping at the first one whose chunk isn't loaded. */
	private static void step(Job job) {
		int end = Math.min(job.order.size(), job.formed + job.perTick);
		while (job.formed < end) {
			BlockPos pos = job.order.get(job.formed);
			if (!job.level.isLoaded(pos)) break;
			form(job, pos);
			job.formed++;
		}
		if (job.age <= job.setDelay) return;
		// Once it has all formed, setting catches up twice as fast.
		int setEnd = Math.min(job.formed, job.set + job.perTick * (job.formed >= job.order.size() ? 2 : 1));
		while (job.set < setEnd) {
			BlockPos pos = job.order.get(job.set);
			if (!job.level.isLoaded(pos)) break;
			set(job, pos);
			job.set++;
		}
	}

	/** The builders' rings stream blue construct light into the forming block. */
	private static void beams(Job job) {
		if (job.level.getGameTime() % 4 != 0) return;
		Corps before = Corps.enter(Corps.BLUE);
		try {
			Vec3 to = Vec3.atCenterOf(job.formed < job.order.size() ? job.current() : job.order.get(Math.min(job.set, job.order.size() - 1)));
			for (Entity e : job.builders) {
				RingFx.send(job.level, RingFxPayload.Kind.ALLY_SHOT, e.position().add(0, e.getBbHeight() * 0.6, 0), to);
			}
		} finally {
			Corps.restore(before);
		}
	}

	/** Never cuts through the world: only air, plants, water and the city's own blocks give way. */
	static boolean allowed(ServerLevel level, BlockPos pos) {
		BlockState current = level.getBlockState(pos);
		if (CityBlocks.isCity(current) || current.is(Blocks.FARMLAND) || current.getBlock() instanceof BedBlock) return true;
		if (current.getBlock() instanceof ChestBlock) return true;
		return !current.hasBlockEntity() && current.canBeReplaced();
	}

	private static void form(Job job, BlockPos pos) {
		ServerLevel level = job.level;
		if (!allowed(level, pos)) return;
		BlockState want = job.blocks.get(pos);
		if (want.isAir()) {
			if (!level.getBlockState(pos).isAir()) level.setBlock(pos, want, FLAGS);
			return;
		}
		// A chest that's already there keeps its contents.
		if (level.getBlockState(pos).getBlock() instanceof ChestBlock) return;
		level.setBlock(pos, CityBlocks.SKY_LIGHT.defaultBlockState(), FLAGS);
		if (level.getRandom().nextInt(12) == 0) {
			level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5,
					3, 0.3, 0.3, 0.3, 0.02);
		}
		if (level.getRandom().nextInt(50) == 0) {
			level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1f, 1.5f);
		}
	}

	private static void set(Job job, BlockPos pos) {
		ServerLevel level = job.level;
		BlockState want = job.blocks.get(pos);
		if (want.isAir() || !allowed(level, pos)) return;
		BlockState now = level.getBlockState(pos);
		// Only the light it formed sets; a block someone placed meanwhile stays.
		if (!now.is(CityBlocks.SKY_LIGHT) && !now.isAir()) return;
		setFinal(level, pos, want);
		if (!want.is(CityBlocks.SKY_LIGHT) && level.getRandom().nextInt(16) == 0) {
			level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), pos.getX() + 0.5, pos.getY() + 1.0, pos.getZ() + 0.5,
					2, 0.4, 0.1, 0.4, 0.01);
		}
		if (level.getRandom().nextInt(60) == 0) {
			level.playSound(null, pos, want.getSoundType().getPlaceSound(), SoundSource.BLOCKS, 1f, 0.8f);
		}
	}

	private static void setFinal(ServerLevel level, BlockPos pos, BlockState want) {
		if (level.getBlockState(pos).getBlock() instanceof ChestBlock && want.getBlock() instanceof ChestBlock) return;
		level.setBlock(pos, want, FLAGS);
		if (level.getBlockEntity(pos) instanceof ChestBlockEntity chest) {
			chest.setLootTable(VAULT_LOOT, level.getRandom().nextLong());
		}
	}

	private CityBuilds() {
	}
}
