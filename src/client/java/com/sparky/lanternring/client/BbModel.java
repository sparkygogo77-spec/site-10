package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.LanternRing;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;

/**
 * A Blockbench model (Modded Entity, box UV) read from assets/lanternring/bbmodel/<name>.bbmodel,
 * textured with textures/entity/bb/<name>.png. Cubes named "glow..." are drawn full-bright,
 * glowing in the dark; "core..." cubes glow too and can be swelled about their centre (the
 * Nebula battery's orb); "glass..." cubes are drawn see-through and full-bright. Drawn in Blockbench's own coordinates (+Y up, 1 unit = 1/16 of a block) relative to
 * the current pose; tools/blockbench_models.py generates the shipped models.
 */
public final class BbModel {
	private static final int FULL_BRIGHT = 0xF000F0;

	private final Identifier texture;
	private final ModelPart solid;
	private final ModelPart glow;
	private final ModelPart core;
	private final ModelPart glass;
	/** The middle of the core cubes, in Blockbench units. */
	private final float[] coreCentre;

	private BbModel(Identifier texture, ModelPart solid, ModelPart glow, ModelPart core, ModelPart glass, float[] coreCentre) {
		this.texture = texture;
		this.solid = solid;
		this.glow = glow;
		this.core = core;
		this.glass = glass;
		this.coreCentre = coreCentre;
	}

	public static BbModel load(String name) {
		String path = "/assets/" + LanternRing.MOD_ID + "/bbmodel/" + name + ".bbmodel";
		JsonObject json;
		try (InputStream in = BbModel.class.getResourceAsStream(path)) {
			if (in == null) throw new IllegalStateException("missing " + path);
			json = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
		} catch (Exception e) {
			throw new IllegalStateException("Couldn't read " + path, e);
		}
		JsonObject resolution = json.getAsJsonObject("resolution");
		int texW = resolution.get("width").getAsInt();
		int texH = resolution.get("height").getAsInt();

		MeshDefinition solidMesh = new MeshDefinition();
		MeshDefinition glowMesh = new MeshDefinition();
		MeshDefinition coreMesh = new MeshDefinition();
		MeshDefinition glassMesh = new MeshDefinition();
		float[] coreCentre = new float[3];
		int cores = 0;
		int i = 0;
		for (JsonElement e : json.getAsJsonArray("elements")) {
			JsonObject el = e.getAsJsonObject();
			if (!"cube".equals(str(el, "type", "cube")) || (el.has("visibility") && !el.get("visibility").getAsBoolean())) continue;
			float[] from = vec(el, "from");
			float[] to = vec(el, "to");
			float[] origin = el.has("origin") ? vec(el, "origin") : new float[3];
			float[] rot = el.has("rotation") ? vec(el, "rotation") : new float[3];
			float[] uv = el.has("uv_offset") ? vec(el, "uv_offset") : new float[2];
			float inflate = el.has("inflate") ? el.get("inflate").getAsFloat() : 0f;

			// Blockbench is +Y up; entity model space is the same turned 180 degrees about Z
			// (x and y negated). render() turns it back, so the model shows as authored.
			float px = -origin[0];
			float py = -origin[1];
			float pz = origin[2];
			CubeListBuilder cube = CubeListBuilder.create().texOffs((int) uv[0], (int) uv[1])
					.addBox(-to[0] - px, -to[1] - py, from[2] - pz, to[0] - from[0], to[1] - from[1], to[2] - from[2],
							new CubeDeformation(inflate));
			PartPose pose = PartPose.offsetAndRotation(px, py, pz,
					-rot[0] * Mth.DEG_TO_RAD, -rot[1] * Mth.DEG_TO_RAD, rot[2] * Mth.DEG_TO_RAD);
			String cubeName = str(el, "name", "");
			MeshDefinition mesh = cubeName.startsWith("glow") ? glowMesh : cubeName.startsWith("core") ? coreMesh
					: cubeName.startsWith("glass") ? glassMesh : solidMesh;
			if (mesh == coreMesh) {
				for (int k = 0; k < 3; k++) coreCentre[k] += (from[k] + to[k]) / 2f;
				cores++;
			}
			PartDefinition root = mesh.getRoot();
			root.addOrReplaceChild("c" + i++, cube, pose);
		}
		Identifier texture = LanternRing.id("textures/entity/bb/" + name + ".png");
		if (cores > 0) for (int k = 0; k < 3; k++) coreCentre[k] /= cores;
		return new BbModel(texture,
				LayerDefinition.create(solidMesh, texW, texH).bakeRoot(),
				LayerDefinition.create(glowMesh, texW, texH).bakeRoot(),
				LayerDefinition.create(coreMesh, texW, texH).bakeRoot(),
				LayerDefinition.create(glassMesh, texW, texH).bakeRoot(), coreCentre);
	}

	/** The same model with another texture, e.g. a corps' recoloured one (see CorpsTint.texture). */
	public BbModel retextured(Identifier texture) {
		return new BbModel(texture, solid, glow, core, glass, coreCentre);
	}

	/** This model's texture in the corps' colour. */
	public BbModel forCorps(Corps corps) {
		return corps == Corps.GREEN ? this : retextured(CorpsTint.texture(texture, corps));
	}

	/** Draws the model; {@code glowColor} (ARGB) tints the glowing cubes, so darker means dimmer. */
	public void render(PoseStack poseStack, SubmitNodeCollector collector, int light, int glowColor) {
		render(poseStack, collector, light, glowColor, 1f);
	}

	/** Draws the model with its core cubes swelled {@code coreScale} times about their centre. */
	public void render(PoseStack poseStack, SubmitNodeCollector collector, int light, int glowColor, float coreScale) {
		render(poseStack, collector, light, glowColor, coreScale, RenderTypes.eyes(texture));
	}

	/**
	 * Draws the model lit up from inside: the solid cubes full-bright too, and the glow cubes in a
	 * type that still glows under shader packs ({@code eyes} draws black on the first-person hand
	 * there). For the ring worn on the hand.
	 */
	public void renderLit(PoseStack poseStack, SubmitNodeCollector collector, int glowColor) {
		render(poseStack, collector, FULL_BRIGHT, glowColor, 1f,
				SoulSight.shaderPackOn() ? RenderTypes.entityTranslucentEmissive(texture) : RenderTypes.eyes(texture));
	}

	private void render(PoseStack poseStack, SubmitNodeCollector collector, int light, int glowColor, float coreScale,
			RenderType glowType) {
		poseStack.pushPose();
		poseStack.rotateDegrees(Axis.ZP, 180f);
		if (has(solid)) collector.submitModelPart(solid, poseStack, RenderTypes.entityCutout(texture), light, OverlayTexture.NO_OVERLAY, null);
		if ((glowColor & 0xFFFFFF) != 0) {
			if (has(glow)) collector.submitModelPart(glow, poseStack, glowType, FULL_BRIGHT, OverlayTexture.NO_OVERLAY, null, glowColor);
			if (has(core)) {
				// Entity model space is Blockbench's turned 180 degrees about Z: x and y flip.
				poseStack.pushPose();
				poseStack.translate(-coreCentre[0] / 16f, -coreCentre[1] / 16f, coreCentre[2] / 16f);
				poseStack.scale(coreScale, coreScale, coreScale);
				poseStack.translate(coreCentre[0] / 16f, coreCentre[1] / 16f, -coreCentre[2] / 16f);
				// The core never dims: it is the one very bright point inside the dark glass.
				collector.submitModelPart(core, poseStack, glowType, FULL_BRIGHT, OverlayTexture.NO_OVERLAY, null, -1);
				poseStack.popPose();
			}
		}
		if (has(glass)) {
			collector.submitModelPart(glass, poseStack, RenderTypes.entityTranslucent(texture), FULL_BRIGHT, OverlayTexture.NO_OVERLAY, null);
		}
		poseStack.popPose();
	}

	/**
	 * A soft shell of light round the whole model: every cube again, {@code grow} times bigger, in
	 * {@code type} (an additive or see-through glow) tinted {@code color}.
	 */
	public void renderAura(PoseStack poseStack, SubmitNodeCollector collector, RenderType type, int color, float grow) {
		poseStack.pushPose();
		poseStack.rotateDegrees(Axis.ZP, 180f);
		poseStack.scale(grow, grow, grow);
		for (ModelPart part : new ModelPart[] {solid, glow, core}) {
			if (has(part)) collector.order(1).submitModelPart(part, poseStack, type, FULL_BRIGHT, OverlayTexture.NO_OVERLAY, null, color);
		}
		poseStack.popPose();
	}

	/** Draws only the glowing cubes, e.g. a second time on top for extra brightness. */
	public void renderGlow(PoseStack poseStack, SubmitNodeCollector collector, int glowColor) {
		poseStack.pushPose();
		poseStack.rotateDegrees(Axis.ZP, 180f);
		collector.submitModelPart(glow, poseStack, RenderTypes.eyes(texture), FULL_BRIGHT, OverlayTexture.NO_OVERLAY, null, glowColor);
		poseStack.popPose();
	}

	/** A grey of the given brightness, 0..1, as a glow tint. */
	public static int glow(float brightness) {
		int v = Mth.clamp((int) (brightness * 255), 0, 255);
		return 0xFF000000 | v << 16 | v << 8 | v;
	}

	/** Whether a baked root holds any cubes (they sit in its children; the root itself has none). */
	private static boolean has(ModelPart root) {
		return root.getAllParts().size() > 1;
	}

	private static float[] vec(JsonObject o, String key) {
		JsonArray a = o.getAsJsonArray(key);
		float[] out = new float[a.size()];
		for (int i = 0; i < out.length; i++) out[i] = a.get(i).getAsFloat();
		return out;
	}

	private static String str(JsonObject o, String key, String fallback) {
		return o.has(key) ? o.get(key).getAsString() : fallback;
	}
}
