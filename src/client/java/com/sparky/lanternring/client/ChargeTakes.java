package com.sparky.lanternring.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.sparky.lanternring.LanternCharge;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import net.minecraft.util.Mth;
import org.joml.Matrix3f;
import org.joml.Vector3f;

/**
 * The charge takes J picked in the lead Blender chat (docs/handoff/2026-10-14-lantern-charge, packed by
 * tools/charge_takes_json.py into poses/charge_takes.json):
 * <ul>
 * <li>L1c, the lean: the lantern stands on a block in front of you, you take a half step in and drive the ring
 * fist into the emblem port, twice, tipping the lantern away about its far bottom edge.</li>
 * <li>K3c, kneel and pick up: one knee down, the ring hand takes the handle, the lantern drags on the floor like a
 * kickstand until it clears it, then swings from the handle as you lift it to the chest and stand.</li>
 * </ul>
 *
 * <p>Every tick (20 a second) of a take is the solved pose of eight parts (the legs have knees: thigh and shin),
 * each a rotation in radians and an offset in model pixels from the vanilla pivot, for a right-handed player.
 * Positions here are in "rig" pixels: Minecraft model space, y down, -z ahead, the feet at y = 24.
 */
public final class ChargeTakes {
	public enum Take {
		L1C("L1c"), K3C("K3c");

		final String key;

		Take(String key) {
			this.key = key;
		}
	}

	public static final int HEAD = 0, BODY = 1, RARM = 2, LARM = 3, RLEG = 4, LLEG = 5, RSHIN = 6, LSHIN = 7;
	/** The vanilla pivots the offsets are measured from (the shins pivot at the knee, 6 px below the hip). */
	static final float[][] PIVOT = {{0, 0, 0}, {0, 0, 0}, {-5, 2, 0}, {5, 2, 0}, {-1.9f, 12, 0}, {1.9f, 12, 0}, {-1.9f, 18, 0}, {1.9f, 18, 0}};
	/** The ground, in rig pixels. */
	static final float GROUND = 24f;
	/** The tip of the ring arm (the fist), in the arm's own space. */
	private static final Vector3f FIST = new Vector3f(-1f, 10f, 0f);

	// The scene, from the Blender source (213_kneel_lean_round4.update.py), in rig pixels.
	/** The lantern's height with its handle, placed. */
	static final float LANTERN_HEIGHT = 16f;
	/** The grip on the handle, above the lantern's base. */
	static final float GRIP = LANTERN_HEIGHT - 0.5f;
	/** L1c: the block stands one block tall, its centre this far ahead of your feet. */
	static final float BLOCK_AHEAD = 15f, BLOCK_HEIGHT = 16f;
	/** L1c: the port's centre above the block (52% of the Dark Lantern's body) and its front face's distance ahead. */
	static final float PORT_UP = 21f * LANTERN_HEIGHT / 28.5f * 0.52f, PORT_AHEAD = BLOCK_AHEAD - 11f * LANTERN_HEIGHT / 28.5f / 2f;

	// L1c's keys (Blender ticks): idle 0, lean 9, push 26, lean 42, push 58, lean 70, idle 84; the ring charges 9 to 70.
	static final float L1C_CHARGE_FROM = 9f, L1C_CHARGE_TO = 70f, END = 84f;
	// K3c: kneel by 10, the hand on the handle by 30 (carry_from_tick), raised to the chest by 44, held to 52, standing by 62.
	static final float K3C_KNEEL = 10f, K3C_GRAB = 30f, K3C_RAISED = 44f, K3C_HOLD = 52f;
	/** K3c: ticks the lift from the floor to the chest takes, in real time, once the hand has the handle. */
	static final float K3C_LIFT_TICKS = 20f;
	/** Ticks at the end of the afterglow over which the body eases back out of the take. */
	static final float BLEND_OUT = 10f;

	record Data(float[][][] parts, float[] tilt, int carry) {
		int last() {
			return parts.length - 1;
		}
	}

	private static Data l1c, k3c;

	private ChargeTakes() {
	}

	static Data data(Take take) {
		if (l1c == null) load();
		return take == Take.L1C ? l1c : k3c;
	}

	private static void load() {
		try (InputStream in = ChargeTakes.class.getResourceAsStream("/assets/lanternring/poses/charge_takes.json")) {
			JsonObject takes = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonObject("takes");
			l1c = parse(takes.getAsJsonObject(Take.L1C.key));
			k3c = parse(takes.getAsJsonObject(Take.K3C.key));
		} catch (Exception e) {
			throw new IllegalStateException("charge takes", e);
		}
	}

	private static Data parse(JsonObject take) {
		JsonArray ticks = take.getAsJsonArray("parts"), tilts = take.getAsJsonArray("tilt");
		float[][][] parts = new float[ticks.size()][8][6];
		float[] tilt = new float[ticks.size()];
		for (int t = 0; t < ticks.size(); t++) {
			JsonArray row = ticks.get(t).getAsJsonArray();
			for (int p = 0; p < 8; p++) {
				JsonArray v = row.get(p).getAsJsonArray();
				for (int c = 0; c < 6; c++) parts[t][p][c] = v.get(c).getAsFloat();
			}
			tilt[t] = tilts.get(t).getAsFloat();
		}
		int carry = take.get("carry_from_tick").isJsonNull() ? -1 : take.get("carry_from_tick").getAsInt();
		return new Data(parts, tilt, carry);
	}

	/** The pose at Blender tick {@code k}, between whole ticks by a straight blend. */
	static float[][] pose(Data d, float k) {
		k = Mth.clamp(k, 0f, d.last());
		int a = Math.min((int) k, d.last() - 1);
		float f = k - a;
		float[][] out = new float[8][6];
		for (int p = 0; p < 8; p++) {
			for (int c = 0; c < 6; c++) out[p][c] = Mth.lerp(f, d.parts[a][p][c], d.parts[a + 1][p][c]);
		}
		return out;
	}

	/** The lantern's tilt on its block at tick {@code k} (radians, top away from you): the spring's target. */
	static float tilt(Data d, float k) {
		k = Mth.clamp(k, 0f, d.last());
		int a = Math.min((int) k, d.last() - 1);
		return Mth.lerp(k - a, d.tilt[a], d.tilt[a + 1]);
	}

	/** A part's rotation as a matrix: Minecraft's order (z, then y, then x), as in ModelPart and the Blender rig. */
	static Matrix3f rotation(float[] part) {
		return new Matrix3f().rotationZYX(part[2], part[1], part[0]);
	}

	/** Where the part's pivot is, in rig pixels. */
	static Vector3f pivot(float[][] pose, int part) {
		return new Vector3f(PIVOT[part][0] + pose[part][3], PIVOT[part][1] + pose[part][4], PIVOT[part][2] + pose[part][5]);
	}

	/** The ring fist (right hand), in rig pixels. */
	static Vector3f fist(float[][] pose) {
		return rotation(pose[RARM]).transform(new Vector3f(FIST)).add(pivot(pose, RARM));
	}

	// ---- the takes' timelines on the real charge ------------------------------------------------------

	/**
	 * The Blender tick to show {@code t} ticks into the charge (from the right-click), or {@code a} ticks after the
	 * ring filled when {@code t} is past it. The actions play at their own speed; only the charge's long middle is
	 * stretched (L1c's two pushes) or held (K3c's lantern at the chest).
	 */
	static float tick(Take take, float t, float after) {
		int hold = LanternCharge.hold(), seat = hold + LanternCharge.reach(), done = LanternCharge.done();
		if (after >= 0) {
			return take == Take.L1C ? Math.min(END, L1C_CHARGE_TO + after) : Math.min(END, K3C_HOLD + after);
		}
		if (t < 0) return -1f;
		if (take == Take.L1C) {
			if (t < seat) return L1C_CHARGE_FROM * smooth(t / seat);
			return L1C_CHARGE_FROM + (L1C_CHARGE_TO - L1C_CHARGE_FROM) * Mth.clamp((t - seat) / Math.max(1, done - seat), 0f, 1f);
		}
		if (t < hold) return K3C_KNEEL * t / hold;
		if (t < seat) return K3C_KNEEL + (K3C_GRAB - K3C_KNEEL) * (t - hold) / Math.max(1, seat - hold);
		float lift = (t - seat) / K3C_LIFT_TICKS;
		if (lift < 1f) return K3C_GRAB + (K3C_RAISED - K3C_GRAB) * lift;
		float rest = (t - seat - K3C_LIFT_TICKS) / Math.max(1, done - seat - K3C_LIFT_TICKS);
		return K3C_RAISED + (K3C_HOLD - K3C_RAISED) * Mth.clamp(rest, 0f, 1f);
	}

	/** How much of the take is on the body: easing in at the start, out at the end of the afterglow. */
	static float weight(Take take, float t, float after) {
		if (after >= 0) return 1f - smooth((after - (LanternCharge.DEPLETE - BLEND_OUT)) / BLEND_OUT);
		if (t < 0) return 0f;
		// L1c starts with the fist already at the port: ease into it while the clicks are held and a little after.
		return take == Take.L1C ? smooth(t / (LanternCharge.hold() + 10f)) : 1f;
	}

	static float smooth(float x) {
		x = Mth.clamp(x, 0f, 1f);
		return x * x * (3 - 2 * x);
	}

	/** The (x, y, z) angles of R = Rz Ry Rx (JOML is column-major: m[col][row]). */
	static Vector3f euler(Matrix3f r) {
		float y = (float) Math.asin(Mth.clamp(-r.m02, -1f, 1f));
		return new Vector3f((float) Math.atan2(r.m12, r.m22), y, (float) Math.atan2(r.m01, r.m00));
	}

	/**
	 * Turns the ring arm of {@code pose} (rig px, right-handed) so its fist reaches {@code target}, by the smallest turn
	 * of the whole arm about the shoulder. When the target is nearer or further than the arm is long the shoulder gives
	 * a little (up to 2 px along the arm), as a shrug or a reach would.
	 */
	static void aim(float[][] pose, Vector3f target) {
		Vector3f shoulder = pivot(pose, RARM);
		Vector3f from = fist(pose).sub(shoulder);
		Vector3f to = new Vector3f(target).sub(shoulder);
		float len = from.length(), want = to.length();
		if (len < 1e-4f || want < 1e-4f) return;
		Matrix3f turn = new Matrix3f().rotation(new org.joml.Quaternionf().rotationTo(from.normalize(new Vector3f()), to.normalize(new Vector3f())));
		Vector3f e = euler(turn.mul(rotation(pose[RARM])));
		pose[RARM][0] = e.x;
		pose[RARM][1] = e.y;
		pose[RARM][2] = e.z;
		Vector3f slide = to.normalize(new Vector3f()).mul(Mth.clamp(want - len, -2f, 2f));
		pose[RARM][3] += slide.x;
		pose[RARM][4] += slide.y;
		pose[RARM][5] += slide.z;
	}

	// ---- the lantern's own motion -----------------------------------------------------------------------

	/**
	 * L1c: the lantern rocking on its block, a damped spring toward the tilt the data holds it at (Blender's rock():
	 * 2.6 Hz, damping 0.18). It sits on its base, so it can't tip back past upright: it lands with a small bounce.
	 */
	static final class Rock {
		private static final float W = Mth.TWO_PI * 2.6f, ZETA = 0.18f;
		float tilt, tiltO;
		private float speed;

		void reset() {
			tilt = tiltO = speed = 0f;
		}

		void tick(float target) {
			tiltO = tilt;
			int sub = 20;
			float dt = 1f / 20f / sub;
			for (int i = 0; i < sub; i++) {
				float acc = W * W * (target - tilt) - 2f * ZETA * W * speed;
				speed += acc * dt;
				tilt += speed * dt;
				if (tilt < 0f) {
					tilt = 0f;
					speed = -0.35f * speed;
				}
			}
		}

		float at(float partialTick) {
			return Mth.lerp(partialTick, tiltO, tilt);
		}
	}

	/**
	 * K3c: the lantern picked up by its handle (Blender's carry_physics). While the grip is lower than the lantern is
	 * tall, the base stays on the floor and drags or tips under the hand like a kickstand. Once the grip lifts it clear
	 * it swings as a pendulum from the handle, starting from the tilt and spin it already had, lagging the hand.
	 * {@code phi} is (about z, about x) in rig space.
	 */
	static final class Carry {
		private static final float ZETA = 0.12f, G = 9.81f * 16f;
		/** The handle's length (grip to base) and the swing's centre below the grip, in rig px: set by the lantern's size. */
		private float handle = GRIP, centre = GRIP * 0.62f, w0 = (float) Math.sqrt(G / centre);
		final float[] phi = new float[2], phiO = new float[2];
		private final float[] speed = new float[2];
		private boolean airborne;
		private float baseX, baseZ, lastDirX, lastDirZ = -1f;
		private Vector3f grip, gripO, gripOO;

		void reset(Vector3f spot, float gripLength) {
			handle = gripLength;
			// Blender's lantern swings about a point 62% of the way down from the grip (its body's middle).
			centre = handle * 0.62f;
			w0 = (float) Math.sqrt(G / centre);
			phi[0] = phi[1] = phiO[0] = phiO[1] = speed[0] = speed[1] = 0f;
			airborne = false;
			baseX = spot.x;
			baseZ = spot.z;
			lastDirX = 0f;
			lastDirZ = -1f;
			grip = gripO = gripOO = null;
		}

		boolean airborne() {
			return airborne;
		}

		/** One game tick with the hand at {@code hand} (rig px). */
		void tick(Vector3f hand) {
			phiO[0] = phi[0];
			phiO[1] = phi[1];
			gripOO = gripO;
			gripO = grip;
			grip = new Vector3f(hand);
			float h = GROUND - hand.y;
			if (!airborne && h < handle - 0.02f) {
				float dx = baseX - hand.x, dz = baseZ - hand.z;
				float r = (float) Math.sqrt(Math.max(handle * handle - h * h, 0f));
				float n = (float) Math.hypot(dx, dz);
				float ux = n > 1e-6f ? dx / n : lastDirX, uz = n > 1e-6f ? dz / n : lastDirZ;
				lastDirX = ux;
				lastDirZ = uz;
				baseX = hand.x + ux * r;
				baseZ = hand.z + uz * r;
				float nx = (float) Math.asin(Mth.clamp((hand.x - baseX) / handle, -1f, 1f));
				float nz = (float) Math.asin(Mth.clamp((baseZ - hand.z) / handle, -1f, 1f));
				speed[0] = (nx - phi[0]) * 20f;
				speed[1] = (nz - phi[1]) * 20f;
				phi[0] = nx;
				phi[1] = nz;
				return;
			}
			airborne = true;
			// The hand's acceleration drives the swing (it lags behind the motion).
			float ax = 0f, az = 0f;
			if (gripO != null && gripOO != null) {
				ax = (grip.x - 2f * gripO.x + gripOO.x) * 400f;
				az = -(grip.z - 2f * gripO.z + gripOO.z) * 400f;
			}
			int sub = 20;
			float dt = 1f / 20f / sub;
			float[] a = {ax, az};
			for (int i = 0; i < sub; i++) {
				for (int c = 0; c < 2; c++) {
					float al = -(G / centre) * Mth.sin(phi[c]) + a[c] / centre * Mth.cos(phi[c]) - 2f * ZETA * w0 * speed[c];
					speed[c] += al * dt;
					phi[c] += speed[c] * dt;
				}
			}
		}

		float x(float partialTick) {
			return Mth.lerp(partialTick, phiO[0], phi[0]);
		}

		float z(float partialTick) {
			return Mth.lerp(partialTick, phiO[1], phi[1]);
		}
	}
}
