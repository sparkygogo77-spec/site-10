package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModEffects;
import java.util.Random;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.effect.MobEffectInstance;

/**
 * Fear on your own screen: the dark closes in from the edges over the first two seconds until
 * only a small opening is left, beating like a heart, and pairs of yellow eyes open and blink in
 * the dark round it. Works under shader packs too (unlike the fog, see FearFog).
 */
public final class FearVignette {
	private static final Identifier VIGNETTE = LanternRing.id("textures/misc/lantern_vignette.png");
	/** Ticks the dark takes to close in. */
	private static final float CLOSE = 40f;
	/** When the local player's current Fear started (game time), -1 without one. */
	private static long since = -1;

	private FearVignette() {
	}

	public static void register() {
		HudElementRegistry.addFirst(LanternRing.id("fear_vignette"), FearVignette::extract);
	}

	/** How far the dark has closed in on the local player, 0 (none) to 1. */
	static float strength(float partial) {
		Minecraft mc = Minecraft.getInstance();
		LocalPlayer player = mc.player;
		MobEffectInstance fear = player == null ? null : player.getEffect(ModEffects.FEAR);
		if (fear == null || mc.level == null) {
			since = -1;
			return 0f;
		}
		long now = mc.level.getGameTime();
		if (since < 0 || since > now) since = now;
		float closing = Mth.clamp((now - since + partial) / CLOSE, 0f, 1f);
		float lifting = fear.isInfiniteDuration() ? 1f : Mth.clamp((fear.getDuration() - partial) / 20f, 0f, 1f);
		return closing * closing * (3 - 2 * closing) * lifting;
	}

	private static void extract(GuiGraphicsExtractor graphics, DeltaTracker delta) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.player == null) return;
		float partial = delta.getGameTimeDeltaPartialTick(false);
		float s = strength(partial);
		if (s <= 0.003f) return;
		int w = graphics.guiWidth();
		int h = graphics.guiHeight();
		float age = mc.player.tickCount + partial;
		// A heartbeat: two quick pulses, then a rest.
		float beat = age % 24f;
		float pulse = beat < 3 ? beat / 3 : beat < 6 ? 1 - (beat - 3) / 3 : beat < 9 ? 0.6f * (beat - 6) / 3 : beat < 12 ? 0.6f * (1 - (beat - 9) / 3) : 0;
		int size = Math.round(Math.max(w, h) * Mth.lerp(s, 2.8f, 0.9f) * (1f - 0.04f * pulse));
		int alpha = Math.round(255 * Math.min(1f, 0.92f * s)) << 24;
		int cx = w / 2, cy = h / 2;
		int x0 = cx - size / 2, y0 = cy - size / 2;
		graphics.blit(RenderPipelines.GUI_TEXTURED, VIGNETTE, x0, y0, 0f, 0f, size, size, 256, 256, 256, 256, alpha);
		if (y0 > 0) graphics.fill(0, 0, w, y0, alpha);
		if (y0 + size < h) graphics.fill(0, y0 + size, w, h, alpha);
		if (x0 > 0) graphics.fill(0, Math.max(0, y0), x0, Math.min(h, y0 + size), alpha);
		if (x0 + size < w) graphics.fill(x0 + size, Math.max(0, y0), w, Math.min(h, y0 + size), alpha);

		// Eyes in the dark: a few pairs at a time, each open for a moment, blinking.
		if (s < 0.5f) return;
		int slot = (int) (age / 14f);
		Random random = new Random(slot * 31L + 7);
		int pairs = 2 + random.nextInt(3);
		float open = Mth.sin((age % 14f) / 14f * Mth.PI);
		int eyeAlpha = Math.round(230 * open * (s - 0.5f) * 2f);
		if (eyeAlpha < 8) return;
		int pixel = Math.max(1, h / 160);
		for (int i = 0; i < pairs; i++) {
			double a = random.nextDouble() * Math.PI * 2;
			double r = size * (0.36 + 0.12 * random.nextDouble());
			int ex = cx + (int) (Math.cos(a) * r * 1.4);
			int ey = cy + (int) (Math.sin(a) * r);
			if (ex < 4 || ey < 4 || ex > w - 4 || ey > h - 4) continue;
			int gap = pixel * (2 + random.nextInt(3));
			int color = eyeAlpha << 24 | (random.nextBoolean() ? 0xFFD21A : 0xFFE870);
			graphics.fill(ex - gap - pixel, ey, ex - gap + pixel, ey + pixel, color);
			graphics.fill(ex + gap - pixel, ey, ex + gap + pixel, ey + pixel, color);
		}
	}
}
