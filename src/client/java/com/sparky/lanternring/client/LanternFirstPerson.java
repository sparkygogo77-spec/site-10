package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.ModRegistry;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.player.AvatarRenderer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.client.renderer.state.level.PlayerRenderState;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.PlayerModelType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;

/**
 * First person: the Power Battery held in the off hand is drawn as the Blockbench lantern hanging
 * from your fist and swinging as you move (see {@link LanternSway}). Holding right-click with the
 * ring raises it and pushes the ring into its lens while it lights up (timeline in
 * {@link LanternCharge}).
 */
public final class LanternFirstPerson {
	/** Lantern size in hand, relative to a placed block. */
	public static float scale = 0.42f;
	/** How far the gripping fist moves when the lantern is raised: toward the middle, up, forward. */
	public static final Vector3f RAISE_BY = new Vector3f(0.15f, 0.15f, 0f);
	/** The off hand sits higher than the ring hand so the lantern hanging under it is in view. */
	public static final RingFirstPerson.Tuning HOLD = new RingFirstPerson.Tuning(-30, 35, -35, 0, 0, 0, -0.3f, 0.75f);
	/** Last frame's positions, for screenshot tests to print. */
	public static String debug = "";
	/** How far the lantern turns its lens toward the ring hand when raised, in degrees. */
	public static float raisedYaw = 50f;
	/** The fist grips the top of the handle here, in arm space (skin pixels). */
	private static final float GRIP_Y = 10.5f;
	/** Top of the handle and the lens, in the lantern model's own units. */
	private static final float HANDLE_TOP = 20f;
	private static final Vector3f LENS = new Vector3f(0f, 7f, -5.4f);

	private static BbModel model;
	/** Where the lens was drawn last frame, in camera space; the ring hand aims at it. */
	private static Vector3f lensTarget;

	private LanternFirstPerson() {
	}

	/** Returns true when it drew the lantern, so the normal item rendering is skipped. */
	public static boolean render(PlayerRenderState playerState, InteractionHand hand, float swing, float equip,
			ItemStack stack, PoseStack poseStack, SubmitNodeCollector collector, int light, float partialTick) {
		if (hand != InteractionHand.OFF_HAND || !stack.is(ModRegistry.POWER_BATTERY_ITEM)) return false;
		AvatarRenderState avatar = playerState.avatarRenderState;
		if (avatar == null || avatar.skin == null) return false;
		if (model == null) model = BbModel.load("power_lantern");
		AvatarRenderer<?> renderer = Minecraft.getInstance().getEntityRenderDispatcher().getRenderer(avatar);
		boolean right = avatar.mainArm.getOpposite() == HumanoidArm.RIGHT;
		boolean slim = avatar.skin.model() == PlayerModelType.SLIM;
		float f = right ? 1f : -1f;
		ModelPart armPart = right ? renderer.getModel().rightArm : renderer.getModel().leftArm;
		float gripX = f * (slim ? -0.5f : -1f);

		float raise = raise(partialTick);
		poseStack.pushPose();
		Runnable place = () -> {
			RingFirstPerson.placeArm(poseStack, right, swing, equip, HOLD);
			armPart.translateAndRotate(poseStack);
		};
		poseStack.translate(-f * RAISE_BY.x * raise, RAISE_BY.y * raise, RAISE_BY.z * raise);

		// The arm, then the lantern hanging from wherever the fist ended up.
		Vector3f hangAbs = RingFirstPerson.pointAfter(poseStack, place, gripX / 16f, GRIP_Y / 16f, 0f);
		poseStack.pushPose();
		RingFirstPerson.placeArm(poseStack, right, swing, equip, HOLD);
		Identifier skin = avatar.skin.body().texturePath();
		if (right) renderer.renderRightHand(poseStack, collector, light, skin, avatar.showRightSleeve);
		else renderer.renderLeftHand(poseStack, collector, light, skin, avatar.showLeftSleeve);
		poseStack.popPose();

		Vector3f here = poseStack.last().pose().transformPosition(new Vector3f());
		Vector3f hang = RingFirstPerson.towards(poseStack, here, hangAbs);
		poseStack.translate(hang.x, hang.y, hang.z);
		float steady = 1f - raise;
		poseStack.rotateDegrees(Axis.ZP, LanternSway.roll(partialTick) * steady);
		poseStack.rotateDegrees(Axis.XP, LanternSway.pitch(partialTick) * steady);
		// Lens toward the camera, turning toward the ring hand as it rises.
		poseStack.rotateDegrees(Axis.YP, 180f + f * -1f * raisedYaw * raise);
		poseStack.scale(scale, scale, scale);
		poseStack.translate(0f, -HANDLE_TOP / 16f, 0f);

		float glow = glow(partialTick);
		model.render(poseStack, collector, light, BbModel.glow(Math.min(glow, 1f)));
		if (glow > 1f) model.renderGlow(poseStack, collector, BbModel.glow(glow - 1f));
		lensTarget = poseStack.last().pose().transformPosition(LENS.x / 16f, LENS.y / 16f, LENS.z / 16f, new Vector3f());
		debug = "grip=" + hangAbs + " lens=" + lensTarget + " raise=" + raise + " glow=" + glow;
		poseStack.popPose();
		return true;
	}

	/** The lantern's lens in camera space, or null if no lantern was drawn lately. */
	static Vector3f lensTarget() {
		return lensTarget;
	}

	// ---- timeline -----------------------------------------------------------------------

	/** Ticks right-click has been held with the ring and lantern, or -1 when not charging. */
	static float held(float partialTick) {
		LocalPlayer player = Minecraft.getInstance().player;
		if (player == null || !LanternCharge.isCharging(player)) return -1f;
		return 72000 - player.getUseItemRemainingTicks() + partialTick;
	}

	private static float smooth(float x) {
		x = Mth.clamp(x, 0f, 1f);
		return x * x * (3 - 2 * x);
	}

	/** 0 = hanging at your side, 1 = held up in front of you. */
	static float raise(float partialTick) {
		float t = held(partialTick);
		if (t < 0) return 0f;
		int hold = LanternCharge.HOLD;
		int done = LanternCharge.done();
		if (t < hold) return 0.12f * smooth(t / hold);
		if (t < done) return 0.12f + 0.88f * smooth((t - hold) / LanternCharge.REACH);
		return 1f - smooth((t - done) / LanternCharge.SETTLE);
	}

	/** 0 = ring hand in its normal place, 1 = ring pressed against the lens. */
	static float reach(float partialTick) {
		float t = held(partialTick);
		if (t < 0) return 0f;
		int start = LanternCharge.HOLD + 2;
		int done = LanternCharge.done();
		if (t < done) return smooth((t - start) / (LanternCharge.REACH - 2));
		return 1f - smooth((t - done) / LanternCharge.SETTLE);
	}

	/** Brightness of the lantern's light; above 1 it is drawn twice for the flash. */
	static float glow(float partialTick) {
		Minecraft mc = Minecraft.getInstance();
		float time = mc.level == null ? 0 : mc.level.getGameTime() + partialTick;
		float idle = 0.6f + 0.08f * Mth.sin(time * 0.15f);
		float t = held(partialTick);
		if (t < 0) return idle;
		int hold = LanternCharge.HOLD;
		int contact = hold + LanternCharge.REACH;
		int done = LanternCharge.done();
		// Pixel-y flicker: steps once per tick rather than smoothly.
		float flicker = ((int) t * 7919 % 13) / 13f;
		if (t < hold) return idle + 0.25f * (t / hold) + 0.1f * flicker;
		if (t < contact) return 0.95f + 0.15f * flicker;
		if (t < done) return 1f + 0.8f * ((t - contact) / (done - contact)) + 0.25f * flicker;
		return Math.max(idle, 2f - (t - done) / LanternCharge.SETTLE * 1.4f);
	}

	/** Called every client tick: motes drawn from the lantern into the ring while it charges. */
	public static void tick(Minecraft mc) {
		LanternSway.tick(mc);
		LocalPlayer player = mc.player;
		if (player == null || mc.level == null || mc.isPaused() || !mc.options.getCameraType().isFirstPerson()) return;
		float t = held(0f);
		int contact = LanternCharge.HOLD + LanternCharge.REACH;
		if (t < contact || t > LanternCharge.done()) return;
		// Roughly where the raised lantern is: a little ahead and to the off-hand side of the eyes.
		Vec3 look = player.getViewVector(1f);
		Vec3 side = look.cross(new Vec3(0, 1, 0)).normalize();
		float f = player.getMainArm() == HumanoidArm.RIGHT ? -1f : 1f;
		Vec3 lantern = player.getEyePosition().add(look.scale(1.4)).add(side.scale(0.3 * f)).add(0, -0.25, 0);
		RandomSource r = mc.level.getRandom();
		for (int i = 0; i < 2; i++) {
			Vec3 at = lantern.add((r.nextDouble() - 0.5) * 0.25, (r.nextDouble() - 0.5) * 0.25, (r.nextDouble() - 0.5) * 0.25);
			LabFx.spawn(ModParticles.MOTE, at, lantern.subtract(at).scale(0.12).add(0, 0.01, 0), 0.3f);
		}
	}
}
