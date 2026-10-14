package com.sparky.lanternring.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.LanternRing;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import org.jspecify.annotations.Nullable;

/**
 * Third person: J's Blender combat poses (packed by tools/combat_poses.py into assets/lanternring/poses/combat.json),
 * for every player, started by the server's CombatFxPayload (CombatFx):
 * <ul>
 * <li>the big flight slam (pass 510, S3): the take whose fall fits the slam's own ticks (H6 4, H5 3, H3 2), its fall
 * stretched to them, then the touchdown, the 0.7 s lock and the stand-up;
 * <li>the flying flurry (pass 509, F2): jab, cross and the spinning backfist, the body turning a full circle;
 * <li>the absorb (pass 503, R4): braced while the shot is held (its small shake looping), and the lunge as it goes;
 * <li>the construct hammer (pass 503, R2): only the ring arm comes up to aim while the hammer forms and swings;
 * <li>the primed slams (pass 518, poses/primed_slam.json from tools/primed_slam_poses.py): P1 the ring fist leading
 * the dive from flight, P2 head-down from a super jump, each held in its dive until touchdown, then the landing and
 * the stand; and the ring arm pointing at the crater while you rebuild it.
 * </ul>
 * While one plays, FlightPoses' own flight tilt steps aside (override).
 */
public final class CombatPoses {
	/** A packed take: per tick six parts of {xRot, yRot, zRot, x, y, z px}, the ring glow, the body spin (rad), and the touchdown index. */
	record Take(float[][][] ticks, float[] glow, float[] spin, int td) {
	}

	/** Absorb loop marks: when the shot is caught, the held loop's end, and the release (R4's ticks). */
	private static final int CAUGHT = 16, LOOP_END = 52, BRACE_FROM = 10;
	private static final float OUT = 4f;

	private static @Nullable Take h6, h5, h3, flurry, absorb, hammer;
	/** Pass 518: the primed slams (P1, P2) and their rebuild gestures. */
	private static final Take[] PRIMED = new Take[2], REBUILD = new Take[2];
	/** The rebuild gesture's index where the arm is up, held while you keep rebuilding. */
	private static final int REBUILD_UP = 10, REBUILD_HELD = 6;
	/** Each absorb take's ring glow (R4a, R4b, R4c). */
	private static final float[][] ABSORB_GLOW = new float[3][];
	private static boolean loaded;

	private static final class Track {
		long slamAt = -1, landAt = -1, flurryAt = -1, catchAt = -1, releaseAt = -1, hammerAt = -1;
		int slamTicks = 3;
		/** The primed slam: when primed, when it touched down, and which (0 P1, 1 P2); the rebuild gesture's start and last report. */
		long primedAt = -1, primedLand = -1, rebuildAt = -1, rebuildLast = -1;
		int primedTake;
	}

	private static final Int2ObjectMap<Track> TRACKS = new Int2ObjectOpenHashMap<>();

	private CombatPoses() {
	}

	static void load() {
		if (loaded) return;
		loaded = true;
		try (InputStream in = CombatPoses.class.getResourceAsStream("/assets/" + LanternRing.MOD_ID + "/poses/combat.json")) {
			if (in == null) return;
			JsonObject root = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
			JsonObject slam = root.getAsJsonObject("slam");
			h6 = take(slam.getAsJsonObject("H6"));
			h5 = take(slam.getAsJsonObject("H5"));
			h3 = take(slam.getAsJsonObject("H3"));
			flurry = take(root.getAsJsonObject("flurry"));
			JsonObject ab = root.getAsJsonObject("absorb");
			absorb = take(ab);
			if (root.has("hammer")) hammer = take(root.getAsJsonObject("hammer"));
			try (InputStream p = CombatPoses.class.getResourceAsStream("/assets/" + LanternRing.MOD_ID + "/poses/primed_slam.json")) {
				if (p != null) {
					JsonObject primed = JsonParser.parseReader(new InputStreamReader(p, StandardCharsets.UTF_8)).getAsJsonObject();
					for (int i = 0; i < 2; i++) {
						PRIMED[i] = take(primed.getAsJsonObject("P" + (i + 1)));
						REBUILD[i] = take(primed.getAsJsonObject("P" + (i + 1) + "_rebuild"));
					}
				}
			}
			String[] names = {"R4a", "R4b", "R4c"};
			for (int i = 0; i < 3; i++) {
				JsonArray g = ab.getAsJsonObject("glow").getAsJsonArray(names[i]);
				ABSORB_GLOW[i] = new float[g.size()];
				for (int k = 0; k < g.size(); k++) ABSORB_GLOW[i][k] = g.get(k).getAsFloat();
			}
		} catch (Exception e) {
			LanternRing.LOGGER.warn("Couldn't read the combat poses", e);
		}
	}

	private static Take take(JsonObject o) {
		JsonArray ticks = o.getAsJsonArray("ticks");
		float[][][] poses = new float[ticks.size()][6][6];
		float[] glow = new float[ticks.size()], spin = new float[ticks.size()];
		for (int i = 0; i < poses.length; i++) {
			JsonObject t = ticks.get(i).getAsJsonObject();
			if (t.has("g")) glow[i] = t.get("g").getAsFloat();
			if (t.has("s")) spin[i] = t.get("s").getAsFloat();
			JsonArray parts = t.getAsJsonArray("p");
			for (int p = 0; p < 6; p++) {
				JsonArray part = parts.get(p).getAsJsonArray();
				for (int k = 0; k < 6; k++) poses[i][p][k] = part.get(k).getAsFloat();
			}
		}
		return new Take(poses, glow, spin, o.has("td") ? o.get("td").getAsInt() : 0);
	}

	private static @Nullable Track track(int id) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return null;
		load();
		return TRACKS.computeIfAbsent(id, k -> new Track());
	}

	private static long now() {
		Minecraft mc = Minecraft.getInstance();
		return mc.level == null ? 0 : mc.level.getGameTime();
	}

	/** The slam fired: ticks left to the ground. */
	static void slam(int id, int ticks) {
		Track t = track(id);
		if (t == null) return;
		t.slamAt = now();
		t.landAt = -1;
		t.slamTicks = Math.max(1, ticks);
	}

	static void slamLand(int id) {
		Track t = track(id);
		if (t == null) return;
		if (t.slamAt < 0) {
			t.slamAt = now() - t.slamTicks;
			t.slamTicks = 3;
		}
		t.landAt = now();
	}

	/** Primed for a slam (0 P1 from flight, 1 P2 from a super jump): the locked dive, held until touchdown. */
	static void primeDive(int id, int take) {
		Track t = track(id);
		if (t == null || t.primedAt >= 0 && t.primedLand < 0 && t.primedTake == take) return;
		t.primedAt = now();
		t.primedLand = -1;
		t.primedTake = take;
		t.slamAt = t.landAt = -1;
	}

	/** The local primed dive was let go before it fired. */
	static void primeCancel(int id) {
		Track t = TRACKS.get(id);
		if (t != null && t.primedLand < 0) t.primedAt = -1;
	}

	/** The primed slam touched down. */
	static void primedLand(int id, int take) {
		Track t = track(id);
		if (t == null) return;
		Take p = PRIMED[take];
		if (t.primedAt < 0 || t.primedTake != take) {
			t.primedTake = take;
			t.primedAt = now() - (p == null ? 0 : p.td());
		}
		t.primedLand = now();
		t.slamAt = t.landAt = -1;
	}

	/** Rebuilding the crater: the ring arm comes up to point at it and stays while you keep at it. */
	static void rebuild(int id) {
		Track t = track(id);
		if (t == null) return;
		long now = now();
		Take r = REBUILD[t.primedTake];
		if (t.rebuildAt < 0 || r == null || now - t.rebuildLast > REBUILD_HELD + r.ticks().length) t.rebuildAt = now;
		t.rebuildLast = now;
	}

	static void flurry(int id) {
		Track t = track(id);
		if (t != null) t.flurryAt = now();
	}

	/** The construct hammer was called up {@code since} ticks ago. */
	static void hammer(int id, int since) {
		Track t = track(id);
		if (t != null) t.hammerAt = now() - since;
	}

	static void absorbCatch(int id) {
		Track t = track(id);
		if (t == null) return;
		t.catchAt = now();
		t.releaseAt = -1;
	}

	static void absorbRelease(int id) {
		Track t = track(id);
		if (t == null) return;
		if (t.catchAt < 0) t.catchAt = now() - CAUGHT;
		t.releaseAt = now();
	}

	static void absorbEnd(int id) {
		Track t = TRACKS.get(id);
		if (t != null) t.catchAt = t.releaseAt = -1;
	}

	/** The absorb take's ring glow for this player now (0 when none plays), for R4c's burning ring. */
	static float absorbGlow(int id, int take) {
		Track t = TRACKS.get(id);
		float[] g = take >= 0 && take < 3 ? ABSORB_GLOW[take] : null;
		if (t == null || g == null || t.catchAt < 0) return 0f;
		return g[Math.min(g.length - 1, (int) absorbIndex(t, now()))];
	}

	static void tick(Minecraft mc) {
		if (mc.level == null) {
			TRACKS.clear();
			return;
		}
		long now = mc.level.getGameTime();
		TRACKS.values().removeIf(t -> {
			if (t.slamAt >= 0 && now - t.slamAt > 120) t.slamAt = t.landAt = -1;
			if (t.flurryAt >= 0 && now - t.flurryAt > 60) t.flurryAt = -1;
			if (t.releaseAt >= 0 && now - t.releaseAt > 40) t.catchAt = t.releaseAt = -1;
			if (t.hammerAt >= 0 && now - t.hammerAt > 80) t.hammerAt = -1;
			if (t.primedAt >= 0 && (t.primedLand < 0 ? now - t.primedAt > 400 : now - t.primedLand > 80)) t.primedAt = t.primedLand = -1;
			if (t.rebuildAt >= 0 && now - t.rebuildLast > 60) t.rebuildAt = t.rebuildLast = -1;
			return t.slamAt < 0 && t.flurryAt < 0 && t.catchAt < 0 && t.hammerAt < 0 && t.primedAt < 0 && t.rebuildAt < 0;
		});
	}

	private static @Nullable Take slamTake(Track t) {
		return t.slamTicks >= 4 ? h6 : t.slamTicks == 3 ? h5 : h3;
	}

	/** The slam's index into its take: the fall stretched to the slam's own ticks, then on from touchdown. */
	private static float slamIndex(Track t, Take take, float now) {
		float age = now - t.slamAt;
		if (t.landAt < 0) return Math.min(take.td(), age * take.td() / t.slamTicks);
		return take.td() + now - t.landAt;
	}

	private static float slamWeight(Track t, float now) {
		Take take = slamTake(t);
		if (t.slamAt < 0 || take == null) return 0f;
		float i = slamIndex(t, take, now);
		return SuperJumpPoses.smooth((now - t.slamAt) + 0.5f) * (1f - SuperJumpPoses.smooth((i - (take.ticks().length - 1)) / OUT));
	}

	/** The primed slam's index: the dive played up to the tick before touchdown and held there, then on from touchdown. */
	private static float primedIndex(Track t, Take take, float now) {
		if (t.primedLand < 0) return Math.min(now - t.primedAt, take.td() - 1);
		return take.td() + now - t.primedLand;
	}

	private static float primedWeight(Track t, float now) {
		Take take = PRIMED[t.primedTake];
		if (t.primedAt < 0 || take == null) return 0f;
		float i = primedIndex(t, take, now);
		return SuperJumpPoses.smooth((now - t.primedAt) / 2f + 0.25f) * (1f - SuperJumpPoses.smooth((i - (take.ticks().length - 1)) / OUT));
	}

	/** The rebuild gesture's index: up, held while you keep rebuilding, then down. */
	private static float rebuildIndex(Track t, float now) {
		float age = now - t.rebuildAt;
		if (age < REBUILD_UP) return age;
		float off = now - t.rebuildLast - REBUILD_HELD;
		return off <= 0 ? REBUILD_UP : REBUILD_UP + off;
	}

	private static float rebuildWeight(Track t, float now) {
		Take take = REBUILD[t.primedTake];
		if (t.rebuildAt < 0 || take == null) return 0f;
		float i = rebuildIndex(t, now);
		return SuperJumpPoses.smooth((now - t.rebuildAt) / 3f) * (1f - SuperJumpPoses.smooth((i - (take.ticks().length - 1)) / OUT));
	}

	/** 0..1: how far this player is in a slam's dive or its landing, primed or not (first person: the ring fist leads it). */
	public static float slamFist(int id, float partial) {
		Track t = TRACKS.get(id);
		Minecraft mc = Minecraft.getInstance();
		if (t == null || mc.level == null) return 0f;
		float now = mc.level.getGameTime() + partial;
		float slam = slamWeight(t, now);
		Take take = PRIMED[t.primedTake];
		if (take == null || t.primedAt < 0) return slam;
		// Through the lock (14 ticks after touchdown) the fist stays down in the crater.
		float w = SuperJumpPoses.smooth((now - t.primedAt) / 2f + 0.25f);
		if (t.primedLand >= 0) w *= 1f - SuperJumpPoses.smooth((now - t.primedLand - 14) / OUT);
		return Math.max(slam, w);
	}

	/** 0..1: how far the local player's ring arm is up rebuilding their crater (first person). */
	public static float rebuilding(int id, float partial) {
		Track t = TRACKS.get(id);
		Minecraft mc = Minecraft.getInstance();
		if (t == null || mc.level == null) return 0f;
		return rebuildWeight(t, mc.level.getGameTime() + partial);
	}

	private static float flurryWeight(Track t, float now) {
		if (t.flurryAt < 0 || flurry == null) return 0f;
		float age = now - t.flurryAt;
		return SuperJumpPoses.smooth(age + 0.5f) * (1f - SuperJumpPoses.smooth((age - (flurry.ticks().length - 1)) / 6f));
	}

	private static float hammerWeight(Track t, float now) {
		if (t.hammerAt < 0 || hammer == null) return 0f;
		float age = now - t.hammerAt;
		return SuperJumpPoses.smooth(age / 3f) * (1f - SuperJumpPoses.smooth((age - (hammer.ticks().length - 1)) / OUT));
	}

	/** Index into R4: the brace to the catch, the held loop while held, then the release. */
	private static float absorbIndex(Track t, float now) {
		if (t.releaseAt >= 0) return LOOP_END + now - t.releaseAt;
		float age = now - t.catchAt;
		if (age < CAUGHT - BRACE_FROM) return BRACE_FROM + age;
		return CAUGHT + (age - (CAUGHT - BRACE_FROM)) % (LOOP_END - CAUGHT);
	}

	private static float absorbWeight(Track t, float now) {
		if (t.catchAt < 0 || absorb == null) return 0f;
		float i = absorbIndex(t, now);
		return SuperJumpPoses.smooth((now - t.catchAt) / 3f) * (1f - SuperJumpPoses.smooth((i - (absorb.ticks().length - 1)) / OUT));
	}

	/** 0..1: how far a combat pose holds this player, so FlightPoses' flight pose steps aside for it. */
	public static float override(int id, float partial) {
		Track t = TRACKS.get(id);
		Minecraft mc = Minecraft.getInstance();
		if (t == null || mc.level == null) return 0f;
		float now = mc.level.getGameTime() + partial;
		return Math.max(Math.max(Math.max(slamWeight(t, now), hammerWeight(t, now)), Math.max(flurryWeight(t, now), absorbWeight(t, now))),
				Math.max(primedWeight(t, now), rebuildWeight(t, now)));
	}

	public static void pose(PlayerModel model, AvatarRenderState state) {
		Minecraft mc = Minecraft.getInstance();
		Track t = TRACKS.get(state.id);
		if (t == null || mc.level == null || !(mc.level.getEntity(state.id) instanceof Player player)) return;
		boolean right = ringRight(state, player);
		float now = mc.level.getGameTime() + mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
		boolean posed = false;
		float w = slamWeight(t, now);
		Take slam = slamTake(t);
		if (w > 0f && slam != null) {
			SuperJumpPoses.apply(model, right, at(slam, slamIndex(t, slam, now)), w);
			posed = true;
		}
		w = flurryWeight(t, now);
		if (w > 0f && flurry != null) {
			SuperJumpPoses.apply(model, right, at(flurry, now - t.flurryAt), w);
			posed = true;
		}
		w = absorbWeight(t, now);
		if (w > 0f && absorb != null) {
			SuperJumpPoses.apply(model, right, at(absorb, absorbIndex(t, now)), w);
			posed = true;
		}
		w = hammerWeight(t, now);
		if (w > 0f && hammer != null) {
			SuperJumpPoses.apply(model, right, at(hammer, now - t.hammerAt), w);
			posed = true;
		}
		Take primed = PRIMED[t.primedTake];
		w = primedWeight(t, now);
		if (w > 0f && primed != null) {
			SuperJumpPoses.apply(model, right, at(primed, primedIndex(t, primed, now)), w);
			posed = true;
		}
		Take rebuild = REBUILD[t.primedTake];
		w = rebuildWeight(t, now);
		if (w > 0f && rebuild != null) {
			SuperJumpPoses.apply(model, right, at(rebuild, rebuildIndex(t, now)), w);
			posed = true;
		}
		if (posed) model.head.xRot = Math.max(model.head.xRot, model.body.xRot - MovePoses.NECK);
	}

	/** The spinning backfist turns the whole body a full circle about its own axis. */
	public static void rotate(AvatarRenderState state, PoseStack poseStack) {
		Minecraft mc = Minecraft.getInstance();
		Track t = TRACKS.get(state.id);
		if (t == null || flurry == null || mc.level == null) return;
		float now = mc.level.getGameTime() + mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
		float w = flurryWeight(t, now);
		if (w <= 0f) return;
		float i = Mth.clamp(now - t.flurryAt, 0f, flurry.spin().length - 1);
		int a = Mth.floor(i), b = Math.min(a + 1, flurry.spin().length - 1);
		float spin = Mth.lerp(i - a, flurry.spin()[a], flurry.spin()[b]);
		if (spin == 0f) return;
		float side = state.mainArm == HumanoidArm.LEFT ? -1f : 1f;
		poseStack.rotateDegrees(Axis.YP, side * spin * Mth.RAD_TO_DEG * w);
	}

	private static float[][] at(Take take, float index) {
		float[][][] ticks = take.ticks();
		float i = Mth.clamp(index, 0f, ticks.length - 1);
		int a = Mth.floor(i);
		int b = Math.min(a + 1, ticks.length - 1);
		return SuperJumpPoses.mix(ticks[a], ticks[b], i - a);
	}

	private static boolean ringRight(AvatarRenderState state, Player player) {
		if (FlightPoses.isRing(state.rightHandItemStack)) return true;
		if (FlightPoses.isRing(state.leftHandItemStack)) return false;
		return player.getMainArm() == HumanoidArm.RIGHT;
	}
}
