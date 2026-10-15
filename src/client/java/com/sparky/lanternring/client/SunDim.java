package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.RingTuning;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;

/**
 * The sun dims round a ring charging at its lantern (J, 2026-10-13): once the lantern is up, the
 * daylight round the bearer fades over {@link RingTuning#CHARGE_DIM_IN}, as if the lantern were
 * drinking it, and it comes back over {@link RingTuning#CHARGE_DIM_OUT} when the charge ends. The
 * dimming is strongest at the bearer and gone by {@link #RADIUS} blocks out.
 *
 * <p>Without a shader pack the game's own sky light and sky are turned down by {@link #level}
 * (mixins on the lightmap and the sky). Under the Lantern Ring copy of Complementary the pack does
 * it per pixel, so the ground near you goes dark while distant hills stay sunlit: the held ring
 * hands Iris {@link #level} inside its light colour (PowerRingItem#getLightColor), and the patch
 * scales the sun and sky light by distance from your eyes.
 *
 * <p>A Black Hole does the same as you near it and as it lives and feeds (BlackHoleFx.darknessAt),
 * only darker, so its green is the only light left.
 */
public final class SunDim {
	/** Blocks from the bearer where the sunlight is back to normal (J: about 50). */
	public static final float RADIUS = 50f;
	/** How dark the charge itself gets before the end (of the way to {@link #MAX}). */
	public static final float DRAIN = 0.55f;
	/** The last part of the charge in which it plunges to black, and how fast it may (ticks for all of it). */
	private static final float PLUNGE = 0.2f;
	private static final float PLUNGE_TICKS = 6f;
	/** Ticks it stays black after the burst. */
	private static final float BURST_HOLD = 20f;
	/** Within this many blocks the dimming is at full strength. */
	public static final float NEAR = 10f;
	/** How much of the sunlight goes at full strength: about 90% black (J), some kept so you can still see. */
	public static final float MAX = 0.6f;
	/**
	 * How much of its full dimming the charge hands the patched pack (J, 2026-10-15: "the rays are game breaking", the
	 * sky went dark purple): the charge darkens the world, it no longer blacks it out. A Black Hole still goes all the way.
	 */
	private static final float SHADER_CHARGE = 0.55f;

	/** How much of the sunlight a Black Hole can take at its darkest: nearly all. */
	public static final float HOLE_MAX = 0.96f;

	private static float level;
	private static float prevLevel;
	/** The same for the nearest Black Hole (BlackHoleFx.darknessAt), kept apart so it can go darker. */
	private static float hole;
	private static float prevHole;

	private SunDim() {
	}

	/** Every client tick: eases the dimming towards how near the closest charging ring is. */
	public static void tick(Minecraft mc) {
		prevLevel = level;
		LocalPlayer me = mc.player;
		prevHole = hole;
		if (me == null || mc.level == null) {
			level = prevLevel = hole = prevHole = 0f;
			return;
		}
		float dark = BlackHoleFx.darknessAt(mc.gameRenderer.mainCamera().position(), mc.level.getGameTime());
		hole += Mth.clamp(dark - hole, -0.08f, 0.08f);
		// Your own charge: drains from the lantern rising, goes nearly black as it fills.
		float target = ownTarget();
		float[] near = {target};
		LanternFlash.forEachCharger(mc, (bearer, power) -> near[0] = Math.max(near[0], falloff(me, bearer) * fromPower(power)));
		target = near[0];
		float in = 1f / Math.max(1, RingTuning.CHARGE_DIM_IN.ticks());
		// The last stretch to black comes on fast, as the ring fills and flashes.
		if (target > DRAIN + 0.01f) in = Math.max(in, 1f / PLUNGE_TICKS);
		float out = 1f / Math.max(1, RingTuning.CHARGE_DIM_OUT.ticks());
		level = target > level ? Math.min(target, level + in) : Math.max(target, level - out);
	}

	/**
	 * How dark it should go for a charge {@code p} of the way (0..1) from the ring meeting the lens
	 * to full (J, 2026-10-14): the daylight drains to {@link #DRAIN} over the charge, then in the
	 * last {@link #PLUNGE} of it, and at the burst, plunges to all the way (about 90% black).
	 */
	static float darkFor(float p) {
		if (p < 0f) return DRAIN * 0.6f;
		if (p < 1f - PLUNGE) return DRAIN * (0.6f + 0.4f * p / (1f - PLUNGE));
		return DRAIN + (1f - DRAIN) * smooth((p - (1f - PLUNGE)) / PLUNGE);
	}

	private static float ownTarget() {
		float t = LanternFirstPerson.held(0f);
		int contact = LanternCharge.hold() + LanternCharge.reach();
		int done = LanternCharge.done();
		// Just after the burst it stays black for a moment, then the light comes back.
		float after = LanternGlare.after(0f);
		if (after >= 0f && after < BURST_HOLD) return 1f;
		if (t < LanternCharge.hold()) return 0f;
		if (t < contact) return darkFor(-1f);
		return darkFor((t - contact) / Math.max(1f, done - contact));
	}

	/** The same from the light another bearer is pouring out (server LanternFlash: 0.25 at the lens, 1 nearly full, above at the burst). */
	private static float fromPower(float power) {
		if (power >= 1f) return 1f;
		float p = (float) Math.pow(Mth.clamp((power - 0.25f) / 0.75f, 0f, 1f), 2.0 / 3.0);
		return darkFor(p);
	}

	private static float falloff(Entity me, Entity bearer) {
		float d = (float) me.distanceTo(bearer);
		return 1f - smooth((d - NEAR) / (RADIUS - NEAR));
	}

	private static float smooth(float x) {
		x = Mth.clamp(x, 0f, 1f);
		return x * x * (3 - 2 * x);
	}

	/** Whether your own lantern is up for a charge: the held light goes to full (you're the sun). */
	public static boolean charging() {
		return LanternFirstPerson.held(0f) >= LanternCharge.hold();
	}

	/** How dimmed the sunlight is where you stand, 0 (normal) to 1 (as dark as it gets), eased. */
	public static float level(float partialTick) {
		return smooth(Mth.lerp(partialTick, prevLevel, level));
	}

	/** How dark a Black Hole near you has made the world, 0 to 1, eased. */
	public static float hole(float partialTick) {
		return Mth.clamp(Mth.lerp(partialTick, prevHole, hole), 0f, 1f);
	}

	/** How much of the game's own sky light is kept: 1 normally, down to 1 - MAX (1 - HOLE_MAX by a Black Hole). */
	public static float vanillaKeep(float partialTick) {
		// A shader pack lights the world itself; the patched one dims per pixel instead.
		if (SoulSight.shaderPackOn()) return 1f;
		return 1f - Math.max(MAX * level(partialTick), HOLE_MAX * hole(partialTick));
	}

	/** What the held ring tells the patched pack (PowerRingItem#getLightColor), or -1 for no pack. */
	public static float forShader() {
		if (!ShaderGlow.patchedPackOn()) return -1f;
		float partial = Minecraft.getInstance().getDeltaTracker().getGameTimeDeltaPartialTick(false);
		return Math.max(SHADER_CHARGE * level(partial), hole(partial));
	}
}
