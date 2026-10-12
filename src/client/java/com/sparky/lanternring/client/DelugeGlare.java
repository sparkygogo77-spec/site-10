package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.minecraft.client.Camera;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.HumanoidArm;
import org.joml.Vector3f;

/**
 * Your own ring forming the Deluge's ball (RingEmit.hold): in first person it flares up over your
 * fist in the ring's colour and drinks in the light round the screen, the edges sinking into dark
 * while the glare at the ring swells and throbs. It lets go as the held top runs down.
 */
public final class DelugeGlare {
	private static final Identifier VIGNETTE = LanternRing.id("textures/misc/lantern_vignette.png");
	private static final Identifier GLARE = LanternRing.id("textures/misc/lantern_glare.png");
	/** How dark the screen round the ring gets at full strength. */
	private static final float MAX_DARK = 0.85f;
	/** How fast the flare takes the screen (per tick), and how fast it lets go. */
	private static final float RISE = 0.2f, FALL = 0.12f;

	private static float level, levelO;
	private static Corps corps = Corps.GREEN;

	private DelugeGlare() {
	}

	public static void register() {
		HudElementRegistry.addFirst(LanternRing.id("deluge_glare"), DelugeGlare::extract);
	}

	public static void tick(Minecraft mc) {
		levelO = level;
		LocalPlayer player = mc.player;
		float target = player == null ? 0f : RingEmit.held(player, 0f);
		if (player != null && RingEmit.heldCorps(player) != null) corps = RingEmit.heldCorps(player);
		level = target > level ? Math.min(target, level + RISE) : Math.max(target, level - FALL);
	}

	private static void extract(GuiGraphicsExtractor graphics, DeltaTracker delta) {
		Minecraft mc = Minecraft.getInstance();
		LocalPlayer player = mc.player;
		if (player == null || mc.level == null || !mc.options.getCameraType().isFirstPerson()) return;
		float partial = delta.getGameTimeDeltaPartialTick(false);
		float s = Mth.lerp(partial, levelO, level);
		if (s <= 0.01f) return;
		int w = graphics.guiWidth();
		int h = graphics.guiHeight();

		// Over the ring on your fist, as it was drawn (the hand has its own fixed field of view).
		HumanoidArm arm = RingEmit.ringArm(player);
		float cx = w * (arm == HumanoidArm.RIGHT ? 0.62f : 0.38f);
		float cy = h * 0.68f;
		Vector3f face = RingFirstPerson.drawnView(arm);
		if (face != null && face.z < -0.05f) {
			float tan = (float) Math.tan(Math.toRadians(Camera.BASE_HUD_FOV / 2f));
			float aspect = w / (float) h;
			cx = w * 0.5f * (1f + face.x / (-face.z * tan * aspect));
			cy = h * 0.5f * (1f - face.y / (-face.z * tan));
		}

		// The light round the screen is drawn in: dark everywhere but an opening on the ring.
		float time = mc.level.getGameTime() + partial;
		float throb = 0.5f + 0.5f * Mth.sin(time * 0.9f);
		float dark = MAX_DARK * s;
		int alpha = Math.round(255 * dark) << 24;
		int size = Math.round(Math.max(w, h) * (1.9f - 0.95f * s - 0.06f * throb));
		int x0 = Math.round(cx - size / 2f);
		int y0 = Math.round(cy - size / 2f);
		graphics.blit(RenderPipelines.GUI_TEXTURED, VIGNETTE, x0, y0, 0f, 0f, size, size, 256, 256, 256, 256, alpha);
		if (y0 > 0) graphics.fill(0, 0, w, y0, alpha);
		if (y0 + size < h) graphics.fill(0, y0 + size, w, h, alpha);
		if (x0 > 0) graphics.fill(0, Math.max(0, y0), x0, Math.min(h, y0 + size), alpha);
		if (x0 + size < w) graphics.fill(x0 + size, Math.max(0, y0), w, Math.min(h, y0 + size), alpha);

		// And poured into the ring: a wide halo in its colour and a hot core, throbbing.
		glow(graphics, cx, cy, h * (1.0f + 0.2f * throb) * s, corps.rgb, s);
		glow(graphics, cx, cy, h * (0.45f + 0.1f * throb) * s, corps.rgb, s);
		glow(graphics, cx, cy, h * (0.2f + 0.05f * throb) * s, lerpRgb(corps.rgb, 0xFFFFFF, 0.5f), s);
	}

	/** Adds a soft round glow of the given size, colour and strength (0..1) centred on (x, y). */
	private static void glow(GuiGraphicsExtractor graphics, float x, float y, float size, int rgb, float strength) {
		int sz = Math.round(size);
		if (sz < 2) return;
		int r = Math.round((rgb >> 16 & 0xFF) * strength);
		int g = Math.round((rgb >> 8 & 0xFF) * strength);
		int b = Math.round((rgb & 0xFF) * strength);
		// Almost no alpha with a premultiplied texture: the glow adds light instead of covering.
		int color = 1 << 24 | Mth.clamp(r, 0, 255) << 16 | Mth.clamp(g, 0, 255) << 8 | Mth.clamp(b, 0, 255);
		graphics.blit(RenderPipelines.GUI_TEXTURED_PREMULTIPLIED_ALPHA, GLARE, Math.round(x - sz / 2f), Math.round(y - sz / 2f),
				0f, 0f, sz, sz, 128, 128, 128, 128, color);
	}

	private static int lerpRgb(int from, int to, float t) {
		int r = Math.round(Mth.lerp(t, from >> 16 & 0xFF, to >> 16 & 0xFF));
		int g = Math.round(Mth.lerp(t, from >> 8 & 0xFF, to >> 8 & 0xFF));
		int b = Math.round(Mth.lerp(t, from & 0xFF, to & 0xFF));
		return r << 16 | g << 8 | b;
	}
}
