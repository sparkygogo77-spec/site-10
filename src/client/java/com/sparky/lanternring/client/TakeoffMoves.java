package com.sparky.lanternring.client;

import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.net.MoveFxPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * Your own pass 403 take-off and soft landing (Blender designer chat, 2026-10-14). Movement is the local player's, so
 * it runs here; each move is reported (MoveFxPayload TAKEOFF and SOFT_LAND) so every client draws its poses and
 * construct rings (TakeoffFx, MovePoses).
 * <ul>
 * <li><b>Second jump</b>: a jump pressed while airborne from a jump (or vanilla's double-tap switching flight on just
 * off the ground). Under 0.15 blocks a tick across the ground it is the standing puff, at or over it the running dart.
 * <li><b>Standing</b> (Ring Lab "takeoff_stand"): S1 eases up to 3.2 blocks above the jump's ground in 3 ticks
 * ("takeoff_puff"); S2a and S2b are critically damped springs that rise faster and settle at 3.2, never above it.
 * A burst ring, a subtle shake (RingShake.puff), then the hero hover, bobbing 0.07 blocks over 1.5 s.
 * <li><b>Running</b>: the R3 dart, along the horizontal velocity only, flat at 5 blocks 6 ticks after the second jump
 * ("takeoff_arc"), speeding from 0.3 to 0.95 blocks a tick; then it is normal flight at that speed. Sprinting and
 * looking down 25 degrees or more skims the ground in ground flight (FlightMoves) instead.
 * <li><b>Soft landing</b> (L2): double-tap jump while flying within about 5 blocks of the ground. An eased descent
 * (smoothstep, "soft_landing_descent") to a block over the ground at 0.8 slowing to 0.3 blocks a tick, the first jump
 * backwards onto the feet (3 ticks), touchdown with a cushion ring, and a run-out from 0.3 to 0.06 blocks a tick
 * ("soft_landing_runout") easing to a stand.
 * </ul>
 * It never drags (J): the puff and the dart own only their own ticks (steering still turns the dart), the hover ends
 * on any movement input, any flight input cancels the landing's descent back into flight, and any input ends the
 * run-out.
 */
public final class TakeoffMoves {
	/** Horizontal speed (blocks a tick) at the second jump from which it is a running take-off. */
	private static final double RUNNING = 0.15;
	/** Standing: the hover's height above the jump's ground, its bob (blocks), the bob's period (1.5 s) and when it starts after the puff. */
	private static final double HOVER = 3.2, BOB = 0.07;
	private static final int BOB_PERIOD = 30, BOB_FROM = 9;
	/** S2a and S2b: the springs' rate per tick of the 3-tick puff (2.66 and 2.92 blocks up one tick in, from 1.17). */
	private static final double SPRING_A = 2.6, SPRING_B = 3.5;
	/** Running: the dart's flight height over the jump's ground, its speed at the second jump and at the top of the arc. */
	private static final double DART_HEIGHT = 5, DART_FROM = 0.3, DART_TOP = 0.95;
	/** How much of the way to the steering input the dart turns each tick. */
	private static final double STEER = 0.2;
	/** Soft landing: how near the ground a double tap starts it, its speed at the start (at most), at the bottom and at the run-out's end. */
	private static final double LAND_REACH = 5.5, LAND_FROM = 0.8, LAND_SLOW = 0.3, RUN_END = 0.06;
	/** Ticks the run-out takes to ease from its end speed to a stand. */
	private static final int STAND = 8;
	/** The first jump's heights (vanilla's jump one, two and three ticks in), played backwards onto the feet. */
	private static final double[] JUMP_BACK = {1.001, 0.753, 0.42, 0};
	/** Sprinting and looking down at least this far (degrees) at the second jump skims the ground (ground flight). */
	private static final float SKIM_PITCH = 25f;
	/** Ticks after this switched flight on in which vanilla would take a third tap as its double-tap and switch it off. */
	private static final int VANILLA_TAP = 7;
	/** How recently you must have stood on the ground for vanilla switching flight on to count as a second jump. */
	private static final int GROUNDED_WITHIN = 10;

	private enum Mode { NONE, PUFF, HOVER, DART, DESCEND, RUNOUT }

	private static Mode mode = Mode.NONE;
	private static int ticks;
	private static boolean jumpWas, jumpLifted, wasFlying, wasOnGround, jumped;
	private static int sinceGround = 99, ownFlight = -1;
	private static double groundY, fromY, topY;
	private static double speed0;
	private static Vec3 heading = new Vec3(0, 0, 1);
	private static LabSettings.TakeoffStand take = LabSettings.TakeoffStand.S1;

	private TakeoffMoves() {
	}

	/** True while a take-off or the soft landing drives your movement (FastFlight's glide stays out of it). */
	public static boolean controls() {
		return mode != Mode.NONE;
	}

	/** True in the standing take-off's hover (for tests). */
	public static boolean hovering() {
		return mode == Mode.HOVER;
	}

	/** Ticks into the current move, and which move it is (for tests): "puff", "hover", "dart", "descend", "runout" or "none". */
	public static String state() {
		return mode.name().toLowerCase() + " " + ticks;
	}

	static void reset() {
		mode = Mode.NONE;
		wasFlying = wasOnGround = jumped = false;
		ownFlight = -1;
		sinceGround = 99;
	}

	/** Called every client tick (FlightMoves.tick) with your player, after vanilla has moved it. */
	static void tick(Minecraft mc, LocalPlayer p) {
		boolean flying = p.getAbilities().flying;
		boolean jumpDown = mc.options.keyJump.isDown();
		boolean pressed = jumpDown && !jumpWas;
		jumpWas = jumpDown;
		if (!jumpDown) jumpLifted = true;
		if (ownFlight >= 0 && ++ownFlight > VANILLA_TAP) ownFlight = -1;

		boolean grounded = p.onGround() && !flying;
		// The first jump: leaving the ground on the way up with jump held (its own press isn't the second jump).
		boolean firstJump = !grounded && wasOnGround && !flying && jumpDown && p.getDeltaMovement().y > 0;
		if (firstJump) jumped = true;
		if (grounded) {
			groundY = p.getY();
			sinceGround = 0;
			jumped = false;
		} else {
			sinceGround++;
		}
		boolean toggledOn = flying && !wasFlying, toggledOff = !flying && wasFlying;
		wasOnGround = grounded;

		if (toggledOff && pressed) {
			if (ownFlight >= 0 || mode == Mode.PUFF || mode == Mode.DART) {
				// Vanilla counted our second jump as the first tap of its double-tap, or the take-off still owns
				// these ticks: stay in flight.
				setFlying(p, true);
				flying = true;
			} else if ((mode == Mode.NONE || mode == Mode.HOVER) && able(p)) {
				Double ground = groundBelow(p, LAND_REACH);
				if (ground != null) {
					setFlying(p, true);
					flying = true;
					startLanding(mc, p, ground);
				}
			}
		}
		wasFlying = flying;

		switch (mode) {
			case PUFF, HOVER -> standing(mc, p);
			case DART -> dart(mc, p);
			case DESCEND -> descend(mc, p);
			case RUNOUT -> runOut(mc, p);
			case NONE -> {
			}
		}
		if (mode != Mode.NONE || FlightMoves.controls() || !able(p) || SuperJumpInput.airborne()) return;

		double across = Math.hypot(p.getX() - p.xo, p.getZ() - p.zo);
		Vec3 flat = new Vec3(p.getDeltaMovement().x, 0, p.getDeltaMovement().z);
		float yaw = p.getYRot() * Mth.DEG_TO_RAD;
		Vec3 dir = flat.lengthSqr() > 1e-4 ? flat.normalize() : new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
		if (LabSettings.get().takeoff == LabSettings.Takeoff.OFF) {
			// Take-offs switched off: vanilla flight, and the older sprinting double-tap into ground flight.
			if (toggledOn && sinceGround <= GROUNDED_WITHIN && p.isSprinting() && across > 0.1) FlightMoves.groundFlight(p, dir);
			return;
		}
		boolean second = !p.onGround() && !firstJump && (jumped && (pressed || toggledOn) || toggledOn && sinceGround <= GROUNDED_WITHIN);
		if (!second || !flying && !p.getAbilities().mayfly) return;
		if (!flying) {
			setFlying(p, true);
			ownFlight = 0;
		}
		jumped = false;
		jumpLifted = false;
		if (across < RUNNING) {
			startStanding(mc, p);
		} else if (p.isSprinting() && p.getXRot() >= SKIM_PITCH) {
			FlightMoves.groundFlight(p, dir);
		} else {
			startDart(mc, p, dir);
		}
	}

	// ---- standing: the puff and the hero hover ---------------------------------------------

	private static void startStanding(Minecraft mc, LocalPlayer p) {
		mode = Mode.PUFF;
		ticks = 0;
		take = LabSettings.get().takeoffStand;
		fromY = p.getY();
		topY = Math.max(fromY, groundY + HOVER);
		RingShake.puff();
		float yaw = p.getYRot() * Mth.DEG_TO_RAD;
		send(MoveFxPayload.TAKEOFF, p.position(), new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw)), 1 + take.ordinal());
		standing(mc, p);
	}

	private static void standing(Minecraft mc, LocalPlayer p) {
		if (!p.getAbilities().flying || p.isInWater() || p.isPassenger()) {
			mode = Mode.NONE;
			return;
		}
		int puff = Math.max(1, RingTuning.TAKEOFF_PUFF.ticks());
		if (mode == Mode.HOVER && moving(mc)) {
			// Any movement input: ordinary flight from here, on your own input.
			mode = Mode.NONE;
			return;
		}
		// Held back by a ceiling: hover where you are.
		if (ticks > 0 && p.getY() < target(ticks, puff) - 0.4) topY = fromY = p.getY();
		ticks++;
		if (mode == Mode.PUFF && ticks >= puff) mode = Mode.HOVER;
		double y = target(ticks, puff);
		if (ticks >= puff + BOB_FROM) y += BOB * Math.sin(Math.PI * 2 * (ticks - puff - BOB_FROM) / BOB_PERIOD);
		// The puff owns its ticks: the movement keys don't push you about until the hover.
		p.setDeltaMovement(new Vec3(0, y - p.getY(), 0).subtract(FlightMoves.vanillaPush(mc, p)).subtract(0, lift(mc, p), 0));
		p.resetFallDistance();
	}

	/** The standing take's height after t ticks: S1 eases out over the puff, S2a and S2b spring up and settle. */
	private static double target(int t, int puff) {
		double u = t / (double) puff;
		double f = switch (take) {
			case S1 -> {
				double v = 1 - Math.min(1, u);
				yield 1 - v * v * v;
			}
			case S2A -> spring(SPRING_A * 3 * u);
			case S2B -> spring(SPRING_B * 3 * u);
		};
		return fromY + (topY - fromY) * f;
	}

	/** A critically damped spring's way to its rest, k rates in: it never overshoots. */
	private static double spring(double k) {
		return 1 - (1 + k) * Math.exp(-k);
	}

	// ---- running: the R3 dart ----------------------------------------------------------------

	private static void startDart(Minecraft mc, LocalPlayer p, Vec3 dir) {
		mode = Mode.DART;
		ticks = 0;
		heading = dir;
		fromY = p.getY();
		topY = Math.max(fromY, groundY + DART_HEIGHT);
		send(MoveFxPayload.TAKEOFF, p.position(), dir, 4);
		dart(mc, p);
	}

	private static void dart(Minecraft mc, LocalPlayer p) {
		if (!p.getAbilities().flying || p.isInWater() || p.isPassenger() || ticks > 0 && p.horizontalCollision) {
			mode = Mode.NONE;
			return;
		}
		int arc = Math.max(1, RingTuning.TAKEOFF_ARC.ticks());
		ticks++;
		// Steering still turns the arc's velocity: it never drags you somewhere you don't want to go.
		Vec3 wish = wish(mc, p);
		if (wish != null) {
			Vec3 turned = heading.scale(1 - STEER).add(wish.scale(STEER));
			if (turned.lengthSqr() > 1e-4) heading = turned.normalize();
		}
		double u = Math.min(1, ticks / (double) arc);
		double speed = DART_FROM + (DART_TOP - DART_FROM) * SuperJumpPoses.smooth((float) u);
		double y = fromY + (topY - fromY) * u;
		p.setDeltaMovement(heading.scale(speed).add(0, y - p.getY(), 0).subtract(FlightMoves.vanillaPush(mc, p)).subtract(0, lift(mc, p), 0));
		p.resetFallDistance();
		// Flat at the top of the arc: normal flight from the next tick, carrying the dart's speed.
		if (ticks >= arc) mode = Mode.NONE;
	}

	// ---- the L2 soft landing -------------------------------------------------------------------

	private static void startLanding(Minecraft mc, LocalPlayer p, double ground) {
		mode = Mode.DESCEND;
		ticks = 0;
		groundY = ground;
		fromY = p.getY();
		Vec3 flat = new Vec3(p.getDeltaMovement().x, 0, p.getDeltaMovement().z);
		float yaw = p.getYRot() * Mth.DEG_TO_RAD;
		heading = flat.length() > 0.05 ? flat.normalize() : new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
		speed0 = Mth.clamp(flat.length(), LAND_SLOW, LAND_FROM);
		jumpLifted = false;
		send(MoveFxPayload.SOFT_LAND, p.position(), heading, 1);
		descend(mc, p);
	}

	private static void descend(Minecraft mc, LocalPlayer p) {
		if (p.isInWater() || p.isPassenger()) {
			mode = Mode.NONE;
			return;
		}
		if (moving(mc)) {
			// Any flight input cancels it back into flight.
			mode = Mode.NONE;
			send(MoveFxPayload.SOFT_LAND, p.position(), heading, 0);
			return;
		}
		int down = Math.max(1, RingTuning.SOFT_LANDING_DESCENT.ticks());
		if (!p.getAbilities().flying || p.onGround() || ticks >= down + JUMP_BACK.length - 1) {
			touchdown(p);
			return;
		}
		ticks++;
		// The ground may rise under you on the way (a slope, a step): never aim below it.
		Double ground = groundBelow(p, Math.max(2, p.getY() - groundY + 1));
		if (ground != null && ground > groundY) groundY = ground;
		double low = groundY + Mth.clamp(fromY - groundY, 0, JUMP_BACK[0]);
		double y, speed;
		if (ticks <= down) {
			double s = SuperJumpPoses.smooth(ticks / (float) down);
			y = low + (Math.max(fromY, low) - low) * (1 - s);
			speed = speed0 + (LAND_SLOW - speed0) * s;
		} else {
			int k = Math.min(ticks - down, JUMP_BACK.length - 1);
			y = groundY + (low - groundY) * JUMP_BACK[k] / JUMP_BACK[0];
			speed = LAND_SLOW;
		}
		if (p.horizontalCollision) speed0 = speed = 0;
		p.setDeltaMovement(heading.scale(speed).add(0, y - p.getY(), 0).subtract(FlightMoves.vanillaPush(mc, p)).subtract(0, lift(mc, p), 0));
		p.resetFallDistance();
	}

	private static void touchdown(LocalPlayer p) {
		setFlying(p, false);
		mode = Mode.RUNOUT;
		ticks = 0;
		send(MoveFxPayload.SOFT_LAND, p.position(), heading, 2);
	}

	private static void runOut(Minecraft mc, LocalPlayer p) {
		int run = RingTuning.SOFT_LANDING_RUNOUT.ticks();
		if (moving(mc) || p.isInWater() || p.isPassenger() || p.getAbilities().flying || ticks > 0 && p.horizontalCollision || ticks >= run + STAND) {
			mode = Mode.NONE;
			return;
		}
		ticks++;
		// The legs run it out forwards, from 0.3 down to 0.06 blocks a tick, then ease to a stand.
		double speed = ticks <= run ? LAND_SLOW - (LAND_SLOW - RUN_END) * ticks / run
				: RUN_END * (1 - SuperJumpPoses.smooth((ticks - run) / (float) STAND));
		p.setDeltaMovement(heading.scale(speed).add(0, p.getDeltaMovement().y, 0));
	}

	// ---- helpers -------------------------------------------------------------------------------

	private static boolean able(LocalPlayer p) {
		return FlightPoses.carriesRing(p) && !p.isInWater() && !p.isPassenger() && !p.isSpectator() && !p.isFallFlying();
	}

	/** Any movement input: the movement keys, sneak, or a jump pressed again after the one that started the move. */
	private static boolean moving(Minecraft mc) {
		var o = mc.options;
		return o.keyUp.isDown() || o.keyDown.isDown() || o.keyLeft.isDown() || o.keyRight.isDown() || o.keyShift.isDown()
				|| jumpLifted && o.keyJump.isDown();
	}

	/** Where the movement keys point across the ground, or null with none held. */
	private static Vec3 wish(Minecraft mc, LocalPlayer p) {
		float forward = (mc.options.keyUp.isDown() ? 1 : 0) - (mc.options.keyDown.isDown() ? 1 : 0);
		float strafe = (mc.options.keyLeft.isDown() ? 1 : 0) - (mc.options.keyRight.isDown() ? 1 : 0);
		if (forward == 0 && strafe == 0) return null;
		float yaw = p.getYRot() * Mth.DEG_TO_RAD;
		Vec3 ahead = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
		Vec3 left = new Vec3(Mth.cos(yaw), 0, Mth.sin(yaw));
		return ahead.scale(forward).add(left.scale(strafe)).normalize();
	}

	/** The rise or fall vanilla flight adds next tick for held jump or sneak; taken out so the move is ours. */
	private static double lift(Minecraft mc, LocalPlayer p) {
		if (!p.getAbilities().flying) return 0;
		int i = (mc.options.keyJump.isDown() ? 1 : 0) - (mc.options.keyShift.isDown() ? 1 : 0);
		return i * p.getAbilities().getFlyingSpeed() * 3;
	}

	/** The top of the ground within reach blocks under your feet, or null. */
	private static Double groundBelow(LocalPlayer p, double reach) {
		Vec3 from = p.position().add(0, 0.05, 0);
		BlockHitResult hit = p.level().clip(new ClipContext(from, from.subtract(0, reach, 0), ClipContext.Block.COLLIDER, ClipContext.Fluid.ANY, p));
		return hit.getType() == HitResult.Type.MISS ? null : hit.getLocation().y;
	}

	private static void setFlying(LocalPlayer p, boolean on) {
		if (p.getAbilities().flying == on) return;
		p.getAbilities().flying = on;
		p.onUpdateAbilities();
	}

	private static void send(int action, Vec3 at, Vec3 dir, float value) {
		if (ClientPlayNetworking.canSend(MoveFxPayload.TYPE)) ClientPlayNetworking.send(new MoveFxPayload(action, at, dir, value));
	}
}
