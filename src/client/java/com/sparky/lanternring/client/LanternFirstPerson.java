package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.mojang.blaze3d.systems.RenderSystem;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.LanternRing;
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
import java.util.HashMap;
import java.util.Map;
import org.joml.Matrix4f;
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
	/** The left fist and shoulder at rest and with the lantern raised (mirrored for a left-handed player). */
	public static final Vector3f GRIP = new Vector3f(-0.4f, 0.15f, -1.0f);
	public static final Vector3f SHOULDER = new Vector3f(-0.75f, -0.5f, -0.35f);
	public static final Vector3f GRIP_RAISED = new Vector3f(-0.18f, 0.1f, -1.0f);
	public static final Vector3f SHOULDER_RAISED = new Vector3f(-0.6f, -0.62f, -0.35f);
	/** Last frame's positions, for screenshot tests to print. */
	public static String debug = "";
	/** How far the lantern turns its lens toward the ring hand when raised, in degrees. */
	public static float raisedYaw = 80f;
	/** The fist grips the top of the handle here, in arm space (skin pixels). */
	private static final float GRIP_Y = 10.5f;
	/**
	 * How far the lantern hangs to the side of the fist, toward the middle of the screen, so the
	 * fist holds the outer end of the handle bar and the arm stays clear of the lantern's side.
	 */
	public static float hangSide = 0.1f;
	/**
	 * One lantern look: its Blockbench model, its size in hand relative to {@link #scale}, the top
	 * of its handle and where its charging port sits (centred on the front face, low on the body),
	 * in the model's own units. The ring docks into the port.
	 */
	private record Look(String name, float size, float handleTop, Vector3f port) {
	}

	/** The port's size relative to its model (lantern_port.bbmodel is 10 units across). */
	private static final float PORT_SCALE = 0.7f;
	/** How far in front of the lantern's face the ring's face rests: on the port's sunken plate. */
	private static final float PORT_PLATE = 0.5f * PORT_SCALE;

	private static final Look KEYCHAIN = new Look("power_lantern", 1f, 20f, new Vector3f(0f, 7.5f, -6.4f));
	private static final Look DARK = new Look("dark_lantern", 0.88f, 23f, new Vector3f(0f, 7.5f, -4.4f));
	private static final Look STONE = new Look("stone_lantern", 0.9f, 21f, new Vector3f(0f, 6f, -3.5f));
	private static final Look TORUS = new Look("torus_lantern", 0.85f, 24f, new Vector3f(0f, 7f, -4.5f));
	private static final Look NEBULA = new Look("nebula_lantern", 0.85f, 21f, new Vector3f(0f, 9.5f, -5.05f));
	/** The Nebula battery's flowing glass: frames nebula_glass_f0..f23, each shown for this many ticks. */
	private static final int NEBULA_FRAMES = 24;
	private static final int NEBULA_FRAME_TICKS = 3;
	private static final Look COMPACT = new Look("compact_lantern", 0.85f, 18f, new Vector3f(0f, 5.5f, -4f));

	private static final Map<String, BbModel> MODELS = new HashMap<>();
	/** Where the lens was drawn last frame, and which way it faced, in camera space; the ring hand presses on it. */
	private static Vector3f lensTarget;
	private static Vector3f lensNormal;
	/** The lens in view space (as seen through the hand's fixed field of view), for the glare on screen. */
	private static Vector3f lensView;

	private LanternFirstPerson() {
	}

	/** Returns true when it drew the lantern, so the normal item rendering is skipped. */
	public static boolean render(PlayerRenderState playerState, InteractionHand hand, float swing, float equip,
			ItemStack stack, PoseStack poseStack, SubmitNodeCollector collector, int light, float partialTick) {
		if (hand != InteractionHand.OFF_HAND || !stack.is(ModRegistry.POWER_BATTERY_ITEM)) return false;
		AvatarRenderState avatar = playerState.avatarRenderState;
		if (avatar == null || avatar.skin == null) return false;
		Look look = switch (LabSettings.get().lanternModel) {
			case STONE -> STONE;
			case TORUS -> TORUS;
			case NEBULA -> NEBULA;
			case COMPACT -> COMPACT;
			case DARK -> DARK;
			case KEYCHAIN -> KEYCHAIN;
		};
		Corps corps = Corps.ofLantern(stack);
		BbModel model = MODELS.computeIfAbsent(look.name() + "/" + corps, k -> BbModel.load(look.name()).forCorps(corps));
		AvatarRenderer<?> renderer = Minecraft.getInstance().getEntityRenderDispatcher().getRenderer(avatar);
		boolean right = avatar.mainArm.getOpposite() == HumanoidArm.RIGHT;
		boolean slim = avatar.skin.model() == PlayerModelType.SLIM;
		float f = right ? 1f : -1f;
		ModelPart armPart = right ? renderer.getModel().rightArm : renderer.getModel().leftArm;
		float gripX = f * (slim ? -0.5f : -1f);

		float raise = raise(partialTick);
		// The fist (holding the handle) and the shoulder, in first-person hand space (x right,
		// y up, -z ahead) for a left hand; the shoulder is below and behind the screen's edge.
		Vector3f grip = new Vector3f(GRIP).lerp(GRIP_RAISED, raise);
		Vector3f shoulder = new Vector3f(SHOULDER).lerp(SHOULDER_RAISED, raise);
		grip.y -= equip * 0.6f;
		shoulder.y -= equip * 0.6f;
		grip.x *= -f;
		shoulder.x *= -f;

		poseStack.pushPose();
		armPart.resetPose();
		// Point the arm from the shoulder to the fist, back of the hand turned up toward the eyes.
		Vector3f along = new Vector3f(grip).sub(shoulder).normalize();
		Vector3f back = new Vector3f(0f, 1f, 0.6f);
		back.sub(new Vector3f(along).mul(back.dot(along))).normalize();
		Vector3f xAxis = new Vector3f(back).mul(-f);
		Vector3f zAxis = new Vector3f(xAxis).cross(along);
		Matrix4f aim = new Matrix4f(
				xAxis.x, xAxis.y, xAxis.z, 0f,
				along.x, along.y, along.z, 0f,
				zAxis.x, zAxis.y, zAxis.z, 0f,
				0f, 0f, 0f, 1f);
		poseStack.translate(grip.x, grip.y, grip.z);
		poseStack.mulPose(aim);
		poseStack.translate(-(armPart.x + gripX) / 16f, -(armPart.y + GRIP_Y) / 16f, -armPart.z / 16f);
		Identifier skin = avatar.skin.body().texturePath();
		if (right) renderer.renderRightHand(poseStack, collector, light, skin, avatar.showRightSleeve);
		else renderer.renderLeftHand(poseStack, collector, light, skin, avatar.showLeftSleeve);
		poseStack.popPose();

		// The lantern hangs from the fist.
		poseStack.pushPose();
		poseStack.translate(grip.x - f * hangSide, grip.y, grip.z);
		float steady = 1f - raise;
		poseStack.rotateDegrees(Axis.ZP, LanternSway.roll(partialTick) * steady);
		poseStack.rotateDegrees(Axis.XP, LanternSway.pitch(partialTick) * steady);
		// Lens toward the camera, turning toward the ring hand as it rises.
		poseStack.rotateDegrees(Axis.YP, 180f + f * -1f * raisedYaw * raise);
		poseStack.scale(scale * look.size(), scale * look.size(), scale * look.size());
		poseStack.translate(0f, -look.handleTop() / 16f, 0f);

		float glow = glow(partialTick);
		// The Nebula's orb is a tiny bright point at rest and swells into a sun inside the glass as the charge builds.
		float coreScale = 1f + 2.4f * smooth((glow - 0.75f) / 0.5f);
		model.render(poseStack, collector, light, BbModel.glow(Math.min(glow, 1f)), coreScale);
		if (glow > 1f) model.renderGlow(poseStack, collector, BbModel.glow(glow - 1f));
		if (look == NEBULA) {
			Minecraft mc = Minecraft.getInstance();
			long time = mc.level == null ? 0 : mc.level.getGameTime();
			int frame = (int) (time / NEBULA_FRAME_TICKS % NEBULA_FRAMES);
			BbModel glass = MODELS.computeIfAbsent("nebula_glass/" + corps + "/" + frame, k -> BbModel.load("nebula_glass")
					.retextured(LanternRing.id("textures/entity/bb/nebula_glass_f" + frame + ".png")).forCorps(corps));
			glass.render(poseStack, collector, light, BbModel.glow(1f));
		}
		// The charging port on the front, in the lantern's colour; the ring docks onto its plate.
		Vector3f port = look.port();
		BbModel portModel = MODELS.computeIfAbsent("lantern_port/" + corps, k -> BbModel.load("lantern_port").forCorps(corps));
		poseStack.pushPose();
		poseStack.translate(port.x / 16f, port.y / 16f, port.z / 16f);
		poseStack.scale(PORT_SCALE, PORT_SCALE, PORT_SCALE);
		portModel.render(poseStack, collector, light, BbModel.glow(Math.min(glow, 1f)));
		poseStack.popPose();
		lensTarget = poseStack.last().pose().transformPosition(port.x / 16f, port.y / 16f, (port.z - PORT_PLATE) / 16f, new Vector3f());
		lensNormal = poseStack.last().pose().transformDirection(0f, 0f, -1f, new Vector3f()).normalize();
		lensView = RenderSystem.getModelViewStack().transformPosition(new Vector3f(lensTarget));
		debug = "grip=" + grip + " lens=" + lensTarget + " raise=" + raise + " glow=" + glow + " view=" + lensView;
		poseStack.popPose();
		return true;
	}

	/** The lantern's lens in camera space, or null if no lantern was drawn lately. */
	static Vector3f lensTarget() {
		return lensTarget;
	}

	/** The lens in view space, or null if no lantern was drawn lately. */
	static Vector3f lensView() {
		return lensView;
	}

	/** The lens's outward facing in camera space, or null if no lantern was drawn lately. */
	static Vector3f lensNormal() {
		return lensNormal;
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
		int hold = LanternCharge.hold();
		int done = LanternCharge.done();
		if (t < hold) return 0.12f * smooth(t / hold);
		if (t < done) return 0.12f + 0.88f * smooth((t - hold) / LanternCharge.REACH);
		return 1f - smooth((t - done) / LanternCharge.SETTLE);
	}

	/** 0 = ring hand in its normal place, 1 = ring pressed against the lens. */
	static float reach(float partialTick) {
		float t = held(partialTick);
		if (t < 0) return 0f;
		int start = LanternCharge.hold() + 2;
		int done = LanternCharge.done();
		if (t < done) return smooth((t - start) / (LanternCharge.REACH - 2));
		return 1f - smooth((t - done) / LanternCharge.SETTLE);
	}

	/** Brightness of the lantern's light; above 1 it is drawn twice for the flash. */
	static float glow(float partialTick) {
		// Steady when idle. The build-up to blinding, the climax and the smooth settle afterwards
		// (which plays on after letting go) come from the glare.
		float idle = LanternGlare.IDLE;
		float light = LanternGlare.light(partialTick);
		if (light >= 0) return light;
		float t = held(partialTick);
		if (t < 0) return idle;
		int hold = LanternCharge.hold();
		// Pixel-y flicker: steps once per tick rather than smoothly.
		float flicker = ((int) t * 7919 % 13) / 13f;
		if (t < hold) return idle + 0.25f * (t / hold) + 0.1f * flicker;
		return idle;
	}

	/** Called every client tick: motes drawn from the lantern into the ring while it charges. */
	public static void tick(Minecraft mc) {
		LanternSway.tick(mc);
		LocalPlayer player = mc.player;
		if (player == null || mc.level == null || mc.isPaused() || !mc.options.getCameraType().isFirstPerson()) return;
		float t = held(0f);
		int contact = LanternCharge.hold() + LanternCharge.REACH;
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
