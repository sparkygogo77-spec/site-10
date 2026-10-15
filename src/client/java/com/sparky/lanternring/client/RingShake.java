package com.sparky.lanternring.client;

import com.sparky.lanternring.net.RingFxPayload;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.phys.Vec3;

/**
 * The camera kick when this player fires a shot, like an RPG going off in GTA V: the view snaps up
 * and twists a little in a few hundredths of a second, rattles, then settles in about 0.3 s. It only
 * turns the camera (CameraMixin), so the FOV and where the shot aims never change. Strength comes
 * from the shot (a charged Beam kicks hardest) and the Ring Lab's "Screen shake" row.
 */
public final class RingShake {
	/** How far a shot's start can be from this player's eyes and still count as theirs. */
	private static final double SHOOTER_RANGE = 3.0;
	/** Seconds until a kick is gone. */
	private static final float LIFE = 0.45f;
	/** Seconds from the shot to the top of the kick. */
	private static final float ATTACK = 0.03f;
	/** At strength 1: degrees the view kicks up, rolls and jitters sideways. */
	private static final float PITCH = 2.6f, ROLL = 1.6f, JITTER = 0.7f;

	/** down: the view dips (a heavy landing) instead of snapping up. */
	private record Kick(long start, float strength, float rollSign, float phase, boolean down) {
	}

	/** An earthquake: a rattle that builds fast and rolls on for life seconds, starting at start. */
	private record Rumble(long start, float strength, float life, float phase) {
	}

	/** A sonic boom's jitter: amp degrees of yaw and pitch at freq shakes a second, dying away over life seconds. */
	private record Jitter(long start, float life, float amp, float freq, float phase) {
	}

	private static final List<Kick> KICKS = new ArrayList<>();
	private static final List<Jitter> JITTERS = new ArrayList<>();
	/** The sonic boom's field of view kick: when, and how many degrees at its start. */
	private static long fovStart;
	private static float fovDegrees;
	private static final List<Rumble> RUMBLES = new ArrayList<>();

	/** This frame's offsets in degrees: pitch (negative looks up), yaw and roll. */
	public static float pitch, yaw, roll;

	private RingShake() {
	}

	/** A shot effect arrived; kick the camera if this player fired it. */
	public static void shot(RingFxPayload fx) {
		float strength = switch (fx.kind()) {
			case BEAM -> 1f;
			case BEAM_CHARGED -> 1.8f;
			case BLAST -> 0.55f + 0.25f * Math.max(0, fx.variant() - 1);
			case BLAST_DRILL -> fx.value() == 2f ? 0.55f + 0.25f * Math.max(0, (fx.variant() & 3) - 1) : 0f;
			case PUSH -> 0.9f;
			default -> 0f;
		};
		if (strength <= 0) return;
		LocalPlayer player = Minecraft.getInstance().player;
		if (player == null) return;
		// Someone else's shot doesn't shake this camera, even fired from right beside it.
		if (fx.bearer() >= 0 && fx.bearer() != player.getId()) return;
		Vec3 from = fx.from();
		double near = Math.min(player.getEyePosition().distanceToSqr(from), player.position().distanceToSqr(from));
		if (near > SHOOTER_RANGE * SHOOTER_RANGE) return;
		kick(strength);
	}

	/** How far a lasso slam shakes cameras, in blocks; it fades out to nothing there. */
	private static final double SLAM_RANGE = 28;

	/** A lassoed mob slammed into a block at "from" at value blocks a tick: everyone nearby feels it. */
	public static void impact(RingFxPayload fx) {
		LocalPlayer player = Minecraft.getInstance().player;
		if (player == null) return;
		double d = player.position().distanceTo(fx.from());
		if (d > SLAM_RANGE) return;
		float falloff = (float) (1 - d / SLAM_RANGE);
		// A light slam is a nudge; a heavy one (1.6 blocks a tick and up) a hard jolt.
		float strength = Math.min(2.6f, 0.5f + fx.value() * 0.7f) * falloff * falloff;
		kick(strength);
	}

	public static void kick(float strength) {
		kick(strength, false);
	}

	/** A kick; down dips the view, like the jolt of landing a super jump. */
	public static void kick(float strength, boolean down) {
		strength *= LabSettings.get().screenShake.amount();
		if (strength <= 0) return;
		ThreadLocalRandom r = ThreadLocalRandom.current();
		synchronized (KICKS) {
			KICKS.add(new Kick(System.nanoTime(), strength, r.nextBoolean() ? 1f : -1f, r.nextFloat() * 6.283f, down));
		}
	}

	/**
	 * An earthquake rolling under this camera: strength 1 is a hard rumble, delay is the seconds
	 * until its wave arrives (a super jump's landing reaches the far ones later).
	 */
	public static void quake(float strength, float delay) {
		strength *= LabSettings.get().screenShake.amount();
		if (strength <= 0.02f) return;
		long start = System.nanoTime() + (long) (Math.max(0f, delay) * 1e9);
		synchronized (KICKS) {
			RUMBLES.add(new Rumble(start, strength, 0.5f + 0.5f * Math.min(1.5f, strength), ThreadLocalRandom.current().nextFloat() * 6.283f));
		}
	}

	/**
	 * A sonic boom (J, pass 218): your own is "extremely fast", 6 ticks of jitter at about 27 shakes a
	 * second from 1.2 degrees down to nothing; a nearby one is about 10 ticks at 12 a second, strength
	 * (1 - distance / 24). Scaled by the Ring Lab's "Sonic boom: screen shake".
	 */
	public static void boom(boolean own, float strength) {
		strength *= LabSettings.get().flightShake.amount();
		if (strength <= 0.02f) return;
		float phase = ThreadLocalRandom.current().nextFloat() * 6.283f;
		synchronized (KICKS) {
			JITTERS.add(own ? new Jitter(System.nanoTime(), 0.3f, 1.2f * strength, 27f, phase)
					: new Jitter(System.nanoTime(), 0.5f, 1.2f * strength, 12f, phase));
		}
	}

	/** Pass 403's standing take-off: the puff's subtle shake, pitch and yaw in degrees per tick (Blender's cam_shake). */
	private static final float[][] PUFF = {{0.5f, -0.3f}, {-0.38f, 0.23f}, {0.25f, -0.15f}, {-0.12f, 0.07f}, {0f, 0f}};
	private static long puffStart;
	private static float puffAmount;

	/** Your own standing take-off: 0.5 degrees of pitch and 0.3 of yaw, alternating and gone over 4 ticks. */
	public static void puff() {
		puffAmount = LabSettings.get().screenShake.amount();
		puffStart = System.nanoTime();
	}

	/** Widens your view by about this many degrees for a moment, springing back (your own sonic boom). */
	public static void fovKick(float degrees) {
		fovDegrees = degrees * LabSettings.get().flightShake.amount();
		fovStart = System.nanoTime();
	}

	/** This moment's field of view kick in degrees (0 when none). */
	public static float fovKick() {
		if (fovDegrees <= 0) return 0f;
		float t = (System.nanoTime() - fovStart) / 1e9f;
		if (t > 0.8f) return 0f;
		return fovDegrees * (float) Math.exp(-t / 0.12f);
	}

	/** Works out this frame's offsets; called while the camera is set up. */
	public static void update() {
		pitch = yaw = roll = 0f;
		long now = System.nanoTime();
		if (puffAmount > 0f) {
			float tick = (now - puffStart) / 5e7f;
			if (tick >= PUFF.length - 1) {
				puffAmount = 0f;
			} else {
				int i = (int) tick;
				pitch += puffAmount * (PUFF[i][0] + (PUFF[i + 1][0] - PUFF[i][0]) * (tick - i));
				yaw += puffAmount * (PUFF[i][1] + (PUFF[i + 1][1] - PUFF[i][1]) * (tick - i));
			}
		}
		synchronized (KICKS) {
			if (KICKS.isEmpty() && RUMBLES.isEmpty() && JITTERS.isEmpty()) return;
			KICKS.removeIf(k -> (now - k.start) / 1e9f > LIFE);
			JITTERS.removeIf(j -> (now - j.start) / 1e9f > j.life);
			for (Jitter j : JITTERS) {
				// Sampled every frame, not every tick, so the fast one really is 25-30 shakes a second.
				float t = (now - j.start) / 1e9f;
				float env = j.amp * (1f - t / j.life);
				float w = 6.283f * j.freq * t;
				yaw += env * (float) Math.sin(w + j.phase);
				pitch += env * (float) Math.sin(w * 1.13f + j.phase * 2f);
			}
			RUMBLES.removeIf(q -> (now - q.start) / 1e9f > q.life);
			for (Rumble q : RUMBLES) {
				float t = (now - q.start) / 1e9f;
				if (t < 0) continue;
				// Hits within a twentieth of a second, then dies away over its life.
				float env = q.strength * Math.min(1f, t / 0.05f) * (float) Math.exp(-3.2f * t / q.life);
				pitch += env * (1.3f * (float) Math.sin(t * 47 + q.phase) + 0.8f * (float) Math.sin(t * 83 + q.phase * 2));
				yaw += env * 0.9f * (float) Math.sin(t * 61 + q.phase * 3);
				roll += env * 1.1f * (float) Math.sin(t * 39 + q.phase);
			}
			for (Kick k : KICKS) {
				float t = (now - k.start) / 1e9f;
				// Rises to 1 at ATTACK, then falls away fast with a slight dip below zero (the settle).
				float x = t / ATTACK;
				float punch = x * (float) Math.exp(1 - x);
				float settle = 0.18f * (float) Math.sin(Math.min(1f, t / 0.25f) * Math.PI) * (float) Math.exp(-t / 0.12f);
				float rattle = (float) Math.exp(-t / 0.07f) * Math.min(1f, x);
				float s = k.strength;
				pitch += (k.down ? 1.4f : -1f) * PITCH * s * (punch - settle);
				roll += ROLL * s * k.rollSign * punch + 0.35f * ROLL * s * rattle * (float) Math.sin(t * 190 + k.phase);
				yaw += JITTER * s * rattle * (float) Math.sin(t * 150 + k.phase * 1.7f);
			}
		}
		// Even several shots at once stay a jolt rather than a spin.
		pitch = Math.max(-8f, Math.min(8f, pitch));
		roll = Math.max(-5f, Math.min(5f, roll));
		yaw = Math.max(-3f, Math.min(3f, yaw));
	}
}
