package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternCharge;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.HumanoidArm;

/**
 * Third person: the Shoulder lean charge style (J's L3 pick from the Blender kneel and lean pass,
 * docs/handoff/2026-10-13-round1-picks/lean_L3_poses.json). The lantern stands set down at your ring
 * side (LanternShrine); you lean your ring shoulder into it and push the ring onto its port, twice
 * pressing harder as the charge builds, then straighten up.
 *
 * <p>Key poses are on Blender's 80-tick timeline, where the charge runs from tick 10 to 70; here they
 * are stretched over the real charge (LanternCharge hold to done). Each pose is six parts (head,
 * body, ring arm, free arm, ring leg, free leg): rotation in radians, then the offset in model
 * pixels from the part's default place. They are for a right-handed player and mirrored for a
 * left-handed one, as in SuperJumpPoses.
 */
public final class LeanPoses {
	private static final float[][] IDLE = {{0f, 0f, 0f, 0f, 0f, 0f}, {0f, 0f, 0f, 0f, 0f, 0f}, {0.05f, 0f, 0.05f, 0f, 0f, 0f},
			{0.05f, 0f, -0.05f, 0f, 0f, 0f}, {0f, 0f, 0f, 0f, 0f, 0f}, {0f, 0f, 0f, 0f, 0f, 0f}};
	private static final float[][] LEAN = {{-0.05f, 0.25f, 0.1f, -2.415f, 0.029f, -3.063f}, {0.05f, -0.35f, -0.22f, -2.415f, 0.029f, -3.063f},
			{-1.55f, 0.35f, 0.55f, -1.596f, 1.011f, -4.684f}, {0.15f, 0f, -0.35f, -2.429f, -1.039f, -1.255f},
			{0.05f, 0f, -0.22f, 0.158f, -0.23f, -3.152f}, {-0.05f, 0f, -0.28f, -0.158f, -0.23f, -1.848f}};
	private static final float[][] PUSH = {{0.05f, 0.3f, 0.1f, -2.619f, 0.111f, -3.903f}, {0.1f, -0.4f, -0.26f, -2.619f, 0.111f, -3.903f},
			{-1.5f, 0.35f, 0.6f, -1.633f, 1.238f, -5.667f}, {0.15f, 0f, -0.4f, -2.732f, -1.13f, -1.772f},
			{0.05f, 0f, -0.22f, 0.209f, -0.23f, -3.54f}, {-0.05f, 0f, -0.28f, -0.209f, -0.23f, -2.06f}};
	/** Blender's timeline: the tick of each key and its pose. */
	private static final float[] TICKS = {0, 10, 30, 50, 64, 70, 80};
	private static final float[][][] KEYS = {IDLE, LEAN, PUSH, LEAN, PUSH, LEAN, IDLE};
	/** Where the charge starts and ends on Blender's timeline. */
	private static final float CHARGE_FROM = 10, CHARGE_TO = 70, END = 80;

	/** Default places: head, body, ring arm, free arm, ring leg, free leg (right-handed). */
	private static final float[][] HOME = {{0, 0, 0}, {0, 0, 0}, {-5, 2, 0}, {5, 2, 0}, {-1.9f, 12, 0}, {1.9f, 12, 0}};

	private LeanPoses() {
	}

	/** Blender's timeline tick for a charge time t (ticks the clicks have been held), or -1 when not leaning. */
	static float tick(float t) {
		int hold = LanternCharge.hold(), done = LanternCharge.done();
		if (t < 0) return -1f;
		if (t < hold) return CHARGE_FROM * t / Math.max(hold, 1);
		if (t < done) return CHARGE_FROM + (CHARGE_TO - CHARGE_FROM) * (t - hold) / Math.max(done - hold, 1);
		float k = CHARGE_TO + (END - CHARGE_TO) * (t - done) / LanternCharge.SETTLE;
		return k <= END ? k : -1f;
	}

	/** The pose at a timeline tick, eased between keys. */
	static float[][] at(float k) {
		int i = 0;
		while (i < TICKS.length - 2 && k > TICKS[i + 1]) i++;
		float f = Mth.clamp((k - TICKS[i]) / (TICKS[i + 1] - TICKS[i]), 0f, 1f);
		f = f * f * (3f - 2f * f);
		float[][] a = KEYS[i], b = KEYS[i + 1], out = new float[6][6];
		for (int p = 0; p < 6; p++) {
			for (int c = 0; c < 6; c++) out[p][c] = Mth.lerp(f, a[p][c], b[p][c]);
		}
		return out;
	}

	public static void pose(PlayerModel model, AvatarRenderState state) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.player == null || state.id != mc.player.getId() || !LanternShrine.leaning()) return;
		float k = tick(LanternFirstPerson.held(mc.getDeltaTracker().getGameTimeDeltaPartialTick(false)));
		if (k < 0) return;
		boolean right = mc.player.getMainArm() == HumanoidArm.RIGHT;
		float[][] pose = at(k);
		ModelPart[] p = {model.head, model.body, right ? model.rightArm : model.leftArm, right ? model.leftArm : model.rightArm,
				right ? model.rightLeg : model.leftLeg, right ? model.leftLeg : model.rightLeg};
		float m = right ? 1f : -1f;
		for (int i = 0; i < 6; i++) {
			float[] q = pose[i];
			// The head keeps following where you look, with the lean's tilt on top.
			p[i].xRot = i == 0 ? p[i].xRot + q[0] : q[0];
			p[i].yRot = i == 0 ? p[i].yRot + m * q[1] : m * q[1];
			p[i].zRot = m * q[2];
			p[i].x = m * (HOME[i][0] + q[3]);
			p[i].y = HOME[i][1] + q[4];
			p[i].z = HOME[i][2] + q[5];
		}
	}
}
