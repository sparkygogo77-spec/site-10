package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModEffects;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.util.Mth;

/**
 * Red rage on your own screen (J, 2026-10-13: 38c): a dark red glow at the edges that beats slowly
 * like a pulse, fading in when the rage takes you and out when it ends. You can see through it.
 */
public final class RageTint {
	private static final int EDGE = 0x8A0606;
	private static final float GLOW = 0.42f;
	private static float rage, prevRage;

	private RageTint() {
	}

	public static void register() {
		HudElementRegistry.addFirst(LanternRing.id("red_rage"), RageTint::extract);
	}

	public static void tick(Minecraft mc) {
		prevRage = rage;
		boolean on = mc.player != null && mc.player.hasEffect(ModEffects.RAGE);
		rage = Mth.approach(rage, on ? 1f : 0f, on ? 0.05f : 0.02f);
	}

	private static void extract(GuiGraphicsExtractor graphics, DeltaTracker delta) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.player == null) return;
		float s = Mth.lerp(delta.getGameTimeDeltaPartialTick(false), prevRage, rage);
		if (s <= 0.004f) return;
		int w = graphics.guiWidth(), h = graphics.guiHeight();
		float age = mc.player.tickCount + delta.getGameTimeDeltaPartialTick(false);
		// A heartbeat: two quick thumps, then a rest.
		float beat = age % 24f;
		float pulse = 0.75f + 0.25f * (Math.max(0f, 1f - Math.abs(beat - 2f) / 2f) + 0.7f * Math.max(0f, 1f - Math.abs(beat - 6f) / 2f));
		int bands = 18;
		int step = Math.max(1, Math.round(Math.min(w, h) * 0.009f));
		for (int i = 0; i < bands; i++) {
			float k = 1f - i / (float) bands;
			int a = Math.round(255 * Math.min(1f, GLOW * s * pulse * k * k));
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
