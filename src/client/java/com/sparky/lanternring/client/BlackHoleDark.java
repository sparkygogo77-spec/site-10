package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternRing;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.minecraft.client.Camera;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.renderer.RenderPipelines;
import net.minecraft.resources.Identifier;
import net.minecraft.world.phys.Vec3;
import org.joml.Matrix4f;
import org.joml.Vector3fc;
import org.joml.Vector4f;

/**
 * Up close to a Black Hole the rest of your screen sinks into darkness: everything but the hole
 * and the light round it goes black, closing in the nearer you are and the longer it has fed
 * (BlackHoleFx.darkness). Drawn over the screen, so it works the same under shader packs.
 */
public final class BlackHoleDark {
	private static final Identifier VIGNETTE = LanternRing.id("textures/misc/lantern_vignette.png");

	private BlackHoleDark() {
	}

	static void register() {
		HudElementRegistry.addFirst(LanternRing.id("black_hole_dark"), BlackHoleDark::extract);
	}

	private static void extract(GuiGraphicsExtractor graphics, DeltaTracker delta) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		Camera camera = mc.gameRenderer.mainCamera();
		Vec3 cam = camera.position();
		float now = mc.level.getGameTime() + delta.getGameTimeDeltaPartialTick(false);
		BlackHoleFx.Hole hole = BlackHoleFx.nearest(cam);
		if (hole == null) return;
		float dark = BlackHoleFx.darkness(hole, cam, now);
		if (dark < 0.01f) return;
		int w = graphics.guiWidth(), h = graphics.guiHeight();
		Matrix4f view = camera.getViewRotationProjectionMatrix(new Matrix4f());
		Vec3 rel = BlackHoleFx.center(hole).subtract(cam);
		Vector4f c = view.transform(new Vector4f((float) rel.x, (float) rel.y, (float) rel.z, 1));
		if (c.w <= 0.05f) {
			// Turned away from it: the whole view is dimmed, less than round it so you can still get away.
			graphics.fill(0, 0, w, h, Math.round(255 * 0.6f * dark) << 24);
			return;
		}
		// Where the hole is on screen, and how big the part left clear looks.
		float sx = (c.x / c.w * 0.5f + 0.5f) * w, sy = (0.5f - c.y / c.w * 0.5f) * h;
		Vector3fc upv = camera.upVector();
		float r = BlackHoleFx.clearRadius(hole, now, dark);
		Vector4f e = view.transform(new Vector4f((float) rel.x + upv.x() * r, (float) rel.y + upv.y() * r, (float) rel.z + upv.z() * r, 1));
		float ex = (e.x / e.w * 0.5f + 0.5f) * w, ey = (0.5f - e.y / e.w * 0.5f) * h;
		float radius = (float) Math.hypot(ex - sx, ey - sy);
		// The clear middle of the vignette is about a third of its size.
		int size = Math.max(24, Math.round(Math.min(radius * 2 / 0.6f, 8f * Math.max(w, h))));
		int alpha = Math.round(255 * Math.min(1f, 0.97f * dark)) << 24;
		int x0 = Math.round(sx) - size / 2, y0 = Math.round(sy) - size / 2;
		graphics.blit(RenderPipelines.GUI_TEXTURED, VIGNETTE, x0, y0, 0f, 0f, size, size, 256, 256, 256, 256, alpha);
		if (y0 > 0) graphics.fill(0, 0, w, Math.min(h, y0), alpha);
		if (y0 + size < h) graphics.fill(0, Math.max(0, y0 + size), w, h, alpha);
		if (x0 > 0) graphics.fill(0, Math.max(0, y0), Math.min(w, x0), Math.min(h, y0 + size), alpha);
		if (x0 + size < w) graphics.fill(Math.max(0, x0 + size), Math.max(0, y0), w, Math.min(h, y0 + size), alpha);
	}
}
