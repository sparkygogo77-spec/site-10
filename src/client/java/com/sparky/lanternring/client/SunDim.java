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
	/** Blocks from the bearer where the sunlight is back to normal. */
	public static final float RADIUS = 48f;
	/** How far the darkness spreads round another bearer at the height of their charge (J, 2026-10-14). */
	public static final float STEAL_RADIUS = 96f;
	/** Within this many blocks the dimming is at full strength. */
	public static final float NEAR = 10f;
	/** How much of the sunlight goes at full strength (some is kept so you can still see). */
	public static final float MAX = 0.88f;

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
		float target = 0f;
		// Your own charge: from the lantern rising until you let go.
		if (LanternFirstPerson.held(0f) >= LanternCharge.hold()) target = 1f;
		float[] near = {target};
		LanternFlash.forEachCharger(mc, (bearer, power) -> near[0] = Math.max(near[0], falloff(me, bearer, power)));
		target = near[0];
		float in = 1f / Math.max(1, RingTuning.CHARGE_DIM_IN.ticks());
		float out = 1f / Math.max(1, RingTuning.CHARGE_DIM_OUT.ticks());
		level = target > level ? Math.min(target, level + in) : Math.max(target, level - out);
	}

	/**
	 * How dimmed it is for someone {@code me} near another bearer charging with this much light:
	 * the darkness spreads further the more light the charger pulls in, out to {@link #STEAL_RADIUS}.
	 */
	private static float falloff(Entity me, Entity bearer, float power) {
		float d = (float) me.distanceTo(bearer);
		float reach = Mth.lerp(Mth.clamp(power, 0f, 1f), RADIUS, STEAL_RADIUS);
		return 1f - smooth((d - NEAR) / (reach - NEAR));
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
		return Math.max(level(partial), hole(partial));
	}
}
