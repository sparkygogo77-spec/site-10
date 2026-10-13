package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.block.LightConstructBlock;
import com.sparky.lanternring.mixin.FallingBlockAccessor;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.Container;
import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.ChestBlock;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The Blue squad levels its rescue spot, slowly, once everything is quiet (J, 2026-10-13: 5b,
 * 24-26). It never breaks a block: a patch of ground above the spot's floor (earth, stone, sand,
 * trees) rattles and shakes, then a hard-light platform rises from below and lifts the patch out
 * whole. Earthy stuff (dirt, sand, gravel, leaves) is flung away over the walls, where it lands
 * as blocks again; stone, logs and the rest float over to a chest it sets by the lantern. Buildings
 * are left alone: any column with something built in it is skipped.
 */
final class BlueClearing {
	/** Quiet ticks before it starts, how far round the spot it levels, and how tall it looks. */
	private static final int START_AFTER = 200, RADIUS = 10, TALL = 14;
	/** Ticks of rattling, of lifting (and blocks risen), of carrying away, and between patches. */
	private static final int SHAKE = 30, LIFT = 24, AWAY = 40, REST = 20;
	private static final double RISE = 3;

	private enum Stage {
		SHAKE, LIFT, AWAY
	}

	private static final class Lift {
		final List<BlockPos> blocks;
		final BlockPos middle;
		Stage stage = Stage.SHAKE;
		int ticks;
		final List<FallingBlockEntity> load = new ArrayList<>(), platform = new ArrayList<>();

		Lift(List<BlockPos> blocks, BlockPos middle) {
			this.blocks = blocks;
			this.middle = middle;
		}
	}

	private static final class Job {
		@Nullable
		Lift lift;
		long restUntil;
		boolean done;
	}

	private static final Map<BlockPos, Job> JOBS = new HashMap<>();

	private BlueClearing() {
	}

	static void register() {
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> JOBS.clear());
	}

	/** Every tick of a quiet rescue spot. */
	static void tick(ServerLevel level, BlockPos lantern, BlockPos centre, long quietFor) {
		if (quietFor < START_AFTER) return;
		Job job = JOBS.computeIfAbsent(lantern, k -> new Job());
		long now = level.getGameTime();
		if (job.lift == null) {
			if (job.done && now % 200 != 0) return;
			if (now < job.restUntil) return;
			List<BlockPos> patch = nextPatch(level, lantern, centre);
			job.done = patch.isEmpty();
			if (job.done) return;
			job.lift = new Lift(patch, patch.getFirst());
		}
		if (step(level, lantern, centre, job.lift)) {
			job.lift = null;
			job.restUntil = now + REST;
		}
	}

	// ---- picking ground to lift ------------------------------------------------------------------

	private static List<BlockPos> nextPatch(ServerLevel level, BlockPos lantern, BlockPos centre) {
		int floor = centre.getY();
		List<BlockPos> columns = new ArrayList<>();
		for (int dx = -RADIUS; dx <= RADIUS; dx++) {
			for (int dz = -RADIUS; dz <= RADIUS; dz++) {
				if (dx * dx + dz * dz > RADIUS * RADIUS) continue;
				columns.add(new BlockPos(centre.getX() + dx, floor, centre.getZ() + dz));
			}
		}
		columns.sort(Comparator.comparingDouble(c -> c.distSqr(centre)));
		for (BlockPos c : columns) {
			if (!needsLift(level, lantern, c)) continue;
			List<BlockPos> blocks = new ArrayList<>();
			for (int dx = -1; dx <= 1; dx++) {
				for (int dz = -1; dz <= 1; dz++) {
					BlockPos col = c.offset(dx, 0, dz);
					if (col.distSqr(centre) > RADIUS * RADIUS || !needsLift(level, lantern, col)) continue;
					for (int y = 0; y < TALL; y++) {
						BlockPos p = col.above(y);
						if (natural(level.getBlockState(p))) blocks.add(p);
					}
				}
			}
			if (!blocks.isEmpty()) {
				// The first entry is the patch's middle (on the floor), the rest are the blocks.
				blocks.addFirst(c);
				return blocks;
			}
		}
		return List.of();
	}

	/** A column with natural ground above the floor and nothing built in it. */
	private static boolean needsLift(ServerLevel level, BlockPos lantern, BlockPos col) {
		if (Math.abs(col.getX() - lantern.getX()) <= 2 && Math.abs(col.getZ() - lantern.getZ()) <= 2) return false;
		boolean any = false;
		for (int y = 0; y < TALL; y++) {
			BlockState s = level.getBlockState(col.above(y));
			if (s.isAir() || s.canBeReplaced()) continue;
			if (!natural(s)) return false;
			any = true;
		}
		return any;
	}

	static boolean natural(BlockState s) {
		return s.is(BlockTags.DIRT) || s.is(BlockTags.SAND) || s.is(BlockTags.LOGS) || s.is(BlockTags.LEAVES) || s.is(BlockTags.BASE_STONE_OVERWORLD)
				|| s.is(BlockTags.SNOW) || s.is(Blocks.GRAVEL) || s.is(Blocks.CLAY) || s.is(BlockTags.TERRACOTTA) || s.is(Blocks.SANDSTONE);
	}

	private static boolean earthy(BlockState s) {
		return s.is(BlockTags.DIRT) || s.is(BlockTags.SAND) || s.is(BlockTags.LEAVES) || s.is(BlockTags.SNOW) || s.is(Blocks.GRAVEL) || s.is(Blocks.CLAY);
	}

	// ---- one lift ------------------------------------------------------------------------------

	/** Advances a lift a tick; true once it's over. */
	private static boolean step(ServerLevel level, BlockPos lantern, BlockPos centre, Lift lift) {
		lift.ticks++;
		BlockPos mid = lift.blocks.getFirst();
		Vec3 m = Vec3.atBottomCenterOf(mid);
		switch (lift.stage) {
			case SHAKE -> {
				// The ground rattles: dust jumps off the patch, harder as it goes.
				if (lift.ticks % 3 == 0) {
					for (BlockPos p : lift.blocks.subList(1, lift.blocks.size())) {
						BlockState s = level.getBlockState(p);
						if (!level.getBlockState(p.above()).isAir() || s.isAir()) continue;
						level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, s), p.getX() + 0.5, p.getY() + 1.02, p.getZ() + 0.5,
								1 + lift.ticks / 10, 0.35, 0.02, 0.35, 0.05 + lift.ticks * 0.004);
					}
				}
				if (lift.ticks % 8 == 0) level.playSound(null, mid, SoundEvents.ROOTED_DIRT_BREAK, SoundSource.BLOCKS, 0.5f + lift.ticks * 0.02f, 0.6f);
				if (lift.ticks >= SHAKE) {
					lift.stage = Stage.LIFT;
					lift.ticks = 0;
					start(level, lift);
				}
			}
			case LIFT -> {
				double up = RISE / LIFT;
				for (FallingBlockEntity e : lift.load) hold(e, new Vec3(0, up, 0));
				for (FallingBlockEntity e : lift.platform) hold(e, new Vec3(0, up, 0));
				if (lift.ticks % 6 == 0) level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), m.x, m.y, m.z, 6, 1.5, 0.2, 1.5, 0.02);
				if (lift.ticks >= LIFT) {
					lift.stage = Stage.AWAY;
					lift.ticks = 0;
					away(level, lantern, centre, lift);
				}
			}
			case AWAY -> {
				Vec3 chest = Vec3.atCenterOf(chestPos(lantern)).add(0, 1.2, 0);
				for (FallingBlockEntity e : lift.load) {
					if (e.isRemoved() || e.isNoGravity() == false) continue;
					// Off to the chest.
					Vec3 to = chest.subtract(e.position());
					if (to.length() < 0.8) {
						store(level, lantern, e.getBlockState());
						e.discard();
					} else {
						hold(e, to.scale(Math.min(0.6, to.length() * 0.2) / to.length()));
					}
				}
				for (FallingBlockEntity e : lift.platform) hold(e, new Vec3(0, -RISE / 12, 0));
				if (lift.ticks == 12) {
					// The platform sinks out of sight and is gone.
					for (FallingBlockEntity e : lift.platform) {
						level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), e.getX(), e.getY() + 0.5, e.getZ(), 2, 0.3, 0.3, 0.3, 0.02);
						e.discard();
					}
					lift.platform.clear();
				}
				if (lift.ticks >= AWAY) {
					for (FallingBlockEntity e : lift.load) {
						if (!e.isRemoved() && e.isNoGravity()) {
							store(level, lantern, e.getBlockState());
							e.discard();
						}
					}
					return true;
				}
			}
		}
		return false;
	}

	/** Lifts the patch out on its platform. */
	private static void start(ServerLevel level, Lift lift) {
		BlockPos mid = lift.blocks.getFirst();
		for (BlockPos p : lift.blocks.subList(1, lift.blocks.size())) {
			BlockState s = level.getBlockState(p);
			if (!natural(s)) continue;
			FallingBlockEntity e = FallingBlockEntity.fall(level, p, s);
			e.setNoGravity(true);
			e.disableDrop();
			e.time = 1;
			lift.load.add(e);
		}
		// The platform: a rimmed 5x5 deck with a 3x3 keel under it, rising from under the floor.
		Corps before = Corps.enter(Corps.BLUE);
		try {
			BlockState shell = Corps.state(ModRegistry.LIGHT_CONSTRUCT);
			BlockState rim = shell.setValue(LightConstructBlock.RIM, true);
			int deck = mid.getY() - 1;
			for (int dx = -2; dx <= 2; dx++) {
				for (int dz = -2; dz <= 2; dz++) {
					boolean edge = Math.abs(dx) == 2 || Math.abs(dz) == 2;
					platform(level, lift, mid.getX() + dx, deck, mid.getZ() + dz, edge ? rim : shell);
					if (Math.abs(dx) <= 1 && Math.abs(dz) <= 1) platform(level, lift, mid.getX() + dx, deck - 1, mid.getZ() + dz, dx == 0 && dz == 0 ? rim : shell);
				}
			}
		} finally {
			Corps.restore(before);
		}
		level.playSound(null, mid, SoundEvents.BEACON_POWER_SELECT, SoundSource.BLOCKS, 1f, 0.6f);
		level.playSound(null, mid, SoundEvents.PISTON_EXTEND, SoundSource.BLOCKS, 0.8f, 0.5f);
	}

	private static void platform(ServerLevel level, Lift lift, int x, int y, int z, BlockState state) {
		FallingBlockEntity e = FallingBlockAccessor.lanternring$create(level, x + 0.5, y, z + 0.5, state);
		e.setNoGravity(true);
		e.disableDrop();
		e.time = 1;
		level.addFreshEntity(e);
		lift.platform.add(e);
	}

	/** Earth is flung away over the walls (it lands as blocks out there); the rest heads for the chest. */
	private static void away(ServerLevel level, BlockPos lantern, BlockPos centre, Lift lift) {
		Vec3 c = Vec3.atBottomCenterOf(centre);
		boolean flung = false;
		for (FallingBlockEntity e : lift.load) {
			if (!earthy(e.getBlockState()) && chest(level, lantern) != null) continue;
			Vec3 out = new Vec3(e.getX() - c.x, 0, e.getZ() - c.z);
			out = out.lengthSqr() < 0.01 ? new Vec3(1, 0, 0) : out.normalize();
			double spread = 0.7 + level.getRandom().nextDouble() * 0.5;
			e.setNoGravity(false);
			e.setDeltaMovement(out.x * spread, 0.8 + level.getRandom().nextDouble() * 0.2, out.z * spread);
			e.time = 1;
			// It lands as a block again (nothing is destroyed), and drops nothing if it can't.
			e.dropItem = false;
			e.needsSync = true;
			flung = true;
		}
		if (flung) level.playSound(null, lift.blocks.getFirst(), SoundEvents.WIND_CHARGE_BURST.value(), SoundSource.BLOCKS, 1f, 0.7f);
	}

	private static void hold(FallingBlockEntity e, Vec3 v) {
		e.time = 1;
		e.setDeltaMovement(v);
		e.needsSync = true;
	}

	// ---- the chest ---------------------------------------------------------------------------

	private static BlockPos chestPos(BlockPos lantern) {
		return lantern.relative(Direction.EAST, 2);
	}

	private static @Nullable Container chest(ServerLevel level, BlockPos lantern) {
		BlockPos p = chestPos(lantern);
		if (level.getBlockState(p).isAir() && level.getBlockState(p.below()).isFaceSturdy(level, p.below(), Direction.UP)) {
			level.setBlockAndUpdate(p, Blocks.CHEST.defaultBlockState().setValue(ChestBlock.FACING, Direction.WEST));
		}
		return level.getBlockEntity(p) instanceof ChestBlockEntity c ? c : null;
	}

	/** Puts a lifted block in the chest (or sets it down by it if the chest is full). */
	private static void store(ServerLevel level, BlockPos lantern, BlockState s) {
		ItemStack item = new ItemStack(s.getBlock().asItem());
		Container chest = chest(level, lantern);
		if (chest != null && !item.isEmpty()) {
			for (int i = 0; i < chest.getContainerSize() && !item.isEmpty(); i++) {
				ItemStack in = chest.getItem(i);
				if (in.isEmpty()) {
					chest.setItem(i, item);
					item = ItemStack.EMPTY;
				} else if (ItemStack.isSameItemSameComponents(in, item) && in.getCount() < in.getMaxStackSize()) {
					in.grow(1);
					item = ItemStack.EMPTY;
				}
			}
			chest.setChanged();
		}
		Vec3 at = Vec3.atCenterOf(chestPos(lantern));
		if (!item.isEmpty()) level.addFreshEntity(new net.minecraft.world.entity.item.ItemEntity(level, at.x, at.y + 1, at.z, item));
		level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), at.x, at.y + 0.8, at.z, 3, 0.2, 0.2, 0.2, 0.02);
	}
}
