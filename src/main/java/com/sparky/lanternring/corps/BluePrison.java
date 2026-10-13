package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.Lasso;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RingFx;
import com.sparky.lanternring.city.CityBlocks;
import com.sparky.lanternring.city.HardLightSet;
import com.sparky.lanternring.net.RingFxPayload;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.SlabType;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The Blue Lantern's floating prison (J, 2026-10-13). Once everything round a lantern is safe,
 * its flyers collect the monsters caged on the ground (BlueCage): each is lassoed, pulled straight
 * up, carried over and lowered into its own capsule in a structure floating above the lantern.
 * The capsules stand in a ring round a hub, eight to a level, joined to the hub by walkways, with a
 * new level above when one fills. A capsule forms round its prisoner as it comes in (hard light
 * setting into Skystone and Hope crystal) and its roof closes once the prisoner is down.
 *
 * <p>Prisoners stay frozen (no AI) and are no threat to anyone (ConstructAlly.isBadMob). The
 * prison is real blocks once set, so it outlasts a restart; which capsule is free is worked out
 * from who's in them.
 */
final class BluePrison {
	/** On a monster locked in a capsule. */
	static final String PRISONER = "lanternring.blue_prisoner";
	/** The first level's floor above the lantern, the levels' spacing, and capsules per level. */
	private static final int RISE = 12, LEVEL = 6, PER_LEVEL = 8, LEVELS = 4;
	/** Hub radius, and the ring the capsules' middles stand on. */
	private static final int HUB = 5, RING = 9;
	/** Blocks formed per tick while a piece builds, so it sweeps into being. */
	private static final int FORM_RATE = 10;
	/** How far over a capsule the flyer carries its prisoner before lowering it in. */
	private static final double OVER = 4, HANG = 2.6;
	private static final int CARRY_LIMIT = 900;

	enum Stage {
		FETCH, UP, ACROSS, DOWN
	}

	private static final class Transfer {
		final Mob mob;
		final int cell;
		Stage stage = Stage.FETCH;
		final long started;

		Transfer(Mob mob, int cell, long started) {
			this.mob = mob;
			this.cell = cell;
			this.started = started;
		}
	}

	private static final class Prison {
		final BlockPos lantern;
		boolean hubBuilt;
		final Map<UUID, Transfer> moving = new HashMap<>();
		final Deque<BlockPos> queue = new ArrayDeque<>();
		final Map<BlockPos, BlockState> want = new HashMap<>();

		Prison(BlockPos lantern) {
			this.lantern = lantern;
		}
	}

	private static final Map<BlockPos, Prison> PRISONS = new HashMap<>();

	private BluePrison() {
	}

	static void register() {
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> {
			PRISONS.clear();
			// It holds ServerLevels: keeping them past a world reload leaks the old world.
			LEVELS_SEEN.clear();
		});
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			for (Prison p : PRISONS.values()) {
				for (int i = 0; i < FORM_RATE && !p.queue.isEmpty(); i++) {
					BlockPos pos = p.queue.poll();
					BlockState st = p.want.remove(pos);
					ServerLevel level = levelOf(p);
					if (st != null && level != null && level.getBlockState(pos).canBeReplaced()) HardLightSet.form(level, pos, st);
				}
			}
		});
	}

	/** The level a prison's flyers are in (any of them will do). */
	private static @Nullable ServerLevel levelOf(Prison p) {
		for (Transfer t : p.moving.values()) {
			if (t.mob.level() instanceof ServerLevel s) return s;
		}
		return LEVELS_SEEN.get(p.lantern);
	}

	private static final Map<BlockPos, ServerLevel> LEVELS_SEEN = new HashMap<>();

	static boolean prisoner(LivingEntity e) {
		return e.entityTags().contains(PRISONER);
	}

	/** Whether this flyer is carrying a prisoner (it finishes before it fights). */
	static boolean carrying(CorpsVillager v) {
		BlockPos post = v.squadPost();
		Prison p = post == null ? null : PRISONS.get(post);
		Transfer t = p == null ? null : p.moving.get(v.getUUID());
		return t != null && t.stage != Stage.FETCH;
	}

	/**
	 * A flyer with nothing to fight and no one left to rescue: takes the next caged monster up to
	 * the prison. False when there's none (it circles instead).
	 */
	static boolean flyer(ServerLevel level, CorpsVillager v, BlockPos lantern) {
		Prison p = PRISONS.computeIfAbsent(lantern, Prison::new);
		LEVELS_SEEN.put(lantern, level);
		long now = level.getGameTime();
		Transfer t = p.moving.get(v.getUUID());
		if (t != null && (!t.mob.isAlive() || now - t.started > CARRY_LIMIT || t.stage != Stage.FETCH && Lasso.npcCaught(v) != t.mob)) {
			// Lost it (or it took too long): put it down and let the cage take it again.
			if (Lasso.npcCaught(v) == t.mob) Lasso.npcSetDown(v);
			if (t.mob.isAlive() && !prisoner(t.mob)) BlueCage.recage(level, t.mob);
			p.moving.remove(v.getUUID());
			t = null;
		}
		if (t == null) {
			Mob next = nextCaged(p, lantern);
			if (next == null) return false;
			int cell = freeCell(level, p, lantern);
			if (cell < 0) return false;
			t = new Transfer(next, cell, now);
			p.moving.put(v.getUUID(), t);
			if (!p.hubBuilt) {
				hub(p, lantern);
				p.hubBuilt = true;
			}
			capsule(p, lantern, cell, false);
		}
		Vec3 cell = cellCentre(lantern, t.cell);
		double top = cell.y + 3 + OVER;
		switch (t.stage) {
			case FETCH -> {
				Vec3 at = t.mob.position();
				v.squadFly(at.add(0, t.mob.getBbHeight() + HANG + 0.5, 0), t.mob.getEyePosition());
				if (v.distanceToSqr(t.mob) < 7 * 7) {
					BlueCage.open(t.mob);
					if (Lasso.npcCatch(level, v, t.mob)) {
						t.stage = Stage.UP;
						v.fired();
						Corps before = Corps.enter(Corps.BLUE);
						try {
							RingFx.send(level, RingFxPayload.Kind.TETHER, CorpsVillager.ringPos(v, 1f, t.mob.getBoundingBox().getCenter()), t.mob.getBoundingBox().getCenter());
						} finally {
							Corps.restore(before);
						}
						level.playSound(null, t.mob.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.NEUTRAL, 1f, 1.3f);
					} else {
						BlueCage.recage(level, t.mob);
					}
				}
			}
			case UP -> {
				// Straight up from where it was caged.
				Vec3 above = new Vec3(t.mob.getX(), top + HANG, t.mob.getZ());
				v.squadFly(above, null);
				v.aimAt(t.mob);
				Lasso.npcHold(v, new Vec3(t.mob.getX(), Math.min(top, t.mob.getY() + 1.2) + t.mob.getBbHeight() / 2, t.mob.getZ()));
				if (t.mob.getY() > top - 1.5) t.stage = Stage.ACROSS;
			}
			case ACROSS -> {
				Vec3 over = new Vec3(cell.x, top + HANG, cell.z);
				v.squadFly(over, null);
				v.aimAt(t.mob);
				Lasso.npcHold(v, v.position().subtract(0, HANG, 0));
				if (horizontal(t.mob.position(), cell) < 1.2) t.stage = Stage.DOWN;
			}
			case DOWN -> {
				v.squadFly(new Vec3(cell.x, top + HANG, cell.z), null);
				v.aimAt(t.mob);
				Vec3 bubble = t.mob.position();
				Lasso.npcHold(v, new Vec3(cell.x, Math.max(cell.y, bubble.y - 0.2) + t.mob.getBbHeight() / 2, cell.z));
				if (bubble.y - cell.y < 0.4 && horizontal(bubble, cell) < 0.8) {
					Lasso.npcSetDown(v);
					t.mob.teleportTo(cell.x, cell.y, cell.z);
					t.mob.setDeltaMovement(Vec3.ZERO);
					t.mob.setNoAi(true);
					t.mob.removeTag(BlueCage.CAGED);
					t.mob.addTag(PRISONER);
					capsule(p, lantern, t.cell, true);
					level.playSound(null, t.mob.blockPosition(), SoundEvents.IRON_DOOR_CLOSE, SoundSource.NEUTRAL, 1f, 0.7f);
					level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), cell.x, cell.y + 1, cell.z, 20, 1, 1, 1, 0.03);
					p.moving.remove(v.getUUID());
					v.aimAt(null);
				}
			}
		}
		return true;
	}

	private static @Nullable Mob nextCaged(Prison p, BlockPos lantern) {
		for (Mob m : BlueCage.cagedNear(Vec3.atCenterOf(lantern), BlueSquad.CLEAR_RADIUS + 8)) {
			boolean taken = false;
			for (Transfer t : p.moving.values()) taken |= t.mob == m;
			if (!taken) return m;
		}
		return null;
	}

	/** The first capsule nobody's in or heading to, or -1 when the prison is full. */
	private static int freeCell(ServerLevel level, Prison p, BlockPos lantern) {
		for (int cell = 0; cell < PER_LEVEL * LEVELS; cell++) {
			boolean taken = false;
			for (Transfer t : p.moving.values()) taken |= t.cell == cell;
			if (taken) continue;
			Vec3 c = cellCentre(lantern, cell);
			AABB inside = new AABB(c.x - 1.5, c.y, c.z - 1.5, c.x + 1.5, c.y + 3, c.z + 1.5);
			if (level.getEntitiesOfClass(LivingEntity.class, inside, LivingEntity::isAlive).isEmpty()) return cell;
		}
		return -1;
	}

	/** Where a capsule's prisoner stands: bottom middle of its 3x3x3 inside. */
	private static Vec3 cellCentre(BlockPos lantern, int cell) {
		BlockPos b = cellBase(lantern, cell);
		return Vec3.atBottomCenterOf(b);
	}

	private static BlockPos cellBase(BlockPos lantern, int cell) {
		int lvl = cell / PER_LEVEL, i = cell % PER_LEVEL;
		double a = i * Math.PI * 2 / PER_LEVEL;
		return lantern.offset((int) Math.round(Math.cos(a) * RING), RISE + lvl * LEVEL, (int) Math.round(Math.sin(a) * RING));
	}

	// ---- building --------------------------------------------------------------------------------

	private static void queue(Prison p, BlockPos pos, BlockState st) {
		if (p.want.put(pos.immutable(), st) == null) p.queue.add(pos.immutable());
	}

	/** The hub: a round Skystone floor over the lantern with an open shaft in the middle and lamps round its rim. */
	private static void hub(Prison p, BlockPos lantern) {
		BlockPos c = lantern.above(RISE - 1);
		for (int r = 2; r <= HUB; r++) {
			for (int dx = -r; dx <= r; dx++) {
				for (int dz = -r; dz <= r; dz++) {
					double d = Math.sqrt(dx * dx + dz * dz);
					if (d > r || d <= r - 1) continue;
					BlockState st = r == HUB ? CityBlocks.HOPE_QUARTZ_BRICKS.defaultBlockState()
							: r == 2 ? CityBlocks.HOPE_INLAY.defaultBlockState() : CityBlocks.SKYSTONE_TILES.defaultBlockState();
					queue(p, c.offset(dx, 0, dz), st);
				}
			}
		}
		// Walkways out to every capsule on this level.
		for (int i = 0; i < PER_LEVEL; i++) {
			double a = i * Math.PI * 2 / PER_LEVEL;
			for (int r = HUB + 1; r <= RING - 2; r++) {
				queue(p, c.offset((int) Math.round(Math.cos(a) * r), 0, (int) Math.round(Math.sin(a) * r)), CityBlocks.SKYSTONE_TILES.defaultBlockState());
			}
		}
		for (int i = 0; i < 8; i++) {
			double a = (i + 0.5) * Math.PI / 4;
			queue(p, c.offset((int) Math.round(Math.cos(a) * HUB), 1, (int) Math.round(Math.sin(a) * HUB)), CityBlocks.HOPE_LAMP.defaultBlockState());
		}
	}

	/** A capsule: floor, crystal walls and pillar corners round its prisoner; the roof once it's in. */
	private static void capsule(Prison p, BlockPos lantern, int cell, boolean roof) {
		BlockPos b = cellBase(lantern, cell);
		BlockState pillar = CityBlocks.HOPE_QUARTZ_PILLAR.defaultBlockState().setValue(RotatedPillarBlock.AXIS, Direction.Axis.Y);
		BlockState crystal = CityBlocks.HOPE_CRYSTAL.defaultBlockState();
		BlockState tiles = CityBlocks.SKYSTONE_TILES.defaultBlockState();
		if (!roof) {
			for (int dx = -2; dx <= 2; dx++) {
				for (int dz = -2; dz <= 2; dz++) {
					boolean edge = Math.abs(dx) == 2 || Math.abs(dz) == 2, corner = Math.abs(dx) == 2 && Math.abs(dz) == 2;
					queue(p, b.offset(dx, -1, dz), corner ? CityBlocks.HOPE_QUARTZ_BRICKS.defaultBlockState() : tiles);
					if (!edge) continue;
					for (int y = 0; y < 3; y++) queue(p, b.offset(dx, y, dz), corner ? pillar : crystal);
				}
			}
			// A walkway from the hub's level up or down to it is the hub's own on level one; higher levels get a ring path.
			if (cell >= PER_LEVEL) {
				double a = (cell % PER_LEVEL) * Math.PI * 2 / PER_LEVEL;
				for (int r = HUB + 1; r <= RING - 3; r++) {
					queue(p, lantern.offset((int) Math.round(Math.cos(a) * r), b.getY() - lantern.getY() - 1, (int) Math.round(Math.sin(a) * r)), tiles);
				}
			}
			return;
		}
		for (int dx = -2; dx <= 2; dx++) {
			for (int dz = -2; dz <= 2; dz++) {
				boolean edge = Math.abs(dx) == 2 || Math.abs(dz) == 2;
				queue(p, b.offset(dx, 3, dz), edge ? CityBlocks.SKYSTONE_SLAB.defaultBlockState().setValue(SlabBlock.TYPE, SlabType.DOUBLE)
						: dx == 0 && dz == 0 ? CityBlocks.HOPE_LAMP.defaultBlockState() : crystal);
			}
		}
	}

	private static double horizontal(Vec3 a, Vec3 b) {
		double dx = a.x - b.x, dz = a.z - b.z;
		return Math.sqrt(dx * dx + dz * dz);
	}
}
