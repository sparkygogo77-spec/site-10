package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;

/**
 * The 3D ring worn on the player's arm. Coordinates are in arm-model pixels: the arm cube runs
 * y -2..10 (shoulder to fist) and z -2..2; the right arm is x -3..1 (x -2..1 for slim skins), and
 * its back of the hand faces -x. Left arms are mirrored.
 */
public final class RingModels {
	enum Mat {
		GOLD("gold", false), BAND("band", false), DARK("dark", false), GEM("gem", false),
		GLOW("gem_glow", true), HALO("halo", true);

		final Identifier texture;
		final boolean emissive;

		Mat(String name, boolean emissive) {
			this.texture = LanternRing.id("textures/entity/ring/" + name + ".png");
			this.emissive = emissive;
		}

		RenderType renderType(Corps corps) {
			Identifier tex = CorpsTint.texture(texture, corps);
			// Under a shader pack eyes draws black on the first-person hand; this one still glows.
			if (!emissive) return RenderTypes.entityCutout(tex);
			return SoulSight.shaderPackOn() ? RenderTypes.entityTranslucentEmissive(tex) : RenderTypes.eyes(tex);
		}
	}

	private record Box(Mat mat, float x0, float y0, float z0, float x1, float y1, float z1) {
		Box inflate(float d, Mat as) {
			return new Box(as, x0 - d, y0 - d, z0 - d, x1 + d, y1 + d, z1 + d);
		}

		Box mirrored() {
			return new Box(mat, -x1, y0, z0, -x0, y1, z1);
		}
	}

	private static final int FULL_BRIGHT = 0xF000F0;
	private static final Map<String, Map<Mat, ModelPart>> CACHE = new HashMap<>();
	/** Blockbench rings (assets/lanternring/bbmodel/), loaded on first use. */
	private static final Map<String, BbModel> BB = new HashMap<>();

	private RingModels() {
	}

	/** Draws the ring; the pose stack must already be in the arm's model space. */
	public static void render(PoseStack poseStack, SubmitNodeCollector collector, int light,
			LabSettings.RingModel model, boolean leftArm, boolean slim) {
		// The ring lights itself: full-bright whatever the light around it, with a soft glow on its face.
		BeamChargeGlow.renderIdle(poseStack, collector, model, leftArm, slim);
		Placement at = placement(model);
		if (at != null) {
			renderBb(poseStack, collector, light, model, at, leftArm, slim);
			return;
		}
		String key = model + "/" + leftArm + "/" + slim;
		Map<Mat, ModelPart> parts = CACHE.computeIfAbsent(key, k -> bake(boxes(model, leftArm, slim)));
		for (Map.Entry<Mat, ModelPart> e : parts.entrySet()) {
			Mat mat = e.getKey();
			collector.submitModelPart(e.getValue(), poseStack, mat.renderType(CorpsTint.current()),
					FULL_BRIGHT, OverlayTexture.NO_OVERLAY, null);
		}
	}

	/**
	 * Where a Blockbench ring sits: on the fist's punching face (arm y = 10) facing out of it,
	 * {@code inset} skin pixels in from the back of the hand, over the middle finger.
	 * {@code units} is how many model units make one skin pixel; {@code height} how far the face
	 * stands off the fist, in skin pixels.
	 */
	private record Placement(String file, float units, float inset, float height) {
	}

	private static Placement placement(LabSettings.RingModel model) {
		return switch (model) {
			case FORGED -> new Placement("ring_forged", 16f, 1f, 12f / 16f);
			case CREST -> new Placement("ring_crest", 16f, 1f, 13f / 16f);
			case CREST_GOLD -> new Placement("ring_crest_gold", 16f, 1f, 14f / 16f);
			case BEACON -> new Placement("ring_beacon", 16f, 1f, 15f / 16f);
			case EMBLEM -> new Placement("power_ring", 6f, 0.8f, 5f / 6f);
			default -> null;
		};
	}

	private static final float RING_Z = -0.5f;
	private static final Identifier AURA = LanternRing.id("textures/entity/ring_halo.png");
	/** How much bigger than the ring its aura shell is. */
	private static final float AURA_GROW = 1.14f;

	/** Additive: the corps colour scaled by brightness. Under a shader pack: see-through, faint by alpha. */
	private static int auraColor(Corps corps, float pulse, boolean shaders) {
		int rgb = corps.rgb;
		if (shaders) return (int) (0.5f * pulse * 255) << 24 | rgb & 0xFFFFFF;
		float b = 0.45f * pulse;
		int r = (int) ((rgb >> 16 & 0xFF) * b), g = (int) ((rgb >> 8 & 0xFF) * b), bl = (int) ((rgb & 0xFF) * b);
		return 0xFF000000 | r << 16 | g << 8 | bl;
	}

	private static void renderBb(PoseStack poseStack, SubmitNodeCollector collector, int light, LabSettings.RingModel model,
			Placement at, boolean leftArm, boolean slim) {
		// In the colour of the ring being drawn (see CorpsTint).
		Corps corps = CorpsTint.current();
		BbModel bb = BB.computeIfAbsent(model + "/" + corps, k -> BbModel.load(at.file()).forCorps(corps));
		float x = (slim ? -2f : -3f) + at.inset();
		poseStack.pushPose();
		poseStack.translate((leftArm ? -x : x) / 16f, 10f / 16f, RING_Z / 16f);
		if (leftArm) poseStack.rotateDegrees(com.mojang.math.Axis.YP, 180f);
		poseStack.scale(1 / at.units(), 1 / at.units(), 1 / at.units());
		bb.renderLit(poseStack, collector, BbModel.glow(1f));
		// An aura outline round the ring in its corps' colour, like the wearer's glint (RingAuraLayer).
		float age = (System.nanoTime() / 1_000_000L % 3_600_000L) / 50f;
		float pulse = 0.8f + 0.2f * Mth.sin(age * 0.1f);
		boolean shaders = SoulSight.shaderPackOn();
		RenderType aura = shaders ? RenderTypes.entityTranslucentEmissive(AURA)
				: RenderTypes.energySwirl(AURA, age * 0.004f % 1f, age * 0.0025f % 1f);
		bb.renderAura(poseStack, collector, aura, auraColor(corps, pulse, shaders), AURA_GROW);
		poseStack.popPose();
	}

	/** The centre of the ring's face in arm space (skin pixels), for things that aim at it. */
	static float[] ringFace(LabSettings.RingModel model, boolean leftArm, boolean slim) {
		Placement at = placement(model);
		if (at == null) at = placement(LabSettings.RingModel.CREST);
		float x = (slim ? -2f : -3f) + at.inset();
		return new float[] {leftArm ? -x : x, 10f + at.height(), RING_Z};
	}

	private static Map<Mat, ModelPart> bake(List<Box> boxes) {
		Map<Mat, CubeListBuilder> builders = new EnumMap<>(Mat.class);
		for (Box b : boxes) {
			builders.computeIfAbsent(b.mat, m -> CubeListBuilder.create().texOffs(0, 0))
					.addBox(b.x0, b.y0, b.z0, b.x1 - b.x0, b.y1 - b.y0, b.z1 - b.z0);
		}
		Map<Mat, ModelPart> parts = new EnumMap<>(Mat.class);
		for (Map.Entry<Mat, CubeListBuilder> e : builders.entrySet()) {
			MeshDefinition mesh = new MeshDefinition();
			mesh.getRoot().addOrReplaceChild("ring", e.getValue(), PartPose.ZERO);
			parts.put(e.getKey(), LayerDefinition.create(mesh, 16, 16).bakeRoot().getChild("ring"));
		}
		return parts;
	}

	private static List<Box> boxes(LabSettings.RingModel model, boolean leftArm, boolean slim) {
		List<Box> out = new ArrayList<>();
		float ax0 = slim ? -2 : -3;
		float ax1 = 1;
		switch (model) {
			case SIGNET -> {
				float yc = 7.6f;
				float ox0 = band(out, Mat.BAND, ax0, ax1, yc, 1.6f, 0.3f, 0.5f);
				out.add(new Box(Mat.GOLD, ox0 - 0.5f, yc - 1.6f, -1.9f, ox0, yc + 1.6f, 1.9f));
				out.add(new Box(Mat.DARK, ox0 - 0.75f, yc - 1.0f, -1.4f, ox0 - 0.5f, yc + 1.0f, 1.4f));
				out.add(new Box(Mat.GOLD, ox0 - 0.9f, yc + 1.0f, -1.9f, ox0 - 0.5f, yc + 1.6f, 1.9f));
				out.add(new Box(Mat.GOLD, ox0 - 0.9f, yc - 1.6f, -1.9f, ox0 - 0.5f, yc - 1.0f, 1.9f));
				Box gem = new Box(Mat.GEM, ox0 - 1.05f, yc - 0.75f, -0.95f, ox0 - 0.75f, yc + 0.75f, 0.95f);
				glowingGem(out, gem, 0.3f);
			}
			case SLIM -> {
				float yc = 7.8f;
				float ox0 = band(out, Mat.GOLD, ax0, ax1, yc, 1.0f, 0.2f, 0.35f);
				out.add(new Box(Mat.GOLD, ox0 - 0.4f, yc - 0.9f, -0.9f, ox0, yc + 0.9f, 0.9f));
				Box gem = new Box(Mat.GEM, ox0 - 0.75f, yc - 0.6f, -0.6f, ox0 - 0.4f, yc + 0.6f, 0.6f);
				glowingGem(out, gem, 0.2f);
			}
			case LANTERN -> {
				float yc = 7.4f;
				float ox0 = band(out, Mat.BAND, ax0, ax1, yc, 2.0f, 0.35f, 0.6f);
				out.add(new Box(Mat.DARK, ox0 - 0.6f, yc - 2.0f, -2.2f, ox0, yc + 2.0f, 2.2f));
				out.add(new Box(Mat.GOLD, ox0 - 1.0f, yc + 1.3f, -2.3f, ox0 - 0.6f, yc + 2.1f, 2.3f));
				out.add(new Box(Mat.GOLD, ox0 - 1.0f, yc - 2.1f, -2.3f, ox0 - 0.6f, yc - 1.3f, 2.3f));
				out.add(new Box(Mat.GEM, ox0 - 1.1f, yc + 1.5f, -1.9f, ox0 - 1.0f, yc + 1.9f, 1.9f));
				out.add(new Box(Mat.GEM, ox0 - 1.1f, yc - 1.9f, -1.9f, ox0 - 1.0f, yc - 1.5f, 1.9f));
				out.add(new Box(Mat.GOLD, ox0 - 0.9f, yc - 1.1f, -2.0f, ox0 - 0.6f, yc + 1.1f, -1.6f));
				out.add(new Box(Mat.GOLD, ox0 - 0.9f, yc - 1.1f, 1.6f, ox0 - 0.6f, yc + 1.1f, 2.0f));
				Box gem = new Box(Mat.GEM, ox0 - 1.2f, yc - 1.0f, -1.2f, ox0 - 0.6f, yc + 1.0f, 1.2f);
				glowingGem(out, gem, 0.35f);
			}
		}
		if (leftArm) out.replaceAll(Box::mirrored);
		return out;
	}

	/** A rectangular band standing slightly off the arm; returns the outer -x face it sits on. */
	private static float band(List<Box> out, Mat mat, float ax0, float ax1, float yc, float height, float standoff, float thick) {
		float y0 = yc - height / 2;
		float y1 = yc + height / 2;
		float ox0 = ax0 - standoff - thick;
		float ox1 = ax1 + standoff + thick;
		float oz0 = -2 - standoff - thick;
		float oz1 = 2 + standoff + thick;
		out.add(new Box(mat, ox0, y0, oz0, ox1, y1, oz0 + thick));
		out.add(new Box(mat, ox0, y0, oz1 - thick, ox1, y1, oz1));
		out.add(new Box(mat, ox0, y0, oz0 + thick, ox0 + thick, y1, oz1 - thick));
		out.add(new Box(mat, ox1 - thick, y0, oz0 + thick, ox1, y1, oz1 - thick));
		return ox0;
	}

	/** The gem, its full-bright glow pass, and a faint shell of light around it. */
	private static void glowingGem(List<Box> out, Box gem, float halo) {
		out.add(gem);
		out.add(gem.inflate(0.01f, Mat.GLOW));
		out.add(gem.inflate(halo, Mat.HALO));
	}
}
