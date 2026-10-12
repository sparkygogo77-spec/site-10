package com.sparky.lanternring.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.sparky.lanternring.LanternRing;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.util.Mth;

/**
 * A rigged Blockbench model (Modded Entity, box UV, with groups): unlike {@link BbModel}, every
 * Blockbench group becomes a ModelPart of the same name with its pivot and rest rotation, nested
 * as in the outliner, so code can animate the bones by name (see DivingHawkModel). The result is
 * an entity model like the vanilla ones: feet on y=24 in model space, drawn by a LivingEntityRenderer.
 * Cubes named "glow..." go into a second layer with the same bones (drawn full-bright on top).
 */
public final class BbRig {
	public record Layers(LayerDefinition solid, LayerDefinition glow) {
	}

	private BbRig() {
	}

	public static Layers load(String name) {
		String path = "/assets/" + LanternRing.MOD_ID + "/bbmodel/" + name + ".bbmodel";
		JsonObject json;
		try (InputStream in = BbRig.class.getResourceAsStream(path)) {
			if (in == null) throw new IllegalStateException("missing " + path);
			json = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
		} catch (Exception e) {
			throw new IllegalStateException("Couldn't read " + path, e);
		}
		JsonObject resolution = json.getAsJsonObject("resolution");
		int texW = resolution.get("width").getAsInt();
		int texH = resolution.get("height").getAsInt();
		Map<String, JsonObject> cubes = new HashMap<>();
		for (JsonElement e : json.getAsJsonArray("elements")) {
			JsonObject el = e.getAsJsonObject();
			if (!"cube".equals(str(el, "type", "cube")) || (el.has("visibility") && !el.get("visibility").getAsBoolean())) continue;
			cubes.put(el.get("uuid").getAsString(), el);
		}
		return new Layers(build(json, cubes, false, texW, texH), build(json, cubes, true, texW, texH));
	}

	private static LayerDefinition build(JsonObject json, Map<String, JsonObject> cubes, boolean glow, int texW, int texH) {
		MeshDefinition mesh = new MeshDefinition();
		// Blockbench has the feet on y=0 and +Y up; entity models have them on y=24 and +Y down.
		PartDefinition root = mesh.getRoot().addOrReplaceChild("rig", CubeListBuilder.create(), PartPose.offset(0, 24, 0));
		int[] counter = {0};
		List<String> loose = new ArrayList<>();
		for (JsonElement e : json.getAsJsonArray("outliner")) {
			if (e.isJsonObject()) {
				group(root, e.getAsJsonObject(), new float[3], cubes, glow, counter);
			} else {
				loose.add(e.getAsString());
			}
		}
		// Cubes outside any group hang straight off the root.
		CubeListBuilder rest = CubeListBuilder.create();
		for (String id : loose) {
			JsonObject el = cubes.get(id);
			if (el != null && wanted(el, glow)) addCube(root, rest, el, new float[3], counter);
		}
		root.addOrReplaceChild("loose", rest, PartPose.ZERO);
		return LayerDefinition.create(mesh, texW, texH);
	}

	private static void group(PartDefinition parent, JsonObject g, float[] parentOrigin, Map<String, JsonObject> cubes, boolean glow, int[] counter) {
		float[] origin = g.has("origin") ? vec(g, "origin") : new float[3];
		float[] rot = g.has("rotation") ? vec(g, "rotation") : new float[3];
		List<JsonObject> plain = new ArrayList<>();
		List<JsonObject> turned = new ArrayList<>();
		for (JsonElement ch : g.getAsJsonArray("children")) {
			if (ch.isJsonObject()) continue;
			JsonObject el = cubes.get(ch.getAsString());
			if (el == null || !wanted(el, glow)) continue;
			(isTurned(el) ? turned : plain).add(el);
		}
		CubeListBuilder list = CubeListBuilder.create();
		for (JsonObject el : plain) box(list, el, origin);
		// Entity model space is Blockbench's turned 180 degrees about Z: x and y flip.
		PartDefinition part = parent.addOrReplaceChild(str(g, "name", "bone" + counter[0]++), list,
				PartPose.offsetAndRotation(-(origin[0] - parentOrigin[0]), -(origin[1] - parentOrigin[1]), origin[2] - parentOrigin[2],
						-rot[0] * Mth.DEG_TO_RAD, -rot[1] * Mth.DEG_TO_RAD, rot[2] * Mth.DEG_TO_RAD));
		for (JsonObject el : turned) addCube(part, null, el, origin, counter);
		for (JsonElement ch : g.getAsJsonArray("children")) {
			if (ch.isJsonObject()) group(part, ch.getAsJsonObject(), origin, cubes, glow, counter);
		}
	}

	private static boolean wanted(JsonObject el, boolean glow) {
		return str(el, "name", "").startsWith("glow") == glow;
	}

	private static boolean isTurned(JsonObject el) {
		if (!el.has("rotation")) return false;
		float[] r = vec(el, "rotation");
		return r[0] != 0 || r[1] != 0 || r[2] != 0;
	}

	/** A cube with its own rotation becomes a child part pivoting on the cube's origin. */
	private static void addCube(PartDefinition parent, CubeListBuilder list, JsonObject el, float[] origin, int[] counter) {
		if (!isTurned(el) && list != null) {
			box(list, el, origin);
			return;
		}
		float[] pivot = el.has("origin") ? vec(el, "origin") : origin;
		float[] rot = el.has("rotation") ? vec(el, "rotation") : new float[3];
		CubeListBuilder one = CubeListBuilder.create();
		box(one, el, pivot);
		parent.addOrReplaceChild("c" + counter[0]++, one, PartPose.offsetAndRotation(-(pivot[0] - origin[0]), -(pivot[1] - origin[1]),
				pivot[2] - origin[2], -rot[0] * Mth.DEG_TO_RAD, -rot[1] * Mth.DEG_TO_RAD, rot[2] * Mth.DEG_TO_RAD));
	}

	private static void box(CubeListBuilder list, JsonObject el, float[] origin) {
		float[] from = vec(el, "from");
		float[] to = vec(el, "to");
		float[] uv = el.has("uv_offset") ? vec(el, "uv_offset") : new float[2];
		float inflate = el.has("inflate") ? el.get("inflate").getAsFloat() : 0f;
		list.texOffs((int) uv[0], (int) uv[1]).addBox(origin[0] - to[0], origin[1] - to[1], from[2] - origin[2],
				to[0] - from[0], to[1] - from[1], to[2] - from[2], new CubeDeformation(inflate));
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
