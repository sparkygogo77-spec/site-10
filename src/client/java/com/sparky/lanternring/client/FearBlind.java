package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModEffects;
import com.sparky.lanternring.RingTuning;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.util.Mth;
import net.minecraft.world.effect.MobEffectInstance;

/**
 * Fear Blind on your own screen, from standing in the Dread Runner's fear (corps/DreadTrails):
 * like the lantern flashbang, but dark. The screen drowns in a yellow-black shadow with sickly
 * yellow light burning at its edges, throbbing, and it fades once you're out of the fear, over
 * RingTuning.DREAD_BLIND.
 */
public final class FearBlind {
	/** The shadow, and the light at its edges. */
	private static final int SHADOW = 0x0E0B02;
	private static final int EDGE = 0xC9A21C;
	private static float blind;
	private static float prevBlind;

	private FearBlind() {
	}

	public static void register() {
		HudElementRegistry.addFirst(LanternRing.id("fear_blind"), FearBlind::extract);
	}

	/** Every client tick: closes in fast while you have it, and follows the effect running out after. */
	public static void tick(Minecraft mc) {
		prevBlind = blind;
		MobEffectInstance effect = mc.player == null ? null : mc.player.getEffect(ModEffects.FEAR_BLIND);
		float target = effect == null ? 0f : Mth.clamp(effect.getDuration() / (float) Math.max(1, RingTuning.DREAD_BLIND.ticks()), 0f, 1f);
		blind = target > blind ? blind + (target - blind) * 0.35f : target;
	}

	/** Test hook: how blinded the screen is right now, 0 to 1. */
	public static float blind() {
		return blind;
	}

	private static void extract(GuiGraphicsExtractor graphics, DeltaTracker delta) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.player == null) return;
		float s = Mth.lerp(delta.getGameTimeDeltaPartialTick(false), prevBlind, blind);
		if (s <= 0.004f) return;
		int w = graphics.guiWidth();
		int h = graphics.guiHeight();
		float age = mc.player.tickCount + delta.getGameTimeDeltaPartialTick(false);
		float pulse = 0.85f + 0.15f * Mth.sin(age * 0.35f);
		float eased = s * s * (3 - 2 * s);
		graphics.fill(0, 0, w, h, Math.round(255 * 0.9f * eased) << 24 | SHADOW);
		// The yellow light round the edges: bands of it, brightest at the rim, fading inward.
		int bands = 28;
		int step = Math.max(1, Math.round(Math.min(w, h) * (0.008f + 0.002f * pulse)));
		for (int i = 0; i < bands; i++) {
			float k = 1f - i / (float) bands;
			int a = Math.round(255 * Math.min(1f, 0.8f * eased * pulse * k * k));
			if (a < 2) continue;
			int c = a << 24 | EDGE;
			int o = i * step, n = o + step;
			if (n * 2 >= Math.min(w, h)) break;
			graphics.fill(o, o, w - o, n, c);
			graphics.fill(o, h - n, w - o, h - o, c);
			graphics.fill(o, n, n, h - n, c);
			graphics.fill(w - n, n, w - o, h - n, c);
		}
	}
}
