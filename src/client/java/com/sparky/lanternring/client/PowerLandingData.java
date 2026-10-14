package com.sparky.lanternring.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.sparky.lanternring.LanternRing;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

/**
 * J's Blender power landing poses (pass 400, hand-off 2026-10-14-power-landing on the Blender branch,
 * packed by tools/power_landing_poses.py into assets/lanternring/poses/power_landing.json): A3 dissolve,
 * B2 plough and D0 stop dead, each tick from touchdown on six parts (head, body, ring arm, free arm,
 * ring leg, free leg) of {xRot, yRot, zRot, x, y, z offset px} for a right-handed ring, and the ring glow.
 */
final class PowerLandingData {
	/** A take: its ticks from touchdown (poses and ring glow) and how many of them are the slide. */
	record Take(float[][][] ticks, float[] glow, int slide) {
	}

	static final Map<String, Take> TAKES = new HashMap<>();
	private static boolean loaded;

	private PowerLandingData() {
	}

	static void load() {
		if (loaded) return;
		loaded = true;
		try (InputStream in = PowerLandingData.class.getResourceAsStream("/assets/" + LanternRing.MOD_ID + "/poses/power_landing.json")) {
			if (in == null) return;
			JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
			for (String name : root.keySet()) {
				JsonObject take = root.getAsJsonObject(name);
				JsonArray ticks = take.getAsJsonArray("ticks");
				float[][][] poses = new float[ticks.size()][6][6];
				float[] glow = new float[ticks.size()];
				for (int i = 0; i < poses.length; i++) {
					JsonObject t = ticks.get(i).getAsJsonObject();
					glow[i] = t.get("g").getAsFloat();
					JsonArray parts = t.getAsJsonArray("p");
					for (int p = 0; p < 6; p++) {
						JsonArray part = parts.get(p).getAsJsonArray();
						for (int k = 0; k < 6; k++) poses[i][p][k] = part.get(k).getAsFloat();
					}
				}
				TAKES.put(name, new Take(poses, glow, take.get("slide").getAsInt()));
			}
		} catch (Exception e) {
			LanternRing.LOGGER.warn("Couldn't read the power landing poses", e);
		}
	}
}
