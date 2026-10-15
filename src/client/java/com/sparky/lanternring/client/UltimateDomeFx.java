package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.UltimateDome;
import com.sparky.lanternring.net.RingFxPayload;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.Vec3;

/**
 * The Green Lantern's ultimate dome (UltimateDome, J's pick D1 from Blender pass 835), drawn as one mesh of the
 * construct brick texture, 55% opaque and lit from within. The shell is revealed by the server's own fronts
 * (UltimateDome.topPolar / bottomPolar), snapped to whole blocks and whole ticks, so every spot pops in on the
 * tick its front reaches it, and a one-block band of saturated green rides each front. The beam up is the
 * ring's normal line (sent by the server as EMIT), so it follows J's laser pick when that lands.
 */
public final class UltimateDomeFx {
	/** The shell's quads are about this many blocks across, one texture tile each: bigger than on placed constructs, so the bricks still read (and don't shimmer) from 150 blocks away. */
	private static final double TILE = 12;
	private static final float ALPHA = 0.55f;
	/** Edge and apex colour (pass 835): saturated green, never white. */
	private static final float[] EDGE = {0.06f, 1f, 0.28f};
	/** The body's tint over the brick texture. */
	private static final float[] BODY = {0.75f, 1f, 0.8f};
	private static final int FLASH = 12;
	/** The dome's centre relative to the camera, and how far out it is drawn at most, for the dome being drawn. */
	private static Vec3 off = Vec3.ZERO;
	private static double reach = 96;

	private static final class Dome {
		final Vec3 center;
		final Corps corps;
		long started;
		int form;
		long brokeAt = -1;

		Dome(Vec3 center, Corps corps) {
			this.center = center;
			this.corps = corps;
		}
	}

	/** Keyed by centre, so a dome whose caster logged off still finishes. */
	private static final Map<Vec3, Dome> DOMES = new HashMap<>();

	private UltimateDomeFx() {
	}

	public static void register() {
		LevelRenderEvents.COLLECT_SUBMITS.register(UltimateDomeFx::submit);
	}

	static void handle(RingFxPayload fx) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		long now = mc.level.getGameTime();
		Dome d = DOMES.get(fx.from());
		if (fx.value() < 0) {
			if (d != null && d.brokeAt < 0) d.brokeAt = now;
			return;
		}
		if (d == null) {
			d = new Dome(fx.from(), fx.corps());
			DOMES.put(fx.from(), d);
		}
		d.started = now - (long) fx.value();
		d.form = Math.max(1, fx.variant());
	}

	private static void submit(LevelRenderContext ctx) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) {
			DOMES.clear();
			return;
		}
		if (DOMES.isEmpty()) return;
		long tick = mc.level.getGameTime();
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		for (Iterator<Dome> it = DOMES.values().iterator(); it.hasNext(); ) {
			Dome d = it.next();
			// Lost track of it (out of range when it ended): let it go after a while without news.
			if (d.brokeAt >= 0 && tick - d.brokeAt > UltimateDome.BREAK || tick - d.started > 20 * 60 * 20) it.remove();
		}
		TextureAtlasSprite brick = SuperLandConstruct.sprite(ModRegistry.CONSTRUCT_BRICK, Corps.GREEN);
		int light = ShaderGlow.light(0.9f);
		int edgeLight = ShaderGlow.light(1f);
		RandomSource r = mc.level.getRandom();
		for (Dome d : DOMES.values()) {
			long t = tick - d.started;
			if (t < UltimateDome.APEX) continue;
			double top = UltimateDome.topPolar(t, d.form);
			double bottom = UltimateDome.bottomPolar(t, d.form);
			// Coming apart, top first: everything above "gone" has broken off.
			double gone = d.brokeAt < 0 ? -1 : (tick - d.brokeAt) / (double) UltimateDome.BREAK * UltimateDome.MAX_POLAR;
			float[] body = CorpsTint.apply(d.corps, BODY[0], BODY[1], BODY[2]);
			float[] edge = CorpsTint.apply(d.corps, EDGE[0], EDGE[1], EDGE[2]);
			PoseStack pose = ctx.poseStack();
			Vec3 o = d.center.subtract(cam);
			// Past the fog the shell would fade into the sky, so far parts are drawn pulled in toward the camera
			// along their own line of sight: the same picture, just nearer (and still behind closer terrain).
			double far = Math.max(32, mc.options.getEffectiveRenderDistance() * 16 * 0.6);
			boolean forming = top < UltimateDome.MAX_POLAR;
			float flash = Math.max(0f, 1f - (t - UltimateDome.APEX) / (float) FLASH);
			ctx.submitNodeCollector().submitCustomGeometry(pose, RenderTypes.entityTranslucentEmissive(TextureAtlas.LOCATION_BLOCKS), (p, vc) -> {
				off = o;
				reach = far;
				double from = Math.max(0, gone);
				shell(p, vc, brick, from, Math.min(top, UltimateDome.MAX_POLAR), UltimateDome.RADIUS, body, ALPHA, light);
				if (bottom <= UltimateDome.MAX_POLAR) shell(p, vc, brick, Math.max(from, bottom), UltimateDome.MAX_POLAR, UltimateDome.RADIUS, body, ALPHA, light);
				double band = 1.0 / UltimateDome.RADIUS;
				float rr = UltimateDome.RADIUS + 0.08f;
				if (forming && gone < 0) {
					// One thin bright ring on each front, moved every tick with it.
					shell(p, vc, brick, Math.max(0, top - band), top, rr, edge, 0.95f, edgeLight);
					if (bottom <= UltimateDome.MAX_POLAR) shell(p, vc, brick, bottom, Math.min(UltimateDome.MAX_POLAR, bottom + band), rr, edge, 0.95f, edgeLight);
				}
				if (gone >= 0 && gone < UltimateDome.MAX_POLAR) {
					shell(p, vc, brick, gone, Math.min(UltimateDome.MAX_POLAR, gone + band), rr, edge, 0.95f, edgeLight);
				}
				// The apex flash where the beam hits the top.
				if (flash > 0) shell(p, vc, brick, 0, 6.0 / UltimateDome.RADIUS * (1 + flash), rr + 0.05f, edge, flash, edgeLight);
			});
			if (gone >= 0 && gone < UltimateDome.MAX_POLAR && !mc.isPaused()) shards(d, gone, r);
		}
	}

	/** Pieces breaking off along the line where the dome is coming apart, near the camera's side of it. */
	private static void shards(Dome d, double polar, RandomSource r) {
		Corps before = CorpsTint.enter(d.corps);
		try {
			for (int i = 0; i < 24; i++) {
				double yaw = r.nextDouble() * Math.PI * 2;
				Vec3 dir = new Vec3(Math.cos(yaw) * Math.sin(polar), Math.cos(polar), Math.sin(yaw) * Math.sin(polar));
				LabFx.spawn(ModParticles.SHARD, d.center.add(dir.scale(UltimateDome.RADIUS)), dir.scale(-0.05).add(0, -0.15, 0), 2.5f);
			}
		} finally {
			CorpsTint.restore(before);
		}
	}

	/** The part of the sphere between polar angles p0 and p1 (0 straight up), as tiles of the brick texture. */
	private static void shell(PoseStack.Pose pose, VertexConsumer vc, TextureAtlasSprite s, double p0, double p1, float radius,
			float[] c, float alpha, int light) {
		if (p1 <= p0) return;
		double step = TILE / radius;
		int first = (int) Math.floor(p0 / step), last = (int) Math.ceil(p1 / step);
		for (int ring = first; ring < last; ring++) {
			double a = Math.max(p0, ring * step), b = Math.min(p1, (ring + 1) * step);
			if (b <= a) continue;
			// Where the clipped band sits inside its tile, so a tile popping in shows only the part that's there.
			float va = (float) (a / step - ring), vb = (float) (b / step - ring);
			double mid = (ring + 0.5) * step;
			int segs = Math.max(8, (int) Math.ceil(2 * Math.PI * radius * Math.sin(Math.min(mid, Math.PI / 2)) / TILE));
			for (int seg = 0; seg < segs; seg++) {
				double y0 = seg * Math.PI * 2 / segs, y1 = (seg + 1) * Math.PI * 2 / segs;
				vertex(pose, vc, radius, y0, a, s.getU0(), Mth.lerp(va, s.getV0(), s.getV1()), c, alpha, light);
				vertex(pose, vc, radius, y0, b, s.getU0(), Mth.lerp(vb, s.getV0(), s.getV1()), c, alpha, light);
				vertex(pose, vc, radius, y1, b, s.getU1(), Mth.lerp(vb, s.getV0(), s.getV1()), c, alpha, light);
				vertex(pose, vc, radius, y1, a, s.getU1(), Mth.lerp(va, s.getV0(), s.getV1()), c, alpha, light);
			}
		}
	}

	private static void vertex(PoseStack.Pose pose, VertexConsumer vc, float radius, double yaw, double polar, float u, float v,
			float[] c, float alpha, int light) {
		float nx = (float) (Math.cos(yaw) * Math.sin(polar));
		float ny = (float) Math.cos(polar);
		float nz = (float) (Math.sin(yaw) * Math.sin(polar));
		double x = off.x + nx * radius, y = off.y + ny * radius, z = off.z + nz * radius;
		double dist = Math.sqrt(x * x + y * y + z * z);
		if (dist > reach) {
			double k = reach / dist;
			x *= k;
			y *= k;
			z *= k;
		}
		vc.addVertex(pose, (float) x, (float) y, (float) z)
				.setColor(c[0], c[1], c[2], alpha)
				.setUv(u, v)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(light)
				.setNormal(pose, nx, ny, nz);
	}
}
