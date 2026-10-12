package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.sparky.lanternring.LanternCharge;
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
	private static final int FULL_BRIGHT = 0xF000F0;
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
		if (LanternCharge.holdsBattery(player) && LanternCharge.started(player)) return -1f;
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
		return SoulSight.shaderPackOn() ? RenderTypes.entityTranslucentEmissive(SWIRL) : RenderTypes.energySwirl(SWIRL, u, v);
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
				FULL_BRIGHT, OverlayTexture.NO_OVERLAY, null, glow(b));
		poseStack.popPose();

		// The ring: a tighter, brighter knot of light on its face that grows with the charge.
		float[] face = RingModels.ringFace(model, leftArm, slim);
		ModelPart knot = PARTS.computeIfAbsent("knot", k -> part(-1f, -1f, -1f, 2f, 2f, 2f, 0.25f));
		poseStack.pushPose();
		poseStack.translate(face[0] / 16f, (face[1] - 0.5f) / 16f, face[2] / 16f);
		float size = 0.6f + 0.5f * p + (p >= 1f ? 0.1f * Mth.sin(time * 0.7f) : 0f);
		poseStack.scale(size, size, size);
		collector.submitModelPart(knot, poseStack, swirl(-scroll * 2f % 1f, scroll * 1.3f % 1f),
				FULL_BRIGHT, OverlayTexture.NO_OVERLAY, null, glow(b));
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
				FULL_BRIGHT, OverlayTexture.NO_OVERLAY, null, glow(b));
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
				FULL_BRIGHT, OverlayTexture.NO_OVERLAY, null, glow((firstPerson ? 0.45f : 0.7f) * f));
		float[] face = RingModels.ringFace(model, leftArm, slim);
		ModelPart knot = PARTS.computeIfAbsent("knot", k -> part(-1f, -1f, -1f, 2f, 2f, 2f, 0.25f));
		poseStack.pushPose();
		poseStack.translate(face[0] / 16f, (face[1] - 0.5f) / 16f, face[2] / 16f);
		// Bursts out big at once, then shrinks back into the ring as it fades.
		float size = firstPerson ? 0.6f + 0.7f * f : 0.8f + 2.2f * f;
		poseStack.scale(size, size, size);
		collector.submitModelPart(knot, poseStack, swirl(-scroll * 2f % 1f, scroll * 1.3f % 1f),
				FULL_BRIGHT, OverlayTexture.NO_OVERLAY, null, glow(Math.min(1f, (firstPerson ? 0.9f : 1.3f) * f)));
		poseStack.popPose();
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
			// Fewer, wider-flung motes at first; a dense, tight stream as it nears full.
			int n = LabFx.count(0.6f + 2.2f * p);
			for (int i = 0; i < n; i++) {
				Vec3 dir = new Vec3(r.nextGaussian(), r.nextGaussian(), r.nextGaussian()).normalize();
				double dist = 0.55 - 0.25 * p + 0.2 * r.nextDouble();
				// Short-lived motes moving inward at the speed that lands them on the ring.
				LabFx.spawn(ModParticles.MOTE, at.add(dir.scale(dist)), dir.scale(-dist / 7.0), 0.35f + 0.35f * p);
			}
			if (p >= 1f && r.nextInt(3) == 0) LabFx.spawn(ModParticles.SPARK, at, Vec3.ZERO, 0.5f);
		}
	}
}
