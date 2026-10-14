package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.Saws;
import com.sparky.lanternring.net.RingFxPayload;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.Vec3;

/**
 * Draws the Saw ({@link Saws}): a big upright disc of hard light, half sunk in the ground, in the
 * bearer's corps colour. A see-through body with a bright hub, curved spokes, an inner ring and a
 * rim of hooked teeth; it spins forward (the top running the way it rolls) while left-click is
 * held and winds down when it is let go. Sparks fly off its teeth where it bites the ground.
 * The server re-sends it every tick (SAW); a saw not heard from in STALE ticks is dropped.
 */
public final class SawFx {
	private static final Identifier GLASS = LanternRing.id("textures/entity/shockwave_glass.png");
	private static final float FADE_IN = 6f;
	private static final float FADE_OUT = 8f;
	private static final int STALE = 20;
	/** Spin while left-click is held, in radians a tick, and how quickly it spins up and winds down. */
	private static final float SPIN = 0.55f;
	private static final float SPIN_UP = 0.06f;
	private static final float SPIN_DOWN = 0.025f;
	private static final int TEETH = 28;
	private static final int SEGMENTS = TEETH * 2;
	private static final double HALF_WIDTH = 0.28;
	private static final int FRAMES = 64;
	private static final int GRID = 8;
	private static final int FRAME_TICKS = 2;

	private static final class Saw {
		Vec3 prev;
		Vec3 cur;
		Vec3 dir = new Vec3(0, 0, 1);
		Corps corps;
		boolean spinning;
		boolean up = true;
		int lastSeen;
		float shown;
		float speed;
		float angle;
		float prevAngle;
	}

	private static final Int2ObjectMap<Saw> SAWS = new Int2ObjectOpenHashMap<>();
	private static int clock;

	private SawFx() {
	}

	/** SAW, while LabFx has the effect's corps current. */
	static void handle(RingFxPayload fx) {
		Saw s = SAWS.get(fx.variant());
		if (fx.value() < 0) {
			if (s != null) {
				s.up = false;
				LabFx.burst(s.cur, 70, 0.35);
			}
			return;
		}
		if (s == null) {
			SAWS.put(fx.variant(), s = new Saw());
			s.prev = s.cur = fx.from();
		}
		s.prev = s.cur;
		s.cur = fx.from();
		Vec3 d = fx.to().subtract(fx.from());
		if (d.lengthSqr() > 1e-4) s.dir = d.normalize();
		s.spinning = fx.value() > 0.5f;
		s.corps = CorpsTint.current();
		s.lastSeen = clock;
		s.up = true;
	}

	static void tick(Minecraft mc) {
		if (mc.level == null) {
			SAWS.clear();
			return;
		}
		if (mc.isPaused()) return;
		clock++;
		RandomSource r = mc.level.getRandom();
		var it = SAWS.values().iterator();
		while (it.hasNext()) {
			Saw s = it.next();
			if (clock - s.lastSeen > STALE) s.up = false;
			s.shown = s.up ? Math.min(1f, s.shown + 1f / FADE_IN) : s.shown - 1f / FADE_OUT;
			if (s.shown <= 0) {
				it.remove();
				continue;
			}
			s.speed = s.spinning && s.up ? Math.min(SPIN, s.speed + SPIN_UP) : Math.max(0f, s.speed - SPIN_DOWN);
			s.prevAngle = s.angle;
			// Rolling forward: the top runs the way it goes.
			s.angle -= s.speed;
			if (s.speed > 0.15f) {
				Corps before = CorpsTint.enter(s.corps);
				try {
					// Sparks thrown up and back off the teeth where they bite the ground.
					Vec3 bite = s.cur.add(s.dir.scale(Saws.RADIUS * 0.92)).add(0, 0.15, 0);
					for (int i = 0; i < LabFx.count(3 * s.speed / SPIN); i++) {
						Vec3 v = s.dir.scale(-0.15 - r.nextDouble() * 0.25).add(0, 0.25 + r.nextDouble() * 0.3, 0).add(LabFx.jitter(r, 0.08));
						LabFx.spawn(i % 3 == 0 ? ModParticles.SHARD : ModParticles.MOTE, bite.add(LabFx.jitter(r, 0.3)), v);
					}
				} finally {
					CorpsTint.restore(before);
				}
			}
		}
	}

	public static void render(LevelRenderContext ctx) {
		if (SAWS.isEmpty()) return;
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float partial = ctx.levelState().worldPartialTicks;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		float now = mc.level.getGameTime() + partial;
		int frame = Math.floorMod((int) (now / FRAME_TICKS), FRAMES);
		for (Saw s : SAWS.values()) {
			float fade = Mth.clamp(s.shown + (s.up ? partial / FADE_IN : -partial / FADE_OUT), 0f, 1f);
			if (fade <= 0) continue;
			Vec3 mid = s.prev.lerp(s.cur, partial);
			float angle = Mth.lerp(partial, s.prevAngle, s.angle);
			float blur = s.speed / SPIN;
			PoseStack pose = ctx.poseStack();
			pose.pushPose();
			pose.translate(mid.x - cam.x, mid.y - cam.y, mid.z - cam.z);
			RenderType glass = RenderTypes.entityTranslucentEmissive(CorpsTint.texture(GLASS, s.corps));
			Vec3 fwd = s.dir;
			Vec3 side = new Vec3(-fwd.z, 0, fwd.x);
			ctx.submitNodeCollector().submitCustomGeometry(pose, glass, (p, vc) -> disc(p, vc, fwd, side, angle, fade, blur, frame));
			pose.popPose();
		}
	}

	/** A point on the disc at radius r and angle a (0 = straight ahead), w across its thickness. */
	private static Vec3 at(Vec3 fwd, Vec3 side, double r, double a, double w) {
		return fwd.scale(r * Math.cos(a)).add(0, r * Math.sin(a), 0).add(side.scale(w));
	}

	/** The rim's radius at segment i: every other segment is a tooth's tip, hooked forward. */
	private static double rim(int i) {
		return i % 2 == 0 ? Saws.RADIUS + 0.45 : Saws.RADIUS - 0.05;
	}

	private static void disc(PoseStack.Pose pose, VertexConsumer vc, Vec3 fwd, Vec3 side, float spin, float fade, float blur, int frame) {
		float cell = 1f / GRID;
		float fu = (frame % GRID) * cell, fv = (frame / GRID) * cell;
		double step = Math.PI * 2 / SEGMENTS;
		double r = Saws.RADIUS;
		for (int face = -1; face <= 1; face += 2) {
			double w = face * HALF_WIDTH;
			Vec3 n = side.scale(face);
			for (int i = 0; i < SEGMENTS; i++) {
				// Teeth lean back against the spin, like a real blade's hooks.
				double a0 = spin + i * step + (i % 2 == 0 ? -step * 0.45 : 0), a1 = spin + (i + 1) * step + ((i + 1) % 2 == 0 ? -step * 0.45 : 0);
				float u0 = fu + cell * (i % 4) / 4f, u1 = fu + cell * (i % 4 + 1) / 4f;
				// The body: faint see-through glass from the hub out to the inner ring, brighter in its outer band.
				quad(pose, vc, n, at(fwd, side, r * 0.18, a0, w), at(fwd, side, r * 0.18, a1, w), at(fwd, side, r * 0.62, a1, w), at(fwd, side, r * 0.62, a0, w),
						u0, fv, u1, fv + cell * 0.5f, 0.75f, 0.85f, 0.8f, fade * (0.16f + 0.1f * blur), 0.55f);
				quad(pose, vc, n, at(fwd, side, r * 0.62, a0, w), at(fwd, side, r * 0.62, a1, w), at(fwd, side, r * 0.7, a1, w), at(fwd, side, r * 0.7, a0, w),
						u0, fv, u1, fv + cell * 0.25f, 0.95f, 1f, 0.95f, fade * 0.85f, 1f);
				quad(pose, vc, n, at(fwd, side, r * 0.7, a0, w), at(fwd, side, r * 0.7, a1, w), at(fwd, side, r * 0.86, a1, w), at(fwd, side, r * 0.86, a0, w),
						u0, fv, u1, fv + cell * 0.5f, 0.8f, 0.9f, 0.85f, fade * (0.3f + 0.15f * blur), 0.7f);
				// The toothed rim: bright, the tips brightest.
				quad(pose, vc, n, at(fwd, side, r * 0.86, a0, w), at(fwd, side, r * 0.86, a1, w), at(fwd, side, rim(i + 1), a1, w), at(fwd, side, rim(i), a0, w),
						u0, fv, u1, fv + cell, 0.95f, 1f, 0.95f, fade * 0.9f, 1f);
			}
			// Six curved spokes from the hub to the inner ring, so the spin reads.
			for (int k = 0; k < 6; k++) {
				double base = spin + k * Math.PI / 3;
				for (int j = 0; j < 4; j++) {
					double t0 = j / 4.0, t1 = (j + 1) / 4.0;
					double r0 = Mth.lerp(t0, r * 0.18, r * 0.62), r1 = Mth.lerp(t1, r * 0.18, r * 0.62);
					double b0 = base + t0 * 0.6, b1 = base + t1 * 0.6;
					double h0 = 0.09 / Math.max(0.3, r0 / r), h1 = 0.09 / Math.max(0.3, r1 / r);
					double ws = w + face * 0.01;
					quad(pose, vc, n, at(fwd, side, r0, b0 - h0, ws), at(fwd, side, r1, b1 - h1, ws), at(fwd, side, r1, b1 + h1, ws), at(fwd, side, r0, b0 + h0, ws),
							fu, fv, fu + cell * 0.25f, fv + cell * 0.25f, 0.9f, 1f, 0.92f, fade * (0.9f - 0.4f * blur), 1f);
				}
			}
			// The hub: a solid bright boss.
			for (int i = 0; i < 12; i++) {
				double a0 = spin + i * Math.PI / 6, a1 = spin + (i + 1) * Math.PI / 6;
				double ws = w + face * 0.03;
				quad(pose, vc, n, at(fwd, side, 0, a0, ws), at(fwd, side, 0, a1, ws), at(fwd, side, r * 0.18, a1, ws), at(fwd, side, r * 0.18, a0, ws),
						fu, fv, fu + cell * 0.25f, fv + cell * 0.25f, 1f, 1f, 1f, fade, 1f);
			}
		}
		// The rim's edge, joining the two faces round the teeth.
		for (int i = 0; i < SEGMENTS; i++) {
			double a0 = spin + i * step + (i % 2 == 0 ? -step * 0.45 : 0), a1 = spin + (i + 1) * step + ((i + 1) % 2 == 0 ? -step * 0.45 : 0);
			Vec3 mid = at(fwd, side, Saws.RADIUS, (a0 + a1) / 2, 0).normalize();
			quad(pose, vc, mid, at(fwd, side, rim(i), a0, -HALF_WIDTH), at(fwd, side, rim(i + 1), a1, -HALF_WIDTH), at(fwd, side, rim(i + 1), a1, HALF_WIDTH),
					at(fwd, side, rim(i), a0, HALF_WIDTH), fu, fv, fu + cell * 0.25f, fv + cell, 0.95f, 1f, 0.95f, fade * 0.9f, 1f);
		}
	}

	private static void quad(PoseStack.Pose pose, VertexConsumer vc, Vec3 n, Vec3 a, Vec3 b, Vec3 c, Vec3 d,
			float u0, float v0, float u1, float v1, float red, float green, float blue, float alpha, float glow) {
		vertex(pose, vc, n, a, u0, v0, red, green, blue, alpha, glow);
		vertex(pose, vc, n, b, u1, v0, red, green, blue, alpha, glow);
		vertex(pose, vc, n, c, u1, v1, red, green, blue, alpha, glow);
		vertex(pose, vc, n, d, u0, v1, red, green, blue, alpha, glow);
	}

	private static void vertex(PoseStack.Pose pose, VertexConsumer vc, Vec3 n, Vec3 p, float u, float v,
			float red, float green, float blue, float alpha, float glow) {
		vc.addVertex(pose, (float) p.x, (float) p.y, (float) p.z)
				.setColor(red, green, blue, alpha)
				.setUv(u, v)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(ShaderGlow.light(glow))
				.setNormal(pose, (float) n.x, (float) n.y, (float) n.z);
	}
}
