package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModRegistry;
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
import net.minecraft.world.item.ItemStack;
import org.joml.Vector3f;

/**
 * The screen while the ring charges in the lantern: as the light builds, everything around the
 * lantern sinks into darkness and the lantern's glare grows until it's blinding. At the climax
 * (the ring is full) the screen flashes in the lantern's colour, then the dark lifts and the
 * light eases smoothly back to the lantern's normal steady glow (timeline in
 * {@link LanternCharge}). Drawn under the rest of the HUD so the hotbar stays readable.
 */
public final class LanternGlare {
	private static final Identifier VIGNETTE = LanternRing.id("textures/misc/lantern_vignette.png");
	private static final Identifier GLARE = LanternRing.id("textures/misc/lantern_glare.png");
	/** How dark the screen gets around the lantern at the climax. */
	private static final float MAX_DARK = 0.92f;
	/** The lantern's normal, steady glow (see {@link #light}). */
	static final float IDLE = 0.6f;
	/** Ticks the climax holds at full brightness before the light starts to settle. */
	private static final int PEAK = 4;

	/** Game time when the ring filled, or Long.MIN_VALUE if it hasn't lately. */
	private static long doneAt = Long.MIN_VALUE;
	/** True while a charge is running and hasn't reached the climax yet. */
	private static boolean building;
	/** The colour of the lantern that last charged the ring, so the fade-out keeps it after letting go. */
	private static Corps corps = Corps.GREEN;

	private LanternGlare() {
	}

	public static void register() {
		HudElementRegistry.addFirst(LanternRing.id("lantern_glare"), LanternGlare::extract);
	}

	/** Called every client tick: notices the climax, so the burn-out plays on even after letting go. */
	public static void tick(Minecraft mc) {
		LocalPlayer player = mc.player;
		if (player == null || mc.level == null) return;
		float t = LanternFirstPerson.held(0f);
		if (t >= 0) {
			ItemStack off = LanternCharge.lantern(player);
			if (off.is(ModRegistry.POWER_BATTERY_ITEM)) corps = Corps.ofLantern(off);
		}
		long now = mc.level.getGameTime();
		if (t >= 0 && t < LanternCharge.done()) {
			building = true;
		} else if (building && t >= LanternCharge.done()) {
			building = false;
			doneAt = now;
		} else if (t < 0) {
			building = false;
		}
	}

	/** 0..1 through the build-up (from the ring touching the lens to full), or -1 outside it. */
	static float build(float partialTick) {
		float t = LanternFirstPerson.held(partialTick);
		int start = LanternCharge.hold();
		int done = LanternCharge.done();
		if (t < start || t >= done || !building) return -1f;
		return (t - start) / (done - start);
	}

	/** Ticks since the ring filled (the climax), or -1 once it has settled. */
	static float after(float partialTick) {
		Minecraft mc = Minecraft.getInstance();
		if (doneAt == Long.MIN_VALUE || mc.level == null) return -1f;
		float a = mc.level.getGameTime() - doneAt + partialTick;
		return a < 0 || a > LanternCharge.DEPLETE ? -1f : a;
	}

	private static float smooth(float x) {
		x = Mth.clamp(x, 0f, 1f);
		return x * x * (3 - 2 * x);
	}

	/** How dark the screen around the lantern is, 0..MAX_DARK. */
	static float darkness(float partialTick) {
		float x = build(partialTick);
		if (x >= 0) return MAX_DARK * (float) Math.pow(x, 1.4);
		float a = after(partialTick);
		if (a < 0) return 0f;
		if (a < PEAK) return MAX_DARK;
		// The dark lifts as the light drains, a little behind it.
		return MAX_DARK * (1f - smooth((a - PEAK) / (LanternCharge.DEPLETE * 0.75f - PEAK)));
	}

	/**
	 * The lantern's light, {@link #IDLE} = its normal glow, up to about 4 at the climax. The
	 * first-person lantern model and the glare on screen both follow it.
	 */
	static float light(float partialTick) {
		float x = build(partialTick);
		Minecraft mc = Minecraft.getInstance();
		float time = mc.level == null ? 0 : mc.level.getGameTime() + partialTick;
		if (x >= 0) {
			// Speeds up and swells: a gentle start, then a rush at the end.
			float flicker = 0.08f + 0.35f * x * x;
			return 1f + 3f * x * x * x + flicker * Mth.sin(time * (0.8f + 2.2f * x));
		}
		float a = after(partialTick);
		if (a < 0) return -1f;
		if (a < PEAK) return 4f;
		// Then it eases straight back to its normal steady glow: no flicker once the ring is full.
		return IDLE + (4f - IDLE) * (1f - smooth((a - PEAK) / (LanternCharge.DEPLETE - PEAK)));
	}

	private static void extract(GuiGraphicsExtractor graphics, DeltaTracker delta) {
		Minecraft mc = Minecraft.getInstance();
		LocalPlayer player = mc.player;
		if (player == null) return;
		float partial = delta.getGameTimeDeltaPartialTick(false);
		float dark = darkness(partial);
		float light = light(partial);
		if (dark <= 0.003f && light <= 1.05f) return;
		int w = graphics.guiWidth();
		int h = graphics.guiHeight();

		// Where the lantern is on screen.
		float cx = w * (player.getMainArm() == HumanoidArm.RIGHT ? 0.38f : 0.62f);
		float cy = h * 0.5f;
		Vector3f lens = LanternFirstPerson.lensView();
		if (mc.options.getCameraType().isFirstPerson() && lens != null && lens.z < -0.05f) {
			// The hand is drawn with a fixed field of view, so project with that one.
			float tan = (float) Math.tan(Math.toRadians(Camera.BASE_HUD_FOV / 2f));
			float aspect = w / (float) h;
			cx = w * 0.5f * (1f + lens.x / (-lens.z * tan * aspect));
			cy = h * 0.5f * (1f - lens.y / (-lens.z * tan));
		}

		// Darkness everywhere but a soft opening around the lantern.
		if (dark > 0.003f) {
			int alpha = Math.round(255 * dark) << 24;
			// The opening narrows as the light gets brighter, like eyes squinting against it.
			int size = Math.round(Math.max(w, h) * (2.6f - 1.0f * Math.min(1f, dark / MAX_DARK)));
			int x0 = Math.round(cx - size / 2f);
			int y0 = Math.round(cy - size / 2f);
			graphics.blit(RenderPipelines.GUI_TEXTURED, VIGNETTE, x0, y0, 0f, 0f, size, size, 256, 256, 256, 256, alpha);
			if (y0 > 0) graphics.fill(0, 0, w, y0, alpha);
			if (y0 + size < h) graphics.fill(0, y0 + size, w, h, alpha);
			if (x0 > 0) graphics.fill(0, Math.max(0, y0), x0, Math.min(h, y0 + size), alpha);
			if (x0 + size < w) graphics.fill(x0 + size, Math.max(0, y0), w, Math.min(h, y0 + size), alpha);
		}

		// The glare: light added onto the screen, a wide coloured halo and a white-hot core.
		// Only from your own eyes: in third person there's no lantern at that spot on screen.
		boolean own = mc.options.getCameraType().isFirstPerson();
		float glare = own ? Mth.clamp((light - 1f) / 3f, 0f, 1.2f) : 0f;
		if (glare > 0.01f) {
			glow(graphics, cx, cy, h * (0.5f + 0.8f * glare), corps.rgb, 0.85f * glare);
			glow(graphics, cx, cy, h * (0.2f + 0.5f * glare), 0xFFFFFF, Math.min(1f, 1.1f * glare * glare));
		}

		// The sun where the ring meets the lens (LanternFlash): a small white-hot disc in a corps halo,
		// bright enough to read as a sun but kept small so you can still see past it.
		float sun = player == null ? 0f : LanternFlash.sun(player, partial);
		if (sun > 0.01f && mc.options.getCameraType().isFirstPerson() && LabSettings.get().lanternSun == LabSettings.LanternSun.SUN) {
			float s = Math.min(sun, 1.3f);
			glow(graphics, cx, cy, h * (0.35f + 0.35f * s), corps.rgb, 0.7f * s);
			glow(graphics, cx, cy, h * (0.12f + 0.14f * s), 0xFFFFFF, Math.min(1f, 0.9f * s));
		}

		// The climax: a burst of white-hot light from the lantern that fades into the dark.
		float a = after(partial);
		if (own && a >= 0 && a < PEAK + 6) {
			float flash = Mth.clamp(a < 1 ? a : 1f - (a - 1) / (PEAK + 5), 0f, 1f);
			glow(graphics, cx, cy, h * 1.7f, lerpRgb(corps.rgb, 0xFFFFFF, 0.4f), 0.75f * flash);
		}
	}

	/** Adds a soft round glow of the given size, colour and strength (0..1) centred on (x, y). */
	private static void glow(GuiGraphicsExtractor graphics, float x, float y, float size, int rgb, float strength) {
		int s = Math.round(size);
		int r = Math.round((rgb >> 16 & 0xFF) * strength);
		int g = Math.round((rgb >> 8 & 0xFF) * strength);
		int b = Math.round((rgb & 0xFF) * strength);
		// Almost no alpha with a premultiplied texture: the glow adds light instead of covering.
		int color = 1 << 24 | Mth.clamp(r, 0, 255) << 16 | Mth.clamp(g, 0, 255) << 8 | Mth.clamp(b, 0, 255);
		graphics.blit(RenderPipelines.GUI_TEXTURED_PREMULTIPLIED_ALPHA, GLARE, Math.round(x - s / 2f), Math.round(y - s / 2f),
				0f, 0f, s, s, 128, 128, 128, 128, color);
	}

	private static int lerpRgb(int from, int to, float t) {
		int r = Math.round(Mth.lerp(t, from >> 16 & 0xFF, to >> 16 & 0xFF));
		int g = Math.round(Mth.lerp(t, from >> 8 & 0xFF, to >> 8 & 0xFF));
		int b = Math.round(Mth.lerp(t, from & 0xFF, to & 0xFF));
		return r << 16 | g << 8 | b;
	}
}
