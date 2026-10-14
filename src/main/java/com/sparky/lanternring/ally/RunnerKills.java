package com.sparky.lanternring.ally;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.sparky.lanternring.LanternRing;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 * The Dread Runner's kill clips (Blender pass 420, tools/runner_kill_clips.py): the "kill_k*" entries
 * of bbmodel/dread_runner_rig.json's "clips", in name order (K1..K4), read by the server (the runner's
 * and victim's movement, the hit) and by DreadRunnerRenderer (the poses). 24 frames a second; root
 * and target are model px (x right, y forward, z up) at the rig's own size (DreadRunner.SCALE scales them).
 */
public final class RunnerKills {
	public static final float FPS = 24f;

	/**
	 * One clip. {@code root[i]}: the runner's offset from where the clip started; {@code target[i]}: where the
	 * victim's middle is held, from a standing mob's middle at the runner's start (null once it's let go).
	 */
	public record Clip(String name, int hit, float[][] root, float[][] target, List<JsonObject> frames) {
		public int length() {
			return root.length;
		}

		/** The clip's length in game ticks. */
		public int ticks() {
			return (int) Math.ceil(length() / FPS * 20f);
		}
	}

	private static List<Clip> clips;

	private RunnerKills() {
	}

	public static List<Clip> clips() {
		if (clips != null) return clips;
		clips = new ArrayList<>();
		String path = "/assets/" + LanternRing.MOD_ID + "/bbmodel/dread_runner_rig.json";
		try (InputStream in = RunnerKills.class.getResourceAsStream(path)) {
			if (in == null) return clips;
			JsonObject rig = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
			if (!rig.has("clips")) return clips;
			Map<String, JsonElement> sorted = new TreeMap<>(rig.getAsJsonObject("clips").asMap());
			for (Map.Entry<String, JsonElement> e : sorted.entrySet()) {
				if (!e.getKey().startsWith("kill_k")) continue;
				JsonObject c = e.getValue().getAsJsonObject();
				JsonArray root = c.getAsJsonArray("root"), target = c.getAsJsonArray("target");
				float[][] r = new float[root.size()][];
				float[][] t = new float[root.size()][];
				List<JsonObject> frames = new ArrayList<>();
				for (int i = 0; i < r.length; i++) {
					r[i] = vec(root.get(i).getAsJsonArray());
					JsonElement ti = i < target.size() ? target.get(i) : null;
					t[i] = ti == null || ti.isJsonNull() ? null : vec(ti.getAsJsonArray());
					frames.add(c.getAsJsonArray("frames").get(i).getAsJsonObject());
				}
				clips.add(new Clip(e.getKey(), c.get("hit").getAsInt(), r, t, frames));
			}
		} catch (Exception e) {
			LanternRing.LOGGER.warn("Couldn't read the Dread Runner kill clips", e);
		}
		return clips;
	}

	private static float[] vec(JsonArray a) {
		float[] out = new float[a.size()];
		for (int i = 0; i < out.length; i++) out[i] = a.get(i).getAsFloat();
		return out;
	}
}
