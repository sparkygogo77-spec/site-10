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
 */
public final class SunDim {
	/** Blocks from the bearer where the sunlight is back to normal. */
	public static final float RADIUS = 48f;
	/** Within this many blocks the dimming is at full strength. */
	public static final float NEAR = 10f;
	/** How much of the sunlight goes at full strength (some is kept so you can still see). */
	public static final float MAX = 0.88f;

	private static float level;
	private static float prevLevel;

	private SunDim() {
	}

	/** Every client tick: eases the dimming towards how near the closest charging ring is. */
	public static void tick(Minecraft mc) {
		prevLevel = level;
		LocalPlayer me = mc.player;
		if (me == null || mc.level == null) {
			level = prevLevel = 0f;
			return;
		}
		float target = 0f;
		// Your own charge: from the lantern rising until you let go.
		if (LanternFirstPerson.held(0f) >= LanternCharge.hold()) target = 1f;
		float[] near = {target};
		LanternFlash.forEachCharger(mc, bearer -> near[0] = Math.max(near[0], falloff(me, bearer)));
		target = near[0];
		float in = 1f / Math.max(1, RingTuning.CHARGE_DIM_IN.ticks());
		float out = 1f / Math.max(1, RingTuning.CHARGE_DIM_OUT.ticks());
		level = target > level ? Math.min(target, level + in) : Math.max(target, level - out);
	}

	private static float falloff(Entity me, Entity bearer) {
		float d = (float) me.distanceTo(bearer);
		return 1f - smooth((d - NEAR) / (RADIUS - NEAR));
	}

	private static float smooth(float x) {
		x = Mth.clamp(x, 0f, 1f);
		return x * x * (3 - 2 * x);
	}

	/** How dimmed the sunlight is where you stand, 0 (normal) to 1 (as dark as it gets), eased. */
	public static float level(float partialTick) {
		return smooth(Mth.lerp(partialTick, prevLevel, level));
	}

	/** How much the game's own sky light is kept: 1 normally, down to 1 - MAX. */
	public static float vanillaKeep(float partialTick) {
		// A shader pack lights the world itself; the patched one dims per pixel instead.
		if (SoulSight.shaderPackOn()) return 1f;
		return 1f - MAX * level(partialTick);
	}

	/** What the held ring tells the patched pack (PowerRingItem#getLightColor), or -1 for no pack. */
	public static float forShader() {
		if (!ShaderGlow.patchedPackOn()) return -1f;
		return level(Minecraft.getInstance().getDeltaTracker().getGameTimeDeltaPartialTick(false));
	}
}
