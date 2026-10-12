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
	/** Carried at the hip: the fist and shoulder at rest, out of sight below the screen. */
	public static final Vector3f GRIP_HIP = new Vector3f(-0.45f, -0.8f, -0.75f);
	public static final Vector3f SHOULDER_HIP = new Vector3f(-0.7f, -1.3f, -0.35f);
	/** Floating or summoned: where the lantern's handle top hovers at rest. */
	public static final Vector3f FLOAT_REST = new Vector3f(-0.5f, 0.12f, -1.15f);
	/** Ticks the summoned lantern takes to fade back into light once the ring is full. */
	static final float FADE = 18f;
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
	 * of its handle and where the ring docks on its front, in the model's own units. Lanterns with
	 * an emblem, lens or socket of their own dock on that ({@code socket} null); the plain ones get
	 * a small round socket set into the face, in their own trim ({@code socket} is the texture
	 * suffix: "" for dark jade metal, "_stone" for mossy stone).
	 */
	record Look(String name, float size, float handleTop, Vector3f port, String socket) {
	}

	/** How far in front of the face the ring's face rests in a socket: on its sunken disc. */
	private static final float SOCKET_DISC = 0.25f;

	private static final Look KEYCHAIN = new Look("power_lantern", 1f, 20f, new Vector3f(0f, 8f, -5.55f), null);
	private static final Look DARK = new Look("dark_lantern", 0.82f, 26f, new Vector3f(0f, 9f, -4.85f), null);
	private static final Look CLASSIC = new Look("classic_lantern", 0.88f, 22f, new Vector3f(0f, 9.5f, -7.05f), null);
	/** The Red Lantern battery: every red lantern, whatever look is picked in the Ring Lab. */
	private static final Look RED = new Look("red_lantern", 0.72f, 27.3f, new Vector3f(0f, 11f, -7.05f), null);
	/** The blue corps' own lantern (Blue Lantern sheet): docks on the emblem window in front. */
	private static final Look BLUE = new Look("blue_lantern", 0.88f, 21f, new Vector3f(0f, 8f, -5.75f), null);
	private static final Look STONE = new Look("stone_lantern", 0.88f, 22f, new Vector3f(0f, 7f, -4.52f), "_stone");
	private static final Look TORUS = new Look("torus_lantern", 0.85f, 24f, new Vector3f(0f, 10f, -4.75f), null);
	private static final Look NEBULA = new Look("nebula_lantern", 0.85f, 21f, new Vector3f(0f, 11.5f, -5.05f), null);
	/** The Nebula battery's flowing glass: frames nebula_glass_f0..f23, each shown for this many ticks. */
	private static final int NEBULA_FRAMES = 24;
	private static final int NEBULA_FRAME_TICKS = 3;
	private static final Look COMPACT = new Look("compact_lantern", 0.85f, 18f, new Vector3f(0f, 7f, -4.25f), null);

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
		Corps corps = Corps.ofLantern(stack);
		Look look = look(corps);
		LabSettings.ChargeStyle style = LabSettings.get().chargeStyle;
		// Set down as a shrine: it's drawn in the world (see LanternShrine), and the ring docks there.
		if (style == LabSettings.ChargeStyle.SHRINE && LanternShrine.active()) {
			LanternShrine.aimRing();
			return true;
		}
		AvatarRenderer<?> renderer = Minecraft.getInstance().getEntityRenderDispatcher().getRenderer(avatar);
		boolean right = avatar.mainArm.getOpposite() == HumanoidArm.RIGHT;
		boolean slim = avatar.skin.model() == PlayerModelType.SLIM;
		float f = right ? 1f : -1f;
		ModelPart armPart = right ? renderer.getModel().rightArm : renderer.getModel().leftArm;
		float gripX = f * (slim ? -0.5f : -1f);

		float raise = raise(partialTick);
		boolean held = style.inHand();
		boolean hip = style == LabSettings.ChargeStyle.HIP;
		// The fist (holding the handle) and the shoulder, in first-person hand space (x right,
		// y up, -z ahead) for a left hand; the shoulder is below and behind the screen's edge.
		// Carried at the hip, both start out of sight below the screen.
		Vector3f grip = new Vector3f(hip ? GRIP_HIP : GRIP).lerp(GRIP_RAISED, raise);
		Vector3f shoulder = new Vector3f(hip ? SHOULDER_HIP : SHOULDER).lerp(SHOULDER_RAISED, raise);
		grip.y -= equip * 0.6f;
		shoulder.y -= equip * 0.6f;
		grip.x *= -f;
		shoulder.x *= -f;

		if (held) {
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
		}

		float size = 1f;
		poseStack.pushPose();
		if (held) {
			// The lantern hangs from the fist.
			poseStack.translate(grip.x - f * hangSide, grip.y, grip.z);
			float steady = 1f - raise;
			poseStack.rotateDegrees(Axis.ZP, LanternSway.roll(partialTick) * steady);
			poseStack.rotateDegrees(Axis.XP, LanternSway.pitch(partialTick) * steady);
		} else {
			// Floating (or summoned) on its own off to the side, bobbing gently, and gliding in front of
			// you as the charge starts.
			if (style == LabSettings.ChargeStyle.SUMMON) {
				size = summoned(partialTick);
				if (size <= 0.01f) {
					poseStack.popPose();
					lensTarget = null;
					return true;
				}
			}
			Minecraft mc = Minecraft.getInstance();
			float time = mc.level == null ? 0 : mc.level.getGameTime() + partialTick;
			Vector3f at = new Vector3f(FLOAT_REST).lerp(GRIP_RAISED, raise);
			at.x *= -f;
			at.y += 0.025f * Mth.sin(time * 0.08f) * (1f - raise);
			poseStack.translate(at.x, at.y - equip * 0.6f, at.z);
			poseStack.rotateDegrees(Axis.ZP, 3f * Mth.sin(time * 0.05f) * (1f - raise));
		}
		// Lens toward the camera, turning toward the ring hand as it rises.
		poseStack.rotateDegrees(Axis.YP, 180f + f * -1f * raisedYaw * raise);
		float s = scale * look.size() * size;
		poseStack.scale(s, s, s);
		poseStack.translate(0f, -look.handleTop() / 16f, 0f);

		float glow = glow(partialTick);
		Vector3f dock = drawLantern(poseStack, collector, light, look, corps, glow);
		lensTarget = poseStack.last().pose().transformPosition(dock, new Vector3f());
		lensNormal = poseStack.last().pose().transformDirection(0f, 0f, -1f, new Vector3f()).normalize();
		lensView = RenderSystem.getModelViewStack().transformPosition(new Vector3f(lensTarget));
		debug = "grip=" + grip + " lens=" + lensTarget + " raise=" + raise + " glow=" + glow + " view=" + lensView + " style=" + style;
		poseStack.popPose();
		return true;
	}

	/** The lantern look for this corps: the Red Lantern's own, else the one picked in the Ring Lab. */
	static Look look(Corps corps) {
		return corps == Corps.RED ? RED : corps == Corps.BLUE ? BLUE : switch (LabSettings.get().lanternModel) {
			case STONE -> STONE;
			case CLASSIC -> CLASSIC;
			case TORUS -> TORUS;
			case NEBULA -> NEBULA;
			case COMPACT -> COMPACT;
			case DARK -> DARK;
			case KEYCHAIN -> KEYCHAIN;
		};
	}

	/**
	 * Draws the lantern (standing on 0,0,0 in the model's own units scaled by the pose) with its
	 * light at {@code glow}, and returns where the ring docks on it, in the same space.
	 */
	static Vector3f drawLantern(PoseStack poseStack, SubmitNodeCollector collector, int light, Look look, Corps corps, float glow) {
		BbModel model = MODELS.computeIfAbsent(look.name() + "/" + corps,
				k -> look == RED || look == BLUE ? BbModel.load(look.name()) : BbModel.load(look.name()).forCorps(corps));
		// The Stone Lantern's light is sealed in: its cracks barely seep at rest and blaze as it charges.
		if (look == STONE && glow <= 1f) glow = Mth.clamp((glow - 0.55f) / 0.4f, 0.1f, 1f);
		// The Blue Lantern's windows always show its light: hope never goes out.
		if (look == BLUE) glow = Math.max(glow, 0.75f);
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
		// Where the ring docks: the lantern's own emblem, lens or socket, or a small socket set into
		// a plain face (its disc glows in the lantern's colour).
		Vector3f port = look.port();
		float plate = 0f;
		if (look.socket() != null) {
			plate = SOCKET_DISC;
			BbModel socket = MODELS.computeIfAbsent("lantern_port" + look.socket() + "/" + corps, k -> BbModel.load("lantern_port")
					.retextured(LanternRing.id("textures/entity/bb/lantern_port" + look.socket() + ".png")).forCorps(corps));
			poseStack.pushPose();
			poseStack.translate(port.x / 16f, port.y / 16f, port.z / 16f);
			socket.render(poseStack, collector, light, BbModel.glow(Math.min(glow, 1f)));
			poseStack.popPose();
		}
		return new Vector3f(port.x / 16f, port.y / 16f, (port.z - plate) / 16f);
	}

	/** Sets where the ring docks this frame, for a lantern drawn somewhere else (the shrine). */
	static void dockAt(Vector3f target, Vector3f normal, Vector3f view) {
		lensTarget = target;
		lensNormal = normal;
		lensView = view;
	}

	/**
	 * How much of the summoned lantern has formed: nothing at rest, growing out of light as the
	 * charge starts, whole while it charges, and fading away once the ring is full.
	 */
	static float summoned(float partialTick) {
		float a = LanternGlare.after(partialTick);
		if (a >= 0) return 1f - smooth(a / FADE);
		float t = held(partialTick);
		if (t < 0 || t >= LanternCharge.done()) return 0f;
		return smooth(t / (LanternCharge.hold() + LanternCharge.REACH));
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
		LabSettings.ChargeStyle style = LabSettings.get().chargeStyle;
		if (style == LabSettings.ChargeStyle.SHRINE && LanternShrine.active()) return;
		float t = held(0f);
		int contact = LanternCharge.hold() + LanternCharge.REACH;
		// Roughly where the raised lantern is: a little ahead and to the off-hand side of the eyes.
		Vec3 look = player.getViewVector(1f);
		Vec3 side = look.cross(new Vec3(0, 1, 0)).normalize();
		float f = player.getMainArm() == HumanoidArm.RIGHT ? -1f : 1f;
		Vec3 lantern = player.getEyePosition().add(look.scale(1.4)).add(side.scale(0.3 * f)).add(0, -0.25, 0);
		RandomSource r = mc.level.getRandom();
		if (style == LabSettings.ChargeStyle.SUMMON) {
			float a = LanternGlare.after(0f);
			if (t >= 0 && t < contact) {
				// Light gathering into the lantern as it forms.
				for (int i = 0; i < 3; i++) {
					Vec3 from = lantern.add(r.nextGaussian() * 0.5, r.nextGaussian() * 0.5, r.nextGaussian() * 0.5);
					LabFx.spawn(ModParticles.MOTE, from, lantern.subtract(from).scale(0.18), 0.3f);
				}
			} else if (a >= 0 && a < FADE) {
				// And scattering back into light as it fades.
				for (int i = 0; i < 3; i++) {
					LabFx.spawn(ModParticles.MOTE, lantern, new Vec3(r.nextGaussian(), r.nextGaussian(), r.nextGaussian()).scale(0.05), 0.3f);
				}
			}
		}
		if (t < contact || t > LanternCharge.done()) return;
		for (int i = 0; i < 2; i++) {
			Vec3 at = lantern.add((r.nextDouble() - 0.5) * 0.25, (r.nextDouble() - 0.5) * 0.25, (r.nextDouble() - 0.5) * 0.25);
			LabFx.spawn(ModParticles.MOTE, at, lantern.subtract(at).scale(0.12).add(0, 0.01, 0), 0.3f);
		}
	}
}
