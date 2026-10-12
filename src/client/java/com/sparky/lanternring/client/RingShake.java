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

	private record Kick(long start, float strength, float rollSign, float phase) {
	}

	private static final List<Kick> KICKS = new ArrayList<>();

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

	public static void kick(float strength) {
		strength *= LabSettings.get().screenShake.amount();
		if (strength <= 0) return;
		ThreadLocalRandom r = ThreadLocalRandom.current();
		synchronized (KICKS) {
			KICKS.add(new Kick(System.nanoTime(), strength, r.nextBoolean() ? 1f : -1f, r.nextFloat() * 6.283f));
		}
	}

	/** Works out this frame's offsets; called while the camera is set up. */
	public static void update() {
		pitch = yaw = roll = 0f;
		long now = System.nanoTime();
		synchronized (KICKS) {
			if (KICKS.isEmpty()) return;
			KICKS.removeIf(k -> (now - k.start) / 1e9f > LIFE);
			for (Kick k : KICKS) {
				float t = (now - k.start) / 1e9f;
				// Rises to 1 at ATTACK, then falls away fast with a slight dip below zero (the settle).
				float x = t / ATTACK;
				float punch = x * (float) Math.exp(1 - x);
				float settle = 0.18f * (float) Math.sin(Math.min(1f, t / 0.25f) * Math.PI) * (float) Math.exp(-t / 0.12f);
				float rattle = (float) Math.exp(-t / 0.07f) * Math.min(1f, x);
				float s = k.strength;
				pitch += -PITCH * s * (punch - settle);
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
