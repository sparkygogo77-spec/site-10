package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.item.PowerRingItem;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.player.AvatarRenderer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.client.renderer.state.level.PlayerRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.PlayerModelType;
import net.minecraft.world.item.ItemStack;
import org.joml.Matrix4f;
import org.joml.Vector3f;

/** First person: instead of a flat item, show your own fist wearing the ring. */
public final class RingFirstPerson {
	/** Extra placement on top of vanilla's bare-hand pose. Mutable so tests can sweep it. */
	public static final class Tuning {
		public float twist;
		public float tilt;
		public float lean;
		public float dx;
		public float dy;
		public float dz;
		public float screenX;
		public float screenY;
		public float screenZ;

		public Tuning(float twist, float tilt, float lean, float dx, float dy, float dz, float screenX, float screenY) {
			this(twist, tilt, lean, dx, dy, dz);
			this.screenX = screenX;
			this.screenY = screenY;
		}

		public Tuning(float twist, float tilt, float lean, float dx, float dy, float dz) {
			this.twist = twist;
			this.tilt = tilt;
			this.lean = lean;
			this.dx = dx;
			this.dy = dy;
			this.dz = dz;
		}
	}

	public static final Tuning FIST_DOWN = new Tuning(-30, -10, 0, 0, 0, 0, -0.12f, 0.14f);
	public static final Tuning KNUCKLES_FORWARD = new Tuning(0, -25, 0, 0, 0, 0, -0.12f, 0.14f);

	/**
	 * Knuckles in: the fist held across in front of you with its punching face, where the ring
	 * sits, turned toward your eyes. Positions are in first-person hand space (x right, y up, -z
	 * ahead) for a right hand; mirrored for the left. Mutable so tests can sweep them.
	 */
	public static final Vector3f FIST = new Vector3f(0.36f, -0.3f, -0.66f);
	public static final Vector3f ELBOW = new Vector3f(0.95f, -0.7f, -0.8f);
	/** Which way the back of the hand faces: mostly down, tipped toward you. */
	public static final Vector3f BACK = new Vector3f(0f, -1f, 0.35f);

	/** Last frame's ring position while reaching, for screenshot tests to print. */
	public static String debug = "";

	private RingFirstPerson() {
	}

	/** Returns true when it drew the hand, so the normal item rendering is skipped. */
	public static boolean render(PlayerRenderState playerState, InteractionHand hand, float swing, float equip,
			ItemStack stack, PoseStack poseStack, SubmitNodeCollector collector, int light, float partialTick) {
		LabSettings settings = LabSettings.get();
		if (!(stack.getItem() instanceof PowerRingItem) || settings.handPose == LabSettings.HandPose.FLAT_ITEM) return false;
		AvatarRenderState avatar = playerState.avatarRenderState;
		if (avatar == null || avatar.skin == null) return false;
		AvatarRenderer<?> renderer = Minecraft.getInstance().getEntityRenderDispatcher().getRenderer(avatar);
		HumanoidArm arm = hand == InteractionHand.MAIN_HAND ? avatar.mainArm : avatar.mainArm.getOpposite();
		boolean right = arm == HumanoidArm.RIGHT;
		boolean slim = avatar.skin.model() == PlayerModelType.SLIM;
		Tuning t = settings.handPose == LabSettings.HandPose.FIST_DOWN ? FIST_DOWN : KNUCKLES_FORWARD;
		ModelPart armPart = right ? renderer.getModel().rightArm : renderer.getModel().leftArm;

		armPart.resetPose();
		poseStack.pushPose();
		// Charging from the lantern: slide the whole arm so the ring's face lands on the lantern's lens.
		float reach = hand == InteractionHand.MAIN_HAND ? LanternFirstPerson.reach(partialTick) : 0f;
		Vector3f lens = LanternFirstPerson.lensTarget();
		if (reach > 0f && lens != null) {
			float[] face = RingModels.ringFace(settings.ringModel, !right, slim);
			Vector3f ring = pointAfter(poseStack, () -> {
				place(poseStack, settings.handPose, armPart, right, slim, swing, equip, t);
				armPart.translateAndRotate(poseStack);
			}, face[0] / 16f, face[1] / 16f, face[2] / 16f);
			Vector3f move = towards(poseStack, ring, lens).mul(reach);
			poseStack.translate(move.x, move.y, move.z);
			debug = "ring=" + ring + " reach=" + reach;
		}
		place(poseStack, settings.handPose, armPart, right, slim, swing, equip, t);

		Identifier skin = avatar.skin.body().texturePath();
		if (right) renderer.renderRightHand(poseStack, collector, light, skin, avatar.showRightSleeve);
		else renderer.renderLeftHand(poseStack, collector, light, skin, avatar.showLeftSleeve);

		poseStack.pushPose();
		armPart.translateAndRotate(poseStack);
		RingModels.render(poseStack, collector, light, settings.ringModel, !right, slim);
		poseStack.popPose();
		poseStack.popPose();
		return true;
	}

	private static void place(PoseStack poseStack, LabSettings.HandPose pose, ModelPart armPart, boolean right, boolean slim,
			float swing, float equip, Tuning t) {
		if (pose == LabSettings.HandPose.KNUCKLES_IN) aimArm(poseStack, armPart, right, slim, swing, equip);
		else placeArm(poseStack, right, swing, equip, t);
	}

	/**
	 * Points the arm from {@link #ELBOW} to {@link #FIST} with the back of the hand toward
	 * {@link #BACK}, leaving the pose at the arm's pivot like {@link #placeArm}.
	 */
	static void aimArm(PoseStack poseStack, ModelPart armPart, boolean right, boolean slim, float swing, float equip) {
		float f = right ? 1f : -1f;
		// A punch: the fist darts forward and in, then comes back.
		float sq = Mth.sqrt(swing);
		Vector3f fist = new Vector3f(FIST).add(-0.15f * Mth.sin(sq * Mth.PI), 0.1f * Mth.sin(sq * Mth.TWO_PI), -0.3f * Mth.sin(swing * Mth.PI));
		Vector3f elbow = new Vector3f(ELBOW);
		fist.y -= equip * 0.6f;
		elbow.y -= equip * 0.6f;
		fist.x *= f;
		elbow.x *= f;
		Vector3f along = new Vector3f(fist).sub(elbow).normalize();
		Vector3f back = new Vector3f(BACK);
		back.x *= f;
		back.sub(new Vector3f(along).mul(back.dot(along))).normalize();
		// Arm space: +y runs shoulder to fist, -x is the back of a right hand (+x for a left one).
		Vector3f xAxis = new Vector3f(back).mul(-f);
		Vector3f zAxis = new Vector3f(xAxis).cross(along);
		Matrix4f aim = new Matrix4f(
				xAxis.x, xAxis.y, xAxis.z, 0f,
				along.x, along.y, along.z, 0f,
				zAxis.x, zAxis.y, zAxis.z, 0f,
				0f, 0f, 0f, 1f);
		poseStack.translate(fist.x, fist.y, fist.z);
		poseStack.mulPose(aim);
		// The middle of the fist's end face goes on the fist point.
		float midX = f * (slim ? -0.5f : -1f);
		poseStack.translate(-(armPart.x + midX) / 16f, -(armPart.y + 10f) / 16f, -armPart.z / 16f);
	}

	/**
	 * Moves the pose from the first-person hand origin to the arm's shoulder: vanilla's bare-hand
	 * placement and swing, then our lift into view and twist so the back of the fist faces the eyes.
	 */
	static void placeArm(PoseStack poseStack, boolean right, float swing, float equip, Tuning t) {
		float f = right ? 1f : -1f;
		// The swing and equip motion vanilla uses for the bare hand.
		float sq = Mth.sqrt(swing);
		float sx = -0.3f * Mth.sin(sq * Mth.PI);
		float sy = 0.4f * Mth.sin(sq * Mth.TWO_PI);
		float sz = -0.4f * Mth.sin(swing * Mth.PI);
		// Lift the whole arm into view (screen space), then vanilla's bare-hand placement.
		poseStack.translate(f * t.screenX, t.screenY, t.screenZ);
		poseStack.translate(f * (sx + 0.64000005f), sy - 0.6f + equip * -0.6f, sz - 0.71999997f);
		poseStack.rotateDegrees(Axis.YP, f * 45f);
		float swingYaw = Mth.sin(sq * Mth.PI);
		float swingRoll = Mth.sin(swing * swing * Mth.PI);
		poseStack.rotateDegrees(Axis.YP, f * swingYaw * 70f);
		poseStack.rotateDegrees(Axis.ZP, f * swingRoll * -20f);
		poseStack.translate(f * -1f, 3.6f, 3.5f);
		poseStack.rotateDegrees(Axis.ZP, f * 120f);
		poseStack.rotateDegrees(Axis.XP, 200f);
		poseStack.rotateDegrees(Axis.YP, f * -135f);
		poseStack.translate(f * 5.6f, 0f, 0f);

		// Then turn the arm about its own length so the back of the fist faces the eyes, and tilt
		// it so the fist points down-forward.
		float pivotX = f * -5f / 16f;
		float pivotY = 2f / 16f;
		poseStack.translate(pivotX, pivotY, 0f);
		poseStack.rotateDegrees(Axis.XP, t.tilt);
		poseStack.rotateDegrees(Axis.ZP, f * t.lean);
		poseStack.rotateDegrees(Axis.YP, f * t.twist);
		poseStack.translate(-pivotX, -pivotY, 0f);
		poseStack.translate(f * t.dx, t.dy, t.dz);
	}

	/** Where a point ends up (in camera space) after {@code transform}, without keeping the transform. */
	static Vector3f pointAfter(PoseStack poseStack, Runnable transform, float x, float y, float z) {
		poseStack.pushPose();
		transform.run();
		Vector3f out = poseStack.last().pose().transformPosition(x, y, z, new Vector3f());
		poseStack.popPose();
		return out;
	}

	/** The offset, in the current pose's own axes, that would carry camera-space {@code from} to {@code to}. */
	static Vector3f towards(PoseStack poseStack, Vector3f from, Vector3f to) {
		Matrix4f inverse = new Matrix4f(poseStack.last().pose()).invert();
		return inverse.transformDirection(new Vector3f(to).sub(from));
	}
}
