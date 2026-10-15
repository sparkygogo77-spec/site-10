package com.sparky.lanternring;

import com.sparky.lanternring.net.CombatFxPayload.Kind;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.jspecify.annotations.Nullable;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * J's big flight slam (Blender pass 510, S3 M3 picked): fly freely, nose-dive, and once you're pitched 40 degrees
 * down or more, at a block a tick or faster, within the trigger height of the ground (Ring Lab Flight slam: H5 5
 * blocks, H6 6, H3 3), the slam fits itself into what is left of the fall (2 to 4 ticks): the ring fist swings
 * forward to lead, the legs swing under and you land in it. The local client sees its own flight, so it fires the
 * slam and reports touchdown (CombatInput); the server does the rest.
 * <ul>
 * <li>A 7x7 crater, following the ground up and down 2 blocks (FlightSlams.surface), on the D0 rule, lit 6 ticks longer (M3): ring d (rounded distance from the landing block) lights
 * at tick d - 1 and is gone at 4 + 2d + 6 (RingTuning flight_slam_glow). The landing block holds you, construct for
 * the whole lock, and fades back after it.
 * <li>Mobs out to 7 blocks are launched the tick after touchdown: out 0.95 - 0.111 d and up 0.65 - 0.034 d blocks a
 * tick (fitted to the pass's six mobs), hurt more the closer they are.
 * <li>You're locked in the landing for 0.7 s (RingTuning flight_slam_lock), then stand.
 * </ul>
 */
public final class FlightSlams {
	/** The crater's reach from the landing block (7x7) and the shockwave's. */
	public static final int REACH = 3;
	public static final double WAVE = 7;
	/** The most a slam hurts, right at the landing block. */
	private static final float DAMAGE = 14f;
	/** Ticks a fired slam waits for its touchdown before it's forgotten. */
	private static final int LAND_WAIT = 30;
	/** How far above or below the landing block's level a crater column still finds its ground. */
	private static final int SURFACE = 2;

	/** A crater block: dx, dz from the landing block, the tick it lights and the tick it's gone (-1: the landing block, which stays). */
	public record Cell(int dx, int dz, int lit, int cleared) {
	}

	private record Dive(Corps corps, int at, boolean primed) {
	}

	private record Launch(ServerLevel level, ServerPlayer owner, Vec3 centre, Corps corps, int at) {
	}

	private static final Map<UUID, Dive> DIVES = new HashMap<>();
	private static final List<Launch> LAUNCHES = new ArrayList<>();

	private FlightSlams() {
	}

	static void register() {
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> DIVES.remove(handler.player.getUUID()));
	}

	/** The crater's blocks, lit {@code extra} ticks longer than the D0 rule (M3: 6). Shared with every client's drawing. */
	public static List<Cell> cells(int extra) {
		List<Cell> out = new ArrayList<>();
		for (int dx = -REACH; dx <= REACH; dx++) {
			for (int dz = -REACH; dz <= REACH; dz++) {
				int d = (int) Math.round(Math.sqrt(dx * dx + dz * dz));
				out.add(d == 0 ? new Cell(0, 0, -1, -1) : new Cell(dx, dz, d - 1, 4 + 2 * d + extra));
			}
		}
		return out;
	}

	/**
	 * The ground block a crater column takes: the top solid block within 2 of the landing block's level (plants on it
	 * go with it), so the crater follows bumps and dips instead of only the landing block's own layer (J's report:
	 * on real ground most of it never opened). Null with nothing solid there. Shared with every client's drawing.
	 */
	public static @Nullable BlockPos surface(Level level, BlockPos column) {
		return surface(level, column, SURFACE);
	}

	/** The top solid block with nothing solid on it within reach blocks above or below column, or null. */
	public static @Nullable BlockPos surface(Level level, BlockPos column, int reach) {
		for (int dy = reach; dy >= -reach; dy--) {
			BlockPos pos = column.above(dy);
			if (level.getBlockState(pos).getCollisionShape(level, pos).isEmpty()) continue;
			BlockPos up = pos.above();
			if (level.getBlockState(up).getCollisionShape(level, up).isEmpty()) return pos;
		}
		return null;
	}

	/** The local client fired the slam at "at", moving step a tick, ticks from the ground. */
	static void dive(ServerPlayer p, Vec3 at, Vec3 step, int ticks, boolean primed) {
		if (CombatMoves.chargedRing(p).isEmpty() || p.isSpectator()) return;
		Corps corps = Corps.of(CombatMoves.chargedRing(p));
		DIVES.put(p.getUUID(), new Dive(corps, CombatMoves.now(), primed));
		Corps before = Corps.enter(corps);
		try {
			if (primed) CombatMoves.send(p.level(), Kind.PRIMED_DIVE, p.position(), p.position().add(step), Mth.clamp(ticks, 1, 6), 0, p, -1);
			else CombatMoves.send(p.level(), Kind.SLAM_DIVE, p.position(), p.position().add(step), Mth.clamp(ticks, 1, 6), 0, p, -1);
		} finally {
			Corps.restore(before);
		}
		p.level().playSound(null, p.getX(), p.getY(), p.getZ(), SoundEvents.MACE_SMASH_AIR, SoundSource.PLAYERS, 1.2f, 0.6f);
	}

	/** The local client's slam touched down at feet. */
	static void land(ServerPlayer p, Vec3 feet) {
		Dive dive = DIVES.remove(p.getUUID());
		if (dive == null || CombatMoves.now() - dive.at() > LAND_WAIT) return;
		ServerLevel level = p.level();
		// Stand the feet on the block below (the server can see them a little above it).
		BlockPos.MutableBlockPos under = new BlockPos.MutableBlockPos();
		for (int y = Mth.floor(feet.y + 0.2); y >= Mth.floor(feet.y) - 3; y--) {
			under.set(Mth.floor(feet.x), y, Mth.floor(feet.z));
			var shape = level.getBlockState(under).getCollisionShape(level, under);
			if (!shape.isEmpty()) {
				feet = new Vec3(feet.x, y + shape.max(Direction.Axis.Y), feet.z);
				break;
			}
		}
		p.resetFallDistance();
		int lock = RingTuning.FLIGHT_SLAM_LOCK.ticks(), extra = RingTuning.FLIGHT_SLAM_GLOW.ticks();
		if (dive.primed()) {
			// Pass 518 P1: the whole 7x7 opens at once and is lined; left click rebuilds it (PrimedSlams).
			Corps before = Corps.enter(dive.corps());
			try {
				PrimedSlams.open(p, feet, PrimedSlams.FLIGHT_REACH, false);
				WhatsNew.done(p, "slam.primed_flight");
			} finally {
				Corps.restore(before);
			}
			LAUNCHES.add(new Launch(level, p, feet, dive.corps(), CombatMoves.now() + 1));
			return;
		}
		Corps before = Corps.enter(dive.corps());
		try {
			CombatMoves.send(level, Kind.SLAM_LAND, feet, feet.add(WAVE, 0, 0), lock, extra, p, -1);
			WhatsNew.done(p, "combat.flight_slam");
			BlockPos centre = BlockPos.containing(feet.x, PowerLandings.groundY(feet.y), feet.z);
			for (Cell c : cells(extra)) {
				BlockPos top = c.cleared() < 0 ? null : surface(level, centre.offset(c.dx(), 0, c.dz()));
				if (top != null) CombatMoves.clear(level, p, top, c.cleared());
			}
			BlockState ground = level.getBlockState(centre);
			if (!ground.isAir()) {
				level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, ground), feet.x, feet.y + 0.1, feet.z, 70, 2.0, 0.1, 2.0, 0.35);
			}
			level.sendParticles(ModParticles.of(ModParticles.SHARD, dive.corps()), feet.x, feet.y + 0.2, feet.z, 18, 1.5, 0.1, 1.5, 0.3);
		} finally {
			Corps.restore(before);
		}
		// M3: the mobs go up the tick after touchdown.
		LAUNCHES.add(new Launch(level, p, feet, dive.corps(), CombatMoves.now() + 1));
		level.playSound(null, feet.x, feet.y, feet.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.PLAYERS, 2f, 0.6f);
		level.playSound(null, feet.x, feet.y, feet.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 0.9f, 0.6f);
		level.playSound(null, feet.x, feet.y, feet.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1f, 0.5f);
	}

	/** Every mob out to WAVE blocks thrown out and up, more the closer it is. */
	private static void launch(Launch l) {
		Vec3 c = l.centre();
		for (LivingEntity e : l.level().getEntitiesOfClass(LivingEntity.class, new AABB(c, c).inflate(WAVE, 3, WAVE),
				e -> e != l.owner() && e.isAlive() && !e.isSpectator() && !CombatMoves.spared(e, l.owner()))) {
			double dx = e.getX() - c.x, dz = e.getZ() - c.z;
			double d = Math.sqrt(dx * dx + dz * dz);
			if (d > WAVE) continue;
			Vec3 out = d < 1e-3 ? new Vec3(1, 0, 0) : new Vec3(dx / d, 0, dz / d);
			double side = Math.max(0.15, 0.95 - 0.111 * d), up = Math.max(0.35, 0.65 - 0.0344 * d);
			if (!(e instanceof Player other && other.isCreative())) {
				e.hurtServer(l.level(), l.level().damageSources().indirectMagic(l.owner(), l.owner()), (float) (DAMAGE * (1 - d / (WAVE + 1))));
			}
			e.setDeltaMovement(out.x * side, up, out.z * side);
			RingPowers.syncVelocity(e);
		}
	}

	static void tick(MinecraftServer server) {
		int now = CombatMoves.now();
		DIVES.values().removeIf(d -> now - d.at() > LAND_WAIT);
		for (Iterator<Launch> it = LAUNCHES.iterator(); it.hasNext(); ) {
			Launch l = it.next();
			if (now < l.at()) continue;
			it.remove();
			Corps before = Corps.enter(l.corps());
			try {
				launch(l);
			} finally {
				Corps.restore(before);
			}
		}
	}
}
