package com.sparky.lanternring.client;

import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.SuperJumps;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * Third person: the super jump's body language, for every player (the server announces each jump
 * and landing, see SuperJumpFx). The poses are J's Blender picks (passes 81-84, hand-off
 * docs/handoff/2026-10-13-super-jump-ring-lab-brief.md on the Blender branch):
 * <ul>
 * <li>A1 wind-up while a sprint charges the jump (35% once armed, all of it at full charge, the ring arm trembling);
 * <li>B1 launch, C1 rising (the ring fist up 15 degrees forward and following the aim, easing down toward
 * the fall arms from 45% of the way up);
 * <li>D1 falling, its ring arm picked in the Ring Lab (D1A at the ground, D1B ahead, D1C down and out);
 * <li>E1 or E2 landing (Ring Lab), held, then up through F2 (E1 eases straight back); a fall more than
 * SuperJumps.DEEP below the take-off lands in E3 and rises through F3.
 * </ul>
 * Each pose is six parts (head, body, ring arm, free arm, ring leg, free leg), each its rotation in
 * radians and its offset in model pixels from the part's default place. They are for a right-handed
 * player; a left-handed one swaps sides, with yRot, zRot and the x offsets mirrored.
 */
public final class SuperJumpPoses {
	/** Ticks of the launch pose before the rising one, and the blends (brief: "Timing and blends"). */
	private static final float LAUNCH = 5f, LAUNCH_IN = 2f, RISE_IN = 3f, FALL_IN = 8f, LAND_IN = 2f, STAND_UP = 8f;
	/** How long the deep landing (E3) holds. */
	private static final float DEEP_HOLD = 30f;
	/** From this far up the rise the arms start toward the fall arms. */
	private static final float ARMS_DOWN_FROM = 0.45f;

	/** Default places: head, body, ring arm, free arm, ring leg, free leg (right-handed). */
	private static final float[][] HOME = {{0, 0, 0}, {0, 0, 0}, {-5, 2, 0}, {5, 2, 0}, {-1.9f, 12, 0}, {1.9f, 12, 0}};

	static final float[][] A1 = {
			{-0.55f, 0, 0, 0, 5.93f, -6.27f}, {0.55f, 0, 0, 0, 5.93f, -6.27f}, {1.15f, 0, 0.25f, 0, 5.63f, -5.23f},
			{-0.75f, -0.35f, 0.15f, 0, 5.63f, -5.23f}, {-0.55f, 0, 0.2f, 0, 0.16f, 0}, {0.45f, 0, -0.15f, 0, 0.16f, 0}};
	static final float[][] B1 = {
			{-0.4f, 0, 0, 0, 0.01f, 0.6f}, {-0.05f, 0, 0, 0, 0.01f, 0.6f}, {0.75f, 0, 0.15f, 0, 0.01f, 0.5f},
			{0.75f, 0, -0.15f, 0, 0.01f, 0.5f}, {0.15f, 0, 0.03f, 0, 0, 0}, {0.15f, 0, -0.03f, 0, 0, 0}};
	static final float[][] C1 = {
			{-0.45f, 0, 0, 0, 0.04f, 0.96f}, {-0.08f, 0, 0, 0, 0.04f, 0.96f}, {-3.05f, 0, 0.05f, 0, 0.03f, 0.8f},
			{0.35f, 0, -0.12f, 0, 0.03f, 0.8f}, {-0.95f, 0, 0.05f, 0, 0, 0}, {0.3f, 0, -0.02f, 0, 0, 0}};
	static final float[][] D1A = {
			{0.3f, 0, 0, 0, 0.37f, -2.97f}, {0.25f, 0, 0, 0, 0.37f, -2.97f}, {-0.15f, 0, 0.05f, 0, 0.31f, -2.47f},
			{-0.35f, 0, -1.1f, 0, 0.31f, -2.47f}, {-0.45f, 0, 0.08f, 0, 0, 0}, {0.35f, 0, -0.08f, 0, 0, 0}};
	static final float[][] D1B = ringArm(D1A, -0.75f, 0, 0.12f, 0, 0.31f, -2.47f);
	static final float[][] D1C = ringArm(D1A, -0.3f, 0, 0.4f, 0, 0.31f, -2.47f);
	static final float[][] E1 = {
			{-0.7f, 0, 0, 0, 12.29f, -8.18f}, {0.75f, 0, 0, 0, 12.29f, -8.18f}, {-0.36f, 0, 0.12f, 0, 11.76f, -6.82f},
			{1.3f, 0, -0.5f, 0, 11.76f, -6.82f}, {-1.3f, 0, 0.1f, 0, 3.7f, 0}, {1f, 0, -0.08f, 0, 3.7f, 0}};
	static final float[][] E2 = {
			{-0.9f, 0, 0, 0, 12.5f, -9.76f}, {0.95f, 0, 0, 0, 12.5f, -9.76f}, {-0.36f, 0, -0.05f, 0, 11.66f, -8.13f},
			{0.45f, 0, -1.2f, 0, 11.66f, -8.13f}, {-0.8f, 0, 0.5f, 0, 2.2f, 0}, {0.8f, 0, -0.4f, 0, 2.2f, 0}};
	static final float[][] E3 = {
			{-0.5f, -0.2f, 0, -1.68f, 12.73f, -6.57f}, {0.6f, 0.25f, 0, -1.68f, 12.73f, -6.57f}, {-0.37f, 0, 0.45f, -1.24f, 12.38f, -4.23f},
			{0.9f, 0, -0.25f, -1.55f, 12.38f, -6.71f}, {-1.45f, 0, 0.15f, 0, 5.11f, 0}, {1.15f, 0, -0.1f, 0, 5.11f, 0}};
	static final float[][] F2 = {
			{-0.3f, 0, 0, 0, 2.18f, -4.11f}, {0.35f, 0, 0, 0, 2.18f, -4.11f}, {0.4f, 0, 0.2f, 0, 2.06f, -3.43f},
			{0.5f, 0, -0.3f, 0, 2.06f, -3.43f}, {-0.5f, 0, 0.08f, 0, 0, 0}, {0.35f, 0, -0.05f, 0, 0, 0}};
	static final float[][] F3 = {
			{-0.2f, 0, 0, 0, -0.1f, 1.44f}, {-0.12f, 0, 0, 0, -0.1f, 1.44f}, {-0.3f, 0, 0.1f, 0, -0.11f, 1.2f},
			{0.2f, 0, -0.15f, 0, -0.11f, 1.2f}, {0.05f, 0, 0.06f, 0, 0, 0}, {0.05f, 0, -0.06f, 0, 0, 0}};

	private static final class Jump {
		long jumped;
		float charge, height;
		double fromY;
		/** When the top of the arc was seen, how far the arms had come down by then; when it landed (-1 for not yet). */
		float apex = -1, armsAtApex;
		long landed = -1;
		boolean deep;
	}

	private static final Int2ObjectMap<Jump> JUMPS = new Int2ObjectOpenHashMap<>();
	/** The ring arm as last posed (x, y, z, xRot, yRot, zRot, game time mod 100000), for the fist's place. */
	private static final Int2ObjectMap<float[]> ARMS = new Int2ObjectOpenHashMap<>();

	private SuperJumpPoses() {
	}

	private static float[][] ringArm(float[][] base, float... arm) {
		float[][] out = copy(base);
		out[2] = arm;
		return out;
	}

	static void jumped(int id, float charge, double fromY) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		Jump j = new Jump();
		j.jumped = mc.level.getGameTime();
		j.charge = charge;
		j.height = (float) Mth.lerp(charge, SuperJumps.MIN_HEIGHT, SuperJumps.MAX_HEIGHT);
		j.fromY = fromY;
		JUMPS.put(id, j);
	}

	static void landed(int id, boolean deep) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		Jump j = JUMPS.computeIfAbsent(id, k -> new Jump());
		j.landed = mc.level.getGameTime();
		j.deep = deep;
	}

	/** Whether this player is in the air on a super jump (for the ring's glow on the way). */
	static boolean airborne(int id) {
		Jump j = JUMPS.get(id);
		return j != null && j.landed < 0;
	}

	/** Ticks from landing until the stand-up is over (the landing construct fades after it). */
	static float landingTicks(boolean deep) {
		return LAND_IN + (deep ? DEEP_HOLD : RingTuning.SUPER_LANDING.ticks()) + STAND_UP;
	}

	private static float[][] fall() {
		return switch (LabSettings.get().superFallArm) {
			case D1A -> D1A;
			case D1B -> D1B;
			case D1C -> D1C;
		};
	}

	public static void pose(PlayerModel model, AvatarRenderState state) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null || !(mc.level.getEntity(state.id) instanceof Player player)) return;
		posed(model, player, mc);
		if (!JUMPS.containsKey(player.getId())) return;
		// Where the ring arm ended up, so the trail can come off the fist (SuperJumpAir).
		ModelPart arm = player.getMainArm() == HumanoidArm.RIGHT ? model.rightArm : model.leftArm;
		ARMS.put(player.getId(), new float[] {arm.x, arm.y, arm.z, arm.xRot, arm.yRot, arm.zRot, mc.level.getGameTime() % 100000});
	}

	/** Where the fist of this player's posed ring arm is, or null if it hasn't been drawn lately. */
	static Vec3 fist(Player player, float partial) {
		Minecraft mc = Minecraft.getInstance();
		float[] a = ARMS.get(player.getId());
		if (a == null || mc.level == null || Math.floorMod(mc.level.getGameTime() - (long) a[6], 100000) > 2) return null;
		boolean right = player.getMainArm() == HumanoidArm.RIGHT;
		// The fist in the arm's own space (model pixels), turned like ModelPart.translateAndRotate.
		Vector3f p = new Vector3f(right ? -1 : 1, 10, 0);
		new Quaternionf().rotationZYX(a[5], a[4], a[3]).transform(p);
		p.add(a[0], a[1], a[2]).div(16f);
		// Model space to the world, as LivingEntityRenderer turns and flips the model.
		float yaw = Mth.rotLerp(partial, player.yBodyRotO, player.yBodyRot);
		Vector3f w = new Vector3f(-p.x, 1.501f - p.y, p.z);
		new Quaternionf().rotationY((180f - yaw) * Mth.DEG_TO_RAD).transform(w);
		return player.getPosition(partial).add(w.x, w.y, w.z);
	}

	private static void posed(PlayerModel model, Player player, Minecraft mc) {
		boolean right = player.getMainArm() == HumanoidArm.RIGHT;
		float partial = mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
		float now = mc.level.getGameTime() + partial;

		Jump j = JUMPS.get(player.getId());
		// Flying off a super jump (the double-tap that starts ground flight or a takeoff) ends it: the
		// server drops a jump once you fly, so no landing will come.
		if (j != null && (MovePoses.override(player.getId(), partial) > 0f || player == mc.player && player.getAbilities().flying)) {
			JUMPS.remove(player.getId());
			j = null;
		}
		if (j == null) {
			run(model, player, mc, right, now);
			return;
		}
		if (j.landed >= 0) {
			float t = now - j.landed;
			float hold = j.deep ? DEEP_HOLD : RingTuning.SUPER_LANDING.ticks();
			if (t > LAND_IN + hold + STAND_UP || t < -20) {
				JUMPS.remove(player.getId());
				return;
			}
			boolean e2 = LabSettings.get().superLanding == LabSettings.SuperLanding.E2;
			float[][] land = j.deep ? E3 : e2 ? E2 : E1;
			float[][] up = j.deep ? F3 : e2 ? F2 : null;
			if (t < LAND_IN) {
				apply(model, right, mix(fall(), land, smooth(t / LAND_IN)), 1f);
			} else if (t < LAND_IN + hold) {
				apply(model, right, land, 1f);
			} else {
				// Stand up: through the halfway pose when there is one, else eased straight back.
				float s = (t - LAND_IN - hold) / STAND_UP;
				if (up == null) apply(model, right, land, 1f - smooth(s));
				else if (s < 0.5f) apply(model, right, mix(land, up, smooth(s * 2)), 1f);
				else apply(model, right, up, 1f - smooth((s - 0.5f) * 2));
			}
			return;
		}
		float age = now - j.jumped;
		if (age > 600 || age < -20) {
			JUMPS.remove(player.getId());
			return;
		}
		if (age < LAUNCH) {
			apply(model, right, B1, smooth(age / LAUNCH_IN));
			return;
		}
		double vy = player.getY() - player.yo;
		float[][] fall = fall();
		if (j.apex < 0) {
			// The hand shouldn't stay up the entire way (J): the arms come down over the top of the rise.
			float up = j.height <= 0 ? 0f : Mth.clamp((float) ((player.getY() - j.fromY) / j.height), 0f, 1f);
			float arms = smooth((up - ARMS_DOWN_FROM) / (1 - ARMS_DOWN_FROM));
			if (age > LAUNCH + 1 && vy <= 0) {
				j.apex = now;
				j.armsAtApex = arms;
			} else {
				float lookX = model.head.xRot, lookY = model.head.yRot;
				apply(model, right, mix(B1, withArms(aimed(C1, right, lookX, lookY), fall, arms), smooth((age - LAUNCH) / RISE_IN)), 1f);
				// The head follows the look as normal.
				model.head.xRot = lookX;
				model.head.yRot = lookY;
				return;
			}
		}
		float lookX = model.head.xRot, lookY = model.head.yRot;
		float f = smooth((now - j.apex) / FALL_IN);
		apply(model, right, mix(withArms(aimed(C1, right, lookX, lookY), fall, j.armsAtApex), fall, f), 1f);
		// Out of the look the head had on the way up, into the fall pose's.
		model.head.xRot = Mth.lerp(f, lookX, model.head.xRot);
		model.head.yRot = Mth.lerp(f, lookY, model.head.yRot);
	}

	/**
	 * J's rising arm (pass 88, G2 + G3): C1 with the ring arm following the aim. A level look puts it
	 * 15 degrees forward of straight up; looking up or down tips it by half as much (its elevation
	 * kept between 55 and 90 degrees), and it swings with the head's yaw while the body turns a third
	 * of that and leans in a touch. lookX and lookY are the head's pitch and its yaw from the body.
	 */
	private static float[][] aimed(float[][] base, boolean right, float lookX, float lookY) {
		float[][] out = copy(base);
		float elevation = Mth.clamp(75f + 0.5f * -lookX * Mth.RAD_TO_DEG, 55f, 90f);
		// apply() mirrors yRot for a left-handed player; the aim is already in the world's sense.
		float m = right ? 1f : -1f;
		out[2][0] = -(90f + elevation) * Mth.DEG_TO_RAD;
		out[2][1] = m * lookY;
		out[1][0] += 0.04f;
		out[1][1] = m * lookY / 3f;
		return out;
	}

	/**
	 * The super sprint: leaning into the run and pumping harder as it builds (the local player's
	 * build-up, or for others how fast they're going past vanilla's sprint). Once the local player's
	 * sprint arms the jump, the A1 wind-up takes over the head, body and arms (the legs keep running).
	 */
	private static void run(PlayerModel model, Player player, Minecraft mc, boolean right, float now) {
		if (!player.isSprinting() || player.getAbilities().flying || player.isFallFlying() || player.isInWater()) return;
		float w;
		float wind = 0f;
		if (player == mc.player) {
			w = SuperJumpInput.ramp();
			float charge = SuperJumpInput.charge();
			if (charge >= 0f && player.onGround()) wind = 0.35f + 0.65f * smooth(charge);
		} else {
			double dx = player.getX() - player.xo, dz = player.getZ() - player.zo;
			w = Mth.clamp((float) ((Math.sqrt(dx * dx + dz * dz) - 0.3) / 0.25), 0f, 1f);
		}
		// J's Blender sprint (MovePoses) replaces this lean and pump while the ring is in hand.
		w = smooth(w) * (1f - wind) * (1f - MovePoses.runWeight(player.getId()));
		if (w > 0.01f) {
			model.body.xRot += 0.3f * w;
			model.head.xRot -= 0.2f * w;
			// Longer, harder strides and arm swings than vanilla's sprint.
			float pump = 1f + 0.55f * w;
			model.rightArm.xRot *= pump;
			model.leftArm.xRot *= pump;
			model.rightLeg.xRot *= 1f + 0.35f * w;
			model.leftLeg.xRot *= 1f + 0.35f * w;
			// The body pivots at the neck, so its hips swing back; the legs go with them (like vanilla's crouch).
			model.rightLeg.z += 3.5f * w;
			model.leftLeg.z += 3.5f * w;
		}
		if (wind <= 0f) return;
		float[][] a = copy(A1);
		if (SuperJumpInput.charge() >= 1f) {
			// Fully charged: the ring arm trembles.
			a[2][0] += 0.03f * Mth.sin(now * 3.1f);
			a[2][2] += 0.02f * Mth.sin(now * 4.3f + 1f);
		}
		apply(model, right, a, wind, 4);
	}

	static void apply(PlayerModel model, boolean right, float[][] pose, float w) {
		apply(model, right, pose, w, 6);
	}

	/** Blends the first {@code parts} parts toward the pose by w; a left-handed player gets it mirrored. */
	static void apply(PlayerModel model, boolean right, float[][] pose, float w, int parts) {
		if (w <= 0f) return;
		ModelPart[] p = {model.head, model.body, right ? model.rightArm : model.leftArm, right ? model.leftArm : model.rightArm,
				right ? model.rightLeg : model.leftLeg, right ? model.leftLeg : model.rightLeg};
		float m = right ? 1f : -1f;
		for (int i = 0; i < parts; i++) {
			float[] q = pose[i];
			ModelPart part = p[i];
			part.xRot = Mth.lerp(w, part.xRot, q[0]);
			part.yRot = Mth.lerp(w, part.yRot, m * q[1]);
			part.zRot = Mth.lerp(w, part.zRot, m * q[2]);
			part.x = Mth.lerp(w, part.x, m * (HOME[i][0] + q[3]));
			part.y = Mth.lerp(w, part.y, HOME[i][1] + q[4]);
			part.z = Mth.lerp(w, part.z, HOME[i][2] + q[5]);
		}
	}

	static float[][] mix(float[][] a, float[][] b, float t) {
		float[][] out = new float[6][6];
		for (int i = 0; i < 6; i++) {
			for (int k = 0; k < 6; k++) out[i][k] = Mth.lerp(t, a[i][k], b[i][k]);
		}
		return out;
	}

	/** The pose with its two arms taken toward those of another. */
	private static float[][] withArms(float[][] base, float[][] arms, float t) {
		float[][] out = copy(base);
		for (int i = 2; i <= 3; i++) {
			for (int k = 0; k < 6; k++) out[i][k] = Mth.lerp(t, base[i][k], arms[i][k]);
		}
		return out;
	}

	private static float[][] copy(float[][] pose) {
		float[][] out = new float[pose.length][];
		for (int i = 0; i < pose.length; i++) out[i] = pose[i].clone();
		return out;
	}

	static float smooth(float t) {
		t = Mth.clamp(t, 0f, 1f);
		return t * t * (3 - 2 * t);
	}

}
