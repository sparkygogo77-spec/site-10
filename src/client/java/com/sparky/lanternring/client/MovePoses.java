package com.sparky.lanternring.client;

import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingTuning;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * Third person: J's movement and flight poses from Blender (hand-off 2026-10-14-movement-flight), for
 * every player:
 * <ul>
 * <li>the sprint run with the ring in hand: S1's ring fist held out in front, the free arm pumping, or
 * with the lantern in the off hand S5a/S5b carrying it by the handle (Ring Lab "Sprint: lantern carry
 * height"). The stride is driven by distance (3.36 blocks a stride), so the legs never slide;
 * <li>the F2 rocket takeoff (FlightMoves starts it, the server passes it on to everyone);
 * <li>low ground flight laid out flat, and its brace and settle when the barrier hits a wall;
 * <li>the power landing (pass 400, PowerLandings): D0 stop dead, or the A3 / B2 one-foot skid, its
 * slide part stretched to the slide's own ticks;
 * <li>pass 403's double-jump take-off (the standing puff into the hero hover, or the R3 dart) and the L2 soft
 * landing (TakeoffMoves starts them; TakeoffPoseData holds the poses), each part stretched to its Ring Lab duration.
 * </ul>
 * The model has no shins, so each leg is one bend (tools/movement_flight_poses.py). The neck bends at
 * most a radian back from the body (J, F3).
 */
public final class MovePoses {
	/** Blocks a stride covers (the data's 12-tick stride at 0.28 blocks a tick). */
	private static final float STRIDE = 3.36f;
	/** The takeoff is level from this index of F2 (Blender tick 57); it hands over to the flight poses after it. */
	private static final int TAKEOFF_LEVEL = 33;
	private static final float TAKEOFF_OUT = 6f;
	/** Ground flight: index of the flat skim pose (Blender tick 25), and ticks to ease back out after it ends. */
	private static final int SKIM = 10;
	private static final float GROUND_OUT = 10f;
	/** The neck bends at most this far back from the body (J's head fix, F3). */
	static final float NECK = 1.0f;
	/** The lantern's grip: a stiff, well damped wobble capped near 22 degrees (Blender pass 227). */
	private static final float GRIP = 260f, CAP = 0.38f;
	/** The power landing: ticks after the slide (or touchdown) until it has stood up, and to ease out after. */
	private static final float POWER_STAND = 28f, POWER_OUT = 6f;
	/** Pass 403: ticks to ease out of the hover, the dart (after it is laid out) and the soft landing. */
	private static final float HOP_OUT = 6f, DART_HOLD = 4f, DART_OUT = 4f, LAND_OUT = 6f;

	private static final class Track {
		float phase;
		float run, prevRun;
		float phi, om, prevPhi;
		float handZ0 = Float.NaN, handZ1 = Float.NaN;
		double lastForward;
		long takeoffAt = -1;
		long groundAt = -1, hitAt = -1, groundEnd = -1;
		LabSettings.GroundHalt halt = LabSettings.GroundHalt.H2;
		/** The power landing: when, its take ("A3", "B2", "D0"), its slide's ticks, and when it was cut short by walking off. */
		long powerAt = -1, powerOut = -1;
		String powerTake = "D0";
		int powerSlide;
		/** Pass 403: the standing puff (and when its hover was left), the dart, and the soft landing (touchdown, cut short). */
		long hopAt = -1, hopOut = -1, dartAt = -1, landAt = -1, touchAt = -1, landOut = -1;
		/** Pass 405: the double-tap landing's take (L5, L4, L6). */
		TakeoffPoseData.Land land = TakeoffPoseData.NO_LAND;
		boolean seen;
	}

	private static final Int2ObjectMap<Track> TRACKS = new Int2ObjectOpenHashMap<>();
	/** The ring arm as last posed (x, y, z, xRot, yRot, zRot, game time mod 100000), for where the fist is. */
	private static final Int2ObjectMap<float[]> ARMS = new Int2ObjectOpenHashMap<>();

	private MovePoses() {
	}

	static void tick(Minecraft mc) {
		ArmLeadPoses.tick(mc);
		if (mc.level == null) {
			TRACKS.clear();
			ARMS.clear();
			return;
		}
		MovePoseData.load();
		long time = mc.level.getGameTime();
		for (Track t : TRACKS.values()) t.seen = false;
		for (AbstractClientPlayer p : mc.level.players()) {
			Track t = TRACKS.computeIfAbsent(p.getId(), id -> new Track());
			t.seen = true;
			update(t, p, time);
		}
		TRACKS.values().removeIf(t -> !t.seen);
		ARMS.keySet().removeIf(id -> !TRACKS.containsKey((int) id));
	}

	private static void update(Track t, Player p, long time) {
		double dx = p.getX() - p.xo, dz = p.getZ() - p.zo;
		float speed = (float) Math.sqrt(dx * dx + dz * dz);
		t.phase = (t.phase + speed / STRIDE) % 1f;
		t.prevRun = t.run;
		t.run = approach(t.run, runs(p) ? 1f : 0f, 0.25f);

		// A ground flight that was never closed (a lost packet) ends once they're standing.
		if (t.groundAt >= 0 && t.groundEnd < 0 && p.onGround() && time - t.groundAt > 10) t.groundEnd = time;
		if (t.groundEnd >= 0 && time - t.groundEnd > GROUND_OUT + 2) t.groundAt = t.hitAt = t.groundEnd = -1;
		if (t.takeoffAt >= 0 && time - t.takeoffAt > MovePoseData.takeoff.length + 5) t.takeoffAt = -1;
		if (t.hopAt >= 0) {
			long age = time - t.hopAt;
			// The hover holds until they move off it (or land), then hands over to the flight poses.
			if (t.hopOut < 0 && age > RingTuning.TAKEOFF_PUFF.ticks() + 1
					&& (speed > 0.08f || Math.abs(p.getY() - p.yo) > 0.12 || p.onGround())) t.hopOut = time;
			if (t.hopOut >= 0 && time - t.hopOut > HOP_OUT + 2) t.hopAt = t.hopOut = -1;
		}
		if (t.dartAt >= 0 && time - t.dartAt > RingTuning.TAKEOFF_ARC.ticks() + DART_HOLD + DART_OUT + 2) t.dartAt = -1;
		if (t.landAt >= 0) {
			long age = time - t.landAt;
			int after = t.land.poses().length - 1 - t.land.touch();
			// A touchdown that never came (a lost packet) lets go; walking off after the absorb crouch eases out.
			if (t.touchAt < 0 && t.landOut < 0 && age > t.land.touch() + 20) t.landOut = time;
			if (t.touchAt >= 0 && t.landOut < 0 && time - t.touchAt > 2 && speed > 0.08f) t.landOut = time;
			if (t.landOut >= 0 && time - t.landOut > LAND_OUT + 2 || t.touchAt >= 0 && time - t.touchAt > after + LAND_OUT + 2) {
				t.landAt = t.touchAt = t.landOut = -1;
			}
		}
		if (t.powerAt >= 0) {
			long age = time - t.powerAt;
			// Walking off once it lets go of you cuts the stand-up short.
			if (t.powerOut < 0 && age > t.powerSlide + 8 && speed > 0.08f) t.powerOut = time;
			if (age > t.powerSlide + POWER_STAND + POWER_OUT + 2 || t.powerOut >= 0 && time - t.powerOut > POWER_OUT + 2) t.powerAt = t.powerOut = -1;
		}

		// The gripped lantern wobbles against the carrying hand's motion and the body's speeding up.
		t.prevPhi = t.phi;
		if (t.run > 0.01f && lantern(p) != null) {
			float[][] pose = sprint(t.phase, true);
			float z = pose[3][5] + 10f * Mth.sin(pose[3][0]);
			float yaw = p.yBodyRot * Mth.DEG_TO_RAD;
			double forward = dx * -Mth.sin(yaw) + dz * Mth.cos(yaw);
			float a = 0f;
			if (!Float.isNaN(t.handZ1)) a = (z - 2 * t.handZ0 + t.handZ1) * 400f;
			// Speeding up pushes the hand forward (-z): the lantern lags back.
			a -= (float) (forward - t.lastForward) * 16f * 400f;
			t.handZ1 = t.handZ0;
			t.handZ0 = z;
			t.lastForward = forward;
			float lc = 7f, g = 9.81f * 16f;
			float damp = 2f * 0.55f * Mth.sqrt(g / lc + GRIP);
			for (int i = 0; i < 20; i++) {
				float al = -(g / lc) * Mth.sin(t.phi) - (a / lc) * Mth.cos(t.phi) - GRIP * t.phi - damp * t.om;
				t.om += al / 400f;
				t.phi = Mth.clamp(t.phi + t.om / 400f, -CAP, CAP);
			}
		} else {
			t.phi *= 0.7f;
			t.om = 0f;
			t.handZ0 = t.handZ1 = Float.NaN;
		}
	}

	/** Sprinting on foot with the ring in a hand. */
	private static boolean runs(Player p) {
		return p.isSprinting() && !p.getAbilities().flying && !p.isFallFlying() && !p.isInWater() && !p.isPassenger()
				&& !p.isSpectator() && (FlightPoses.isRing(p.getMainHandItem()) || FlightPoses.isRing(p.getOffhandItem()));
	}

	/** The hand carrying the lantern (the one without the ring), or null. */
	private static HumanoidArm lantern(Player p) {
		boolean ringMain = FlightPoses.isRing(p.getMainHandItem());
		ItemStack other = ringMain ? p.getOffhandItem() : p.getMainHandItem();
		if (!other.is(ModRegistry.POWER_BATTERY_ITEM)) return null;
		return ringMain ? p.getMainArm().getOpposite() : p.getMainArm();
	}

	/** 0..1: how far this player is in the sprint run (for SuperJumpPoses' older lean to step aside). */
	static float runWeight(int id) {
		Track t = TRACKS.get(id);
		return t == null ? 0f : t.run;
	}

	/** For LanternCarry: how far the sprint grip replaces the walking sway (x), and the lantern's tilt in degrees (y). */
	static float[] lanternGrip(int id, float partial) {
		Track t = TRACKS.get(id);
		if (t == null) return new float[] {0f, 0f};
		return new float[] {Mth.lerp(partial, t.prevRun, t.run), Mth.lerp(partial, t.prevPhi, t.phi) * Mth.RAD_TO_DEG};
	}

	static void takeoff(int id) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		TRACKS.computeIfAbsent(id, k -> new Track()).takeoffAt = mc.level.getGameTime();
	}

	static void ground(int id, boolean start) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		Track t = TRACKS.computeIfAbsent(id, k -> new Track());
		long now = mc.level.getGameTime();
		if (start) {
			t.groundAt = now;
			t.hitAt = t.groundEnd = -1;
			t.takeoffAt = t.hopAt = t.dartAt = t.landAt = t.touchAt = -1;
		} else if (t.groundAt >= 0 && t.groundEnd < 0) {
			t.groundEnd = now;
		}
	}

	static void hit(int id, LabSettings.GroundHalt halt) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		Track t = TRACKS.computeIfAbsent(id, k -> new Track());
		if (t.groundAt < 0) t.groundAt = mc.level.getGameTime() - SKIM;
		t.hitAt = mc.level.getGameTime();
		t.halt = halt;
	}

	/** Pass 403's standing puff into the hero hover. */
	static void hop(int id) {
		Track t = fresh(id);
		if (t == null) return;
		t.hopAt = Minecraft.getInstance().level.getGameTime();
	}

	/** Pass 403's R3 running dart. */
	static void dart(int id) {
		Track t = fresh(id);
		if (t == null) return;
		t.dartAt = Minecraft.getInstance().level.getGameTime();
	}

	/** The pass 405 double-tap landing starts at the tap, in take "take". */
	static void land(int id, LabSettings.SoftLanding take) {
		Track t = fresh(id);
		if (t == null) return;
		t.landAt = Minecraft.getInstance().level.getGameTime();
		t.land = TakeoffPoseData.land(take);
	}

	/** The pass 405 landing touches down: the absorb crouch and the stand follow. */
	static void touchdown(int id) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		Track t = TRACKS.computeIfAbsent(id, k -> new Track());
		long now = mc.level.getGameTime();
		if (t.landAt < 0) {
			TakeoffPoseData.load();
			t.land = TakeoffPoseData.land(LabSettings.SoftLanding.L4);
			t.landAt = now - t.land.touch();
		}
		t.touchAt = now;
		t.landOut = -1;
	}

	/** The pass 405 landing was cancelled back into flight. */
	static void landCancelled(int id) {
		Minecraft mc = Minecraft.getInstance();
		Track t = TRACKS.get(id);
		if (t == null || mc.level == null || t.landAt < 0 || t.landOut >= 0) return;
		t.landOut = mc.level.getGameTime();
	}

	/** This player's track with every other move cleared, for a pass 403 move starting now (null with no level). */
	private static Track fresh(int id) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return null;
		TakeoffPoseData.load();
		Track t = TRACKS.computeIfAbsent(id, k -> new Track());
		t.takeoffAt = t.groundAt = t.hitAt = t.groundEnd = t.powerAt = t.powerOut = -1;
		t.hopAt = t.hopOut = t.dartAt = t.landAt = t.touchAt = t.landOut = -1;
		return t;
	}

	/** 0..1: how far a flight move holds this player (take-offs, ground flight, the soft landing until touchdown), for the arm lead. */
	static float flightMove(int id, float partial) {
		Minecraft mc = Minecraft.getInstance();
		Track t = TRACKS.get(id);
		if (t == null || mc.level == null) return 0f;
		float now = mc.level.getGameTime() + partial;
		float land = landWeight(t, now);
		if (t.touchAt >= 0) land *= 1f - SuperJumpPoses.smooth((now - t.touchAt) / 3f);
		return Math.max(Math.max(hopWeight(t, now), dartWeight(t, now)), Math.max(land, Math.max(takeoffWeight(t, now), groundWeight(t, now))));
	}

	/** 0..1: how far this player is laid out along their flight in a pass 403 dart or soft landing (the body then follows the flight). */
	static float laidOut(int id, float partial) {
		Minecraft mc = Minecraft.getInstance();
		Track t = TRACKS.get(id);
		if (t == null || mc.level == null) return 0f;
		float now = mc.level.getGameTime() + partial;
		return Math.max(dartWeight(t, now), landWeight(t, now));
	}

	/** A power landing (POWER_LAND): take is PowerLandings' STOP, DISSOLVE or PLOUGH, slide its ticks. */
	static void power(int id, int take, int slide) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		PowerLandingData.load();
		Track t = TRACKS.computeIfAbsent(id, k -> new Track());
		t.powerAt = mc.level.getGameTime();
		t.powerOut = -1;
		t.powerTake = take == com.sparky.lanternring.PowerLandings.PLOUGH ? "B2" : take == com.sparky.lanternring.PowerLandings.DISSOLVE ? "A3" : "D0";
		t.powerSlide = take == com.sparky.lanternring.PowerLandings.STOP ? 0 : slide;
		t.takeoffAt = t.groundAt = t.hitAt = t.groundEnd = -1;
		t.hopAt = t.dartAt = t.landAt = t.touchAt = -1;
	}

	/**
	 * 0..1: how far a takeoff or ground flight pose holds this player, so FlightPoses' own flight pose
	 * steps aside for it.
	 */
	static float override(int id, float partial) {
		Minecraft mc = Minecraft.getInstance();
		Track t = TRACKS.get(id);
		if (t == null || mc.level == null) return 0f;
		float now = mc.level.getGameTime() + partial;
		float moves = Math.max(hopWeight(t, now), Math.max(dartWeight(t, now), landWeight(t, now)));
		return Math.max(Math.max(Math.max(takeoffWeight(t, now), groundWeight(t, now)), powerWeight(t, now)), moves);
	}

	private static float hopWeight(Track t, float now) {
		if (t.hopAt < 0) return 0f;
		float age = now - t.hopAt;
		if (age < 0) return 0f;
		float w = SuperJumpPoses.smooth((age + 1f) / 2f);
		if (t.hopOut >= 0) w *= 1f - SuperJumpPoses.smooth((now - t.hopOut) / HOP_OUT);
		return w;
	}

	private static float dartWeight(Track t, float now) {
		if (t.dartAt < 0) return 0f;
		float age = now - t.dartAt;
		if (age < 0) return 0f;
		return SuperJumpPoses.smooth((age + 1f) / 1.5f) * (1f - SuperJumpPoses.smooth((age - RingTuning.TAKEOFF_ARC.ticks() - DART_HOLD) / DART_OUT));
	}

	private static float landWeight(Track t, float now) {
		if (t.landAt < 0) return 0f;
		float age = now - t.landAt;
		if (age < 0) return 0f;
		float w = SuperJumpPoses.smooth((age + 1f) / 3f);
		if (t.landOut >= 0) w *= 1f - SuperJumpPoses.smooth((now - t.landOut) / LAND_OUT);
		if (t.touchAt >= 0) {
			float stood = now - t.touchAt - (t.land.poses().length - 1 - t.land.touch());
			w *= 1f - SuperJumpPoses.smooth(stood / LAND_OUT);
		}
		return w;
	}

	/** Where in its take each pass 403 move is: the part before the hover, arc or touchdown stretched to its Ring Lab duration. */
	private static float hopIndex(Track t, float now) {
		float age = now - t.hopAt;
		int puff = Math.max(1, RingTuning.TAKEOFF_PUFF.ticks());
		return age < puff ? age * TakeoffPoseData.STAND_TOP / puff : TakeoffPoseData.STAND_TOP + age - puff;
	}

	private static float dartIndex(Track t, float now) {
		float age = now - t.dartAt;
		int arc = Math.max(1, RingTuning.TAKEOFF_ARC.ticks());
		return age < arc ? age * TakeoffPoseData.DART_TOP / arc : TakeoffPoseData.DART_TOP + age - arc;
	}

	private static float landIndex(Track t, float now) {
		// The drop holds the touchdown pose until the ground is really there; the crouch and the stand play from it.
		if (t.touchAt < 0) return Math.min(now - t.landAt, t.land.touch());
		return t.land.touch() + now - t.touchAt;
	}

	private static float powerWeight(Track t, float now) {
		if (t.powerAt < 0) return 0f;
		float age = now - t.powerAt;
		if (age < 0) return 0f;
		float w = SuperJumpPoses.smooth(age + 0.5f);
		w *= 1f - SuperJumpPoses.smooth((age - t.powerSlide - POWER_STAND) / POWER_OUT);
		if (t.powerOut >= 0) w *= 1f - SuperJumpPoses.smooth((now - t.powerOut) / POWER_OUT);
		return w;
	}

	private static float takeoffWeight(Track t, float now) {
		if (t.takeoffAt < 0) return 0f;
		float age = now - t.takeoffAt;
		if (age < 0) return 0f;
		return SuperJumpPoses.smooth(age / 2f) * (1f - SuperJumpPoses.smooth((age - TAKEOFF_LEVEL) / TAKEOFF_OUT));
	}

	private static float groundWeight(Track t, float now) {
		if (t.groundAt < 0) return 0f;
		float age = now - t.groundAt;
		if (age < 0) return 0f;
		float w = SuperJumpPoses.smooth(age / 3f);
		if (t.groundEnd >= 0) w *= 1f - SuperJumpPoses.smooth((now - t.groundEnd) / GROUND_OUT);
		return w;
	}

	public static void pose(PlayerModel model, AvatarRenderState state) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null || !(mc.level.getEntity(state.id) instanceof Player player)) return;
		Track t = TRACKS.get(player.getId());
		if (t != null) posed(model, state, player, t, mc);
		// Where the ring arm ended up, so the flight trail can come off the fist.
		ModelPart arm = ringRight(state, player) ? model.rightArm : model.leftArm;
		ARMS.put(player.getId(), new float[] {arm.x, arm.y, arm.z, arm.xRot, arm.yRot, arm.zRot, mc.level.getGameTime() % 100000});
	}

	private static void posed(PlayerModel model, AvatarRenderState state, Player player, Track t, Minecraft mc) {
		boolean right = ringRight(state, player);
		float partial = mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
		float now = mc.level.getGameTime() + partial;
		boolean posed = false;

		float take = takeoffWeight(t, now);
		float ground = groundWeight(t, now);
		float power = powerWeight(t, now);
		float hop = hopWeight(t, now), dart = dartWeight(t, now), land = landWeight(t, now);
		PowerLandingData.Take landing = PowerLandingData.TAKES.get(t.powerTake);
		if (power > 0f && landing != null && landing.ticks().length > 0) {
			// The slide part of the take (its first slide ticks) stretched to this slide's own ticks.
			float age = now - t.powerAt;
			float index = t.powerSlide > 0 && age < t.powerSlide ? age * landing.slide() / t.powerSlide
					: age + (t.powerSlide > 0 ? landing.slide() - t.powerSlide : 0);
			SuperJumpPoses.apply(model, right, at(landing.ticks(), index), power);
			posed = true;
		} else if (land > 0f && t.land.poses().length > 0) {
			SuperJumpPoses.apply(model, right, TakeoffPoseData.at(t.land.poses(), landIndex(t, now)), land);
			posed = true;
		} else if (dart > 0f && TakeoffPoseData.dart.length > 0) {
			SuperJumpPoses.apply(model, right, TakeoffPoseData.dart(dartIndex(t, now), LabSettings.get().freeArm), dart);
			posed = true;
		} else if (hop > 0f && TakeoffPoseData.stand.length > 0) {
			SuperJumpPoses.apply(model, right, TakeoffPoseData.at(TakeoffPoseData.stand, hopIndex(t, now)), hop);
			posed = true;
		} else if (take > 0f && MovePoseData.takeoff.length > 0) {
			SuperJumpPoses.apply(model, right, at(MovePoseData.takeoff, now - t.takeoffAt), take);
			posed = true;
		} else if (ground > 0f) {
			MovePoseData.Halt halt = MovePoseData.GROUND.get(t.halt);
			if (halt != null) {
				float index = t.hitAt >= 0 ? halt.hit() + (now - t.hitAt) : Math.min(now - t.groundAt, SKIM);
				SuperJumpPoses.apply(model, right, at(halt.ticks(), index), ground);
				posed = true;
			}
		}
		if (!posed) {
			float run = Mth.lerp(partial, t.prevRun, t.run);
			if (run > 0.01f && !MovePoseData.SPRINT.isEmpty()) {
				float phase = t.phase + (float) Math.sqrt(Math.pow(player.getX() - player.xo, 2) + Math.pow(player.getZ() - player.zo, 2)) * partial / STRIDE;
				SuperJumpPoses.apply(model, right, sprint(phase % 1f, lantern(player) != null), run);
				posed = true;
			}
		}
		// J (F3): the neck bends at most about 57 degrees back from the body.
		if (posed) model.head.xRot = Math.max(model.head.xRot, model.body.xRot - NECK);
	}

	/** The sprint at this point of the stride: S5a/S5b, or with no lantern S1's free arm pumping. */
	private static float[][] sprint(float phase, boolean lantern) {
		float[][][] stride = MovePoseData.SPRINT.get(LabSettings.get().sprintCarry);
		if (stride == null || stride.length == 0) return new float[6][6];
		float i = phase * stride.length;
		int a = Mth.floor(i) % stride.length;
		float[][] pose = SuperJumpPoses.mix(stride[a], stride[(a + 1) % stride.length], i - Mth.floor(i));
		if (!lantern) {
			// S1 (Blender pass 214): the free arm pumps against the ring leg.
			float swing = Mth.sin(phase * Mth.TWO_PI);
			pose[3][0] = 0.15f - 0.95f * swing;
			pose[3][1] = 0f;
			pose[3][2] = 0.08f;
		}
		return pose;
	}

	/** The take at a fractional index, held on its last tick. */
	private static float[][] at(MovePoseData.Tick[] ticks, float index) {
		float i = Mth.clamp(index, 0f, ticks.length - 1);
		int a = Mth.floor(i);
		int b = Math.min(a + 1, ticks.length - 1);
		return SuperJumpPoses.mix(ticks[a].pose(), ticks[b].pose(), i - a);
	}

	private static float[][] at(float[][][] ticks, float index) {
		float i = Mth.clamp(index, 0f, ticks.length - 1);
		int a = Mth.floor(i);
		int b = Math.min(a + 1, ticks.length - 1);
		return SuperJumpPoses.mix(ticks[a], ticks[b], i - a);
	}

	private static boolean ringRight(AvatarRenderState state, Player player) {
		if (FlightPoses.isRing(state.rightHandItemStack)) return true;
		if (FlightPoses.isRing(state.leftHandItemStack)) return false;
		return player.getMainArm() == HumanoidArm.RIGHT;
	}

	/**
	 * Where this player's ring fist is: laid out in the fast glide it reaches ahead along the look;
	 * otherwise from the ring arm as last posed. Null if it hasn't been drawn lately.
	 */
	static Vec3 fist(Player player, float partial) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return null;
		boolean right = FlightPoses.isRing(player.getMainHandItem()) ? player.getMainArm() == HumanoidArm.RIGHT
				: FlightPoses.isRing(player.getOffhandItem()) ? player.getMainArm() != HumanoidArm.RIGHT : player.getMainArm() == HumanoidArm.RIGHT;
		if (FlightPoses.fast(player) > 0.5f) {
			Vec3 look = player.getViewVector(partial);
			Vec3 side = look.cross(new Vec3(0, 1, 0));
			side = side.lengthSqr() < 1e-4 ? Vec3.ZERO : side.normalize().scale(right ? 0.31 : -0.31);
			return player.getPosition(partial).add(0, 0.9, 0).add(look.scale(1.25)).add(side);
		}
		float[] a = ARMS.get(player.getId());
		if (a == null || Math.floorMod(mc.level.getGameTime() - (long) a[6], 100000) > 2) return null;
		// The fist in the arm's own space (model pixels), turned like ModelPart.translateAndRotate.
		Vector3f p = new Vector3f(right ? -1 : 1, 10, 0);
		new Quaternionf().rotationZYX(a[5], a[4], a[3]).transform(p);
		p.add(a[0], a[1], a[2]).div(16f);
		// Model space to the world, as LivingEntityRenderer turns and flips the model.
		// The arm lead may have turned the drawn body to the way they fly (ArmLeadPoses).
		float yaw = ArmLeadPoses.bodyYaw(player.getId(), Mth.rotLerp(partial, player.yBodyRotO, player.yBodyRot));
		Vector3f w = new Vector3f(-p.x, 1.501f - p.y, p.z);
		new Quaternionf().rotationY((180f - yaw) * Mth.DEG_TO_RAD).transform(w);
		return player.getPosition(partial).add(w.x, w.y, w.z);
	}

	private static float approach(float from, float to, float rate) {
		float next = from + (to - from) * rate;
		return Math.abs(to - next) < 0.002f ? to : next;
	}
}
