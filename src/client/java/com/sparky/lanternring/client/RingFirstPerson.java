package com.sparky.lanternring.client;

import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.item.PowerRingItem;
import net.minecraft.client.Camera;
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
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.player.PlayerModelType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import org.joml.Matrix4f;
import org.joml.Quaternionf;
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
	public static final Vector3f FIST = new Vector3f(0.28f, -0.22f, -0.6f);
	public static final Vector3f ELBOW = new Vector3f(0.5f, -0.9f, -1.0f);
	/** Which way the back of the hand faces: up and away, so the knuckles run along the top of the face. */
	public static final Vector3f BACK = new Vector3f(0f, 1f, -0.6f);

	/**
	 * Ring forward: the fist held low to the right with its punching face, where the ring sits,
	 * looking ahead, back of the hand up. Same space as {@link #FIST}. Mutable so tests can sweep them.
	 */
	public static final Vector3f FORWARD_FIST = new Vector3f(0.32f, -0.32f, -0.8f);
	public static final Vector3f FORWARD_ELBOW = new Vector3f(0.55f, -0.75f, -0.1f);
	public static final Vector3f FORWARD_BACK = new Vector3f(0f, 1f, 0f);

	/**
	 * Firing a power (and holding Wall or Dome): the arm punches out toward the crosshair, back of
	 * the hand up, like the third-person aim. Same space as {@link #FIST}. Mutable so tests can sweep them.
	 */
	public static final Vector3f AIM_FIST = new Vector3f(0.17f, -0.2f, -0.95f);
	public static final Vector3f AIM_ELBOW = new Vector3f(0.4f, -0.5f, -0.2f);
	public static final Vector3f AIM_BACK = new Vector3f(0f, 1f, 0f);
	/**
	 * Charging from the lantern, on the way to its port: the elbow bent and the forearm stood up,
	 * the fist turned up so the ring faces you. Same space as {@link #FIST}. Mutable so tests can sweep them.
	 */
	public static final Vector3f SHOW_FIST = new Vector3f(0.32f, -0.26f, -0.98f);
	public static final Vector3f SHOW_ELBOW = new Vector3f(0.45f, -1.0f, -0.82f);
	public static final Vector3f SHOW_BACK = new Vector3f(0f, 0.3f, -1f);
	/**
	 * Degrees the fist is turned clockwise about the arm on the port: a quarter turn, thumb up and
	 * the knuckles running down, with the ring on the knuckle facing ahead into the port. Mutable so
	 * tests can sweep it.
	 */
	public static float pressRoll = 90f;
	/** Holding the Shield: the forearm comes up level across the front, behind the shield (see RiotShields). */
	// J: not pulled across the body any more: the arm pushes straight out, fist up, projecting the shield ahead.
	public static final Vector3f GUARD_FIST = new Vector3f(0.2f, -0.24f, -0.74f);
	public static final Vector3f GUARD_ELBOW = new Vector3f(0.42f, -0.46f, -0.32f);
	public static final Vector3f GUARD_BACK = new Vector3f(0f, 0.7f, 1f);
	/** A slam's dive (pass 510, primed pass 518): the ring fist driven out ahead and down, leading you into the ground. */
	public static final Vector3f DIVE_FIST = new Vector3f(0.14f, -0.42f, -0.9f);
	public static final Vector3f DIVE_ELBOW = new Vector3f(0.38f, -0.42f, -0.25f);
	public static final Vector3f DIVE_BACK = new Vector3f(0f, 1f, 0.3f);
	/** Rebuilding a primed crater (pass 518): the arm out low, the ring pointed at the blocks coming back. */
	public static final Vector3f REBUILD_FIST = new Vector3f(0.22f, -0.32f, -1.0f);
	public static final Vector3f REBUILD_ELBOW = new Vector3f(0.45f, -0.5f, -0.3f);
	public static final Vector3f REBUILD_BACK = new Vector3f(0f, 0.6f, 1f);
	/** Building the Fear Nuke: the fist raised high in the corner of the view, back of the hand to you, holding the bomb up. */
	public static final Vector3f NUKE_FIST = new Vector3f(0.5f, -0.12f, -1.3f);
	public static final Vector3f NUKE_ELBOW = new Vector3f(0.68f, -0.85f, -1.0f);
	public static final Vector3f NUKE_BACK = new Vector3f(0.2f, 0f, 1f);

	/**
	 * Where the ring's face was last drawn, per arm (right, left): in view space (x right, y up, z
	 * back from the camera) at hand-view scale (the hand is drawn with a fixed 70 degree field of
	 * view). View space, not world directions, because shader mods (Iris, Lunar) draw the hand with
	 * their own pose stack that may leave out the camera's turn. See {@link #drawnFace}.
	 */
	private static final Vector3f[] DRAWN_FACE = new Vector3f[2];
	private static final long[] DRAWN_AT = new long[2];
	static final float HAND_FOV = 70f;

	/**
	 * Where the ring drawn on the first-person fist appears in the world, so effects placed there
	 * line up with it on screen at any field of view. Null when the fist hasn't been drawn lately
	 * (hidden HUD, another item).
	 */
	public static Vec3 drawnFace(Minecraft mc, HumanoidArm arm) {
		int i = arm == HumanoidArm.RIGHT ? 0 : 1;
		Vector3f at = DRAWN_FACE[i];
		if (at == null || System.nanoTime() - DRAWN_AT[i] > 200_000_000L) return null;
		Camera camera = mc.gameRenderer.mainCamera();
		// Same spot on screen, seen through the world's field of view instead of the hand's.
		double k = Math.tan(Math.toRadians(camera.getFov()) / 2) / Math.tan(Math.toRadians(HAND_FOV) / 2);
		Vector3f world = camera.rotation().transform(new Vector3f((float) (at.x * k), (float) (at.y * k), at.z));
		return camera.position().add(world.x, world.y, world.z);
	}

	/**
	 * Where the ring's face was last drawn on the first-person fist, in view space at hand-view
	 * scale (see {@link #DRAWN_FACE}), for things drawn over it on screen. Null when it hasn't been lately.
	 */
	public static Vector3f drawnView(HumanoidArm arm) {
		int i = arm == HumanoidArm.RIGHT ? 0 : 1;
		Vector3f at = DRAWN_FACE[i];
		return at == null || System.nanoTime() - DRAWN_AT[i] > 200_000_000L ? null : new Vector3f(at);
	}

	/** Last frame's ring face and facing (when {@link #recordDebug} is on), for screenshot tests to print. */
	public static String debug = "";
	public static boolean recordDebug;

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
		Matrix4f base = new Matrix4f(poseStack.last().pose());
		org.joml.Matrix3f baseNormal = new org.joml.Matrix3f(poseStack.last().normal());
		poseStack.pushPose();
		// Charging from the lantern: the arm bends to show the ring, lines it up and the port pulls it in.
		ChargeMotion.Weights reach = hand == InteractionHand.MAIN_HAND ? ChargeMotion.local(partialTick) : ChargeMotion.Weights.NONE;
		// Firing a power or flying forward: the arm points the ring where you look.
		float point = LanternFirstPerson.held(partialTick) >= 0 ? 0f : FlightPoses.localPoint(partialTick);
		float[] face = RingModels.ringFace(settings.ringModel, !right, slim);
		Runnable rest = () -> {
			switch (settings.handPose) {
				case RING_FORWARD -> aimArm(poseStack, armPart, right, slim, swing, equip, FORWARD_FIST, FORWARD_ELBOW, FORWARD_BACK);
				case KNUCKLES_IN -> aimArm(poseStack, armPart, right, slim, swing, equip, FIST, ELBOW, BACK);
				default -> placeArm(poseStack, right, swing, equip, t);
			}
		};
		Runnable pointing = () -> aimArm(poseStack, armPart, right, slim, swing, equip, AIM_FIST, AIM_ELBOW, AIM_BACK);
		Runnable placed = blend(poseStack, rest, pointing, point);
		Vector3f lens = LanternFirstPerson.lensTarget(base);
		Vector3f lensNormal = LanternFirstPerson.lensNormal(base);
		if (reach.show() > 0f && lens != null && lensNormal != null) {
			float[] dock = RingModels.dockFace(settings.ringModel, !right, slim);
			Runnable show = () -> aimArm(poseStack, armPart, right, slim, swing, equip, SHOW_FIST, SHOW_ELBOW, SHOW_BACK);
			Vector3f off = new Vector3f(lensNormal).mul(ChargeMotion.HOVER).add(lens);
			Runnable line = () -> pressRing(poseStack, armPart, right, dock, off, lensNormal);
			Runnable press = () -> pressRing(poseStack, armPart, right, dock, lens, lensNormal);
			placed = blend(poseStack, placed, show, reach.show());
			placed = blend(poseStack, placed, line, reach.line());
			placed = blend(poseStack, placed, press, reach.pull());
		}
		// Holding the Shield: the arm is pulled up across the body behind it.
		float guard = RiotShields.raise(Minecraft.getInstance().player, partialTick);
		if (guard > 0f && hand == RiotShields.hand(Minecraft.getInstance().player)) {
			Runnable guarding = () -> aimArm(poseStack, armPart, right, slim, swing, equip, GUARD_FIST, GUARD_ELBOW, GUARD_BACK);
			placed = blend(poseStack, placed, guarding, guard);
		}
		// Building the Fear Nuke: the fist goes up and holds the bomb over your head.
		float nuke = NukeHold.raise(Minecraft.getInstance().player, partialTick);
		if (nuke > 0f && arm == NukeHold.arm(Minecraft.getInstance().player)) {
			Runnable raised = () -> aimArm(poseStack, armPart, right, slim, 0f, equip, NUKE_FIST, NUKE_ELBOW, NUKE_BACK);
			placed = blend(poseStack, placed, raised, nuke);
		}
		// A slam's dive and landing: the ring fist leads (pass 510 and 518), rebuilding the crater points the ring at it, and a dash strike leads with it.
		Player self = Minecraft.getInstance().player;
		if (self != null && hand == InteractionHand.MAIN_HAND) {
			float dive = CombatPoses.slamFist(self.getId(), partialTick);
			if (dive > 0f) {
				Runnable diving = () -> aimArm(poseStack, armPart, right, slim, 0f, equip, DIVE_FIST, DIVE_ELBOW, DIVE_BACK);
				placed = blend(poseStack, placed, diving, dive);
			}
			float rebuild = CombatPoses.rebuilding(self.getId(), partialTick);
			if (rebuild > 0f) {
				Runnable pointing2 = () -> aimArm(poseStack, armPart, right, slim, 0f, equip, REBUILD_FIST, REBUILD_ELBOW, REBUILD_BACK);
				placed = blend(poseStack, placed, pointing2, rebuild);
			}
			// The dash strike (pass 505 R3a-3): the ring fist leads the dash, punched out ahead, until just after the hit.
			float dash = CombatPoses.dashFist(self.getId(), partialTick);
			if (dash > 0f) placed = blend(poseStack, placed, pointing, dash);
		}
		placed.run();

		Identifier skin = avatar.skin.body().texturePath();
		if (right) renderer.renderRightHand(poseStack, collector, light, skin, avatar.showRightSleeve);
		else renderer.renderLeftHand(poseStack, collector, light, skin, avatar.showLeftSleeve);
		RingAuraLayer.submitArm(poseStack, collector, armPart, partialTick);

		poseStack.pushPose();
		armPart.translateAndRotate(poseStack);
		if (recordDebug) {
			Matrix4f local = new Matrix4f(base).invert().mul(poseStack.last().pose());
			debug = "point=" + point + " reach=" + reach + " lens=" + lens + " face=" + local.transformPosition(face[0] / 16f, face[1] / 16f, face[2] / 16f, new Vector3f())
				+ " facing=" + local.transformDirection(0f, 1f, 0f, new Vector3f()) + " swing=" + swing + " equip=" + equip;
		}
		Vector3f drawn = poseStack.last().pose().transformPosition(face[0] / 16f, face[1] / 16f, face[2] / 16f, new Vector3f());
		// Into view space: vanilla's pose stack holds the camera's turn undone and the model-view
		// redoes it; a shader mod may skip both. Either way this gives the spot relative to the eye.
		RenderSystem.getModelViewStack().transformPosition(drawn);
		DRAWN_FACE[right ? 0 : 1] = drawn;
		DRAWN_AT[right ? 0 : 1] = System.nanoTime();
		Player charger = Minecraft.getInstance().player;
		RingModels.glintBoost = charger != null && RingEmit.ringArm(charger) == arm ? LanternFlash.sun(charger, partialTick) : 0f;
		// Pass 515: the ring burns brighter with super speed.
		if (charger != null) RingModels.glintBoost = Math.max(RingModels.glintBoost, SuperSpeedFx.glow(charger));
		RingModels.render(poseStack, collector, light, settings.ringModel, !right, slim);
		RingModels.glintBoost = 0f;
		Player player = Minecraft.getInstance().player;
		if (player != null && RingEmit.ringArm(player) == arm) {
			BeamChargeGlow.renderFlash(poseStack, collector, RingEmit.flare(player, partialTick), player.tickCount + partialTick,
					settings.ringModel, !right, slim, true);
			BeamChargeGlow.renderHold(poseStack, collector, RingEmit.held(player, partialTick), player.tickCount + partialTick,
					settings.ringModel, !right, slim, true);
			BeamChargeGlow.renderSun(poseStack, collector, LanternFlash.sun(player, partialTick), player.tickCount + partialTick,
					settings.ringModel, !right, slim, true);
		}
		if (player != null && BeamChargeGlow.chargingArm(player) == arm) {
			BeamChargeGlow.render(poseStack, collector, BeamChargeGlow.progress(player, partialTick), player.tickCount + partialTick,
					settings.ringModel, !right, slim);
		}
		poseStack.popPose();
		poseStack.popPose();
		return true;
	}

	/**
	 * Roughly where the ring's face sits in front of your eyes, as {right, down, ahead} in blocks,
	 * for effects that start at the ring (beams, the lasso rope). {@code point} as in
	 * {@link FlightPoses#localPoint}.
	 */
	public static float[] ringOffset(float point) {
		float[] rest = switch (LabSettings.get().handPose) {
			case RING_FORWARD -> new float[] {0.3f, 0.26f, 0.85f};
			default -> new float[] {0.3f, 0.33f, 0.62f};
		};
		float[] aimed = {0.17f, 0.14f, 1.0f};
		for (int i = 0; i < 3; i++) rest[i] = Mth.lerp(point, rest[i], aimed[i]);
		return rest;
	}

	/** Runs {@code from}, or {@code to}, or a blend of the two by {@code w} (0..1). */
	private static Runnable blend(PoseStack poseStack, Runnable from, Runnable to, float w) {
		if (w <= 0f) return from;
		if (w >= 1f) return to;
		return () -> {
			// Both poses are rigid moves, so blend them as a slide plus a turn.
			Matrix4f a = relative(poseStack, from);
			Matrix4f b = relative(poseStack, to);
			Vector3f move = a.getTranslation(new Vector3f()).lerp(b.getTranslation(new Vector3f()), w);
			Quaternionf turn = a.getNormalizedRotation(new Quaternionf()).slerp(b.getNormalizedRotation(new Quaternionf()), w);
			poseStack.mulPose(new Matrix4f().translation(move).rotate(turn));
		};
	}

	/**
	 * Turns the fist so the ring's face lies flat on the lantern's lens, and slides it there.
	 * {@code face} is {@link RingModels#dockFace}: a face looking out of the punching face (arm +y)
	 * is pressed fist first; one looking out of the back of the hand (a box ring's gem) is pressed
	 * with the back of the hand, the fist raised. {@code lens} and {@code normal} are camera space.
	 */
	static void pressRing(PoseStack poseStack, ModelPart armPart, boolean right, float[] face, Vector3f lens, Vector3f normal) {
		float f = right ? 1f : -1f;
		Matrix4f inverse = new Matrix4f(poseStack.last().pose()).invert();
		Vector3f at = inverse.transformPosition(new Vector3f(lens));
		// Into the lens, against its outward normal.
		Vector3f into = inverse.transformDirection(new Vector3f(normal)).negate().normalize();
		if (face.length > 3 && face[3] > 0.5f) {
			// The back of the hand goes onto the lens, the fist raised beside the lantern.
			Vector3f along = new Vector3f(0f, 1f, 0f);
			along.sub(new Vector3f(into).mul(along.dot(into)));
			if (along.lengthSquared() < 1e-4f) along.set(0f, 0f, -1f).sub(new Vector3f(into).mul(into.z));
			along.normalize();
			orient(poseStack, armPart, f, along, into, at, face[0], face[1], face[2]);
			return;
		}
		// Back of the hand up, so the arm comes in level from the side, then the fist turned
		// clockwise about the arm until the thumb is up and the knuckles run downward.
		Vector3f back = new Vector3f(0f, 1f, 0f);
		back.sub(new Vector3f(into).mul(back.dot(into)));
		if (back.lengthSquared() < 1e-4f) back.set(0f, 0f, -1f).sub(new Vector3f(into).mul(into.z));
		back.normalize();
		back.rotateAxis(f * pressRoll * Mth.DEG_TO_RAD, into.x, into.y, into.z);
		orient(poseStack, armPart, f, into, back, at, face[0], face[1], face[2]);
	}

	/**
	 * Turns arm space so +y runs along {@code along} with the back of the hand toward {@code back},
	 * and puts the arm-space point {@code (px, py, pz)} (skin pixels) at {@code at}, leaving the pose
	 * at the arm's pivot like {@link #placeArm}.
	 */
	private static void orient(PoseStack poseStack, ModelPart armPart, float f, Vector3f along, Vector3f back, Vector3f at,
			float px, float py, float pz) {
		// Arm space: +y runs shoulder to fist, -x is the back of a right hand (+x for a left one).
		Vector3f xAxis = new Vector3f(back).mul(-f);
		Vector3f zAxis = new Vector3f(xAxis).cross(along);
		Matrix4f aim = new Matrix4f(
				xAxis.x, xAxis.y, xAxis.z, 0f,
				along.x, along.y, along.z, 0f,
				zAxis.x, zAxis.y, zAxis.z, 0f,
				0f, 0f, 0f, 1f);
		poseStack.translate(at.x, at.y, at.z);
		poseStack.mulPose(aim);
		poseStack.translate(-(armPart.x + px) / 16f, -(armPart.y + py) / 16f, -(armPart.z + pz) / 16f);
	}

	/** What {@code transform} would multiply onto the current pose, without keeping it. */
	private static Matrix4f relative(PoseStack poseStack, Runnable transform) {
		Matrix4f inverse = new Matrix4f(poseStack.last().pose()).invert();
		poseStack.pushPose();
		transform.run();
		Matrix4f out = inverse.mul(poseStack.last().pose());
		poseStack.popPose();
		return out;
	}

	/**
	 * Points the arm from {@code elbowAt} to {@code fistAt} with the back of the hand toward
	 * {@code backDir}, leaving the pose at the arm's pivot like {@link #placeArm}.
	 */
	static void aimArm(PoseStack poseStack, ModelPart armPart, boolean right, boolean slim, float swing, float equip,
			Vector3f fistAt, Vector3f elbowAt, Vector3f backDir) {
		float f = right ? 1f : -1f;
		// A punch: the fist darts forward and in, then comes back.
		float sq = Mth.sqrt(swing);
		Vector3f fist = new Vector3f(fistAt).add(-0.15f * Mth.sin(sq * Mth.PI), 0.1f * Mth.sin(sq * Mth.TWO_PI), -0.3f * Mth.sin(swing * Mth.PI));
		Vector3f elbow = new Vector3f(elbowAt);
		fist.y -= equip * 0.6f;
		elbow.y -= equip * 0.6f;
		fist.x *= f;
		elbow.x *= f;
		Vector3f along = new Vector3f(fist).sub(elbow).normalize();
		Vector3f back = new Vector3f(backDir);
		back.x *= f;
		back.sub(new Vector3f(along).mul(back.dot(along))).normalize();
		// The middle of the fist's end face goes on the fist point.
		orient(poseStack, armPart, f, along, back, fist, f * (slim ? -0.5f : -1f), 10f, 0f);
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
}
