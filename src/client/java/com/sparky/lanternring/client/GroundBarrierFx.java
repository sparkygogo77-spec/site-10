package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.net.RingFxPayload;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;

/**
 * Ground flight's running barrier meeting a wall (J's Blender pass 228). The barrier is an invisible
 * 3.5 block dome round the flyer; on impact it shows only where it touches the wall (the construct
 * texture fully there within 0.4 block of the face, gone by 1.6), its front flattens on the wall in a
 * dome-shaped crater, about 48 construct sparks burst out of the crater's rim along the wall and fall,
 * and the flattened patch stays on the wall as an imprint that fades over the Ring Lab's "Ground flight:
 * barrier imprint" time, starting a second after the hit. The dome springs back round and is gone again.
 * Everything is in the flyer's corps colour (the construct texture is grey, tinted per corps).
 */
public final class GroundBarrierFx {
	private static final Identifier TEXTURE = LanternRing.id("textures/entity/ground_barrier.png");
	private static final double RADIUS = FlightMoves.RADIUS;
	/** The barrier shows fully within NEAR of the wall face and fades out by FAR. */
	private static final double NEAR = 0.4, FAR = 1.6;
	/** The imprint starts fading this long after the hit. */
	private static final int IMPRINT_HOLD = 20;
	private static final int SPARKS = 48;
	private static final int RINGS = 18, SEGMENTS = 36;

	private static final class Hit {
		int flyer;
		Vec3 contact, normal, center;
		long start;
		MovePoseData.Halt halt;
		float depth;
		Corps corps;
	}

	private static final List<Hit> HITS = new ArrayList<>();

	private GroundBarrierFx() {
	}

	/** GROUND_HIT, while LabFx has the flyer's corps current. */
	static void handle(RingFxPayload fx) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		Vec3 n = fx.to().subtract(fx.from());
		if (n.lengthSqr() < 1e-6) return;
		MovePoseData.load();
		LabSettings.GroundHalt[] halts = LabSettings.GroundHalt.values();
		LabSettings.GroundHalt pick = halts[Mth.clamp(Math.round(fx.value()), 0, halts.length - 1)];
		MovePoses.hit(fx.variant(), pick);
		Hit h = new Hit();
		h.flyer = fx.variant();
		h.contact = fx.from();
		h.normal = n.normalize();
		h.start = mc.level.getGameTime();
		h.halt = MovePoseData.GROUND.get(pick);
		h.depth = h.halt == null ? 1.4f : h.halt.depth();
		h.corps = CorpsTint.current();
		Entity flyer = mc.level.getEntity(fx.variant());
		h.center = flyer != null ? middle(flyer, 1f) : h.contact.add(h.normal.scale(RADIUS));
		HITS.add(h);
		sparks(h);
		if (mc.player != null && mc.player.getId() == fx.variant()) RingShake.kick(1.4f);
	}

	private static Vec3 middle(Entity e, float partial) {
		return e.getPosition(partial).add(0, 0.6, 0);
	}

	/** The crater's rim on the wall at the deepest flattening: its middle and radius. */
	private static double rim(Hit h) {
		double in = Math.min(RADIUS, h.depth + Math.max(0, RADIUS - h.center.subtract(h.contact).dot(h.normal)));
		return Math.sqrt(Math.max(0.25, RADIUS * RADIUS - (RADIUS - in) * (RADIUS - in)));
	}

	private static Vec3 rimMiddle(Hit h) {
		double d = h.center.subtract(h.contact).dot(h.normal);
		return h.center.subtract(h.normal.scale(d)).add(h.normal.scale(0.05));
	}

	/** About 48 construct sparks burst out of the crater rim along the wall, fall and shrink out in 10-18 ticks. */
	private static void sparks(Hit h) {
		RandomSource r = Minecraft.getInstance().level.getRandom();
		Vec3[] b = basis(h.normal);
		Vec3 mid = rimMiddle(h);
		double radius = rim(h);
		for (int i = 0; i < LabFx.count(SPARKS); i++) {
			double a = r.nextDouble() * Math.PI * 2;
			Vec3 out = b[0].scale(Math.cos(a)).add(b[1].scale(Math.sin(a)));
			Vec3 at = mid.add(out.scale(radius * (0.85 + 0.2 * r.nextDouble())));
			Vec3 v = out.scale(0.15 + 0.2 * r.nextDouble()).add(h.normal.scale(0.05 + 0.1 * r.nextDouble())).add(0, 0.08, 0);
			ConstructParticle p = LabFx.spawn(i % 3 == 0 ? ModParticles.SPARK : ModParticles.SHARD, at, v, 0.9f);
			if (p != null) p.lasting(10 + r.nextInt(9));
		}
	}

	static void tick(Minecraft mc) {
		if (mc.level == null) {
			HITS.clear();
			return;
		}
		long now = mc.level.getGameTime();
		int life = IMPRINT_HOLD + Math.max(1, RingTuning.GROUND_IMPRINT.ticks());
		HITS.removeIf(h -> now - h.start > Math.max(life, 40));
	}

	public static void render(LevelRenderContext ctx) {
		if (HITS.isEmpty()) return;
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float partial = ctx.levelState().worldPartialTicks;
		float now = mc.level.getGameTime() + partial;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		float fade = Math.max(1, RingTuning.GROUND_IMPRINT.ticks());
		for (Hit h : HITS) {
			float age = now - h.start;
			float r = h.corps.red(), g = h.corps.green(), b = h.corps.blue();
			// The imprint left on the wall.
			float imprint = age < IMPRINT_HOLD ? 1f : 1f - (age - IMPRINT_HOLD) / fade;
			if (imprint > 0) {
				Vec3 mid = rimMiddle(h).subtract(cam);
				double radius = rim(h);
				Vec3[] basis = basis(h.normal);
				float a = 0.85f * imprint * Math.min(1f, age / 3f);
				ctx.submitNodeCollector().submitCustomGeometry(ctx.poseStack(), RenderTypes.entityTranslucentEmissive(TEXTURE),
						(pose, vc) -> imprint(pose, vc, mid, basis, radius, r, g, b, a));
			}
			// The dome, while the take's alpha says it shows.
			if (h.halt == null) continue;
			float index = h.halt.hit() + age;
			if (index >= h.halt.ticks().length - 1) continue;
			MovePoseData.Tick t0 = h.halt.ticks()[Mth.floor(index)], t1 = h.halt.ticks()[Mth.floor(index) + 1];
			float f = index - Mth.floor(index);
			float alpha = Mth.lerp(f, t0.alpha(), t1.alpha());
			float squash = Mth.lerp(f, t0.squash(), t1.squash());
			if (alpha <= 0.01f) continue;
			Entity flyer = mc.level.getEntity(h.flyer);
			Vec3 center = (flyer != null ? middle(flyer, partial) : h.center).subtract(cam);
			Vec3 plane = h.contact.subtract(cam);
			// How flat the front is pressed: fully while the take squashes it, springing back round as it eases off.
			float flat = Mth.clamp(squash / Math.max(0.2f, h.depth * 0.5f), 0f, 1f);
			float frame = now * 0.5f;
			ctx.submitNodeCollector().submitCustomGeometry(ctx.poseStack(), RenderTypes.entityTranslucentEmissive(TEXTURE),
					(pose, vc) -> dome(pose, vc, center, plane, h.normal, flat, alpha, frame, r, g, b));
		}
	}

	/** The dome, pressed flat where it meets the wall, showing only near the wall face. */
	private static void dome(PoseStack.Pose pose, VertexConsumer vc, Vec3 center, Vec3 plane, Vec3 n, float flat, float alpha,
			float scroll, float r, float g, float b) {
		Vec3[] grid = new Vec3[(RINGS + 1) * (SEGMENTS + 1)];
		float[] shown = new float[grid.length];
		for (int i = 0; i <= RINGS; i++) {
			double theta = Math.PI * i / RINGS;
			for (int k = 0; k <= SEGMENTS; k++) {
				double phi = Math.PI * 2 * k / SEGMENTS;
				Vec3 dir = new Vec3(Math.sin(theta) * Math.cos(phi), Math.cos(theta), Math.sin(theta) * Math.sin(phi));
				Vec3 p = center.add(dir.scale(RADIUS));
				double s = p.subtract(plane).dot(n);
				if (s < 0) p = p.subtract(n.scale(s * flat));
				double after = Math.max(0, p.subtract(plane).dot(n));
				int at = i * (SEGMENTS + 1) + k;
				grid[at] = p;
				shown[at] = alpha * (1f - smoothstep((float) NEAR, (float) FAR, (float) after));
			}
		}
		for (int i = 0; i < RINGS; i++) {
			for (int k = 0; k < SEGMENTS; k++) {
				int a = i * (SEGMENTS + 1) + k, c = a + SEGMENTS + 1;
				if (shown[a] < 0.01f && shown[a + 1] < 0.01f && shown[c] < 0.01f && shown[c + 1] < 0.01f) continue;
				float u0 = k * 4f / SEGMENTS, u1 = (k + 1) * 4f / SEGMENTS;
				float v0 = i * 2f / RINGS + scroll * 0.02f, v1 = (i + 1) * 2f / RINGS + scroll * 0.02f;
				vertex(pose, vc, grid[a], u0, v0, r, g, b, shown[a], n);
				vertex(pose, vc, grid[c], u0, v1, r, g, b, shown[c], n);
				vertex(pose, vc, grid[c + 1], u1, v1, r, g, b, shown[c + 1], n);
				vertex(pose, vc, grid[a + 1], u1, v0, r, g, b, shown[a + 1], n);
				// And from inside, so the flyer sees it pressed on the wall too.
				vertex(pose, vc, grid[a + 1], u1, v0, r, g, b, shown[a + 1], n);
				vertex(pose, vc, grid[c + 1], u1, v1, r, g, b, shown[c + 1], n);
				vertex(pose, vc, grid[c], u0, v1, r, g, b, shown[c], n);
				vertex(pose, vc, grid[a], u0, v0, r, g, b, shown[a], n);
			}
		}
	}

	/** The imprint: an ellipse of construct light on the wall face, softer toward its edge. */
	private static void imprint(PoseStack.Pose pose, VertexConsumer vc, Vec3 mid, Vec3[] basis, double radius,
			float r, float g, float b, float a) {
		int n = 32;
		double wide = radius, high = radius * 0.8;
		for (int k = 0; k < n; k++) {
			double a0 = Math.PI * 2 * k / n, a1 = Math.PI * 2 * (k + 1) / n;
			Vec3 p0 = mid.add(basis[0].scale(Math.cos(a0) * wide)).add(basis[1].scale(Math.sin(a0) * high));
			Vec3 p1 = mid.add(basis[0].scale(Math.cos(a1) * wide)).add(basis[1].scale(Math.sin(a1) * high));
			float u0 = 0.5f + 0.5f * (float) Math.cos(a0), w0 = 0.5f + 0.5f * (float) Math.sin(a0);
			float u1 = 0.5f + 0.5f * (float) Math.cos(a1), w1 = 0.5f + 0.5f * (float) Math.sin(a1);
			vertex(pose, vc, mid, 0.5f, 0.5f, r, g, b, a * 0.6f, basis[2]);
			vertex(pose, vc, p0, u0, w0, r, g, b, a, basis[2]);
			vertex(pose, vc, p1, u1, w1, r, g, b, a, basis[2]);
			vertex(pose, vc, mid, 0.5f, 0.5f, r, g, b, a * 0.6f, basis[2]);
		}
	}

	private static void vertex(PoseStack.Pose pose, VertexConsumer vc, Vec3 p, float u, float v, float r, float g, float b, float a, Vec3 n) {
		vc.addVertex(pose, (float) p.x, (float) p.y, (float) p.z)
				.setColor(Mth.lerp(0.2f, r, 1f), Mth.lerp(0.2f, g, 1f), Mth.lerp(0.2f, b, 1f), a)
				.setUv(u, v)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(ShaderGlow.light(0.8f))
				.setNormal(pose, (float) n.x, (float) n.y, (float) n.z);
	}

	/** Across the wall (sideways, up) and out of it, for a face whose normal is n. */
	private static Vec3[] basis(Vec3 n) {
		Vec3 up = Math.abs(n.y) > 0.95 ? new Vec3(1, 0, 0) : new Vec3(0, 1, 0);
		Vec3 side = up.cross(n).normalize();
		return new Vec3[] {side, n.cross(side).normalize(), n};
	}

	private static float smoothstep(float a, float b, float x) {
		float t = Mth.clamp((x - a) / (b - a), 0f, 1f);
		return t * t * (3 - 2 * t);
	}
}
