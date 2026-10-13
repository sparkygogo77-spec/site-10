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
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
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
	public static final Vector3f GRIP_RAISED = new Vector3f(-0.02f, -0.04f, -1.3f);
	/**
	 * The shoulder sits low and close, so the raised arm points away from you and covers little of
	 * the screen even at a high field of view (Quake Pro), where the hand looks big next to the world.
	 */
	public static final Vector3f SHOULDER_RAISED = new Vector3f(-0.55f, -0.95f, -0.4f);
	/**
	 * On the way up the fist first lifts the lantern clear (up and in), then the wrist turns it and
	 * it settles into place, so the arm doesn't slide in one straight line.
	 */
	public static final Vector3f GRIP_LIFT = new Vector3f(-0.32f, 0.1f, -1.2f);
	/** Last frame's positions, for screenshot tests to print. */
	public static String debug = "";
	/** Carried at the hip: the fist and shoulder at rest, out of sight below the screen. */
	public static final Vector3f GRIP_HIP = new Vector3f(-0.45f, -0.8f, -0.75f);
	public static final Vector3f SHOULDER_HIP = new Vector3f(-0.7f, -1.3f, -0.35f);
	/** Floating or summoned: where the lantern's handle top hovers at rest. */
	public static final Vector3f FLOAT_REST = new Vector3f(-0.5f, 0.12f, -1.15f);
	/** Ticks the summoned lantern takes to fade back into light once the ring is full. */
	static final float FADE = 18f;
	/** Summoned: ticks the lantern takes to break up into construct matter and melt away after the charge (J). */
	static final float MELT = 34f;
	/**
	 * How far the lantern turns its lens toward the ring hand when raised, in degrees: hung in front
	 * of the ring, its port looks back at the fist coming in from the right.
	 */
	public static float raisedYaw = 40f;
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
	private static final Look DARK = new Look("dark_lantern", 0.74f, 28.5f, new Vector3f(0f, 11f, -5.0f), null);
	private static final Look CLASSIC = new Look("classic_lantern", 0.88f, 22f, new Vector3f(0f, 9.5f, -7.05f), null);
	/** The Red Lantern battery: every red lantern, whatever look is picked in the Ring Lab. */
	private static final Look RED = new Look("red_lantern", 0.72f, 27.3f, new Vector3f(0f, 11f, -7.05f), null);
	/**
	 * The blue corps' own lantern (Blue Lantern sheet, built on the pixel grid by
	 * tools/pixel_lantern_bbmodel.py): docks on the domed emblem window in front.
	 */
	private static final Look BLUE = new Look("blue_lantern", 0.72f, 26.5f, new Vector3f(0f, 11.4f, -7.0f), null);
	/** The yellow corps' own lantern (Sinestro Corps sheet): docks on the front window's emblem. */
	private static final Look YELLOW = new Look("yellow_lantern", 0.8f, 24.5f, new Vector3f(0f, 8f, -4.65f), null);
	/** The violet corps' own lantern (Star Sapphire sheet): docks on the star in the front panel. */
	private static final Look VIOLET = new Look("violet_lantern", 0.85f, 20f, new Vector3f(0f, 11.9f, -5.15f), null);
	/** The orange corps' own lantern (Larfleeze sheet): docks on the copper medallion in front. */
	private static final Look ORANGE = new Look("orange_lantern", 0.85f, 16.2f, new Vector3f(0f, 8.5f, -5.4f), null);
	private static final Look STONE = new Look("stone_lantern", 0.88f, 22f, new Vector3f(0f, 7f, -4.52f), "_stone");
	private static final Look TORUS = new Look("torus_lantern", 0.85f, 24f, new Vector3f(0f, 10f, -4.75f), null);
	private static final Look NEBULA = new Look("nebula_lantern", 0.85f, 21f, new Vector3f(0f, 11.5f, -5.05f), null);
	/** The Nebula battery's flowing glass: frames nebula_glass_f0..f23, each shown for this many ticks. */
	private static final int NEBULA_FRAMES = 24;
	private static final int NEBULA_FRAME_TICKS = 3;
	private static final int LIGHT_FRAMES = 32;
	private static final int LIGHT_FRAME_TICKS = 2;
	private static final Look COMPACT = new Look("compact_lantern", 0.85f, 18f, new Vector3f(0f, 7f, -4.25f), null);

	private static final Map<String, BbModel> MODELS = new HashMap<>();
	/** Where the lens was drawn last frame, and which way it faced, in camera space; the ring hand presses on it. */
	private static Vector3f lensTarget;
	private static Vector3f lensNormal;
	/** The lens in view space (as seen through the hand's fixed field of view), for the glare on screen. */
	private static Vector3f lensView;
	/**
	 * The lens and its facing relative to the pose the hands start from (the same for both hands),
	 * so the ring hand docks on it even when its pose stack starts somewhere else than the
	 * lantern's did (shader mods draw the hands in passes of their own). Null for the shrine.
	 */
	private static Vector3f lensLocal;
	private static Vector3f lensNormalLocal;

	private LanternFirstPerson() {
	}

	/** Returns true when it drew the lantern, so the normal item rendering is skipped. */
	public static boolean render(PlayerRenderState playerState, InteractionHand hand, float swing, float equip,
			ItemStack stack, PoseStack poseStack, SubmitNodeCollector collector, int light, float partialTick) {
		if (hand != InteractionHand.OFF_HAND || !stack.is(ModRegistry.POWER_BATTERY_ITEM)) return false;
		// Only ever one lantern on screen: while one is summoned from its slot, the off hand's is hidden.
		if (LanternSlotFx.visible()) return true;
		return draw(playerState, equip, Corps.ofLantern(stack), poseStack, collector, light, partialTick, false);
	}

	/**
	 * The lantern summoned from its own slot (key R, see LanternSlot): floating a little low on the
	 * off-hand side, drifting in as it's summoned and toward you as it charges. Drawn alongside
	 * whatever the off hand holds.
	 */
	public static void renderSlot(PlayerRenderState playerState, PoseStack poseStack, SubmitNodeCollector collector, int light, float partialTick) {
		if (!LanternSlotFx.visible()) return;
		Corps corps = LanternSlotFx.corps();
		Corps before = CorpsTint.enter(corps);
		try {
			draw(playerState, 0f, corps, poseStack, collector, light, partialTick, true);
		} finally {
			CorpsTint.restore(before);
		}
	}

	/** Where the summoned lantern's handle top hovers at rest: lower than the old floating spot. */
	public static final Vector3f SLOT_REST = new Vector3f(-0.48f, -0.06f, -1.1f);
	/** Where it drifts in from as it's summoned (and back out to as it breaks up): further off and lower. */
	public static final Vector3f SLOT_FROM = new Vector3f(-0.75f, -0.45f, -1.9f);

	private static boolean draw(PlayerRenderState playerState, float equip, Corps corps, PoseStack poseStack,
			SubmitNodeCollector collector, int light, float partialTick, boolean slot) {
		AvatarRenderState avatar = playerState.avatarRenderState;
		if (avatar == null || avatar.skin == null) return false;
		Look look = look(corps);
		Matrix4f entry = new Matrix4f(poseStack.last().pose()).invert();
		LabSettings.ChargeStyle style = slot ? LabSettings.ChargeStyle.FLOAT : LabSettings.get().chargeStyle;
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
		Vector3f grip = curve(hip ? GRIP_HIP : GRIP, GRIP_LIFT, GRIP_RAISED, raise);
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
			// The lantern hangs from the fist; with the ring on its port it's knocked back, drawn in
			// toward the ring hand and buzzes like a strong magnet as the charge builds.
			float c = ChargeMotion.onPort(held(partialTick));
			float pull = ChargeMotion.lanternPull(c);
			float buzz = ChargeMotion.buzz(c, Minecraft.getInstance().player == null ? 0f : Minecraft.getInstance().player.tickCount + partialTick);
			float t = held(partialTick);
			ChargeMotion.Weights w = ChargeMotion.local(partialTick);
			poseStack.translate(grip.x - f * hangSide - f * pull + buzz, grip.y + buzz * 0.7f, grip.z + ChargeMotion.shift(t, w.pull()));
			// Its top tips toward you so the port faces down to the ring coming up from below; it
			// leans in to meet the ring, is knocked away when it sticks and settles propped on it.
			poseStack.rotateDegrees(Axis.XP, ChargeMotion.tilt(t, raise, w.pull()));
			// Propped on the ring: a small turn of the wrist tips the lantern's top over onto it,
			// so the port leans against the ring (the ring hand follows the port and tilts with it).
			poseStack.translate(f * hangSide, 0f, 0f);
			poseStack.rotateDegrees(Axis.ZP, f * ChargeMotion.LEAN * ChargeMotion.lean(held(partialTick)));
			poseStack.translate(-f * hangSide, 0f, 0f);
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
					lensLocal = null;
					return true;
				}
			}
			Minecraft mc = Minecraft.getInstance();
			float time = mc.level == null ? 0 : mc.level.getGameTime() + partialTick;
			Vector3f rest = new Vector3f(FLOAT_REST);
			float spin = 0f;
			if (slot) {
				// Summoned: it drifts up and in from further off, growing out of light, and breaks
				// back up the same way when dismissed.
				float a = LanternSlotFx.appear(partialTick);
				if (a <= 0.01f) {
					poseStack.popPose();
					lensTarget = null;
					lensLocal = null;
					return true;
				}
				float in = smooth(a);
				rest = new Vector3f(SLOT_FROM).lerp(SLOT_REST, in);
				size = 0.35f + 0.65f * in;
				spin = 90f * (1f - in);
			}
			Vector3f at = rest.lerp(GRIP_RAISED, raise);
			at.x *= -f;
			at.y += 0.025f * Mth.sin(time * 0.08f) * (1f - raise);
			poseStack.translate(at.x, at.y - equip * 0.6f, at.z);
			poseStack.rotateDegrees(Axis.ZP, 3f * Mth.sin(time * 0.05f) * (1f - raise));
			poseStack.rotateDegrees(Axis.YP, f * spin);
			// Swinging back from its top when the ring hits the port, like a hanging lantern knocked.
			poseStack.rotateDegrees(Axis.XP, ChargeMotion.swing(held(partialTick)));
		}
		// Lens toward the camera, turning toward the ring hand once the lantern is lifted clear.
		float turn = held ? smooth((raise - 0.3f) / 0.7f) : raise;
		poseStack.rotateDegrees(Axis.YP, 180f + f * -1f * raisedYaw * turn);
		float s = scale * look.size() * size;
		poseStack.scale(s, s, s);
		// Melting (J): the lantern slumps down onto its foot and spreads a little as it turns to
		// construct light, shedding pieces and drips (see the particles in tick), instead of shrinking.
		float m = melt(partialTick);
		float slump = smooth(Mth.clamp((m - 0.15f) / 0.85f, 0f, 1f));
		if (slump > 0f) {
			float h = look.handleTop() / 16f;
			poseStack.translate(0f, -h, 0f);
			float spread = 1f + 0.25f * slump;
			poseStack.scale(spread, Math.max(0.02f, 1f - slump), spread);
			poseStack.translate(0f, h, 0f);
		}
		poseStack.translate(0f, -look.handleTop() / 16f, 0f);

		float glow = glow(partialTick);
		// It burns up in light as it breaks into construct matter.
		if (m > 0f) glow = Math.max(glow, LanternGlare.IDLE + 2.2f * smooth(m / 0.3f) * (1f - smooth((m - 0.7f) / 0.3f)));
		Vector3f dock = drawLantern(poseStack, collector, light, look, corps, glow);
		// The ring pushes physically into the port and seats there (2 of the Dark Lantern's pixels).
		float onPort = ChargeMotion.onPort(held(partialTick));
		float seated = onPort >= 0 ? smooth(onPort / 3f) : ChargeMotion.pinned(partialTick) ? 1f : 0f;
		dock.z += (look == DARK ? 0.5f : 1f) / 16f * seated;
		lensTarget = poseStack.last().pose().transformPosition(dock, new Vector3f());
		lensNormal = poseStack.last().pose().transformDirection(0f, 0f, -1f, new Vector3f()).normalize();
		lensView = RenderSystem.getModelViewStack().transformPosition(new Vector3f(lensTarget));
		lensLocal = entry.transformPosition(new Vector3f(lensTarget));
		lensNormalLocal = entry.transformDirection(new Vector3f(lensNormal)).normalize();
		debug = "grip=" + grip + " lens=" + lensTarget + " raise=" + raise + " glow=" + glow + " view=" + lensView + " style=" + style;
		poseStack.popPose();
		return true;
	}

	/** The lantern look for this corps: the Red Lantern's own, else the one picked in the Ring Lab. */
	static Look look(Corps corps) {
		return corps == Corps.RED ? RED : corps == Corps.BLUE ? BLUE : corps == Corps.YELLOW ? YELLOW : corps == Corps.VIOLET ? VIOLET : corps == Corps.ORANGE ? ORANGE : switch (LabSettings.get().lanternModel) {
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
				k -> look == RED || look == BLUE || look == YELLOW || look == VIOLET || look == ORANGE ? BbModel.load(look.name()) : BbModel.load(look.name()).forCorps(corps));
		// The Stone Lantern's light is sealed in: its cracks barely seep at rest and blaze as it charges.
		if (look == STONE && glow <= 1f) glow = Mth.clamp((glow - 0.55f) / 0.4f, 0.1f, 1f);
		// The Dark Lantern is dark at rest; its charge light is baked (see darkCharge).
		if (look == DARK) glow = 0f;
		// The Blue Lantern's windows always show its light (hope never goes out), but calmly enough
		// at rest that the emblem on its lens stays readable under a shader pack's bloom.
		if (look == BLUE) glow = Math.max(glow, BLUE_REST);
		// The Sinestro lantern's windows burn too: fear is always on show.
		if (look == YELLOW) glow = Math.max(glow, 0.75f);
		// The Star Sapphire crystal glows from within at all times.
		if (look == VIOLET) glow = Math.max(glow, 0.75f);
		// The Orange Lantern's column and pool always glow, but its flame only lights as the charge builds.
		if (look == ORANGE) glow = Math.max(glow, 0.7f);
		// Core cubes (the Orange flame) swell as the charge builds.
		float coreScale = look == ORANGE ? Math.min(1.15f, smooth((glow - 0.66f) / 0.3f) + 0.15f * smooth(glow - 1f))
				: 1f + 2.4f * smooth((glow - 0.75f) / 0.5f);
		model.render(poseStack, collector, light, look == BLUE ? blueGlow(Math.min(glow, 1f), glow) : BbModel.glow(Math.min(glow, 1f)), coreScale);
		if (glow > 1f) model.renderGlow(poseStack, collector, look == BLUE ? blueGlow(glow - 1f, glow) : BbModel.glow(glow - 1f));
		if (look == DARK) darkCharge(poseStack, collector, light, corps);
		if (look == NEBULA) {
			Minecraft mc = Minecraft.getInstance();
			long time = mc.level == null ? 0 : mc.level.getGameTime();
			float now = time + mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
			// The chamber is solid light: its texture flows through LIGHT_FRAMES frames while the
			// column slowly turns (so its bands swirl), and a glow copy on top breathes and blazes as
			// the lantern charges.
			int lightFrame = (int) (time / LIGHT_FRAME_TICKS % LIGHT_FRAMES);
			BbModel inner = MODELS.computeIfAbsent("nebula_light/" + corps + "/" + lightFrame, k -> BbModel.load("nebula_light")
					.retextured(LanternRing.id("textures/entity/bb/nebula_light_f" + lightFrame + ".png")).forCorps(corps));
			// (The solid pass is shaded by the hand's lighting, so the added glow carries most of the brightness.)
			float breath = 0.68f + 0.18f * Mth.sin(now * 0.13f) + 0.08f * Mth.sin(now * 0.37f);
			poseStack.pushPose();
			poseStack.rotateDegrees(Axis.YP, now * 1.2f % 360f);
			inner.renderLit(poseStack, collector, BbModel.glow(breath + 0.5f * smooth(glow - 0.75f)));
			poseStack.popPose();
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

	/**
	 * The Dark Lantern's charge light, G3 R4 (J's pick from Blender; tools/pixel_dark_bbmodel.py):
	 * CHARGE_FRAMES baked frames run through the charge (the light spreading out from the port, the
	 * ball growing brighter, the gold cracks filling centre-out), then a climax frame (140%) and the
	 * let-go flash on top; the spinning ball's strands are SWIRL_FRAMES frames of a smaller model.
	 */
	private static final int CHARGE_FRAMES = 16;
	private static final int SWIRL_FRAMES = 8;
	/** After the ring is full (ticks): the overcharge climbs to 140%, holds, the let-go flash pulses, then the slow fade. */
	static final float CLIMAX = 40f, HOLD = 26f, FLASH = 14f, UNDO = 150f;
	/** Ticks the whole afterglow lasts, from the ring filling to dark. */
	static final float AFTERGLOW = CLIMAX + HOLD + FLASH + UNDO;
	/** True while drawing another player's lantern: the charge timeline below is the local player's. */
	static boolean othersLantern;
	/** The spinning ball's turn (radians), accumulated so it only ever turns one way, and when it last moved. */
	private static float spin;
	private static float spinAt = Float.NaN;

	/** Where the Dark Lantern's light is: charge (0..1.4), the charge frame position (0..CHARGE_FRAMES, the last is the climax) and the flash pulse. */
	record DarkLight(float charge, float frame, float flash) {
		static final DarkLight OFF = new DarkLight(0f, 0f, 0f);
	}

	/**
	 * True when the local player's lantern is the Dark Lantern (G3): its light comes from the
	 * lantern itself, so the screen wash and the sun on the ring stay out of the way.
	 */
	static boolean g3() {
		LocalPlayer player = Minecraft.getInstance().player;
		if (player == null) return false;
		ItemStack lantern = LanternCharge.lantern(player);
		return lantern.is(ModRegistry.POWER_BATTERY_ITEM) && look(Corps.ofLantern(lantern)) == DARK;
	}

	/** The local player's Dark Lantern light this frame (G3 R4's timeline, measured from the ring seating in the port). */
	static DarkLight darkLight(float partialTick) {
		float t = held(partialTick);
		int seat = LanternCharge.hold() + LanternCharge.reach();
		if (t >= seat && t < LanternCharge.done()) {
			float u = (t - seat) / Math.max(1, LanternCharge.done() - seat);
			return new DarkLight(smooth(u), u * (CHARGE_FRAMES - 1), 0f);
		}
		float a = LanternGlare.since(partialTick);
		if (a < 0 || a >= AFTERGLOW) return DarkLight.OFF;
		float flash = (float) Math.exp(-Math.pow((a - CLIMAX - HOLD - FLASH / 2f) / (FLASH / 3.5f), 2));
		if (a < CLIMAX + HOLD + FLASH) {
			float over = smooth(a / CLIMAX);
			return new DarkLight(1f + 0.4f * over, CHARGE_FRAMES - 1 + over, flash);
		}
		// "The colour coming undone": back down through the frames to dark.
		float c = 1.4f * (1f - smooth((a - CLIMAX - HOLD - FLASH) / UNDO));
		if (c > 1f) return new DarkLight(c, CHARGE_FRAMES - 1 + (c - 1f) / 0.4f, flash);
		// The frame whose charge is c (charge = smoothstep of the frame's time).
		float u = 0.5f - Mth.sin((float) Math.asin(Mth.clamp(1f - 2f * c, -1f, 1f)) / 3f);
		return new DarkLight(c, u * (CHARGE_FRAMES - 1), flash);
	}

	/** J: the glass never goes fully dark; at rest it glows this much in the corps colour, the ball dim and slowly turning. */
	private static final float IDLE_GLOW = 0.13f;

	private static void darkCharge(PoseStack poseStack, SubmitNodeCollector collector, int light, Corps corps) {
		Minecraft mc = Minecraft.getInstance();
		float partial = mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
		DarkLight d = othersLantern ? DarkLight.OFF : darkLight(partial);
		float now = mc.level == null ? 0f : mc.level.getGameTime() + partial;
		float dt = Float.isNaN(spinAt) ? 0f : Mth.clamp((now - spinAt) / 20f, 0f, 0.25f);
		spinAt = now;
		// Spins faster as it charges, always the same way (from accumulated time, not from the charge).
		spin = (spin + (0.5f + 4.5f * Math.min(d.charge(), 1f)) * dt) % (Mth.TWO_PI * 64f);
		float pack = 0.35f + 0.5f * Math.min(d.charge(), 1f);
		if (d.charge() < IDLE_GLOW && d.flash() <= 0.01f) {
			// Resting: the fully lit glass, very dim, under whatever light is left.
			float rest = IDLE_GLOW - d.charge();
			chargeFrame("c", CHARGE_FRAMES - 1, corps).renderPackSafe(poseStack, collector, light, BbModel.glow(rest), 1f, 0.25f);
			if (d.charge() <= 0.002f) {
				swirl(poseStack, collector, light, corps, 0.12f, 0.25f);
				return;
			}
		}
		int a = Math.min((int) Math.floor(d.frame()), CHARGE_FRAMES);
		int b = Math.min(a + 1, CHARGE_FRAMES);
		float w = d.frame() - a;
		chargeFrame("c", a, corps).renderPackSafe(poseStack, collector, light, BbModel.glow(1f - w), 1f, pack);
		if (w > 0.02f && b != a) chargeFrame("c", b, corps).renderPackSafe(poseStack, collector, light, BbModel.glow(w), 1f, pack);
		if (d.flash() > 0.01f) chargeFrame("flash", 0, corps).renderPackSafe(poseStack, collector, light, BbModel.glow(d.flash()), 1f, 1f);
		swirl(poseStack, collector, light, corps, Math.min(1f, 0.2f + 0.8f * d.charge()), pack);
	}

	/** The ball's strands, one third of a turn over SWIRL_FRAMES, in the middle band. */
	private static void swirl(PoseStack poseStack, SubmitNodeCollector collector, int light, Corps corps, float bright, float pack) {
		float f = spin / (Mth.TWO_PI / 3f) * SWIRL_FRAMES;
		int s0 = Math.floorMod((int) Math.floor(f), SWIRL_FRAMES);
		int s1 = (s0 + 1) % SWIRL_FRAMES;
		float sw = f - (float) Math.floor(f);
		swirlFrame(s0, corps).renderPackSafe(poseStack, collector, light, BbModel.glow(bright * (1f - sw)), 1f, pack);
		if (sw > 0.02f) swirlFrame(s1, corps).renderPackSafe(poseStack, collector, light, BbModel.glow(bright * sw), 1f, pack);
	}

	/** A charge frame of the glow model: "c" 0..CHARGE_FRAMES-1, frame CHARGE_FRAMES = the climax, or "flash". */
	private static BbModel chargeFrame(String kind, int frame, Corps corps) {
		String name = kind.equals("flash") ? "flash" : frame >= CHARGE_FRAMES ? "climax" : "c" + frame;
		return MODELS.computeIfAbsent("dark_lantern_glow/" + corps + "/" + name, k -> BbModel.load("dark_lantern_glow")
				.retextured(LanternRing.id("textures/entity/bb/dark_lantern_glow_" + name + ".png")).forCorps(corps));
	}

	private static BbModel swirlFrame(int frame, Corps corps) {
		return MODELS.computeIfAbsent("dark_lantern_swirl/" + corps + "/" + frame, k -> BbModel.load("dark_lantern_swirl")
				.retextured(LanternRing.id("textures/entity/bb/dark_lantern_swirl_" + frame + ".png")).forCorps(corps));
	}

	/** The Blue Lantern's resting glow (other lanterns rest at 0.75). */
	private static final float BLUE_REST = 0.6f;

	/**
	 * The Blue Lantern's glow tint: a strong blue rather than white, so its light reads as blue
	 * (and a shader pack doesn't bloom it to white). It only pales a little at the very peak of
	 * the flash ({@code light} is the lantern's overall light, up to about 4).
	 */
	private static int blueGlow(float brightness, float light) {
		float pale = 0.45f * smooth((light - 1f) / 3f);
		float b = Mth.clamp(brightness, 0f, 1f) * 255f;
		int r = Math.round(b * Mth.lerp(pale, 0.4f, 1f));
		int g = Math.round(b * Mth.lerp(pale, 0.72f, 1f));
		int bl = Math.round(b);
		return 0xFF000000 | r << 16 | g << 8 | bl;
	}

	/** Sets where the ring docks this frame, for a lantern drawn somewhere else (the shrine). */
	static void dockAt(Vector3f target, Vector3f normal, Vector3f view) {
		lensTarget = target;
		lensNormal = normal;
		lensView = view;
		lensLocal = null;
		lensNormalLocal = null;
	}

	/**
	 * How much of the summoned lantern has formed: nothing at rest, growing out of light as the
	 * charge starts, whole while it charges, and fading away once the ring is full.
	 */
	static float summoned(float partialTick) {
		float a = LanternGlare.after(partialTick);
		// It never shrinks away: it stays full size while it melts (see melt) and is gone once melted.
		if (a >= 0) return a < MELT ? 1f : 0f;
		float t = held(partialTick);
		if (t < 0 || t >= LanternCharge.done()) return 0f;
		return smooth(t / (LanternCharge.hold() + LanternCharge.reach()));
	}

	/** Summoned: how far the lantern has melted into construct matter after the charge, 0..1. */
	static float melt(float partialTick) {
		if (LabSettings.get().chargeStyle != LabSettings.ChargeStyle.SUMMON) return 0f;
		float a = LanternGlare.after(partialTick);
		return a < 0 ? 0f : Mth.clamp(a / MELT, 0f, 1f);
	}

	/** The lantern's lens in camera space, or null if no lantern was drawn lately. */
	static Vector3f lensTarget() {
		return lensTarget;
	}

	/** The lens for a hand whose pose started at {@code base}, or null if no lantern was drawn lately. */
	static Vector3f lensTarget(Matrix4f base) {
		return lensLocal != null ? base.transformPosition(lensLocal, new Vector3f()) : lensTarget;
	}

	/** The lens's outward facing for a hand whose pose started at {@code base}. */
	static Vector3f lensNormal(Matrix4f base) {
		return lensNormalLocal != null ? base.transformDirection(lensNormalLocal, new Vector3f()).normalize() : lensNormal;
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

	/** A smooth path from {@code a} through near {@code mid} to {@code b} (a quadratic curve). */
	private static Vector3f curve(Vector3f a, Vector3f mid, Vector3f b, float t) {
		float u = 1f - t;
		return new Vector3f(a).mul(u * u).add(new Vector3f(mid).mul(2f * u * t)).add(new Vector3f(b).mul(t * t));
	}

	/** 0 = hanging at your side, 1 = held up in front of you (see {@link ChargeMotion}). */
	static float raise(float partialTick) {
		return ChargeMotion.local(partialTick).raise();
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
		if (mc.player == null) return;
		// In the held lantern's colour.
		ItemStack held = LanternCharge.lanternOut(mc.player) ? LanternCharge.lantern(mc.player)
				: mc.player.getOffhandItem().is(ModRegistry.POWER_BATTERY_ITEM) ? mc.player.getOffhandItem() : mc.player.getMainHandItem();
		Corps before = CorpsTint.enter(Corps.ofLantern(held));
		try {
			motes(mc);
		} finally {
			CorpsTint.restore(before);
		}
	}

	private static void motes(Minecraft mc) {
		LocalPlayer player = mc.player;
		if (player == null || mc.level == null || mc.isPaused() || !mc.options.getCameraType().isFirstPerson()) return;
		LabSettings.ChargeStyle style = LanternCharge.lanternOut(player) ? LabSettings.ChargeStyle.FLOAT : LabSettings.get().chargeStyle;
		if (style == LabSettings.ChargeStyle.SHRINE && LanternShrine.active()) return;
		float t = held(0f);
		int contact = LanternCharge.hold() + LanternCharge.reach();
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
			} else if (a >= 0 && a < MELT) {
				// And breaking up into construct matter that melts away: shards and panes flaking off
				// all over it, drips running off its foot, fewer as there is less of it left.
				float m = a / MELT;
				float height = 0.5f * (1f - m);
				int pieces = Math.round(5 * (1f - 0.6f * m));
				for (int i = 0; i < pieces; i++) {
					Vec3 at = lantern.add((r.nextDouble() - 0.5) * 0.3, -0.25 + r.nextDouble() * height, (r.nextDouble() - 0.5) * 0.3);
					Vec3 out = at.subtract(lantern).multiply(1, 0, 1).normalize().scale(0.02 + 0.03 * r.nextDouble()).add(0, -0.01, 0);
					LabFx.spawn(r.nextBoolean() ? ModParticles.SHARD : ModParticles.PANE, at, out, 0.35f);
				}
				for (int i = 0; i < 2; i++) {
					Vec3 at = lantern.add((r.nextDouble() - 0.5) * 0.35, -0.25, (r.nextDouble() - 0.5) * 0.35);
					LabFx.spawn(ModParticles.DRIP, at, new Vec3(0, -0.04, 0), 0.4f);
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
