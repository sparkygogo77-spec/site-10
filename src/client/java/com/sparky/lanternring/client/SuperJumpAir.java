package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

/**
 * A super jump in the air, for every jumper (J's Blender picks, passes 85-86). Rising, a thin jade
 * ribbon (R1, the shortest) streams off the ring fist, locked to it: a point every quarter tick
 * exactly where the fist is, at full strength at once, each lasting 2 ticks and fading over about
 * one more. Falling, the build-up to the landing: the ring's light climbs from low at the top to
 * bright just before touchdown (Blender 20 + 150 u^2.2 over the fall's fraction u, see
 * SuperJumpFx), and a soft glow round the fist grows from 1.5 to 5 px, its pulse quickening from
 * every 8 ticks to every 2, into the touchdown flare.
 */
public final class SuperJumpAir {
	private static final Identifier TRAIL = LanternRing.id("textures/entity/flight_trail.png");
	private static final Identifier GLOW = LanternRing.id("textures/entity/sun_core.png");
	/** Ticks between ribbon points, a point's full life, and its fade at the end of it. */
	private static final float STEP = 0.25f, LIVE = 2f, FADE = 1f;
	/** The ribbon's width, about a pixel. */
	private static final float WIDTH = 0.06f;
	/** The fist glow's radius at the top of the fall and at touchdown (5 px), and its pulse period there (ticks). */
	private static final float GLOW_FROM = 1.5f / 16, GLOW_TO = 5f / 16, PULSE_FROM = 8, PULSE_TO = 2;
	private static final int SEGMENTS = 16;

	private record Point(Vec3 pos, float time) {
	}

	private static final class Air {
		final ArrayDeque<Point> trail = new ArrayDeque<>();
		double topY = Double.NEGATIVE_INFINITY, groundY;
		boolean falling;
		/** 0..1 through the fall, and the glow's pulse phase. */
		float fall, phase;
		Corps corps = Corps.GREEN;
		int lastSeen;
	}

	private static final Int2ObjectMap<Air> AIR = new Int2ObjectOpenHashMap<>();
	private static int clock;

	private SuperJumpAir() {
	}

	/** 0..1: how far through the fall from the top of the jump this player is, or -1 when not falling on one. */
	static float fall(int id) {
		Air a = AIR.get(id);
		return a == null || !a.falling ? -1f : a.fall;
	}

	/** Whether this player is on the way up a super jump. */
	static boolean rising(int id) {
		Air a = AIR.get(id);
		return a != null && !a.falling && SuperJumpPoses.airborne(id);
	}

	static void tick(Minecraft mc) {
		if (mc.level == null) {
			AIR.clear();
			return;
		}
		if (mc.isPaused()) return;
		clock++;
		for (Player p : mc.level.players()) {
			if (!SuperJumpPoses.airborne(p.getId()) || p.onGround()) continue;
			Air a = AIR.computeIfAbsent(p.getId(), k -> new Air());
			a.lastSeen = clock;
			a.corps = Corps.held(p);
			if (p.getY() > a.topY) a.topY = p.getY();
			double vy = p.getY() - p.yo;
			if (!a.falling && vy < 0 && p.getY() < a.topY - 0.05) a.falling = true;
			if (a.falling) {
				a.groundY = mc.level.getHeight(Heightmap.Types.MOTION_BLOCKING, p.getBlockX(), p.getBlockZ());
				double span = a.topY - a.groundY;
				a.fall = span <= 0.5 ? 1f : Mth.clamp((float) ((a.topY - p.getY()) / span), 0f, 1f);
				a.phase += Mth.TWO_PI / Mth.lerp(a.fall, PULSE_FROM, PULSE_TO);
			}
		}
		// A jump that has landed keeps its ribbon until the last point fades.
		AIR.int2ObjectEntrySet().removeIf(e -> clock - e.getValue().lastSeen > LIVE + FADE + 2);
	}

	public static void render(LevelRenderContext ctx) {
		if (AIR.isEmpty()) return;
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float partial = ctx.levelState().worldPartialTicks;
		float now = clock + partial;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		boolean ribbons = false;
		for (Int2ObjectMap.Entry<Air> e : AIR.int2ObjectEntrySet()) {
			Air a = e.getValue();
			Player p = mc.level.getEntity(e.getIntKey()) instanceof Player pl ? pl : null;
			Vec3 fist = p == null ? null : fist(p, partial);
			boolean rising = p != null && !a.falling && SuperJumpPoses.airborne(e.getIntKey());
			if (rising && fist != null && (a.trail.isEmpty() || now - a.trail.peekLast().time >= STEP)) a.trail.add(new Point(fist, now));
			while (!a.trail.isEmpty() && now - a.trail.peekFirst().time > LIVE + FADE) a.trail.pollFirst();
			ribbons |= !a.trail.isEmpty();
		}
		if (ribbons) {
			ctx.submitNodeCollector().submitCustomGeometry(ctx.poseStack(), RenderTypes.entityTranslucentEmissive(TRAIL), (pose, vc) -> {
				for (Int2ObjectMap.Entry<Air> e : AIR.int2ObjectEntrySet()) {
					Air a = e.getValue();
					if (a.trail.size() < 1) continue;
					Player p = mc.level.getEntity(e.getIntKey()) instanceof Player pl ? pl : null;
					List<Point> pts = new ArrayList<>(a.trail);
					// The head is where the fist is this frame, so the ribbon never lags it.
					Vec3 head = p != null && rising(e.getIntKey()) ? fist(p, partial) : null;
					if (head != null) pts.add(new Point(head, now));
					float[] c = CorpsTint.apply(a.corps, 0.35f, 1f, 0.55f);
					for (int i = 0; i + 1 < pts.size(); i++) segment(pose, vc, pts.get(i), pts.get(i + 1), cam, now, c);
				}
			});
		}
		ctx.submitNodeCollector().submitCustomGeometry(ctx.poseStack(), RenderTypes.entityTranslucentEmissive(GLOW), (pose, vc) -> {
			for (Int2ObjectMap.Entry<Air> e : AIR.int2ObjectEntrySet()) {
				Air a = e.getValue();
				if (!a.falling || !SuperJumpPoses.airborne(e.getIntKey())) continue;
				if (!(mc.level.getEntity(e.getIntKey()) instanceof Player p)) continue;
				// Your own glow in first person would sit over your view; the ring's own light carries it there.
				if (p == mc.player && mc.options.getCameraType().isFirstPerson()) continue;
				Vec3 fist = fist(p, partial);
				float pulse = 0.75f + 0.25f * Mth.sin(a.phase + partial * Mth.TWO_PI / Mth.lerp(a.fall, PULSE_FROM, PULSE_TO));
				float radius = Mth.lerp(a.fall, GLOW_FROM, GLOW_TO) * pulse;
				float[] c = CorpsTint.apply(a.corps, 0.4f, 1f, 0.6f);
				glow(pose, vc, fist, cam, radius, c, (0.35f + 0.45f * a.fall) * pulse);
			}
		});
	}

	private static Vec3 fist(Player p, float partial) {
		Vec3 posed = p == Minecraft.getInstance().player && Minecraft.getInstance().options.getCameraType().isFirstPerson() ? null
				: SuperJumpPoses.fist(p, partial);
		return posed != null ? posed : RingEmit.ringNow(p, partial);
	}

	private static float strength(Point p, float now) {
		float age = now - p.time;
		return age <= LIVE ? 1f : Mth.clamp(1f - (age - LIVE) / FADE, 0f, 1f);
	}

	/** One piece of the ribbon: a camera-facing strip about a pixel wide between two points. */
	private static void segment(PoseStack.Pose pose, VertexConsumer vc, Point a, Point b, Vec3 cam, float now, float[] c) {
		Vec3 along = b.pos.subtract(a.pos);
		if (along.lengthSqr() < 1e-8) return;
		Vec3 side = along.cross(cam.subtract(b.pos));
		if (side.lengthSqr() < 1e-10) return;
		side = side.normalize().scale(WIDTH / 2);
		float sa = strength(a, now), sb = strength(b, now);
		if (sa <= 0 && sb <= 0) return;
		int light = ShaderGlow.light(0.55f);
		vertex(pose, vc, a.pos.subtract(side), cam, 0, 1, c, sa, light);
		vertex(pose, vc, a.pos.add(side), cam, 0, 0, c, sa, light);
		vertex(pose, vc, b.pos.add(side), cam, 1, 0, c, sb, light);
		vertex(pose, vc, b.pos.subtract(side), cam, 1, 1, c, sb, light);
	}

	/** A soft disc facing the camera: bright in the middle, nothing at its edge. */
	private static void glow(PoseStack.Pose pose, VertexConsumer vc, Vec3 at, Vec3 cam, float radius, float[] c, float alpha) {
		Vec3 view = at.subtract(cam).normalize();
		Vec3 up = Math.abs(view.y) > 0.95 ? new Vec3(1, 0, 0) : new Vec3(0, 1, 0);
		Vec3 r = view.cross(up).normalize(), u = r.cross(view).normalize();
		int light = ShaderGlow.light(0.6f);
		for (int i = 0; i < SEGMENTS; i++) {
			double a0 = i * Mth.TWO_PI / SEGMENTS, a1 = (i + 1) * Mth.TWO_PI / SEGMENTS;
			Vec3 p0 = at.add(r.scale(Math.cos(a0) * radius)).add(u.scale(Math.sin(a0) * radius));
			Vec3 p1 = at.add(r.scale(Math.cos(a1) * radius)).add(u.scale(Math.sin(a1) * radius));
			vertex(pose, vc, at, cam, 0.5f, 0.5f, c, alpha, light);
			vertex(pose, vc, at, cam, 0.5f, 0.5f, c, alpha, light);
			vertex(pose, vc, p0, cam, 0.5f, 0.5f, c, 0f, light);
			vertex(pose, vc, p1, cam, 0.5f, 0.5f, c, 0f, light);
		}
	}

	private static void vertex(PoseStack.Pose pose, VertexConsumer vc, Vec3 p, Vec3 cam, float u, float v, float[] c, float alpha, int light) {
		vc.addVertex(pose, (float) (p.x - cam.x), (float) (p.y - cam.y), (float) (p.z - cam.z))
				.setColor(c[0], c[1], c[2], alpha)
				.setUv(u, v)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(light)
				.setNormal(pose, 0, 1, 0);
	}
}
