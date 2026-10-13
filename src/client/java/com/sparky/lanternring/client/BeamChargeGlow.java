package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.item.PowerRingItem;
import java.util.HashMap;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/**
 * While right-click is held in Beam mode, light builds up on the ring hand until the charged beam
 * goes off: a swirl of green around the fist and a brighter knot of it on the ring (drawn
 * additively, like a charged creeper's shell, so it glows over the hand instead of covering it),
 * plus motes drawn in toward the ring. Seen in first and third person, and on other players.
 */
public final class BeamChargeGlow {
	private static final Identifier SWIRL = LanternRing.id("textures/entity/charge_swirl.png");
	/** Plain white, tinted per draw: the solid white-hot heart of the lantern sun. */
	private static final Identifier SUN_CORE = LanternRing.id("textures/entity/sun_core.png");
	private static final Map<String, ModelPart> PARTS = new HashMap<>();

	private BeamChargeGlow() {
	}

	/**
	 * How far along the Beam charge {@code player} is, 0..1 (1 = the charged beam is ready), or -1
	 * when they aren't charging the Beam.
	 */
	public static float progress(Player player, float partialTick) {
		if (!player.isUsingItem()) return -1f;
		ItemStack used = player.getUseItem();
		if (!(used.getItem() instanceof PowerRingItem) || PowerRingItem.getMode(used) != RingMode.BEAM) return -1f;
		// Holding both clicks with the lantern charges the ring instead.
		if ((LanternCharge.holdsBattery(player) || LanternCharge.lanternOut(player)) && LanternCharge.started(player)) return -1f;
		float full = Math.max(1, RingTuning.BEAM_CHARGE.ticks());
		return Mth.clamp(player.getTicksUsingItem(partialTick) / full, 0f, 1f);
	}

	/** The arm (as drawn) whose hand is charging, or null. */
	public static HumanoidArm chargingArm(Player player) {
		if (progress(player, 0f) < 0f) return null;
		HumanoidArm main = player.getMainArm();
		return player.getUsedItemHand() == InteractionHand.MAIN_HAND ? main : main.getOpposite();
	}

	/**
	 * The swirling additive glow. Under a shader pack (Iris) the energy swirl, and additive "eyes"
	 * too, draw as a solid black shell around the first-person fist, so there it's see-through
	 * emissive glass instead (as the Riot Shield draws, which Iris handles), coloured by glow().
	 */
	private static RenderType swirl(float u, float v) {
		// Each corps has its own recoloured swirl (the green one tinted would still read green).
		Identifier tex = CorpsTint.texture(SWIRL, CorpsTint.current());
		return SoulSight.shaderPackOn() ? RenderTypes.entityTranslucentEmissive(tex) : RenderTypes.energySwirl(tex, u, v);
	}

	/** The tint for a glow of brightness b: additive green, or under a shader pack, see-through green that fades out instead. */
	private static int glow(float b) {
		if (!SoulSight.shaderPackOn()) return green(b);
		int a = Mth.clamp((int) (b * 0.6f * 255), 0, 255);
		return (green(1f) & 0xFFFFFF) | a << 24;
	}

	/** Brightness of the glow for a charge of {@code p}: builds up, then throbs once it's ready. */
	private static float brightness(float p, float time) {
		if (p >= 1f) return 0.85f + 0.15f * Mth.sin(time * 0.7f);
		return 0.2f + 0.65f * p * p + 0.08f * p * Mth.sin(time * (0.4f + 0.8f * p));
	}

	/** A ring-green tint of the given brightness; additive, so it stays green instead of washing out white. */
	private static int green(float b) {
		int g = Mth.clamp((int) (b * 255), 0, 255);
		return CorpsTint.apply(CorpsTint.current(), 0xFF000000 | (int) (g * 0.45f) << 16 | g << 8 | (int) (g * 0.55f));
	}

	/**
	 * Draws the glow on the ring hand. The pose stack must be in the arm's model space (the same
	 * space {@link RingModels#render} draws in).
	 */
	public static void render(PoseStack poseStack, SubmitNodeCollector collector, float p, float time,
			LabSettings.RingModel model, boolean leftArm, boolean slim) {
		if (p < 0f || !LabSettings.get().chargeGlow.swirl()) return;
		float scroll = time * 0.012f;
		float b = brightness(p, time);

		// The fist: a swirling shell that swells a little as it fills.
		ModelPart hand = PARTS.computeIfAbsent("hand/" + leftArm + "/" + slim, k -> handPart(leftArm, slim));
		float cx = (leftArm ? 1f : -1f) * (slim ? 0.5f : 1f);
		poseStack.pushPose();
		poseStack.translate(cx / 16f, 7.5f / 16f, 0f);
		float grow = 1f + 0.12f * p;
		poseStack.scale(grow, grow, grow);
		poseStack.translate(-cx / 16f, -7.5f / 16f, 0f);
		collector.submitModelPart(hand, poseStack, swirl(scroll % 1f, scroll * 0.7f % 1f),
				ShaderGlow.light(), OverlayTexture.NO_OVERLAY, null, glow(b));
		poseStack.popPose();

		// The ring: a tighter, brighter knot of light on its face that grows with the charge.
		float[] face = RingModels.ringFace(model, leftArm, slim);
		ModelPart knot = PARTS.computeIfAbsent("knot", k -> part(-1f, -1f, -1f, 2f, 2f, 2f, 0.25f));
		poseStack.pushPose();
		poseStack.translate(face[0] / 16f, (face[1] - 0.5f) / 16f, face[2] / 16f);
		float size = 0.6f + 0.5f * p + (p >= 1f ? 0.1f * Mth.sin(time * 0.7f) : 0f);
		poseStack.scale(size, size, size);
		collector.submitModelPart(knot, poseStack, swirl(-scroll * 2f % 1f, scroll * 1.3f % 1f),
				ShaderGlow.light(), OverlayTexture.NO_OVERLAY, null, glow(b));
		poseStack.popPose();
	}

	/**
	 * The ring's own light, always on while it's worn: a soft knot of corps light on its face that
	 * breathes slowly, so the ring glows on the hand and not only its gem. Same pose space as
	 * {@link #render}; drawn in a type that still glows under shader packs.
	 */
	public static void renderIdle(PoseStack poseStack, SubmitNodeCollector collector, LabSettings.RingModel model,
			boolean leftArm, boolean slim) {
		float time = (System.nanoTime() / 1_000_000L % 3_600_000L) / 50f;
		float scroll = time * 0.008f;
		float b = 0.42f + 0.06f * Mth.sin(time * 0.12f);
		float[] face = RingModels.ringFace(model, leftArm, slim);
		ModelPart knot = PARTS.computeIfAbsent("knot", k -> part(-1f, -1f, -1f, 2f, 2f, 2f, 0.25f));
		poseStack.pushPose();
		poseStack.translate(face[0] / 16f, (face[1] - 0.5f) / 16f, face[2] / 16f);
		poseStack.scale(0.9f, 0.9f, 0.9f);
		collector.submitModelPart(knot, poseStack, swirl(-scroll % 1f, scroll * 1.3f % 1f),
				ShaderGlow.light(), OverlayTexture.NO_OVERLAY, null, glow(b));
		poseStack.popPose();
	}

	/**
	 * A power just left the ring: a burst of light on the ring face that swells and fades, with the
	 * fist lit around it. {@code f} runs 1 down to 0 over the flash. Drawn with the hand, so in first
	 * person it shows over the fist instead of hidden behind it. Same pose space as {@link #render}.
	 * {@code firstPerson} keeps it smaller, since your own fist is right in front of your eyes.
	 */
	public static void renderFlash(PoseStack poseStack, SubmitNodeCollector collector, float f, float time,
			LabSettings.RingModel model, boolean leftArm, boolean slim, boolean firstPerson) {
		if (f <= 0f) return;
		float scroll = time * 0.03f;
		ModelPart hand = PARTS.computeIfAbsent("hand/" + leftArm + "/" + slim, k -> handPart(leftArm, slim));
		collector.submitModelPart(hand, poseStack, swirl(scroll % 1f, scroll * 0.7f % 1f),
				ShaderGlow.light(), OverlayTexture.NO_OVERLAY, null, glow((firstPerson ? 0.45f : 0.7f) * f));
		float[] face = RingModels.ringFace(model, leftArm, slim);
		ModelPart knot = PARTS.computeIfAbsent("knot", k -> part(-1f, -1f, -1f, 2f, 2f, 2f, 0.25f));
		poseStack.pushPose();
		poseStack.translate(face[0] / 16f, (face[1] - 0.5f) / 16f, face[2] / 16f);
		// Bursts out big at once, then shrinks back into the ring as it fades.
		float size = firstPerson ? 0.6f + 0.7f * f : 0.8f + 2.2f * f;
		poseStack.scale(size, size, size);
		collector.submitModelPart(knot, poseStack, swirl(-scroll * 2f % 1f, scroll * 1.3f % 1f),
				ShaderGlow.light(), OverlayTexture.NO_OVERLAY, null, glow(Math.min(1f, (firstPerson ? 0.9f : 1.3f) * f)));
		poseStack.popPose();
	}

	/**
	 * The ring held forming something (the Deluge's ball): a steady glow coming from the ring
	 * face, no flashing. A calm knot of light on the ring, a faint slow swirl over the fist, two
	 * crowns of thin rays turning slowly opposite ways round the ring, their lengths breathing
	 * gently, and a few sparks of light circling it. {@code h} 0..1 is how strong it is. Same pose
	 * space as {@link #render}; drawn with the hand, so it shows over the fist in first person.
	 */
	public static void renderHold(PoseStack poseStack, SubmitNodeCollector collector, float h, float time,
			LabSettings.RingModel model, boolean leftArm, boolean slim, boolean firstPerson) {
		if (h <= 0.01f) return;
		float scroll = time * 0.008f;
		float k = firstPerson ? 0.7f : 1f;
		ModelPart hand = PARTS.computeIfAbsent("hand/" + leftArm + "/" + slim, k2 -> handPart(leftArm, slim));
		collector.submitModelPart(hand, poseStack, swirl(scroll % 1f, scroll * 0.7f % 1f),
				ShaderGlow.light(), OverlayTexture.NO_OVERLAY, null, glow(0.22f * h * k));
		float[] face = RingModels.ringFace(model, leftArm, slim);
		poseStack.pushPose();
		poseStack.translate(face[0] / 16f, (face[1] - 0.5f) / 16f, face[2] / 16f);

		ModelPart knot = PARTS.computeIfAbsent("knot", k2 -> part(-1f, -1f, -1f, 2f, 2f, 2f, 0.25f));
		poseStack.pushPose();
		float size = 0.75f + 0.25f * h;
		poseStack.scale(size, size, size);
		collector.submitModelPart(knot, poseStack, swirl(-scroll * 2f % 1f, scroll * 1.3f % 1f),
				ShaderGlow.light(), OverlayTexture.NO_OVERLAY, null, glow(0.75f * h * k));
		poseStack.popPose();

		// The rays: thin shafts of light round the ring, across the arm.
		ModelPart ray = PARTS.computeIfAbsent("ray", k2 -> part(-0.25f, -0.25f, 0f, 0.5f, 0.5f, 1f, 0f));
		for (int crown = 0; crown < 2; crown++) {
			int n = crown == 0 ? 8 : 5;
			float turn = (crown == 0 ? 1f : -1.6f) * time * 1.2f;
			float base = crown == 0 ? 3.2f : 2.0f;
			for (int i = 0; i < n; i++) {
				float len = (base + 1.4f * Mth.sin(time * 0.05f + i * 2.3f + crown)) * h * k;
				if (len < 0.3f) continue;
				poseStack.pushPose();
				poseStack.rotateDegrees(com.mojang.math.Axis.YP, turn + i * 360f / n);
				poseStack.translate(0f, 0f, 0.9f / 16f);
				poseStack.scale(crown == 0 ? 1f : 0.7f, crown == 0 ? 1f : 0.7f, len);
				collector.submitModelPart(ray, poseStack, swirl(scroll * 3f % 1f, (scroll + i * 0.13f) % 1f),
						ShaderGlow.light(), OverlayTexture.NO_OVERLAY, null, glow((crown == 0 ? 0.45f : 0.35f) * h * k));
				poseStack.popPose();
			}
		}

		// Sparks of light circling the ring at a slow tilt.
		ModelPart mote = PARTS.computeIfAbsent("mote", k2 -> part(-0.35f, -0.35f, -0.35f, 0.7f, 0.7f, 0.7f, 0f));
		for (int i = 0; i < 4; i++) {
			float a = (time * 4f + i * 90f) * Mth.DEG_TO_RAD;
			float r = 2.4f + 0.4f * Mth.sin(time * 0.04f + i);
			poseStack.pushPose();
			poseStack.translate(Mth.cos(a) * r / 16f, Mth.sin(a * 0.5f + i) * 0.8f / 16f, Mth.sin(a) * r / 16f);
			collector.submitModelPart(mote, poseStack, swirl(scroll % 1f, scroll % 1f),
					ShaderGlow.light(), OverlayTexture.NO_OVERLAY, null, glow(0.8f * h * k));
			poseStack.popPose();
		}
		poseStack.popPose();
	}

	/**
	 * Charging at the lantern: the ring is a sun. A blazing core on the ring face and shafts of pure
	 * light escaping all round it, pressed against the lantern, long and flickering, in two tilted
	 * crowns so it reads as a ball of light from any side. {@code s} is LanternFlash.sun (about 0.25
	 * up to 1, more at the burst). In first person it's kept to the ring and the gap round it so
	 * the charger can still see; other players see the full sun. Same pose space as {@link #render}.
	 */
	public static void renderSun(PoseStack poseStack, SubmitNodeCollector collector, float s, float time,
			LabSettings.RingModel model, boolean leftArm, boolean slim, boolean firstPerson) {
		if (s <= 0.01f) return;
		if (LabSettings.get().lanternSun == LabSettings.LanternSun.INFLOW) {
			renderInflow(poseStack, collector, s, time, model, leftArm, slim, firstPerson);
			return;
		}
		float scroll = time * 0.02f;
		float k = 1f;
		float throb = 1f + 0.08f * Mth.sin(time * (0.9f + 0.6f * s));
		ModelPart hand = PARTS.computeIfAbsent("hand/" + leftArm + "/" + slim, k2 -> handPart(leftArm, slim));
		collector.submitModelPart(hand, poseStack, swirl(scroll % 1f, scroll * 0.7f % 1f),
				ShaderGlow.light(), OverlayTexture.NO_OVERLAY, null, glow(Math.min(1f, 0.55f * s * k)));
		float[] face = RingModels.ringFace(model, leftArm, slim);
		poseStack.pushPose();
		poseStack.translate(face[0] / 16f, (face[1] - 0.5f) / 16f, face[2] / 16f);

		// The heart: solid white-hot light, a few cubes turned against each other so it reads round.
		ModelPart knot = PARTS.computeIfAbsent("knot", k2 -> part(-1f, -1f, -1f, 2f, 2f, 2f, 0.25f));
		float core = (firstPerson ? 1.6f + 1.4f * Math.min(s, 1.3f) : 1.8f + 2.8f * s) * throb;
		int corpsRgb = CorpsTint.current().rgb;
		RenderType heart = RenderTypes.entityTranslucentEmissive(SUN_CORE);
		for (int i = 0; i < 3; i++) {
			float size = core * (0.42f - 0.08f * i);
			int rgb = lerpRgb(corpsRgb, 0xFFFFFF, 0.45f + 0.25f * i);
			int a = Mth.clamp((int) (255 * Math.min(1f, (0.45f + 0.2f * i) * (0.6f + 0.4f * s))), 0, 255);
			poseStack.pushPose();
			poseStack.rotateDegrees(com.mojang.math.Axis.YP, 45f * i + time * 3f);
			poseStack.rotateDegrees(com.mojang.math.Axis.XP, 35f * i);
			poseStack.scale(size, size, size);
			collector.submitModelPart(knot, poseStack, heart, ShaderGlow.light(), OverlayTexture.NO_OVERLAY, null, a << 24 | rgb);
			poseStack.popPose();
		}
		// Round it, three swirling shells of corps light, each one smaller and brighter.
		for (int i = 0; i < 3; i++) {
			float size = core * (1f - 0.3f * i);
			poseStack.pushPose();
			poseStack.scale(size, size, size);
			collector.submitModelPart(knot, poseStack, swirl((-scroll * (2f + i)) % 1f, (scroll * 1.3f + i * 0.31f) % 1f),
					ShaderGlow.light(), OverlayTexture.NO_OVERLAY, null, glow(Math.min(1f, (0.55f + 0.25f * i) * s * k)));
			poseStack.popPose();
		}

		// The light escaping: shafts all round the ring, turning slowly, lengths flickering.
		ModelPart ray = PARTS.computeIfAbsent("ray", k2 -> part(-0.25f, -0.25f, 0f, 0.5f, 0.5f, 1f, 0f));
		int crowns = firstPerson ? 2 : 3;
		for (int crown = 0; crown < crowns; crown++) {
			int n = crown == 0 ? 14 : 9;
			float tilt = crown == 0 ? 0f : crown == 1 ? 38f : -38f;
			float turn = (crown == 1 ? -1.4f : 1f) * time * 2.2f;
			float base = (firstPerson ? 4.5f : 6f) * (crown == 0 ? 1f : 0.75f);
			for (int i = 0; i < n; i++) {
				float flick = 0.7f + 0.3f * Mth.sin(time * 0.9f + i * 2.7f + crown * 1.3f);
				float len = (base + (firstPerson ? 5f : 9f) * Math.min(s, 1.3f)) * flick * Math.min(1f, 0.5f + s);
				if (len < 0.3f) continue;
				poseStack.pushPose();
				poseStack.rotateDegrees(com.mojang.math.Axis.XP, tilt);
				poseStack.rotateDegrees(com.mojang.math.Axis.YP, turn + i * 360f / n);
				poseStack.translate(0f, 0f, 0.6f / 16f);
				float thick = (crown == 0 ? 1.1f : 0.8f) * (firstPerson ? 0.9f : 1.4f);
				poseStack.scale(thick, thick, len);
				collector.submitModelPart(ray, poseStack, swirl(scroll * 3f % 1f, (scroll + i * 0.13f) % 1f),
						ShaderGlow.light(), OverlayTexture.NO_OVERLAY, null, glow(Math.min(1f, (crown == 0 ? 0.75f : 0.55f) * s * k)));
				poseStack.popPose();
			}
		}
		poseStack.popPose();
	}

	/** Streams of light pulled into the ring from every side (see {@link #renderInflow}). */
	private static final Vec3[] INFLOW_DIRS = fibonacci(20);

	/** {@code n} directions spread evenly over a sphere. */
	private static Vec3[] fibonacci(int n) {
		Vec3[] dirs = new Vec3[n];
		double golden = Math.PI * (3 - Math.sqrt(5));
		for (int i = 0; i < n; i++) {
			double y = 1 - 2 * (i + 0.5) / n;
			double r = Math.sqrt(1 - y * y);
			dirs[i] = new Vec3(Math.cos(golden * i) * r, y, Math.sin(golden * i) * r);
		}
		return dirs;
	}

	/**
	 * The other charging look: the ring is a small black hole. Streams of light come in from every
	 * side in straight lines, bend round as they near it and pour into it, brightening as they go,
	 * with pulses running down them; a thin rim of light spins round its dark heart, and the glint
	 * over the ring itself burns brighter (RingModels.glintBoost). All in the corps' colour. Same
	 * pose space as {@link #render}.
	 */
	private static void renderInflow(PoseStack poseStack, SubmitNodeCollector collector, float s, float time,
			LabSettings.RingModel model, boolean leftArm, boolean slim, boolean firstPerson) {
		float scroll = time * 0.02f;
		float strength = Math.min(1f, s);
		float[] face = RingModels.ringFace(model, leftArm, slim);
		poseStack.pushPose();
		poseStack.translate(face[0] / 16f, (face[1] - 0.5f) / 16f, face[2] / 16f);
		ModelPart ray = PARTS.computeIfAbsent("ray", k -> part(-0.25f, -0.25f, 0f, 0.5f, 0.5f, 1f, 0f));
		ModelPart knot = PARTS.computeIfAbsent("knot", k -> part(-1f, -1f, -1f, 2f, 2f, 2f, 0.25f));

		// The dark heart: light goes in and doesn't come out.
		float heart = (firstPerson ? 0.55f : 0.7f) + 0.15f * strength;
		poseStack.pushPose();
		poseStack.rotateDegrees(com.mojang.math.Axis.YP, time * 2f);
		poseStack.scale(heart, heart, heart);
		collector.submitModelPart(knot, poseStack, RenderTypes.entityTranslucent(SUN_CORE), ShaderGlow.light(),
				OverlayTexture.NO_OVERLAY, null, (int) (235 * Math.min(1f, 0.4f + strength)) << 24 | 0x020405);
		poseStack.popPose();

		// Its rim: a thin ring of light spinning round the edge, flat across the arm.
		int rim = 18;
		float rimR = 1.5f + 0.2f * strength;
		for (int i = 0; i < rim; i++) {
			float a0 = (i * 360f / rim + time * 9f) * Mth.DEG_TO_RAD;
			float a1 = ((i + 1) * 360f / rim + time * 9f) * Mth.DEG_TO_RAD;
			segment(poseStack, collector, ray, new Vec3(Mth.cos(a0) * rimR, 0, Mth.sin(a0) * rimR),
					new Vec3(Mth.cos(a1) * rimR, 0, Mth.sin(a1) * rimR), 0.9f,
					swirl(scroll * 2f % 1f, (scroll + i * 0.07f) % 1f), glow(Math.min(1f, (0.55f + 0.45f * Mth.sin(time * 0.5f + i)) * strength + 0.25f)));
		}

		// The streams: straight in from far off, bending round into the rim, brighter as they get close.
		float far = (firstPerson ? 16f : 30f) * (0.85f + 0.15f * strength);
		int segs = 11;
		float spin = time * 0.6f * Mth.DEG_TO_RAD;
		for (int i = 0; i < INFLOW_DIRS.length; i++) {
			Vec3 d = INFLOW_DIRS[i].yRot(spin);
			// The way it swirls in: across the arm, round the ring.
			Vec3 t = new Vec3(0, 1, 0).cross(d);
			t = t.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : t.normalize();
			Vec3 prev = null;
			for (int j = 0; j <= segs; j++) {
				float u = 1f - j / (float) segs;
				float r = rimR + (far - rimR) * u * u * (0.6f + 0.4f * u) / 1f;
				float twist = 3.0f * (1f - u) * (1f - u);
				Vec3 p = d.scale(Mth.cos(twist) * r).add(t.scale(Mth.sin(twist) * r));
				if (prev != null) {
					// Pulses of light running inward, out of step from one stream to the next.
					float pulse = 0.45f + 0.55f * Mth.sin(u * 9f + time * 0.45f + i * 1.9f);
					float fadeIn = Math.min(1f, (1f - u) * 4f);
					float b = (0.35f + 0.65f * strength) * fadeIn * (0.55f + 0.45f * (1f - u)) * Math.max(0.35f, pulse) * 1.4f;
					float thick = (firstPerson ? 0.9f : 1.5f) * (0.7f + 0.6f * (1f - u));
					segment(poseStack, collector, ray, prev, p, thick, swirl((scroll * 3f + i * 0.11f) % 1f, (scroll * 1.7f) % 1f),
							glow(Math.min(1f, b)));
				}
				prev = p;
			}
		}
		poseStack.popPose();
	}

	/** One straight piece of a stream from {@code a} to {@code b} (in skin pixels), {@code thick} wide. */
	private static void segment(PoseStack poseStack, SubmitNodeCollector collector, ModelPart ray, Vec3 a, Vec3 b,
			float thick, RenderType type, int tint) {
		Vec3 v = b.subtract(a);
		double len = v.length();
		if (len < 1e-3) return;
		poseStack.pushPose();
		poseStack.translate((float) a.x / 16f, (float) a.y / 16f, (float) a.z / 16f);
		poseStack.rotateDegrees(com.mojang.math.Axis.YP, (float) Math.toDegrees(Math.atan2(v.x, v.z)));
		poseStack.rotateDegrees(com.mojang.math.Axis.XP, (float) -Math.toDegrees(Math.asin(Mth.clamp(v.y / len, -1, 1))));
		poseStack.scale(thick, thick, (float) len);
		collector.submitModelPart(ray, poseStack, type, ShaderGlow.light(), OverlayTexture.NO_OVERLAY, null, tint);
		poseStack.popPose();
	}

	private static int lerpRgb(int from, int to, float t) {
		int r = Math.round(Mth.lerp(t, from >> 16 & 0xFF, to >> 16 & 0xFF));
		int g = Math.round(Mth.lerp(t, from >> 8 & 0xFF, to >> 8 & 0xFF));
		int b = Math.round(Mth.lerp(t, from & 0xFF, to & 0xFF));
		return r << 16 | g << 8 | b;
	}

	/** The fist end of the arm (arm y 4..10), as a shell just outside the skin. */
	private static ModelPart handPart(boolean leftArm, boolean slim) {
		float x0 = slim ? -2f : -3f;
		float x1 = 1f;
		if (leftArm) {
			float t = x0;
			x0 = -x1;
			x1 = -t;
		}
		return part(x0, 4f, -2f, x1 - x0, 6.4f, 4f, 0.45f);
	}

	private static ModelPart part(float x, float y, float z, float w, float h, float d, float grow) {
		MeshDefinition mesh = new MeshDefinition();
		mesh.getRoot().addOrReplaceChild("glow", CubeListBuilder.create().texOffs(0, 0)
				.addBox(x, y, z, w, h, d, new CubeDeformation(grow)), PartPose.ZERO);
		return LayerDefinition.create(mesh, 16, 16).bakeRoot().getChild("glow");
	}

	/**
	 * Where the charging ring is: in first person on the fist, otherwise held out ahead at chest
	 * height, where the aim pose puts it (LabFx.ringPos assumes a hanging arm).
	 */
	private static Vec3 ringPos(Minecraft mc, Player player, HumanoidArm arm) {
		if (player == mc.player && mc.options.getCameraType().isFirstPerson()) return LabFx.ringPos(mc, player, arm);
		Vec3 look = player.getViewVector(1f);
		Vec3 right = look.cross(new Vec3(0, 1, 0));
		right = right.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : right.normalize();
		float side = arm == HumanoidArm.RIGHT ? 1f : -1f;
		return player.getEyePosition(1f).add(look.scale(0.7)).add(right.scale(side * 0.33)).add(0, -0.4, 0);
	}

	/** Every client tick: motes drawn in toward each charging ring, sparks once it's full. */
	static void tick(Minecraft mc, RandomSource r) {
		if (!LabSettings.get().chargeGlow.motes()) return;
		for (Player player : mc.level.players()) {
			if (player.distanceToSqr(mc.player) > 48 * 48) continue;
			float p = progress(player, 0f);
			if (p < 0f) continue;
			Vec3 at = ringPos(mc, player, chargingArm(player));
			// In the charging player's ring colour, not the viewer's.
			Corps before = CorpsTint.enter(Corps.of(player.getUseItem()));
			// Fewer, wider-flung motes at first; a dense, tight stream as it nears full.
			int n = LabFx.count(0.6f + 2.2f * p);
			for (int i = 0; i < n; i++) {
				Vec3 dir = new Vec3(r.nextGaussian(), r.nextGaussian(), r.nextGaussian()).normalize();
				double dist = 0.55 - 0.25 * p + 0.2 * r.nextDouble();
				// Short-lived motes moving inward at the speed that lands them on the ring.
				LabFx.spawn(ModParticles.MOTE, at.add(dir.scale(dist)), dir.scale(-dist / 7.0), 0.35f + 0.35f * p);
			}
			if (p >= 1f && r.nextInt(3) == 0) LabFx.spawn(ModParticles.SPARK, at, Vec3.ZERO, 0.5f);
			CorpsTint.restore(before);
		}
	}
}
