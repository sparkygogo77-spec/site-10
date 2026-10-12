package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.Corps;
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
 * The Shockwave dome as one smooth sheet of cracked jade hard light: a sphere-cap mesh drawn every frame,
 * growing at exactly the server's Shockwaves speed so what you see touching a mob is what pushes
 * it. Its texture is the same cracked jade as the block constructs, with glowing smoke drifting
 * inside: shockwave_glass.png holds 64 frames in an 8x8 grid and the mesh steps through them by
 * game time. It is full-bright and mostly solid, with bright edges (its silhouette and a band along
 * its foot) so it reads as a 3D shell. The glowing seam where it cuts into blocks is still drawn by
 * PANE particles (see LabFx.shockwave), which only show where a block is.
 *
 * It uses the vanilla translucent emissive entity render type, which shader packs such as
 * Complementary already know how to draw.
 */
public final class ShockwaveDomes {
	private static final Identifier GLASS = LanternRing.id("textures/entity/shockwave_glass.png");
	private static final int FULL_BRIGHT = 0xF000F0;
	/** Lowest point of the dome, as an angle below the horizon, so it meets slopes and steps. */
	private static final double BOTTOM = -0.15;
	private static final int SEGMENTS = 72;
	private static final int RINGS = 40;
	private static final float START_RADIUS = 0.4f;
	/** Ticks the dome takes to fade away once it is full size. */
	private static final float FADE = 5f;
	/** Tint on the body and at the bright edges; the texture itself carries the jade colour. */
	private static final float[] JADE = {0.86f, 0.92f, 0.88f};
	private static final float[] EDGE = {1f, 1f, 1f};
	/** The texture repeats every this many segments around and rings up the dome. */
	private static final int TILE_SEGS = 6;
	private static final int TILE_RINGS = 5;
	/** Smoke animation: frames in the sheet, its grid size and ticks per frame (as the blocks). */
	private static final int FRAMES = 64;
	private static final int GRID = 8;
	private static final int FRAME_TICKS = 3;
	/** Half a texel of the 1024px sheet, so a frame never samples its neighbour. */
	private static final float INSET = 0.5f / 1024f;
	/** How tall the bright band along the dome's foot is, in blocks. */
	private static final float BAND = 0.9f;

	private record Dome(Vec3 center, long start, float maxRadius, Corps corps) {
	}

	private static final List<Dome> DOMES = new ArrayList<>();

	private ShockwaveDomes() {
	}

	public static void register() {
		LevelRenderEvents.COLLECT_SUBMITS.register(ShockwaveDomes::submit);
	}

	public static void start(Vec3 center, float maxRadius) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level != null) DOMES.add(new Dome(center, mc.level.getGameTime(), maxRadius, CorpsTint.current()));
	}

	private static void submit(LevelRenderContext ctx) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) {
			DOMES.clear();
			return;
		}
		if (DOMES.isEmpty()) return;
		float now = mc.level.getGameTime() + ctx.levelState().worldPartialTicks;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		DOMES.removeIf(d -> now - d.start > growTicks(d) + FADE || now < d.start - 1);
		for (Dome dome : DOMES) {
			float grow = growTicks(dome);
			float age = Math.max(0, now - dome.start);
			float radius = (float) Math.min(dome.maxRadius, START_RADIUS + Shockwaves.SPEED * age);
			float fade = age < grow ? 1f : Math.max(0f, 1f - (age - grow) / FADE);
			if (fade <= 0) continue;
			PoseStack pose = ctx.poseStack();
			pose.pushPose();
			pose.translate(dome.center.x - cam.x, dome.center.y - cam.y, dome.center.z - cam.z);
			Vec3 eye = cam.subtract(dome.center);
			int frame = Math.floorMod((int) (now / FRAME_TICKS), FRAMES);
			RenderType glass = RenderTypes.entityTranslucentEmissive(CorpsTint.texture(GLASS, dome.corps));
			ctx.submitNodeCollector().submitCustomGeometry(pose, glass, (p, vc) -> mesh(p, vc, radius, fade, eye, frame));
			pose.popPose();
		}
	}

	private static float growTicks(Dome dome) {
		return (float) ((dome.maxRadius - START_RADIUS) / Shockwaves.SPEED);
	}

	/** The sphere cap as quads; eye is the camera relative to the dome's centre. */
	private static void mesh(PoseStack.Pose pose, VertexConsumer vc, float radius, float fade, Vec3 eye, int frame) {
		float cell = 1f / GRID;
		float fu = (frame % GRID) * cell, fv = (frame / GRID) * cell;
		for (int ring = 0; ring < RINGS; ring++) {
			double p0 = pitch(ring);
			double p1 = pitch(ring + 1);
			// Where this quad sits inside its texture tile, then inside this frame's cell.
			float v0 = fv + INSET + (cell - 2 * INSET) * (1f - (ring % TILE_RINGS) / (float) TILE_RINGS);
			float v1 = fv + INSET + (cell - 2 * INSET) * (1f - (ring % TILE_RINGS + 1) / (float) TILE_RINGS);
			for (int seg = 0; seg < SEGMENTS; seg++) {
				double y0 = seg * Math.PI * 2 / SEGMENTS;
				double y1 = (seg + 1) * Math.PI * 2 / SEGMENTS;
				float u0 = fu + INSET + (cell - 2 * INSET) * (seg % TILE_SEGS) / (float) TILE_SEGS;
				float u1 = fu + INSET + (cell - 2 * INSET) * (seg % TILE_SEGS + 1) / (float) TILE_SEGS;
				vertex(pose, vc, radius, fade, eye, y0, p0, u0, v0);
				vertex(pose, vc, radius, fade, eye, y0, p1, u0, v1);
				vertex(pose, vc, radius, fade, eye, y1, p1, u1, v1);
				vertex(pose, vc, radius, fade, eye, y1, p0, u1, v0);
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
			double yaw, double pitch, float u, float v) {
		float nx = (float) (Math.cos(yaw) * Math.cos(pitch));
		float ny = (float) Math.sin(pitch);
		float nz = (float) (Math.sin(yaw) * Math.cos(pitch));
		float x = nx * radius, y = ny * radius, z = nz * radius;
		// Edge-on glass looks thicker: the body is fairly solid cracked jade and the silhouette turns
		// bright. A band along the foot of the dome glows too, so the edge shows from inside as well.
		double vx = eye.x - x, vy = eye.y - y, vz = eye.z - z;
		double len = Math.max(1e-4, Math.sqrt(vx * vx + vy * vy + vz * vz));
		float facing = (float) Math.abs((vx * nx + vy * ny + vz * nz) / len);
		float rim = (float) Math.pow(1 - facing, 4);
		float foot = Math.max(0f, 1f - (y - (float) Math.sin(BOTTOM) * radius) / BAND);
		float glow = Math.min(1f, Math.max(rim, foot * foot));
		float alpha = fade * (0.85f + 0.15f * glow);
		vc.addVertex(pose, x, y, z)
				.setColor(mix(0, glow), mix(1, glow), mix(2, glow), alpha)
				.setUv(u, v)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(FULL_BRIGHT)
				.setNormal(pose, nx, ny, nz);
	}
}
