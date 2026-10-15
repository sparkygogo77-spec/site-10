package com.sparky.lanternring;

import com.sparky.lanternring.net.CombatFxPayload.Kind;
import com.sparky.lanternring.net.CraterLiningPayload;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * J's primed slams (Blender pass 518, J's in-game report 2026-10-14): shift held in hyper speed flying into the
 * ground (P1, a 7x7 crater, FlightSlams), or crouch held on a super jump's way down (P2, 9x9, SuperJumps).
 * <ul>
 * <li>The whole crater (the top block of each column, following the ground: FlightSlams.surface) opens the tick
 * after touchdown, all at once. The landing block holds you.
 * <li>The crater floor and a one-block rim round it are lined with construct for RingTuning primed_slam_lining (3 s);
 * the rim goes back to normal blocks as the lining dissolves (each client draws it, SuperLandConstruct).
 * <li>While the lining is up, left click on the crater rebuilds it (REBUILD from the client): P1 ripples out from
 * where you look, a block a tick; P2 follows the crosshair as you sweep it, the blocks within 1.5 of it. Rebuilt
 * blocks come back as they were (every client fades them from construct over 10 ticks). Blocks not rebuilt by the
 * time the lining goes stay gone.
 * </ul>
 */
public final class PrimedSlams {
	/** P1 (flight) and P2 (super jump): the crater's reach from the landing block (7x7, 9x9). */
	public static final int FLIGHT_REACH = 3, JUMP_REACH = 4;
	/** P2's sweep: blocks this near the crosshair are rebuilt. */
	private static final double SWEEP = 1.6;

	private static final class Crater {
		final ServerLevel level;
		final UUID owner;
		final Corps corps;
		BlockPos centre;
		final int reach;
		final boolean sweep;
		final int opens, until;
		/** Each block to take (or taken) and what it was. */
		final Map<BlockPos, BlockState> blocks = new LinkedHashMap<>();
		boolean opened, rippling;

		Crater(ServerLevel level, UUID owner, Corps corps, BlockPos centre, int reach, boolean sweep, int opens, int until) {
			this.level = level;
			this.owner = owner;
			this.corps = corps;
			this.centre = centre;
			this.reach = reach;
			this.sweep = sweep;
			this.opens = opens;
			this.until = until;
		}
	}

	private record Rebuild(Crater crater, BlockPos pos, int at) {
	}

	private static final List<Crater> CRATERS = new ArrayList<>();
	private static final List<Rebuild> REBUILDS = new ArrayList<>();

	private PrimedSlams() {
	}

	/**
	 * A primed slam touched down with the feet at "feet": every client is told (PRIMED_LAND: value the lining's
	 * ticks, variant the reach, + 8 for the sweep), the crater opens next tick and is lined. Called with the corps
	 * current.
	 */
	static void open(ServerPlayer p, Vec3 feet, int reach, boolean sweep) {
		ServerLevel level = p.level();
		int now = CombatMoves.now(), hold = RingTuning.PRIMED_SLAM_LINING.ticks();
		BlockPos centre = BlockPos.containing(feet.x, PowerLandings.groundY(feet.y), feet.z);
		CRATERS.add(new Crater(level, p.getUUID(), Corps.current(), centre, reach, sweep, now + 1, now + 1 + hold));
		level.playSound(null, feet.x, feet.y, feet.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.PLAYERS, 2f, 0.55f);
		level.playSound(null, feet.x, feet.y, feet.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 1f, 0.55f);
		level.playSound(null, feet.x, feet.y, feet.z, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.PLAYERS, 0.8f, 1.2f);
	}

	/**
	 * The tick after touchdown: the crater centres on the block the owner now stands on (the client has locked them
	 * there; the touchdown packet can lag a block behind), every client is told (PRIMED_LAND, the lining), and it opens.
	 */
	private static void place(Crater c) {
		ServerPlayer p = c.level.getPlayerByUUID(c.owner) instanceof ServerPlayer sp && sp.level() == c.level ? sp : null;
		if (p != null && p.onGround() && p.blockPosition().distManhattan(c.centre.above()) <= 3) {
			c.centre = BlockPos.containing(p.getX(), PowerLandings.groundY(p.getY()), p.getZ());
		}
		int hold = c.until - c.opens;
		List<BlockPos> lined = new ArrayList<>();
		for (int dx = -c.reach; dx <= c.reach; dx++) {
			for (int dz = -c.reach; dz <= c.reach; dz++) {
				if (dx == 0 && dz == 0) continue;
				BlockPos top = FlightSlams.surface(c.level, c.centre.offset(dx, 0, dz));
				if (top == null || p != null && !c.level.mayInteract(p, top) || !PowerLandings.takes(c.level, top, c.level.getBlockState(top))) continue;
				c.blocks.put(top, c.level.getBlockState(top));
				lined.add(top);
			}
		}
		Vec3 feet = Vec3.atBottomCenterOf(c.centre.above());
		Corps before = Corps.enter(c.corps);
		try {
			CombatMoves.send(c.level, Kind.PRIMED_LAND, feet, Vec3.atCenterOf(c.centre), hold, c.reach + (c.sweep ? 8 : 0), p, -1);
			CraterLiningPayload.send(c.level, p != null ? p.getId() : -1, c.corps, feet, hold + 1, true, lined);
		} finally {
			Corps.restore(before);
		}
	}

	/** The owner's client says left click is on the crater at "at" (the looked-at spot). */
	static void rebuild(ServerPlayer p, Vec3 at) {
		int now = CombatMoves.now();
		for (Crater c : CRATERS) {
			if (!c.owner.equals(p.getUUID()) || c.level != p.level() || !c.opened || now >= c.until) continue;
			double dx = at.x - (c.centre.getX() + 0.5), dz = at.z - (c.centre.getZ() + 0.5);
			if (Math.abs(dx) > c.reach + 1.5 || Math.abs(dz) > c.reach + 1.5 || Math.abs(at.y - c.centre.getY()) > 4) continue;
			if (c.sweep) {
				for (BlockPos pos : c.blocks.keySet()) {
					if (horizontal(pos, at) <= SWEEP) REBUILDS.add(new Rebuild(c, pos, now));
				}
			} else if (!c.rippling) {
				// Rippling out from where you look, a block a tick.
				c.rippling = true;
				for (BlockPos pos : c.blocks.keySet()) REBUILDS.add(new Rebuild(c, pos, now + (int) Math.round(horizontal(pos, at))));
			}
			return;
		}
	}

	private static double horizontal(BlockPos pos, Vec3 at) {
		double dx = pos.getX() + 0.5 - at.x, dz = pos.getZ() + 0.5 - at.z;
		return Math.sqrt(dx * dx + dz * dz);
	}

	/** Whether this player has a lined crater they could rebuild now (for tests). */
	public static boolean rebuildable(ServerPlayer p) {
		int now = CombatMoves.now();
		for (Crater c : CRATERS) if (c.owner.equals(p.getUUID()) && c.opened && now < c.until) return true;
		return false;
	}

	static void tick(MinecraftServer server) {
		int now = CombatMoves.now();
		for (Crater c : CRATERS) {
			if (c.opened || now < c.opens) continue;
			c.opened = true;
			place(c);
			// Every block at once, the tick after touchdown; whatever grows on them goes too.
			for (Iterator<Map.Entry<BlockPos, BlockState>> it = c.blocks.entrySet().iterator(); it.hasNext(); ) {
				Map.Entry<BlockPos, BlockState> e = it.next();
				BlockPos pos = e.getKey();
				BlockState state = c.level.getBlockState(pos);
				if (!PowerLandings.takes(c.level, pos, state)) {
					it.remove();
					continue;
				}
				e.setValue(state);
				BlockState above = c.level.getBlockState(pos.above());
				if (!above.isAir() && above.canBeReplaced() && above.getFluidState().isEmpty()) c.level.setBlock(pos.above(), Blocks.AIR.defaultBlockState(), 3);
				c.level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
			}
			Vec3 mid = Vec3.atCenterOf(c.centre);
			BlockState ground = c.level.getBlockState(c.centre);
			if (!ground.isAir()) {
				c.level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, ground), mid.x, mid.y + 0.6, mid.z, 120, c.reach * 0.6, 0.3, c.reach * 0.6, 0.4);
			}
			c.level.sendParticles(ModParticles.of(ModParticles.SHARD, c.corps), mid.x, mid.y + 0.7, mid.z, 30, c.reach * 0.5, 0.2, c.reach * 0.5, 0.35);
		}
		for (Iterator<Rebuild> it = REBUILDS.iterator(); it.hasNext(); ) {
			Rebuild r = it.next();
			if (now < r.at()) continue;
			it.remove();
			Crater c = r.crater();
			BlockState was = c.blocks.remove(r.pos());
			if (was == null || now >= c.until) continue;
			BlockState there = c.level.getBlockState(r.pos());
			if (!there.isAir() && !there.canBeReplaced()) continue;
			c.level.setBlock(r.pos(), was, 3);
			Corps before = Corps.enter(c.corps);
			try {
				CombatMoves.send(c.level, Kind.REBUILT, Vec3.atCenterOf(r.pos()), Vec3.atCenterOf(r.pos()), 0, 0, c.level.getPlayerByUUID(c.owner), -1);
			} finally {
				Corps.restore(before);
			}
			if (c.level.getRandom().nextInt(3) == 0) {
				c.level.playSound(null, r.pos(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 0.6f, 1.2f + c.level.getRandom().nextFloat() * 0.4f);
			}
		}
		CRATERS.removeIf(c -> now >= c.until);
	}
}
