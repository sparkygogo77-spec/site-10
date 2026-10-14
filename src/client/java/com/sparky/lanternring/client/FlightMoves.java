package com.sparky.lanternring.client;

import com.sparky.lanternring.net.MoveFxPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.Mth;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * Your own ring flight moves from J's movement and flight hand-off (2026-10-14). Movement is the local
 * player's, so it runs here; each move is reported (MoveFxPayload) so every client draws its pose and
 * effects.
 * <ul>
 * <li><b>Take-off</b>: pass 403's double-jump puff and dart, and the L2 soft landing, are TakeoffMoves (they
 * replaced the F2 rocket takeoff, whose pose MovePoses still draws for older clients).
 * <li><b>Ground flight</b>: a sprinting double jump while looking down (25 degrees or more; with the Ring Lab's
 * take-off off, any sprinting double-tap) skims you forward half a block over the ground.
 * It rides up any one-block step; a wall two or more blocks high is met by the running barrier (an
 * invisible 3.5 block dome), which flattens on it and brings you to a quick halt (Ring Lab H1/H2/H3),
 * then you settle into a hover. Let go of forward, jump or sneak to leave it.
 * <li><b>Sonic boom</b>: once each time the fast glide passes 1.1 blocks a tick (re-armed under 0.9).
 * </ul>
 */
public final class FlightMoves {
	/** Ground flight: the barrier's radius, the skim height and the cruising speed (the Blender take's 0.55 blocks a tick). */
	static final double RADIUS = 3.5, SKIM = 0.5, SPEED = 0.55;
	/** How far ahead the skim looks for a step. */
	private static final double LOOK_AHEAD = 1.6;
	/** Ticks of hover after the halt before ground flight hands back to normal flight. */
	private static final int SETTLE = 10;
	/** Sonic boom speeds (blocks a tick): it goes off above BOOM and re-arms below REARM. */
	private static final float BOOM = 1.1f, REARM = 0.9f;

	private enum Mode { NONE, GROUND }

	private static Mode mode = Mode.NONE;
	private static int ticks;
	private static Vec3 heading = new Vec3(0, 0, 1);
	private static double speed, vy;
	/** Ground flight halt: when the barrier hit (-1 for not yet), where you were and how far it carries you. */
	private static int hitTick = -1;
	private static Vec3 hitPos = Vec3.ZERO;
	private static double haltDepth;
	private static int haltTicks;
	private static boolean boomArmed = true;
	private static boolean jumpLifted;

	private FlightMoves() {
	}

	/** True while a take-off, the soft landing or ground flight drives your movement (FastFlight's glide stays out of it). */
	public static boolean controls() {
		return mode != Mode.NONE || TakeoffMoves.controls();
	}

	/** True while skimming in ground flight (vanilla mustn't land you or stop your sprint on a wall). */
	public static boolean grounded() {
		return mode == Mode.GROUND;
	}

	static void tick(Minecraft mc) {
		LocalPlayer p = mc.player;
		if (p == null || mc.level == null) {
			mode = Mode.NONE;
			TakeoffMoves.reset();
			return;
		}
		if (mc.isPaused()) return;
		// The double-jump take-off and the soft landing (they may start ground flight).
		TakeoffMoves.tick(mc, p);
		if (mode == Mode.GROUND) ground(mc, p);
		sonicBoom(mc, p);
	}

	// ---- ground flight ----------------------------------------------------------------------

	/** Starts low ground flight heading dir (TakeoffMoves, on a sprinting double jump). */
	static void groundFlight(LocalPlayer p, Vec3 dir) {
		MovePoseData.load();
		mode = Mode.GROUND;
		ticks = 0;
		heading = dir;
		speed = p.getDeltaMovement().horizontalDistance();
		vy = 0;
		hitTick = -1;
		jumpLifted = false;
		send(MoveFxPayload.GROUND, p.position(), dir, 1f);
	}

	private static void endGround(LocalPlayer p) {
		if (mode != Mode.GROUND) return;
		mode = Mode.NONE;
		send(MoveFxPayload.GROUND, p.position(), heading, 0f);
	}

	private static void ground(Minecraft mc, LocalPlayer p) {
		ticks++;
		boolean halting = hitTick >= 0;
		// The double-tap's own jump press doesn't count: only a fresh one after it lifts you out.
		if (!mc.options.keyJump.isDown()) jumpLifted = true;
		if (!p.getAbilities().flying || p.isInWater() || p.isPassenger() || mc.options.keyShift.isDown() || (jumpLifted && mc.options.keyJump.isDown())
				|| (!halting && !mc.options.keyUp.isDown())) {
			endGround(p);
			return;
		}
		Level level = mc.level;
		Vec3 pos = p.position();
		double surface = surface(level, pos.x, pos.z, pos.y - SKIM);
		if (!halting) {
			// Steer toward where you face, and build up to the cruising speed.
			float yaw = p.getYRot() * Mth.DEG_TO_RAD;
			Vec3 facing = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
			heading = heading.scale(0.85).add(facing.scale(0.15)).normalize();
			speed += (SPEED - speed) * 0.25;
			Wall wall = wall(level, pos, heading, surface, RADIUS + speed);
			if (wall != null && wall.distance <= RADIUS) {
				LabSettings.GroundHalt halt = LabSettings.get().groundHalt;
				MovePoseData.Halt take = MovePoseData.GROUND.get(halt);
				hitTick = ticks;
				hitPos = pos;
				haltTicks = take == null ? 6 : take.stop();
				// Into the barrier, never closer to the wall than half a block.
				double along = Math.max(0.05, Math.abs(heading.dot(wall.normal)));
				haltDepth = Math.min(take == null ? 1.4 : take.depth(), Math.max(0, (wall.distance - 0.6) / along));
				send(MoveFxPayload.GROUND_HIT, wall.contact, wall.normal, halt.ordinal());
				halting = true;
			}
		}
		if (halting) {
			int t = ticks - hitTick;
			if (t > haltTicks + SETTLE) {
				p.setDeltaMovement(Vec3.ZERO);
				endGround(p);
				return;
			}
			// J: "brought to a halt in the same block where my barrier made the impact, as a quick animation".
		}
		Vec3 move;
		if (halting) {
			int t = ticks - hitTick;
			float w = Mth.clamp(t / (float) haltTicks, 0f, 1f);
			Vec3 target = hitPos.add(heading.scale(haltDepth * (1 - (1 - w) * (1 - w))));
			move = new Vec3(target.x - pos.x, 0, target.z - pos.z);
			speed = 0;
		} else {
			move = heading.scale(speed);
		}
		// Skim half a block over the ground, riding up any one-block step ahead (a critically damped spring).
		Vec3 ahead = pos.add(heading.scale(LOOK_AHEAD));
		double target = Math.max(surface, surface(level, ahead.x, ahead.z, surface)) + SKIM;
		vy += (target - pos.y) * 0.35 - vy * 0.75;
		p.setDeltaMovement(new Vec3(move.x, vy, move.z).subtract(vanillaPush(mc, p)));
		p.resetFallDistance();
	}

	/** The top of the ground under x, z: a step up of one block from "from" counts, a wall (two high) doesn't. */
	private static double surface(Level level, double x, double z, double from) {
		int base = Mth.floor(from + 0.01);
		BlockPos.MutableBlockPos at = new BlockPos.MutableBlockPos();
		// A one-block step: the block at your feet' level is solid but the one above it is clear.
		at.set(Mth.floor(x), base, Mth.floor(z));
		if (solid(level, at) && !solid(level, at.above())) return top(level, at);
		if (solid(level, at)) return from;
		for (int y = base - 1; y >= base - 4; y--) {
			at.set(Mth.floor(x), y, Mth.floor(z));
			if (solid(level, at)) return top(level, at);
		}
		// Open air below (a cliff edge): keep your height rather than dive.
		return from;
	}

	private record Wall(double distance, Vec3 contact, Vec3 normal) {
	}

	/** The first wall two or more blocks high ahead within reach, with its face's distance from your middle. */
	private static Wall wall(Level level, Vec3 pos, Vec3 dir, double surface, double reach) {
		int base = Mth.floor(surface + 0.01);
		BlockPos.MutableBlockPos at = new BlockPos.MutableBlockPos();
		Direction face = Math.abs(dir.x) > Math.abs(dir.z) ? (dir.x > 0 ? Direction.WEST : Direction.EAST) : (dir.z > 0 ? Direction.NORTH : Direction.SOUTH);
		Vec3 normal = new Vec3(face.getStepX(), 0, face.getStepZ());
		double mid = pos.y + 0.6;
		for (double d = 0.3; d <= reach + 1; d += 0.25) {
			Vec3 c = pos.add(dir.scale(d));
			at.set(Mth.floor(c.x), base, Mth.floor(c.z));
			if (!solid(level, at) || !solid(level, at.above())) continue;
			// The face of that block toward you, and how far it is from your middle across the face.
			double plane = face.getAxis() == Direction.Axis.X ? at.getX() + (face == Direction.EAST ? 1 : 0) : at.getZ() + (face == Direction.SOUTH ? 1 : 0);
			double coord = face.getAxis() == Direction.Axis.X ? pos.x : pos.z;
			double distance = Math.abs(coord - plane);
			Vec3 contact = face.getAxis() == Direction.Axis.X ? new Vec3(plane, mid, pos.z + dir.z / Math.max(1e-3, Math.abs(dir.x)) * distance)
					: new Vec3(pos.x + dir.x / Math.max(1e-3, Math.abs(dir.z)) * distance, mid, plane);
			return distance <= reach ? new Wall(distance, contact, normal) : null;
		}
		return null;
	}

	private static boolean solid(Level level, BlockPos pos) {
		BlockState state = level.getBlockState(pos);
		return !state.getCollisionShape(level, pos).isEmpty() && state.isSolid();
	}

	private static double top(Level level, BlockPos pos) {
		VoxelShape shape = level.getBlockState(pos).getCollisionShape(level, pos);
		return pos.getY() + (shape.isEmpty() ? 1 : shape.max(Direction.Axis.Y));
	}

	/** The forward push vanilla flight adds next tick for the held movement keys (sprinting doubles it). */
	static Vec3 vanillaPush(Minecraft mc, LocalPlayer p) {
		float f = p.getAbilities().getFlyingSpeed() * (p.isSprinting() ? 2 : 1);
		float fwd = (mc.options.keyUp.isDown() ? 1 : 0) - (mc.options.keyDown.isDown() ? 1 : 0);
		float side = (mc.options.keyLeft.isDown() ? 1 : 0) - (mc.options.keyRight.isDown() ? 1 : 0);
		float len = Mth.sqrt(fwd * fwd + side * side);
		if (len < 1e-3) return Vec3.ZERO;
		fwd /= Math.max(1, len);
		side /= Math.max(1, len);
		float yaw = p.getYRot() * Mth.DEG_TO_RAD;
		double sin = Mth.sin(yaw), cos = Mth.cos(yaw);
		return new Vec3((side * cos - fwd * sin) * f, 0, (fwd * cos + side * sin) * f);
	}

	// ---- sonic boom -------------------------------------------------------------------------

	private static void sonicBoom(Minecraft mc, LocalPlayer p) {
		float glide = FastFlight.isGliding(p) ? FastFlight.speed() : 0f;
		if (glide < REARM) boomArmed = true;
		if (!boomArmed || glide <= BOOM) return;
		boomArmed = false;
		Vec3 dir = p.getDeltaMovement().lengthSqr() > 1e-4 ? p.getDeltaMovement().normalize() : p.getLookAngle();
		SonicBoom.own(p, dir);
		send(MoveFxPayload.BOOM, p.position(), dir, glide);
	}

	private static void send(int action, Vec3 at, Vec3 dir, float value) {
		if (ClientPlayNetworking.canSend(MoveFxPayload.TYPE)) ClientPlayNetworking.send(new MoveFxPayload(action, at, dir, value));
	}
}
