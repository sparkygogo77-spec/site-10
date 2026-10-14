package com.sparky.lanternring.client;

import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.HumanoidArm;
import org.joml.Matrix3f;
import org.joml.Vector3f;

/**
 * Third person: the body in J's charge takes (ChargeTakes), L1c's lean into the port and K3c's kneel and lift.
 * The legs bend at the knee: each leg (and its pants) has a thigh and a shin added to the player model
 * ({@link #addKnees}); while a take kneels, the whole leg's box is skipped and the two halves are drawn instead,
 * the shin turned at the knee by the angle between the take's thigh and shin.
 */
public final class TakePoses {
	private static final String THIGH = "lanternring_thigh", SHIN = "lanternring_shin";
	/** The crouch (the kneel holds sneak for the camera) lowers the model 2/16 of a block: lift it back, in model px. */
	private static final float CROUCH_DROP = 2f / 0.9375f;

	private TakePoses() {
	}

	/** Adds a thigh and a shin to each leg and pants of the player's skin model, cut from the leg's own texture. */
	public static void addKnees(MeshDefinition mesh) {
		PartDefinition root = mesh.getRoot();
		knees(root.getChild("right_leg"), 0, 16, CubeDeformation.NONE);
		knees(root.getChild("left_leg"), 16, 48, CubeDeformation.NONE);
		knees(root.getChild("right_leg").getChild("right_pants"), 0, 32, new CubeDeformation(0.25f));
		knees(root.getChild("left_leg").getChild("left_pants"), 0, 48, new CubeDeformation(0.25f));
	}

	private static void knees(PartDefinition leg, int u, int v, CubeDeformation d) {
		// The leg's box is 4 x 12 x 4 at (u, v): its sides start 4 rows down, so the top 6 rows of the sides are the
		// thigh's and the next 6 the shin's (shifting the shin's texture 6 rows down lines its sides up with them).
		leg.addOrReplaceChild(THIGH, CubeListBuilder.create().texOffs(u, v).addBox(-2f, 0f, -2f, 4f, 6f, 4f, d), PartPose.ZERO);
		leg.addOrReplaceChild(SHIN, CubeListBuilder.create().texOffs(u, v + 6).addBox(-2f, 0f, -2f, 4f, 6f, 4f, d), PartPose.offset(0f, 6f, 0f));
	}

	public static void pose(PlayerModel model, AvatarRenderState state) {
		boolean bent = false;
		Minecraft mc = Minecraft.getInstance();
		float[][] pose = null;
		float w = 0f;
		if (mc.player != null && state.id == mc.player.getId()) {
			ChargeTakes.Take take = LanternShrine.take();
			if (take != null) {
				float partial = mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
				pose = LanternShrine.takePose(partial);
				w = LanternShrine.takeWeight(partial);
			}
		}
		if (pose != null && w > 0.001f) bent = apply(model, state, pose, w, mc.player.getMainArm() == HumanoidArm.RIGHT);
		showKnees(model, bent);
	}

	private static boolean apply(PlayerModel model, AvatarRenderState state, float[][] pose, float w, boolean right) {
		// The take is for a right-handed player: the ring arm is the right one. Mirrored for a left-handed one.
		float m = right ? 1f : -1f;
		ModelPart[] p = {model.head, model.body, right ? model.rightArm : model.leftArm, right ? model.leftArm : model.rightArm,
				right ? model.rightLeg : model.leftLeg, right ? model.leftLeg : model.rightLeg};
		float lift = state.isCrouching ? -CROUCH_DROP : 0f;
		for (int i = 0; i < 6; i++) {
			float[] q = pose[i];
			ModelPart part = p[i];
			float[] home = ChargeTakes.PIVOT[i];
			// The head keeps following where you look, with the take's bow on top.
			float x = i == ChargeTakes.HEAD ? part.xRot + q[0] : q[0];
			float y = i == ChargeTakes.HEAD ? part.yRot + m * q[1] : m * q[1];
			part.xRot = Mth.lerp(w, part.xRot, x);
			part.yRot = Mth.lerp(w, part.yRot, y);
			part.zRot = Mth.lerp(w, part.zRot, m * q[2]);
			part.x = Mth.lerp(w, part.x, m * (home[0] + q[3]));
			part.y = Mth.lerp(w, part.y, home[1] + q[4] + lift);
			part.z = Mth.lerp(w, part.z, home[2] + q[5]);
		}
		// The knees: the shin's turn relative to its thigh (a bend about the knee).
		boolean bent = false;
		for (int s = 0; s < 2; s++) {
			int leg = ChargeTakes.RLEG + s, shin = ChargeTakes.RSHIN + s;
			Matrix3f rel = ChargeTakes.rotation(pose[leg]).transpose().mul(ChargeTakes.rotation(pose[shin]));
			Vector3f e = euler(rel);
			ModelPart part = s == 0 ? p[4] : p[5];
			ModelPart k = part.getChild(SHIN);
			k.xRot = w * e.x;
			k.yRot = w * m * e.y;
			k.zRot = w * m * e.z;
			ModelPart pants = (s == 0) == right ? model.rightPants : model.leftPants;
			ModelPart pk = pants.getChild(SHIN);
			pk.xRot = k.xRot;
			pk.yRot = k.yRot;
			pk.zRot = k.zRot;
			bent |= Math.abs(k.xRot) + Math.abs(k.yRot) + Math.abs(k.zRot) > 0.01f;
		}
		return bent;
	}

	/** The (x, y, z) angles of R = Rz Ry Rx. */
	private static Vector3f euler(Matrix3f r) {
		// JOML is column-major: m[col][row]. R[2][0] = m02, R[2][1] = m12, R[2][2] = m22, R[1][0] = m01, R[0][0] = m00.
		float y = (float) Math.asin(Mth.clamp(-r.m02, -1f, 1f));
		return new Vector3f((float) Math.atan2(r.m12, r.m22), y, (float) Math.atan2(r.m01, r.m00));
	}

	/** With bent knees the whole legs are skipped and the halves drawn; otherwise the halves stay hidden. */
	private static void showKnees(PlayerModel model, boolean bent) {
		for (ModelPart leg : new ModelPart[] {model.rightLeg, model.leftLeg, model.rightPants, model.leftPants}) {
			if (!leg.hasChild(THIGH)) continue;
			leg.skipDraw = bent;
			leg.getChild(THIGH).visible = bent;
			leg.getChild(SHIN).visible = bent;
		}
	}
}
