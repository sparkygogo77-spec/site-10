package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.Shockwaves;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.world.phys.Vec3;

/**
 * The Shockwave dome as one smooth sheet of deep jade glass: a sphere-cap mesh drawn every frame,
 * growing at exactly the server's Shockwaves speed so what you see touching a mob is what pushes
 * it. It is full-bright and half see-through, with bright edges (its silhouette and a band along
 * its foot) so it reads as a 3D shell. The glowing seam where it cuts into blocks is still drawn by
 * PANE particles (see LabFx.shockwave), which only show where a block is.
 *
 * It uses the vanilla translucent emissive entity render type, which shader packs such as
 * Complementary already know how to draw.
 */
public final class ShockwaveDomes {
	private static final RenderType GLASS = RenderTypes.entityTranslucentEmissive(LanternRing.id("textures/entity/shockwave_glass.png"));
	private static final int FULL_BRIGHT = 0xF000F0;
	/** Lowest point of the dome, as an angle below the horizon, so it meets slopes and steps. */
	private static final double BOTTOM = -0.15;
	private static final int SEGMENTS = 72;
	private static final int RINGS = 40;
	private static final float START_RADIUS = 0.4f;
	/** Ticks the dome takes to fade away once it is full size. */
	private static final float FADE = 5f;
	/** Deep jade for the body of the glass, bright jade-white for its edges. */
	private static final float[] JADE = {0.04f, 0.36f, 0.2f};
	private static final float[] EDGE = {0.55f, 1f, 0.75f};
	/** How tall the bright band along the dome's foot is, in blocks. */
	private static final float BAND = 0.9f;

	private record Dome(Vec3 center, long start) {
	}

	private static final List<Dome> DOMES = new ArrayList<>();

	private ShockwaveDomes() {
	}

	public static void register() {
		LevelRenderEvents.COLLECT_SUBMITS.register(ShockwaveDomes::submit);
	}

	public static void start(Vec3 center) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level != null) DOMES.add(new Dome(center, mc.level.getGameTime()));
	}

	private static void submit(LevelRenderContext ctx) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) {
			DOMES.clear();
			return;
		}
		if (DOMES.isEmpty()) return;
		float grow = (float) ((Shockwaves.RADIUS - START_RADIUS) / Shockwaves.SPEED);
		float now = mc.level.getGameTime() + ctx.levelState().worldPartialTicks;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		DOMES.removeIf(d -> now - d.start > grow + FADE || now < d.start - 1);
		for (Dome dome : DOMES) {
			float age = Math.max(0, now - dome.start);
			float radius = (float) Math.min(Shockwaves.RADIUS, START_RADIUS + Shockwaves.SPEED * age);
			float fade = age < grow ? 1f : Math.max(0f, 1f - (age - grow) / FADE);
			if (fade <= 0) continue;
			PoseStack pose = ctx.poseStack();
			pose.pushPose();
			pose.translate(dome.center.x - cam.x, dome.center.y - cam.y, dome.center.z - cam.z);
			Vec3 eye = cam.subtract(dome.center);
			ctx.submitNodeCollector().submitCustomGeometry(pose, GLASS, (p, vc) -> mesh(p, vc, radius, fade, eye));
			pose.popPose();
		}
	}

	/** The sphere cap as quads; eye is the camera relative to the dome's centre. */
	private static void mesh(PoseStack.Pose pose, VertexConsumer vc, float radius, float fade, Vec3 eye) {
		for (int ring = 0; ring < RINGS; ring++) {
			double p0 = pitch(ring);
			double p1 = pitch(ring + 1);
			for (int seg = 0; seg < SEGMENTS; seg++) {
				double y0 = seg * Math.PI * 2 / SEGMENTS;
				double y1 = (seg + 1) * Math.PI * 2 / SEGMENTS;
				vertex(pose, vc, radius, fade, eye, y0, p0, seg, ring);
				vertex(pose, vc, radius, fade, eye, y0, p1, seg, ring + 1);
				vertex(pose, vc, radius, fade, eye, y1, p1, seg + 1, ring + 1);
				vertex(pose, vc, radius, fade, eye, y1, p0, seg + 1, ring);
			}
		}
	}

	private static float mix(int channel, float t) {
		return JADE[channel] + (EDGE[channel] - JADE[channel]) * t;
	}

	private static double pitch(int ring) {
		return BOTTOM + (Math.PI / 2 - BOTTOM) * ring / RINGS;
	}

	private static void vertex(PoseStack.Pose pose, VertexConsumer vc, float radius, float fade, Vec3 eye,
			double yaw, double pitch, int seg, int ring) {
		float nx = (float) (Math.cos(yaw) * Math.cos(pitch));
		float ny = (float) Math.sin(pitch);
		float nz = (float) (Math.sin(yaw) * Math.cos(pitch));
		float x = nx * radius, y = ny * radius, z = nz * radius;
		// Edge-on glass looks thicker: the body is a fairly solid deep jade and the silhouette turns
		// bright. A band along the foot of the dome glows too, so the edge shows from inside as well.
		double vx = eye.x - x, vy = eye.y - y, vz = eye.z - z;
		double len = Math.max(1e-4, Math.sqrt(vx * vx + vy * vy + vz * vz));
		float facing = (float) Math.abs((vx * nx + vy * ny + vz * nz) / len);
		float rim = (float) Math.pow(1 - facing, 4);
		float foot = Math.max(0f, 1f - (y - (float) Math.sin(BOTTOM) * radius) / BAND);
		float glow = Math.min(1f, Math.max(rim, foot * foot));
		float alpha = fade * (0.6f + 0.35f * glow);
		vc.addVertex(pose, x, y, z)
				.setColor(mix(0, glow), mix(1, glow), mix(2, glow), alpha)
				.setUv(seg / (float) SEGMENTS, 1f - ring / (float) RINGS)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(FULL_BRIGHT)
				.setNormal(pose, nx, ny, nz);
	}
}
