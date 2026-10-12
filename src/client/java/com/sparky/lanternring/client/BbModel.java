package com.sparky.lanternring.client;

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
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;

/**
 * A Blockbench model (Modded Entity, box UV) read from assets/lanternring/bbmodel/<name>.bbmodel,
 * textured with textures/entity/bb/<name>.png. Cubes named "glow..." are drawn full-bright and
 * additive. Drawn in Blockbench's own coordinates (+Y up, 1 unit = 1/16 of a block) relative to
 * the current pose; tools/blockbench_models.py generates the shipped models.
 */
public final class BbModel {
	private static final int FULL_BRIGHT = 0xF000F0;

	private final Identifier texture;
	private final ModelPart solid;
	private final ModelPart glow;

	private BbModel(Identifier texture, ModelPart solid, ModelPart glow) {
		this.texture = texture;
		this.solid = solid;
		this.glow = glow;
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
			boolean glowing = str(el, "name", "").startsWith("glow");
			PartDefinition root = (glowing ? glowMesh : solidMesh).getRoot();
			root.addOrReplaceChild("c" + i++, cube, pose);
		}
		Identifier texture = LanternRing.id("textures/entity/bb/" + name + ".png");
		return new BbModel(texture,
				LayerDefinition.create(solidMesh, texW, texH).bakeRoot(),
				LayerDefinition.create(glowMesh, texW, texH).bakeRoot());
	}

	/** Draws the model; {@code glowColor} (ARGB) tints the glowing cubes, so darker means dimmer. */
	public void render(PoseStack poseStack, SubmitNodeCollector collector, int light, int glowColor) {
		poseStack.pushPose();
		poseStack.rotateDegrees(Axis.ZP, 180f);
		collector.submitModelPart(solid, poseStack, RenderTypes.entityCutout(texture), light, OverlayTexture.NO_OVERLAY, null);
		if ((glowColor & 0xFFFFFF) != 0) {
			collector.submitModelPart(glow, poseStack, RenderTypes.eyes(texture), FULL_BRIGHT, OverlayTexture.NO_OVERLAY, null, glowColor);
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
