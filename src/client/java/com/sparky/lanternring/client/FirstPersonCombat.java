package com.sparky.lanternring.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.sparky.lanternring.LanternRing;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import org.joml.Vector3f;
import org.jspecify.annotations.Nullable;

/**
 * First person (J, 2026-10-15: "no 1st person animation for the punch currently, no flurry either"): both arms
 * through the ring-hand punch (pass 502: P1b step-in jab, P1c hook) and the flying flurry F2 (pass 520: jab, cross,
 * spinning backfist), timed by the same tracks as CombatPoses' third-person takes. Poses packed by
 * tools/first_person_combat.py into poses/first_person_combat.json, in RingFirstPerson's view space for a right hand;
 * the Ring Lab's fp_arms row picks pass 520's vanilla or 1.3x bigger arms.
 */
public final class FirstPersonCombat {
	/** One arm now: fist and elbow points, back of the hand, and the arm's size (right-handed view space). */
	public record Arm(Vector3f fist, Vector3f elbow, Vector3f back, float scale) {
	}

	/** Both arms of the move playing now, and how far it holds them (0..1, blending in and out). */
	public record Now(Arm ring, Arm free, float weight) {
	}

	private record Clip(float scale, float[][] ring, float[][] free) {
	}

	private static final String[] NAMES = {"P1B", "P1C", "FLURRY"};
	/** Indices 0-2 at vanilla size, 3-5 bigger. */
	private static final Clip[] CLIPS = new Clip[6];
	private static boolean loaded;

	private FirstPersonCombat() {
	}

	private static void load() {
		if (loaded) return;
		loaded = true;
		try (InputStream in = FirstPersonCombat.class.getResourceAsStream("/assets/" + LanternRing.MOD_ID + "/poses/first_person_combat.json")) {
			if (in == null) return;
			JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
			for (int i = 0; i < NAMES.length; i++) {
				CLIPS[i] = clip(root.getAsJsonObject(NAMES[i]));
				CLIPS[i + 3] = clip(root.getAsJsonObject(NAMES[i] + "_BIG"));
			}
		} catch (Exception e) {
			LanternRing.LOGGER.warn("Couldn't read the first-person combat poses", e);
		}
	}

	private static @Nullable Clip clip(@Nullable JsonObject o) {
		if (o == null) return null;
		JsonArray ticks = o.getAsJsonArray("ticks");
		float[][] ring = new float[ticks.size()][], free = new float[ticks.size()][];
		for (int i = 0; i < ticks.size(); i++) {
			JsonObject t = ticks.get(i).getAsJsonObject();
			ring[i] = floats(t.getAsJsonArray("r"));
			free[i] = floats(t.getAsJsonArray("l"));
		}
		return new Clip(o.get("scale").getAsFloat(), ring, free);
	}

	private static float[] floats(JsonArray a) {
		float[] out = new float[a.size()];
		for (int i = 0; i < out.length; i++) out[i] = a.get(i).getAsFloat();
		return out;
	}

	/** The punch or flying flurry this player's arms are in now, or null. */
	public static @Nullable Now now(Player player, float partial) {
		float[] at = CombatPoses.firstPerson(player.getId(), partial);
		if (at == null) return null;
		load();
		Clip clip = CLIPS[(int) at[0] + (LabSettings.get().fpArms == LabSettings.FpArms.BIGGER ? 3 : 0)];
		if (clip == null) return null;
		return new Now(arm(clip.ring, clip.scale, at[1]), arm(clip.free, clip.scale, at[1]), at[2]);
	}

	/** For screenshot tests: start the ring-hand punch (in the Ring Lab's pick) or, with {@code flurry}, the flying flurry. */
	public static void play(Player player, boolean flurry) {
		if (flurry) CombatPoses.flurry(player.getId());
		else CombatPoses.punch(player.getId());
	}

	private static Arm arm(float[][] ticks, float scale, float index) {
		float i = Mth.clamp(index, 0f, ticks.length - 1);
		int a = Mth.floor(i), b = Math.min(a + 1, ticks.length - 1);
		float t = i - a;
		float[] p = new float[9];
		for (int k = 0; k < 9; k++) p[k] = Mth.lerp(t, ticks[a][k], ticks[b][k]);
		return new Arm(new Vector3f(p[0], p[1], p[2]), new Vector3f(p[3], p[4], p[5]), new Vector3f(p[6], p[7], p[8]), scale);
	}
}
