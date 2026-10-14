package com.sparky.lanternring.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.sparky.lanternring.LanternRing;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import net.minecraft.util.Mth;

/**
 * J's pass 403 poses for the double-jump take-off and the soft landing, packed by tools/takeoff_landing_poses.py
 * into assets/lanternring/poses/takeoff_landing.json. Poses are six parts (head, body, ring arm, free arm, ring leg,
 * free leg) of {xRot, yRot, zRot, x, y, z offset px} for a right-handed ring, as SuperJumpPoses uses them.
 */
final class TakeoffPoseData {
	/** The standing take-off from the second jump's burst into the hero hover (S1, S2a and S2b share it). */
	static float[][][] stand = new float[0][][];
	/** The R3 running dart from the burst until it is laid out flat, with the A2 free arm. */
	static float[][][] dart = new float[0][][];
	/** The dart's free arm per tick, [xRot, zRot], for A1 (flush) and A3 (forward and out). */
	static float[][] freeA1 = new float[0][], freeA3 = new float[0][];
	/** L2 from the start of the descent: touchdown at {@link #LAND_TOUCH}, run-out to {@link #LAND_STAND}. */
	static float[][][] land = new float[0][][];
	/** L2's indices: end of the eased descent, touchdown (after the jump played backwards), end of the run-out. */
	static final int LAND_DOWN = 8, LAND_TOUCH = 11, LAND_STAND = 23;
	/** The standing take's index where the puff reaches the hover, and the dart's where the arc is flat. */
	static final int STAND_TOP = 3, DART_TOP = 6;
	private static boolean loaded;

	private TakeoffPoseData() {
	}

	static void load() {
		if (loaded) return;
		loaded = true;
		try (InputStream in = TakeoffPoseData.class.getResourceAsStream("/assets/" + LanternRing.MOD_ID + "/poses/takeoff_landing.json")) {
			if (in == null) return;
			JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
			stand = poses(root.getAsJsonArray("stand"));
			dart = poses(root.getAsJsonArray("dart"));
			land = poses(root.getAsJsonArray("land"));
			JsonObject free = root.getAsJsonObject("free");
			freeA1 = pairs(free.getAsJsonArray("A1"));
			freeA3 = pairs(free.getAsJsonArray("A3"));
		} catch (Exception e) {
			LanternRing.LOGGER.warn("Couldn't read the take-off and landing poses", e);
		}
	}

	/** The take at a fractional index, held on its last tick (an empty pose for an empty take). */
	static float[][] at(float[][][] take, float index) {
		if (take.length == 0) return new float[6][6];
		float i = Mth.clamp(index, 0f, take.length - 1);
		int a = Mth.floor(i);
		int b = Math.min(a + 1, take.length - 1);
		return SuperJumpPoses.mix(take[a], take[b], i - a);
	}

	/** The dart at a fractional index with the picked free arm (A2 is the packed one). */
	static float[][] dart(float index, LabSettings.FreeArm arm) {
		float[][] pose = at(dart, index);
		float[][] free = arm == LabSettings.FreeArm.A1 ? freeA1 : arm == LabSettings.FreeArm.A3 ? freeA3 : null;
		if (free != null && free.length > 0) {
			float i = Mth.clamp(index, 0f, free.length - 1);
			int a = Mth.floor(i);
			int b = Math.min(a + 1, free.length - 1);
			pose[3][0] = Mth.lerp(i - a, free[a][0], free[b][0]);
			pose[3][2] = Mth.lerp(i - a, free[a][1], free[b][1]);
		}
		return pose;
	}

	private static float[][][] poses(JsonArray array) {
		float[][][] out = new float[array.size()][6][6];
		for (int i = 0; i < out.length; i++) {
			JsonArray parts = array.get(i).getAsJsonArray();
			for (int p = 0; p < 6; p++) {
				JsonArray v = parts.get(p).getAsJsonArray();
				for (int k = 0; k < 6; k++) out[i][p][k] = v.get(k).getAsFloat();
			}
		}
		return out;
	}

	private static float[][] pairs(JsonArray array) {
		float[][] out = new float[array.size()][2];
		for (int i = 0; i < out.length; i++) {
			JsonArray v = array.get(i).getAsJsonArray();
			out[i][0] = v.get(0).getAsFloat();
			out[i][1] = v.get(1).getAsFloat();
		}
		return out;
	}
}
