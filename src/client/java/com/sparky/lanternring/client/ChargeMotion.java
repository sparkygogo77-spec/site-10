package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternCharge;
import net.minecraft.client.Minecraft;
import net.minecraft.util.Mth;

/**
 * How the hands move while charging the ring from the lantern, shared by the first-person hands
 * and the third-person arms. The lantern comes up first; the ring hand bends and turns up to show
 * the ring, swings round to line it up just off the port, and the last bit is a magnet's pull: it
 * speeds up into the port and stops dead on it. It stays stuck there while the light builds, and at
 * 100% it jumps off the port at once, then the arms ease back down.
 *
 * <p>Each pose is a weight: {@code show} (the bent arm showing the ring), {@code line} (lined up
 * just off the port), {@code pull} (on the port), {@code raise} (the lantern up in front of you).
 * They blend one after another, overlapping so the hand travels one smooth curve.
 */
final class ChargeMotion {
	/** Parts of the reach (0..1) each move takes; they overlap. */
	private static final float SHOW_END = 0.45f, LINE_START = 0.28f, LINE_END = 0.76f, PULL_START = 0.7f;
	/** The lantern is up by this part of the reach, before the ring arrives. */
	private static final float RAISE_END = 0.55f;
	/** How far off the port (blocks, first person) the ring lines up before the pull. */
	static final float HOVER = 0.13f;
	/** Ticks the ring takes to jump off the port at 100% (and after letting go). */
	static final float SNAP = 2f;

	/** The local player's last weights while charging, so letting go early eases back instead of jumping. */
	private static Weights last;
	private static float letGoAt = -1f;

	record Weights(float show, float line, float pull, float raise) {
		static final Weights NONE = new Weights(0f, 0f, 0f, 0f);
	}

	private ChargeMotion() {
	}

	/** The weights {@code t} ticks after the charging right-click went down, or NONE if {@code t < 0}. */
	static Weights at(float t) {
		if (t < 0) return Weights.NONE;
		int hold = LanternCharge.hold();
		int done = LanternCharge.done();
		if (t < hold) return new Weights(0f, 0f, 0f, 0.12f * smooth(t / hold));
		if (t < done) {
			float u = (t - hold) / LanternCharge.reach();
			float x = Mth.clamp((u - PULL_START) / (1f - PULL_START), 0f, 1f);
			return new Weights(smooth(u / SHOW_END), smooth((u - LINE_START) / (LINE_END - LINE_START)),
					// A magnet: slow at first, fastest right as it hits.
					x * x * x, 0.12f + 0.88f * smooth(u / RAISE_END));
		}
		return release(t - done, new Weights(1f, 1f, 1f, 1f));
	}

	/** {@code a} ticks after leaving {@code from}: off the port at once, then everything eases down. */
	private static Weights release(float a, Weights from) {
		float pop = 1f - smooth(a / SNAP);
		float back = 1f - smooth((a - 1f) / (LanternCharge.SETTLE - 1f));
		return new Weights(from.show * back, from.line * back, from.pull * pop, from.raise * back);
	}

	/** The local player's weights this frame, easing back down after letting go early. */
	static Weights local(float partialTick) {
		Minecraft mc = Minecraft.getInstance();
		float t = LanternFirstPerson.held(partialTick);
		if (t >= 0) {
			last = at(t);
			letGoAt = -1f;
			return last;
		}
		if (last == null || mc.level == null) return Weights.NONE;
		float now = mc.level.getGameTime() + partialTick;
		if (letGoAt < 0) letGoAt = now;
		float a = now - letGoAt;
		if (a >= LanternCharge.SETTLE || a < 0) {
			last = null;
			return Weights.NONE;
		}
		return release(a, last);
	}

	/** Ticks since the ring hit the port, or -1 when it isn't on it. */
	static float onPort(float t) {
		float c = t - LanternCharge.hold() - LanternCharge.reach();
		return t < 0 || c < 0 || t >= LanternCharge.done() ? -1f : c;
	}

	/** 0..1: how far the light has built since the ring hit the port. */
	static float built(float c) {
		int span = LanternCharge.done() - LanternCharge.hold() - LanternCharge.reach();
		return c < 0 ? 0f : Mth.clamp(c / Math.max(1, span), 0f, 1f);
	}

	/**
	 * How far the lantern moves toward the ring hand (blocks, negative away): knocked back a little
	 * when the ring hits, then drawn in as the magnet's hold grows with the charge.
	 */
	static float lanternPull(float c) {
		if (c < 0) return 0f;
		float knock = 0.018f * (float) Math.exp(-c / 2.2f) * Mth.sin(c * 1.4f);
		return 0.022f * smooth(built(c)) - knock;
	}

	/** Degrees the lantern leans onto the ring once it's stuck to the port. */
	static final float LEAN = 8f;
	/** Degrees the raised lantern's top tips toward you, its port facing down to the ring coming up from below. */
	static final float TILT = 24f;
	/** Extra tip toward you as it leans in to meet the ring, and where it settles propped on it. */
	private static final float MEET = 9f, PROP = 7f;
	/** How hard the ring knocks it back the other way when it sticks (degrees). */
	private static final float KNOCK = 15f;

	/**
	 * Degrees the lantern's top tips toward you: in with the raise, further as it leans in to meet
	 * the ring, knocked away when the ring sticks and springing back to rest propped on it, then
	 * upright again as the arms come down. {@code raise} is this frame's raise weight.
	 */
	static float tilt(float t, float raise, float pull) {
		float base = TILT * raise;
		if (t < 0) return base;
		float c = t - LanternCharge.hold() - LanternCharge.reach();
		float a = t - LanternCharge.done();
		if (a >= 0) return base + PROP * (1f - smooth(a / (LanternCharge.SETTLE * 0.6f)));
		if (c < 0) return base + MEET * pull;
		float decay = (float) Math.exp(-c / 3f);
		return base + PROP + decay * ((MEET - PROP) * Mth.cos(c) - KNOCK * Mth.sin(c));
	}

	/** Blocks the lantern shifts toward you as the ring comes on, settling a little back once it's propped. */
	static float shift(float t, float pull) {
		if (t < 0) return 0f;
		float c = t - LanternCharge.hold() - LanternCharge.reach();
		float a = t - LanternCharge.done();
		if (a >= 0) return 0.025f * (1f - smooth(a / (LanternCharge.SETTLE * 0.6f)));
		if (c < 0) return 0.045f * pull;
		return 0.025f + 0.02f * (1f - smooth(c / 5f));
	}

	/**
	 * 0..1: how far the lantern is tipped over onto the ring, propped on it: it leans in over a few
	 * ticks once the ring sticks, and rights itself as the arms come down at 100%.
	 */
	static float lean(float t) {
		if (t < 0) return 0f;
		float c = t - LanternCharge.hold() - LanternCharge.reach();
		if (c < 0) return 0f;
		float a = t - LanternCharge.done();
		if (a < 0) return smooth(c / 6f);
		return 1f - smooth(a / (LanternCharge.SETTLE * 0.6f));
	}

	/** A fine buzz in the lantern and ring, growing as the charge nears 100%. */
	static float buzz(float c, float time) {
		if (c < 0) return 0f;
		float b = built(c);
		return 0.0025f * b * b * (Mth.sin(time * 4.1f) + Mth.sin(time * 6.7f)) * 0.5f;
	}

	static float smooth(float x) {
		x = Mth.clamp(x, 0f, 1f);
		return x * x * (3 - 2 * x);
	}
}
