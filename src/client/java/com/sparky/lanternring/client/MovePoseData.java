package com.sparky.lanternring.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.sparky.lanternring.LanternRing;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.EnumMap;
import java.util.Map;

/**
 * J's Blender poses for movement and flight (hand-off 2026-10-14-movement-flight on the Blender branch,
 * packed by tools/movement_flight_poses.py into assets/lanternring/poses/movement_flight.json). Each pose
 * is six parts (head, body, ring arm, free arm, ring leg, free leg) of {xRot, yRot, zRot, x, y, z offset px}
 * for a right-handed ring, as SuperJumpPoses uses them.
 */
final class MovePoseData {
	/** One tick of a take: the pose and its extras (forward and up in blocks, ring glow, dome alpha and squash). */
	record Tick(float[][] pose, float forward, float up, float glow, float alpha, float squash) {
	}

	/** A ground flight halt take: its ticks from laying out (index 0 = Blender tick 15), the hit index, stop ticks and depth. */
	record Halt(Tick[] ticks, int hit, int stop, float depth) {
	}

	/** One stride (12 ticks) of the S5a and S5b sprint. */
	static final Map<LabSettings.SprintCarry, float[][][]> SPRINT = new EnumMap<>(LabSettings.SprintCarry.class);
	/** F2 from the plant (Blender tick 24) on. */
	static Tick[] takeoff = new Tick[0];
	static final Map<LabSettings.GroundHalt, Halt> GROUND = new EnumMap<>(LabSettings.GroundHalt.class);
	private static boolean loaded;

	private MovePoseData() {
	}

	static void load() {
		if (loaded) return;
		loaded = true;
		try (InputStream in = MovePoseData.class.getResourceAsStream("/assets/" + LanternRing.MOD_ID + "/poses/movement_flight.json")) {
			if (in == null) return;
			JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
			JsonObject sprint = root.getAsJsonObject("sprint");
			SPRINT.put(LabSettings.SprintCarry.S5A, poses(sprint.getAsJsonArray("S5a")));
			SPRINT.put(LabSettings.SprintCarry.S5B, poses(sprint.getAsJsonArray("S5b")));
			takeoff = ticks(root.getAsJsonArray("takeoff"));
			JsonObject ground = root.getAsJsonObject("ground");
			for (LabSettings.GroundHalt h : LabSettings.GroundHalt.values()) {
				JsonObject take = ground.getAsJsonObject(h.name());
				GROUND.put(h, new Halt(ticks(take.getAsJsonArray("ticks")), take.get("hit").getAsInt(), take.get("stop").getAsInt(),
						take.get("depth").getAsFloat()));
			}
		} catch (Exception e) {
			LanternRing.LOGGER.warn("Couldn't read the movement and flight poses", e);
		}
	}

	private static float[][][] poses(JsonArray array) {
		float[][][] out = new float[array.size()][][];
		for (int i = 0; i < out.length; i++) out[i] = pose(array.get(i).getAsJsonArray());
		return out;
	}

	private static float[][] pose(JsonArray parts) {
		float[][] out = new float[6][6];
		for (int i = 0; i < 6; i++) {
			JsonArray p = parts.get(i).getAsJsonArray();
			for (int k = 0; k < 6; k++) out[i][k] = p.get(k).getAsFloat();
		}
		return out;
	}

	private static Tick[] ticks(JsonArray array) {
		Tick[] out = new Tick[array.size()];
		for (int i = 0; i < out.length; i++) {
			JsonObject t = array.get(i).getAsJsonObject();
			out[i] = new Tick(pose(t.getAsJsonArray("p")), get(t, "f"), get(t, "u"), get(t, "g"), get(t, "a"), get(t, "s"));
		}
		return out;
	}

	private static float get(JsonObject o, String key) {
		JsonElement e = o.get(key);
		return e == null ? 0f : e.getAsFloat();
	}
}
