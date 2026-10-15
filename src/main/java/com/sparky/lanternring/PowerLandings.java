package com.sparky.lanternring;

import com.sparky.lanternring.net.CraterLiningPayload;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * J's power landing (Blender pass 400, hand-off docs/handoff/2026-10-14-power-landing on the Blender
 * branch): a super jump lands either stopping dead or, fast enough, in a short one-foot skid that
 * clears a trench of construct-lit blocks in front of you, in place of the long run-out slide.
 * <ul>
 * <li>D0 stop dead (under the threshold): the block you land on holds you and the 8 round it
 * dissolve to construct pixels.
 * <li>A3 dissolve (Ring Lab default, above 25 blocks a second): each block of the trench lights up
 * as the planted foot nears it and breaks into pixels as it gets there.
 * <li>B2 plough (Ring Lab option, above 15 blocks a second): a construct bow wave throws them aside.
 * </ul>
 * Every block follows the ground a block up or down (onGround), and the trench is lined with construct for
 * RingTuning power_landing_lining (CraterLiningPayload).
 * The slide runs {@code min(5, 5 x speed / 28)} blocks along the horizontal velocity at touchdown,
 * slowing at a constant rate over {@code round(2 x length / speed)} ticks, and stops on the block it
 * ends over, which stays. The trench is the top layer only, 3 wide, and never takes unbreakable
 * blocks (one in the way ends the slide on it), containers, constructs or claimed ground. The server
 * clears the blocks; every client draws them (PowerLandingFx) and the jumper's own slides it there.
 */
public final class PowerLandings {
	/** POWER_LAND's variant: the take. */
	public static final int STOP = 0, DISSOLVE = 1, PLOUGH = 2;
	/** Speeds (blocks a second) a landing slides above: dissolve, plough. */
	public static final float DISSOLVE_ABOVE = 25f, PLOUGH_ABOVE = 15f;
	/** The longest slide, and the speed (blocks a second) that slides all of it. */
	public static final double MAX_SLIDE = 5, FULL_SPEED = 28;
	/** The blocks light up when the foot is this far from them. */
	public static final double LIGHT_AHEAD = 1.6;
	/** A block a slide meets a block above its level (a bump) goes this many ticks sooner, so you don't run into it. */
	private static final int BUMP_EARLY = 2;
	/** Stop dead: the ticks the 4 beside and 4 corner blocks round your feet go. */
	public static final int STOP_SIDE = 6, STOP_CORNER = 8;

	/** A block of the landing: its place, the tick it lights up and the tick it's gone (after touchdown), and its side (-1, 0, 1). */
	public record Cell(BlockPos pos, int lit, int cleared, int side) {
	}

	/** Each player's Ring Lab Landing slide pick (sent by SuperJumpPayload.SLIDE): DISSOLVE or PLOUGH. */
	private static final Map<UUID, Integer> PICK = new HashMap<>();

	private record Clear(ServerLevel level, BlockPos pos, int at) {
	}

	private static final List<Clear> PENDING = new ArrayList<>();
	private static int now;

	/**
	 * The jumper's client reports where it touched down and how fast (MoveFxPayload.LAND); the server
	 * sees the landing itself a tick or so off from that, so the power landing waits for both and goes
	 * from the client's spot (where the jumper really is). Either may come first; a landing the client
	 * never reports goes from the server's own after REPORT_WAIT ticks.
	 */
	private record Report(Vec3 at, Vec3 step, int time) {
	}

	private record Landed(Corps corps, Vec3 feet, Vec3 step, boolean dig, int time) {
	}

	private static final int REPORT_WAIT = 10;
	private static final Map<UUID, Report> REPORTS = new HashMap<>();
	private static final Map<UUID, Landed> LANDED = new HashMap<>();

	private PowerLandings() {
	}

	static void register() {
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
			PICK.remove(handler.player.getUUID());
			REPORTS.remove(handler.player.getUUID());
			LANDED.remove(handler.player.getUUID());
		});
		ServerTickEvents.END_SERVER_TICK.register(PowerLandings::tick);
	}

	static void pick(ServerPlayer player, int take) {
		PICK.put(player.getUUID(), take == PLOUGH ? PLOUGH : DISSOLVE);
	}

	/** The ground block under feet at y: the block the feet stand on. */
	public static int groundY(double feetY) {
		return Mth.floor(feetY - 0.05);
	}

	/** How far a landing at this speed (blocks a second) slides, before anything in the way shortens it. */
	public static double slideLength(double speed) {
		return Math.min(MAX_SLIDE, MAX_SLIDE * speed / FULL_SPEED);
	}

	/** The slide's ticks: constant deceleration from speed to nothing over length. */
	public static int slideTicks(double length, double speed) {
		return speed <= 0 ? 0 : Math.max(1, (int) Math.round(2 * length / speed * 20));
	}

	/** How far along the slide the feet are k ticks after touchdown (constant deceleration). */
	public static double forward(double length, int ticks, double k) {
		if (ticks <= 0) return length;
		double t = Mth.clamp(k / ticks, 0, 1);
		return length * (1 - (1 - t) * (1 - t));
	}

	/** The first tick the feet are at least at distance s along the slide. */
	private static int reach(double length, int ticks, double s) {
		if (s <= 0) return 0;
		if (s >= length) return ticks;
		return (int) Math.ceil(ticks * (1 - Math.sqrt(1 - s / length)) - 1e-6);
	}

	/**
	 * The blocks a landing takes, in order: stop dead's 8 round the feet, or a slide's trench from
	 * the touchdown block to the one before the halt block. Shared by the server (clearing) and
	 * every client (drawing), so both agree tick for tick.
	 */
	public static List<Cell> cells(Vec3 from, Vec3 dir, double length, double speed, int take) {
		int y = groundY(from.y);
		BlockPos centre = BlockPos.containing(from.x, y, from.z);
		List<Cell> out = new ArrayList<>();
		if (take == STOP) {
			for (int dx = -1; dx <= 1; dx++) {
				for (int dz = -1; dz <= 1; dz++) {
					if (dx == 0 && dz == 0) continue;
					boolean corner = dx != 0 && dz != 0;
					out.add(new Cell(centre.offset(dx, 0, dz), corner ? 1 : 0, corner ? STOP_CORNER : STOP_SIDE, 0));
				}
			}
			return out;
		}
		int ticks = slideTicks(length, speed);
		BlockPos halt = BlockPos.containing(from.x + dir.x * length, y, from.z + dir.z * length);
		boolean alongX = Math.abs(dir.x) >= Math.abs(dir.z);
		Map<BlockPos, Cell> cells = new LinkedHashMap<>();
		BlockPos last = null;
		for (double s = 0; s <= length + 1e-6; s += 0.1) {
			BlockPos at = BlockPos.containing(from.x + dir.x * s, y, from.z + dir.z * s);
			if (at.equals(halt)) break;
			if (at.equals(last)) continue;
			last = at;
			// Cleared as the planted foot gets there (the touchdown block the tick after), lit 1.6 blocks before.
			int cleared = Math.max(1, reach(length, ticks, s));
			int lit = s <= LIGHT_AHEAD ? -1 : reach(length, ticks, s - LIGHT_AHEAD);
			cells.putIfAbsent(at, new Cell(at, lit, cleared, 0));
			for (int side = -1; side <= 1; side += 2) {
				BlockPos beside = alongX ? at.offset(0, 0, side) : at.offset(side, 0, 0);
				// The side columns go a tick later.
				if (!beside.equals(halt)) cells.putIfAbsent(beside, new Cell(beside, lit + 1, cleared + 1, side));
			}
		}
		out.addAll(cells.values());
		return out;
	}

	/**
	 * The landing's blocks moved onto the ground they're over (FlightSlams.surface, a block up or down): a bump in the
	 * way is taken a little ahead of the foot, a dip (or an earlier landing's trench) at its own level, and a column
	 * with nothing there is skipped. The server and every client call it with the level as it is at touchdown, so they
	 * agree.
	 */
	public static List<Cell> onGround(Level level, List<Cell> cells, int y) {
		List<Cell> out = new ArrayList<>();
		for (Cell c : cells) {
			BlockPos top = com.sparky.lanternring.FlightSlams.surface(level, c.pos(), 1);
			if (top == null) continue;
			if (top.getY() > y) out.add(new Cell(top, Math.max(-1, c.lit() - BUMP_EARLY), Math.max(1, c.cleared() - BUMP_EARLY), c.side()));
			else out.add(top.equals(c.pos()) ? c : new Cell(top, c.lit(), c.cleared(), c.side()));
		}
		return out;
	}

	/** Whether the landing may take this block: not air, fluid, unbreakable, a container or a construct. */
	public static boolean takes(Level level, BlockPos pos, BlockState state) {
		return !state.isAir() && state.getFluidState().isEmpty() && state.getDestroySpeed(level, pos) >= 0 && !state.hasBlockEntity()
				&& !state.is(ModRegistry.LIGHT_CONSTRUCT) && !state.is(ModRegistry.CONSTRUCT_BRICK);
	}

	/** The jumper's client says it touched down at "at", moving step a tick across the ground. */
	static void reported(ServerPlayer p, Vec3 at, Vec3 step) {
		Landed landed = LANDED.remove(p.getUUID());
		if (landed != null && now - landed.time() <= REPORT_WAIT) run(p, landed.corps(), at, step, landed.dig());
		else REPORTS.put(p.getUUID(), new Report(at, step, now));
	}

	/** Where the jumper's client says it just touched down (taken), or null: a primed landing's crater goes from there. */
	static @org.jspecify.annotations.Nullable Vec3 takeReport(ServerPlayer p) {
		Report report = REPORTS.remove(p.getUUID());
		return report != null && now - report.time() <= REPORT_WAIT ? report.at() : null;
	}

	/** SuperJumps saw this player's super jump touch down at feet (step: its last move) on the ground, not primed. */
	static void landed(ServerPlayer p, Corps corps, Vec3 feet, Vec3 step, boolean dig) {
		Report report = REPORTS.remove(p.getUUID());
		if (report != null && now - report.time() <= REPORT_WAIT) run(p, corps, report.at(), report.step(), dig);
		else LANDED.put(p.getUUID(), new Landed(corps, feet, step, dig, now));
	}

	private static void run(ServerPlayer p, Corps corps, Vec3 feet, Vec3 step, boolean dig) {
		Corps before = Corps.enter(corps);
		try {
			land(p, feet, step, dig);
		} finally {
			Corps.restore(before);
		}
	}

	/**
	 * A super jump touches down at feet, having moved step (blocks) on its last tick. Picks the take,
	 * shortens the slide to anything in the way, clears the blocks as it goes (when dig) and tells
	 * every client. Called with the jumper's corps current.
	 */
	static void land(ServerPlayer p, Vec3 feet, Vec3 step, boolean dig) {
		ServerLevel level = p.level();
		// The server can see the feet a little above the ground at touchdown: stand them on the block below.
		BlockPos.MutableBlockPos under = new BlockPos.MutableBlockPos();
		for (int y = Mth.floor(feet.y + 0.2); y >= Mth.floor(feet.y) - 3; y--) {
			under.set(Mth.floor(feet.x), y, Mth.floor(feet.z));
			var shape = level.getBlockState(under).getCollisionShape(level, under);
			if (!shape.isEmpty()) {
				feet = new Vec3(feet.x, y + shape.max(net.minecraft.core.Direction.Axis.Y), feet.z);
				break;
			}
		}
		Vec3 flat = new Vec3(step.x, 0, step.z);
		double speed = flat.length() * 20;
		int pick = PICK.getOrDefault(p.getUUID(), DISSOLVE);
		float above = pick == PLOUGH ? PLOUGH_ABOVE : DISSOLVE_ABOVE;
		int take = speed > above && flat.lengthSqr() > 1e-6 ? pick : STOP;
		Vec3 dir = take == STOP ? Vec3.ZERO : flat.normalize();
		double length = take == STOP ? 0 : clip(level, feet, dir, slideLength(speed));
		if (take != STOP && length < 0.3) {
			take = STOP;
			length = 0;
		}
		Vec3 to = feet.add(dir.scale(length));
		RingFx.send(level, Kind.POWER_LAND, feet, to, (float) speed, take, p);
		if (!dig) return;
		int y = groundY(feet.y);
		List<BlockPos> taken = new ArrayList<>();
		for (Cell c : onGround(level, cells(feet, dir, length, speed, take), y)) {
			if (!level.mayInteract(p, c.pos()) || !takes(level, c.pos(), level.getBlockState(c.pos()))) continue;
			PENDING.add(new Clear(level, c.pos(), now + c.cleared()));
			taken.add(c.pos());
		}
		// The whole trench lined with construct, and the ground one block out all round it (pass 518 U1), not just where
		// you touched down (J, 2026-10-14).
		CraterLiningPayload.send(level, p.getId(), Corps.current(), feet, RingTuning.POWER_LANDING_LINING.ticks(), true, taken);
		if (take != STOP) {
			level.playSound(null, feet.x, feet.y, feet.z, SoundEvents.MACE_SMASH_GROUND, SoundSource.PLAYERS, 1f, 0.6f);
			level.playSound(null, to.x, to.y, to.z, SoundEvents.GRAVEL_BREAK, SoundSource.PLAYERS, 1.2f, 0.6f);
		}
		level.playSound(null, feet.x, y + 1, feet.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 0.8f, 0.6f);
	}

	/** The slide's length cut short by a wall at the feet (it stops before it) or an unbreakable block underfoot (it stops on it). */
	private static double clip(ServerLevel level, Vec3 from, Vec3 dir, double length) {
		int y = groundY(from.y);
		BlockPos start = BlockPos.containing(from.x, y, from.z), last = start;
		for (double s = 0; s <= length + 1e-6; s += 0.1) {
			BlockPos at = BlockPos.containing(from.x + dir.x * s, y, from.z + dir.z * s);
			if (at.equals(last)) continue;
			last = at;
			// A wall stops it; a one-block bump it can take is cut away (onGround) and slid through.
			BlockPos bump = at.above();
			BlockState bumpState = level.getBlockState(bump);
			boolean blocked = !bumpState.getCollisionShape(level, bump).isEmpty()
					&& (!takes(level, bump, bumpState) || !level.getBlockState(bump.above()).getCollisionShape(level, bump.above()).isEmpty());
			if (blocked || !level.getBlockState(at.above(2)).getCollisionShape(level, at.above(2)).isEmpty()) {
				return Math.max(0, s - 0.4);
			}
			if (level.getBlockState(at).getDestroySpeed(level, at) < 0) return Math.min(length, s + 0.5);
		}
		return length;
	}

	private static void tick(MinecraftServer server) {
		now++;
		REPORTS.values().removeIf(r -> now - r.time() > REPORT_WAIT);
		for (Iterator<Map.Entry<UUID, Landed>> it = LANDED.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<UUID, Landed> e = it.next();
			Landed l = e.getValue();
			if (now - l.time() <= REPORT_WAIT) continue;
			it.remove();
			ServerPlayer p = server.getPlayerList().getPlayer(e.getKey());
			if (p != null) run(p, l.corps(), l.feet(), l.step(), l.dig());
		}
		for (Iterator<Clear> it = PENDING.iterator(); it.hasNext(); ) {
			Clear c = it.next();
			if (now < c.at()) continue;
			it.remove();
			BlockState state = c.level().getBlockState(c.pos());
			if (!takes(c.level(), c.pos(), state)) continue;
			// Whatever grows on top goes with it; nothing drops (the blocks dissolve to construct pixels).
			BlockPos up = c.pos().above();
			BlockState above = c.level().getBlockState(up);
			if (!above.isAir() && above.canBeReplaced() && above.getFluidState().isEmpty()) c.level().setBlock(up, Blocks.AIR.defaultBlockState(), 3);
			c.level().setBlock(c.pos(), Blocks.AIR.defaultBlockState(), 3);
		}
	}
}
