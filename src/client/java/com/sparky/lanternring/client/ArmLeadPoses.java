package com.sparky.lanternring.client;

import com.sparky.lanternring.RingTuning;
import it.unimi.dsi.fastutil.ints.Int2FloatMap;
import it.unimi.dsi.fastutil.ints.Int2FloatOpenHashMap;
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
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * Pass 404 (J: "arm leading the body by like .08s"): in all ring flight (cruise, the pass 403 take-off and the soft
 * landing) the ring arm points the way you are moving now, and the body follows that same direction 1.6 ticks later
 * (Ring Lab Durations "arm_lead"). It is pose only: it never changes where anyone goes.
 * <ul>
 * <li>Ring arm: xRot = -(90 deg + climb), yRot = heading now - body heading, so it is flat ahead when level and swings
 * into a turn before the body does. In the laid-out glide the whole model is already pitched (FlightPoses.rotate),
 * so the same direction is worked out in that frame.
 * <li>Body: in the glide, the dart and the soft landing it is turned and pitched along the movement direction of 1.6
 * ticks ago (a short history, interpolated).
 * <li>Ring Lab "arm_lead": D1 pure lead; D2 the arm also overshoots by the last two ticks' turn (25% of the rate, as in
 * Blender); D3 D1 plus the body banking into turns, up to 35 degrees.
 * </ul>
 */
public final class ArmLeadPoses {
	/** Ticks of movement direction kept: enough for the longest lead plus D3's turn rate. */
	private static final int HISTORY = 7;
	/** Below this speed (blocks a tick) the climb eases back to level and the arm stops leading. */
	private static final float STILL = 0.04f, LEAD_SPEED = 0.15f;
	/** D3: the most it banks, and the turn rate (degrees a tick) that banks it fully. */
	private static final float BANK = 35f, BANK_RATE = 6f;
	/** The arm doesn't point further round than this from the body (flying backwards). */
	private static final float MAX_SWING = 110f;

	private static final class Track {
		/** Index 0 is the latest tick's movement heading (degrees, unwrapped) and climb (degrees, up positive). */
		final float[] heading = new float[HISTORY], climb = new float[HISTORY];
		float speed, prevSpeed;
		boolean primed, seen;
	}

	private static final Int2ObjectMap<Track> TRACKS = new Int2ObjectOpenHashMap<>();
	/** The body yaw each player was last drawn with when this turned it (for where the fist is). */
	private static final Int2FloatMap BODY = new Int2FloatOpenHashMap();

	private ArmLeadPoses() {
	}

	static void tick(Minecraft mc) {
		if (mc.level == null) {
			TRACKS.clear();
			BODY.clear();
			return;
		}
		for (Track t : TRACKS.values()) t.seen = false;
		for (AbstractClientPlayer p : mc.level.players()) {
			Track t = TRACKS.computeIfAbsent(p.getId(), id -> new Track());
			t.seen = true;
			update(t, p);
		}
		TRACKS.values().removeIf(t -> !t.seen);
		BODY.keySet().removeIf(id -> !TRACKS.containsKey((int) id));
	}

	private static void update(Track t, Player p) {
		double dx = p.getX() - p.xo, dy = p.getY() - p.yo, dz = p.getZ() - p.zo;
		float flat = (float) Math.sqrt(dx * dx + dz * dz);
		float speed = (float) Math.sqrt(dx * dx + dy * dy + dz * dz);
		float last = t.primed ? t.heading[0] : p.yBodyRot;
		// Barely moving sideways (hovering, or straight up), the arm faces the way the body does.
		float heading = flat > 0.03f ? (float) Math.toDegrees(Math.atan2(-dx, dz)) : p.yBodyRot;
		heading = last + Mth.wrapDegrees(heading - last);
		float climb = speed > STILL ? Mth.clamp((float) Math.toDegrees(Math.atan2(dy, flat)), -85f, 85f) : (t.primed ? t.climb[0] * 0.5f : 0f);
		if (!t.primed) {
			java.util.Arrays.fill(t.heading, heading);
			java.util.Arrays.fill(t.climb, climb);
			t.primed = true;
		}
		System.arraycopy(t.heading, 0, t.heading, 1, HISTORY - 1);
		System.arraycopy(t.climb, 0, t.climb, 1, HISTORY - 1);
		t.heading[0] = heading;
		t.climb[0] = climb;
		t.prevSpeed = t.speed;
		t.speed += (speed - t.speed) * 0.5f;
	}

	/** The history at a fractional number of ticks back (0 = the latest tick), held at its oldest. */
	private static float sample(float[] h, float back) {
		float i = Mth.clamp(back, 0f, HISTORY - 1);
		int a = Mth.floor(i);
		int b = Math.min(a + 1, HISTORY - 1);
		return Mth.lerp(i - a, h[a], h[b]);
	}

	/** Ticks back that "now" is this frame (the latest movement is drawn as it finishes over the frame's partial tick). */
	private static float now(float partial) {
		return 1f - partial;
	}

	private static float lead() {
		return (float) (RingTuning.ARM_LEAD.seconds() * 20);
	}

	/** The body's heading and climb: where this player was moving the lead's ticks ago, or null with no track. */
	static float[] body(int id, float partial) {
		Track t = TRACKS.get(id);
		if (t == null || !t.primed) return null;
		float back = now(partial) + lead();
		return new float[] {sample(t.heading, back), sample(t.climb, back)};
	}

	/** D3's bank in degrees (positive: right side down, into a right turn); 0 for D1 and D2. */
	static float bank(int id, float partial) {
		if (LabSettings.get().armLead != LabSettings.ArmLead.D3) return 0f;
		Track t = TRACKS.get(id);
		if (t == null || !t.primed) return 0f;
		float back = now(partial) + lead();
		float rate = sample(t.heading, back) - sample(t.heading, back + 1f);
		return BANK * Mth.clamp(rate / BANK_RATE, -1f, 1f);
	}

	/** The glide's whole-body pitch (FlightPoses.rotate): laid out along the climb of the lead's ticks ago, or the fallback. */
	static float glidePitch(int id, float partial, float fallback) {
		float[] b = body(id, partial);
		return b == null ? fallback : -90f + b[1];
	}

	/** The body yaw this player was last drawn with, if this turned it; otherwise the fallback. */
	static float bodyYaw(int id, float fallback) {
		return BODY.containsKey(id) ? BODY.get(id) : fallback;
	}

	/**
	 * Turns the drawn body to the lagged movement heading while laid out (the glide, the dart, the soft landing),
	 * keeping the head looking where it looked. Called after FlightPoses has filled in its pose.
	 */
	static void extract(int id, AvatarRenderState state, FlightPoses.Pose pose, float partial) {
		float w = Math.max(pose.flying * pose.fast, MovePoses.laidOut(id, partial));
		float[] b = w > 0f ? body(id, partial) : null;
		if (b == null) {
			BODY.remove(id);
			return;
		}
		float old = state.bodyRot;
		float yaw = old + Mth.wrapDegrees(b[0] - old) * Mth.clamp(w, 0f, 1f);
		state.bodyRot = yaw;
		state.yRot = Mth.wrapDegrees(state.yRot + old - yaw);
		BODY.put(id, yaw);
	}

	/** The ring arm points where you fly; runs after the take poses (MovePoses) so it holds through them. */
	public static void pose(PlayerModel model, AvatarRenderState state) {
		Minecraft mc = Minecraft.getInstance();
		Track t = TRACKS.get(state.id);
		if (mc.level == null || t == null || !t.primed || state.isUsingItem) return;
		FlightPoses.Pose pose = ((FlightPoses.Holder) state).lanternring$flightPose();
		float partial = mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
		float flight = Math.max(pose.flying, MovePoses.flightMove(state.id, partial));
		float speed = Mth.lerp(partial, t.prevSpeed, t.speed);
		float w = Mth.clamp(flight, 0f, 1f) * SuperJumpPoses.smooth(speed / LEAD_SPEED) * (1f - pose.aim);
		if (w <= 0.001f) return;

		float back = now(partial);
		float heading = sample(t.heading, back), climb = sample(t.climb, back);
		if (LabSettings.get().armLead == LabSettings.ArmLead.D2) {
			// Blender's anticipation: 25% of the turn rate, over the last two ticks.
			heading += 0.5f * (heading - sample(t.heading, back + 2f));
			climb += 0.5f * (climb - sample(t.climb, back + 2f));
		}
		float swing = Mth.clamp(Mth.wrapDegrees(heading - state.bodyRot), -MAX_SWING, MAX_SWING);
		// The model is already pitched by the flight pose; point the arm the same way in that frame.
		float rootPitch = -FlightPoses.appliedPitch(state) * Mth.DEG_TO_RAD;
		Quaternionf q = new Quaternionf().rotationX(-rootPitch).rotateY(swing * Mth.DEG_TO_RAD)
				.rotateX(-(Mth.HALF_PI + Mth.clamp(climb, -85f, 85f) * Mth.DEG_TO_RAD));
		Vector3f euler = q.getEulerAnglesZYX(new Vector3f());
		ModelPart arm = pose.ringArm == HumanoidArm.RIGHT ? model.rightArm : model.leftArm;
		// Unwrapped onto the arm's current angles, so blending in never swings the long way round.
		float x = arm.xRot + Mth.wrapDegrees((euler.x - arm.xRot) * Mth.RAD_TO_DEG) * Mth.DEG_TO_RAD;
		float y = arm.yRot + Mth.wrapDegrees((euler.y - arm.yRot) * Mth.RAD_TO_DEG) * Mth.DEG_TO_RAD;
		float z = arm.zRot + Mth.wrapDegrees((euler.z - arm.zRot) * Mth.RAD_TO_DEG) * Mth.DEG_TO_RAD;
		arm.xRot = Mth.lerp(w, arm.xRot, x);
		arm.yRot = Mth.lerp(w, arm.yRot, y);
		arm.zRot = Mth.lerp(w, arm.zRot, z);
	}

	/** The free arm in the laid-out glide, relative to the body (Ring Lab "free_arm", pass 403): {xRot, zRot outwards}. */
	static float[] freeArm() {
		return switch (LabSettings.get().freeArm) {
			case A1 -> new float[] {0f, 0.06f};
			case A2 -> new float[] {-0.3f, 0.08f};
			case A3 -> new float[] {-0.45f, 0.32f};
		};
	}
}
