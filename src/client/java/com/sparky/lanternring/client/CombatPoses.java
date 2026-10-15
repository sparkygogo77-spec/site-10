package com.sparky.lanternring.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
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
 * the stand; and the ring arm pointing at the crater while you rebuild it;
 * <li>pass 502 round 4 (poses/combat4.json from tools/combat_poses4.py), in the viewer's Ring Lab pick: the ring-hand
 * punch (P1b step-in jab with its 0.45-block step, or P1c hook), the Blast (P2b: braced while it charges, the kick
 * on the shot with the free hand following the recoil 25%) and the Wall (P5a: only the ring arm sweeps up while it
 * is drawn, the free arm relaxed). Head left to the look; the legs only when standing, the arms only in flight;
 * <li>the dash strike (pass 505, R3a-3): the lean, the flying ring fist through the dash, the punch as it ends and
 * the arms dropping to the sides (DashGhosts draws its afterimages).
 * </ul>
 * While one plays, FlightPoses' own flight tilt steps aside (override).
 */
public final class CombatPoses {
	/** A packed take: per tick six parts of {xRot, yRot, zRot, x, y, z px}, the ring glow, the body spin (rad), and the touchdown index. */
	record Take(float[][][] ticks, float[] glow, float[] spin, float[] fwd, int td) {
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

	/** Pass 502: the punches (P1b, P1c), each played from FROM (the guard, a few ticks before the hit) to TO. */
	private static final Take[] PUNCHES = new Take[2];
	private static final int[] PUNCH_FROM = {5, 6}, PUNCH_HIT = {8, 11}, PUNCH_TO = {20, 21};
	/** P2b: braced while charging (to SET), the kick from KICK (the shot) to the end of its loop. */
	private static @Nullable Take blastTake;
	private static final int BLAST_SET = 22, BLAST_KICK = 23, BLAST_TO = 40;
	/** How long the charge's brace outlasts letting go while the shot's effect is on its way (ticks). */
	private static final int BLAST_GRACE = 4;
	/** P5a: from low (FROM), the ring arm up by UP, held at HOLD while drawn, down from DOWN to TO. */
	private static @Nullable Take wallTake;
	private static final int WALL_FROM = 12, WALL_UP = 20, WALL_HOLD = 24, WALL_DOWN = 32, WALL_TO = 40;
	/** Pass 505 R3a-3: the dash runs from DASH_FROM over DASH_SPAN Blender ticks to the hit, the arms down by DASH_TO. */
	private static @Nullable Take dashTake;
	private static final int DASH_FROM = 10, DASH_HIT = 14, DASH_TO = 30;
	/** Parts the round 4 poses move (SuperJumpPoses.applyParts): not the head (it keeps the look). */
	private static final int ARMS = 0b001100, UPPER = 0b001110, NO_HEAD = 0b111110, ALL = 0b111111;

	private static final class Track {
		long slamAt = -1, landAt = -1, flurryAt = -1, catchAt = -1, releaseAt = -1, hammerAt = -1;
		int slamTicks = 3;
		/** The primed slam: when primed, when it touched down, and which (0 P1, 1 P2); the rebuild gesture's start and last report. */
		long primedAt = -1, primedLand = -1, rebuildAt = -1, rebuildLast = -1;
		int primedTake;
		/** Pass 502: the punch (and which, 0 P1b, 1 P1c), the Blast's charge (start, last tick held) and shot, the Wall (start, release). */
		long punchAt = -1, chargeAt = -1, chargeLast = -1, blastAt = -1, wallAt = -1, wallRelease = -1;
		int punchTake;
		/** Pass 505: the dash strike's start, and its lean and dash in ticks. */
		long dashAt = -1;
		int dashWindup = 2, dashTime = 3;
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
			try (InputStream p = CombatPoses.class.getResourceAsStream("/assets/" + LanternRing.MOD_ID + "/poses/combat4.json")) {
				if (p != null) {
					JsonObject round4 = JsonParser.parseReader(new InputStreamReader(p, StandardCharsets.UTF_8)).getAsJsonObject();
					PUNCHES[0] = take(round4.getAsJsonObject("P1B"));
					PUNCHES[1] = take(round4.getAsJsonObject("P1C"));
					blastTake = take(round4.getAsJsonObject("P2B"));
					wallTake = take(round4.getAsJsonObject("P5A"));
					dashTake = take(round4.getAsJsonObject("R3A3"));
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
		float[] glow = new float[ticks.size()], spin = new float[ticks.size()], fwd = new float[ticks.size()];
		for (int i = 0; i < poses.length; i++) {
			JsonObject t = ticks.get(i).getAsJsonObject();
			if (t.has("g")) glow[i] = t.get("g").getAsFloat();
			if (t.has("s")) spin[i] = t.get("s").getAsFloat();
			if (t.has("f")) fwd[i] = t.get("f").getAsFloat();
			JsonArray parts = t.getAsJsonArray("p");
			for (int p = 0; p < 6; p++) {
				JsonArray part = parts.get(p).getAsJsonArray();
				for (int k = 0; k < 6; k++) poses[i][p][k] = part.get(k).getAsFloat();
			}
		}
		return new Take(poses, glow, spin, fwd, o.has("td") ? o.get("td").getAsInt() : 0);
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

	/** Pass 502: this player threw a punch with the ring hand (the viewer's Ring Lab pick, or nothing for vanilla's swing). */
	static void punch(int id) {
		LabSettings.Punch pick = LabSettings.get().punch;
		if (pick == LabSettings.Punch.VANILLA) return;
		Track t = track(id);
		long now = now();
		// Not over a Blast's kick or a dash strike.
		if (t == null || t.blastAt >= 0 && now - t.blastAt < BLAST_TO - BLAST_KICK || t.dashAt >= 0 && now - t.dashAt < DASH_TO) return;
		t.punchAt = now;
		t.punchTake = pick == LabSettings.Punch.P1C ? 1 : 0;
	}

	/** Pass 502: this player's Blast left the ring: P2b's kick (and no punch over it). */
	static void blast(int id) {
		if (LabSettings.get().blastPose != LabSettings.BlastPose.P2B) return;
		Track t = track(id);
		if (t == null) return;
		t.blastAt = now();
		t.punchAt = -1;
	}

	/** Pass 505: this player's dash strike started (lean, then dash, in ticks). */
	static void dash(int id, int windup, int time) {
		Track t = track(id);
		if (t == null) return;
		t.dashAt = now();
		t.dashWindup = Math.max(0, windup);
		t.dashTime = Math.max(1, time);
		t.punchAt = -1;
	}

	/** The dash strike's index into R3a-3 at age (ticks since the press): the lean to DASH_FROM, the dash stretched to the hit, then on. */
	static float dashIndex(int windup, int time, float age) {
		if (age < windup) return DASH_FROM - windup + age;
		if (age < windup + time) return DASH_FROM + (age - windup) * (DASH_HIT - DASH_FROM) / (float) time;
		return DASH_HIT + age - windup - time;
	}

	/** R3a-3's pose at index (DashGhosts' afterimages), or null before the poses load. */
	static float @Nullable [][] dashPose(float index) {
		load();
		return dashTake == null ? null : at(dashTake, index);
	}

	/** Pass 502: the held ring's power this tick, for every player in view: Blast charging and Wall being drawn. */
	private static void held(Minecraft mc, long now) {
		LabSettings s = LabSettings.get();
		boolean blasts = s.blastPose == LabSettings.BlastPose.P2B, walls = s.wallPose == LabSettings.WallPose.P5A;
		if (!blasts && !walls) return;
		for (Player p : mc.level.players()) {
			ItemStack ring = com.sparky.lanternring.RingSlot.ring(p);
			boolean using = p.isUsingItem() && ring.getItem() instanceof com.sparky.lanternring.item.PowerRingItem;
			com.sparky.lanternring.RingMode mode = using ? com.sparky.lanternring.item.PowerRingItem.getMode(ring) : null;
			Track t = TRACKS.get(p.getId());
			if (blasts && mode == com.sparky.lanternring.RingMode.BLAST) {
				if (t == null) t = track(p.getId());
				if (t != null) {
					if (t.chargeAt < 0 || now - t.chargeLast > BLAST_GRACE) {
						// A new charge: the last shot's kick gives way to it.
						t.chargeAt = now;
						t.blastAt = -1;
					}
					t.chargeLast = now;
				}
			}
			if (walls && mode == com.sparky.lanternring.RingMode.WALL) {
				if (t == null) t = track(p.getId());
				if (t != null && (t.wallAt < 0 || t.wallRelease >= 0)) {
					t.wallAt = now;
					t.wallRelease = -1;
				}
			} else if (t != null && t.wallAt >= 0 && t.wallRelease < 0) {
				// Let go: the sweep always reaches the top before the arm comes down.
				t.wallRelease = Math.max(now, t.wallAt + WALL_UP - WALL_FROM + 2);
			}
		}
	}

	/** At the punch's hit: the ring flashes and 7 construct pixels fly off the fist (pass 502). */
	private static void punchHit(Minecraft mc, int id) {
		if (!(mc.level.getEntity(id) instanceof Player p)) return;
		Corps before = CorpsTint.enter(Corps.of(com.sparky.lanternring.RingSlot.ring(p)));
		try {
			RingEmit.flare(p);
			Vec3 at = RingEmit.ringNow(p, 1f);
			Vec3 look = p.getLookAngle();
			RandomSource r = mc.level.getRandom();
			for (int i = 0; i < LabFx.count(7); i++) {
				ConstructParticle q = LabFx.spawn(ModParticles.MOTE, at, look.scale(0.15).add(LabFx.jitter(r, 0.12)), 0.45f);
				if (q != null) q.lasting(5 + r.nextInt(4));
			}
		} finally {
			CorpsTint.restore(before);
		}
	}

	static void tick(Minecraft mc) {
		if (mc.level == null) {
			TRACKS.clear();
			return;
		}
		long now = mc.level.getGameTime();
		load();
		held(mc, now);
		for (Int2ObjectMap.Entry<Track> e : TRACKS.int2ObjectEntrySet()) {
			Track t = e.getValue();
			if (t.punchAt >= 0 && now - t.punchAt == PUNCH_HIT[t.punchTake] - PUNCH_FROM[t.punchTake]) punchHit(mc, e.getIntKey());
		}
		TRACKS.values().removeIf(t -> {
			if (t.punchAt >= 0 && now - t.punchAt > 40) t.punchAt = -1;
			if (t.chargeAt >= 0 && now - t.chargeLast > BLAST_GRACE + OUT + 2) t.chargeAt = t.chargeLast = -1;
			if (t.blastAt >= 0 && now - t.blastAt > 40) t.blastAt = -1;
			if (t.wallRelease >= 0 && now - t.wallRelease > WALL_TO - WALL_DOWN + OUT + 2) t.wallAt = t.wallRelease = -1;
			if (t.dashAt >= 0 && now - t.dashAt > 60) t.dashAt = -1;
			if (t.slamAt >= 0 && now - t.slamAt > 120) t.slamAt = t.landAt = -1;
			if (t.flurryAt >= 0 && now - t.flurryAt > 60) t.flurryAt = -1;
			if (t.releaseAt >= 0 && now - t.releaseAt > 40) t.catchAt = t.releaseAt = -1;
			if (t.hammerAt >= 0 && now - t.hammerAt > 80) t.hammerAt = -1;
			if (t.primedAt >= 0 && (t.primedLand < 0 ? now - t.primedAt > 400 : now - t.primedLand > 80)) t.primedAt = t.primedLand = -1;
			if (t.rebuildAt >= 0 && now - t.rebuildLast > 60) t.rebuildAt = t.rebuildLast = -1;
			return t.slamAt < 0 && t.flurryAt < 0 && t.catchAt < 0 && t.hammerAt < 0 && t.primedAt < 0 && t.rebuildAt < 0
					&& t.punchAt < 0 && t.chargeAt < 0 && t.blastAt < 0 && t.wallAt < 0 && t.dashAt < 0;
		});
	}

	private static float punchIndex(Track t, float now) {
		return PUNCH_FROM[t.punchTake] + now - t.punchAt;
	}

	private static float punchWeight(Track t, float now) {
		if (t.punchAt < 0 || PUNCHES[t.punchTake] == null) return 0f;
		float i = punchIndex(t, now);
		return SuperJumpPoses.smooth((now - t.punchAt) / 2f + 0.25f) * (1f - SuperJumpPoses.smooth((i - PUNCH_TO[t.punchTake]) / OUT));
	}

	/** P2b's index: braced from low while it charges (held at the set), or the kick from the shot on. */
	private static float blastIndex(Track t, float now) {
		if (t.blastAt >= 0) return BLAST_KICK + now - t.blastAt;
		return Math.min(now - t.chargeAt, BLAST_SET);
	}

	private static float blastWeight(Track t, float now) {
		if (blastTake == null) return 0f;
		if (t.blastAt >= 0) {
			float i = blastIndex(t, now);
			float in = t.chargeAt >= 0 ? 1f : SuperJumpPoses.smooth((now - t.blastAt) / 1.5f + 0.3f);
			return in * (1f - SuperJumpPoses.smooth((i - BLAST_TO) / OUT));
		}
		if (t.chargeAt < 0) return 0f;
		return SuperJumpPoses.smooth((now - t.chargeAt) / 3f) * (1f - SuperJumpPoses.smooth((now - t.chargeLast - BLAST_GRACE) / OUT));
	}

	/** P5a's index: low to up, held while drawn, then down. */
	private static float wallIndex(Track t, float now) {
		if (t.wallRelease >= 0 && now >= t.wallRelease) return WALL_DOWN + now - t.wallRelease;
		return Math.min(WALL_FROM + now - t.wallAt, WALL_HOLD);
	}

	private static float wallWeight(Track t, float now) {
		if (t.wallAt < 0 || wallTake == null) return 0f;
		float i = wallIndex(t, now);
		return SuperJumpPoses.smooth((now - t.wallAt) / 2f + 0.25f) * (1f - SuperJumpPoses.smooth((i - WALL_TO) / OUT));
	}

	private static float dashWeight(Track t, float now) {
		if (t.dashAt < 0 || dashTake == null) return 0f;
		float i = dashIndex(t.dashWindup, t.dashTime, now - t.dashAt);
		return SuperJumpPoses.smooth((now - t.dashAt) / 1.5f + 0.3f) * (1f - SuperJumpPoses.smooth((i - DASH_TO) / OUT));
	}

	/** 0..1: how far the local player's ring fist leads a dash strike, from the lean to just after the hit (first person). */
	public static float dashFist(int id, float partial) {
		Track t = TRACKS.get(id);
		Minecraft mc = Minecraft.getInstance();
		if (t == null || t.dashAt < 0 || mc.level == null) return 0f;
		float age = mc.level.getGameTime() + partial - t.dashAt;
		float hit = t.dashWindup + t.dashTime;
		return SuperJumpPoses.smooth(age / Math.max(1f, t.dashWindup) + 0.3f) * (1f - SuperJumpPoses.smooth((age - hit - 2) / 5f));
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

	/**
	 * First person (FirstPersonCombat): {clip, index, weight} of the move this player's arms are in, clip 0 P1b, 1 P1c
	 * (the punch's own index into combat4.json's take) or 2 the flying flurry (from its jab, as combat.json), or null.
	 */
	public static float @Nullable [] firstPerson(int id, float partial) {
		Track t = TRACKS.get(id);
		Minecraft mc = Minecraft.getInstance();
		if (t == null || mc.level == null) return null;
		float now = mc.level.getGameTime() + partial;
		float w = flurryWeight(t, now);
		if (w > 0f) return new float[] {2f, now - t.flurryAt, w};
		w = punchWeight(t, now);
		if (w > 0f) return new float[] {t.punchTake, punchIndex(t, now), w};
		return null;
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
				Math.max(Math.max(primedWeight(t, now), rebuildWeight(t, now)), dashWeight(t, now)));
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
		// Pass 502 round 4: the head keeps the look; the legs only standing still, and only the arms in flight.
		boolean flying = player.getAbilities().flying;
		int mask = flying ? ARMS : state.walkAnimationSpeed > 0.15f ? UPPER : NO_HEAD;
		Take punch = PUNCHES[t.punchTake];
		w = flying ? 0f : punchWeight(t, now);
		if (w > 0f && punch != null) SuperJumpPoses.applyParts(model, right, at(punch, punchIndex(t, now)), w, mask);
		w = blastWeight(t, now);
		if (w > 0f && blastTake != null) SuperJumpPoses.applyParts(model, right, at(blastTake, blastIndex(t, now)), w, mask);
		w = wallWeight(t, now);
		if (w > 0f && wallTake != null) SuperJumpPoses.applyParts(model, right, at(wallTake, wallIndex(t, now)), w, mask);
		w = dashWeight(t, now);
		if (w > 0f && dashTake != null) {
			SuperJumpPoses.applyParts(model, right, at(dashTake, dashIndex(t.dashWindup, t.dashTime, now - t.dashAt)), w, ALL);
			posed = true;
		}
		if (posed) model.head.xRot = Math.max(model.head.xRot, model.body.xRot - MovePoses.NECK);
	}

	/** The spinning backfist turns the whole body a full circle about its own axis. */
	public static void rotate(AvatarRenderState state, PoseStack poseStack) {
		Minecraft mc = Minecraft.getInstance();
		Track t = TRACKS.get(state.id);
		if (t == null || mc.level == null) return;
		float now = mc.level.getGameTime() + mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
		// P1b's step in: the body goes 0.45 blocks forward with the jab and back (forward is -z here).
		Take punch = PUNCHES[t.punchTake];
		float pw = punchWeight(t, now);
		if (pw > 0f && punch != null) {
			float i = Mth.clamp(punchIndex(t, now), 0f, punch.fwd().length - 1);
			int a = Mth.floor(i), b = Math.min(a + 1, punch.fwd().length - 1);
			float step = Mth.lerp(i - a, punch.fwd()[a], punch.fwd()[b]) * pw;
			if (step != 0f) poseStack.translate(0f, 0f, -step);
		}
		if (flurry == null) return;
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
