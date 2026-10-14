package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingTuning;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/**
 * J's flight trail T4 (Blender pass 218): a thin ribbon "made out of light" off the ring hand in the
 * fast glide, in the ring's corps colour, its braided light scrolling along it; wind streaks past the
 * flyer above 0.8 blocks a tick, and a ring of light at 1.1 (the sonic boom replaces it at the moment it
 * goes off). J: "I should be able to see the line but it's more for other players based on how fast it
 * is": width, length and brightness grow with speed, from nothing at 0.3 blocks a tick to full at 1.5,
 * and your own is drawn at about 35% in first person and fades before it crosses your view. The Ring
 * Lab's "Flight trail fade" duration is how long the ribbon lasts at full speed.
 */
public final class FlightTrail {
	private static final Identifier TEXTURE = LanternRing.id("textures/entity/flight_trail_light.png");
	/** 16 frames of 64 x 64 down the texture, scrolling along the ribbon. */
	private static final int FRAMES = 16;
	/** Speeds (blocks a tick): nothing below MIN, full at FULL; wind streaks above WIND, speed rings above RING. */
	private static final double MIN = 0.3, FULL = 1.5, WIND = 0.8, RING = 1.1;
	private static final float MAX_HALF_WIDTH = 0.22f;
	/** Your own trail in first person. */
	private static final float OWN = 0.35f;
	/** Ticks between speed rings, and how long each lasts. */
	private static final int RING_EVERY = 8, RING_LIFE = 8;
	private static final int STREAK_LIFE = 6;
	private static final int NO_OVERLAY = 0xA0000;

	private record Point(Vec3 pos, int tick, float speed) {
	}

	private record Streak(Vec3 pos, Vec3 back, float length, int tick) {
	}

	private record SpeedRing(Vec3 pos, Vec3 dir, int tick, Corps corps) {
	}

	private static final class Trail {
		final ArrayDeque<Point> points = new ArrayDeque<>();
		Corps corps = Corps.GREEN;
		float speed;
		int nextRing;
		boolean seen;
	}

	private static final Int2ObjectMap<Trail> TRAILS = new Int2ObjectOpenHashMap<>();
	private static final List<Streak> STREAKS = new ArrayList<>();
	private static final List<SpeedRing> RINGS = new ArrayList<>();
	private static int clock;

	private FlightTrail() {
	}

	/** 0..1: how much trail this speed makes. */
	private static float amount(double speed) {
		return (float) Mth.clamp((speed - MIN) / (FULL - MIN), 0, 1);
	}

	static void tick(Minecraft mc) {
		if (mc.level == null) {
			TRAILS.clear();
			STREAKS.clear();
			RINGS.clear();
			return;
		}
		clock++;
		int life = Math.max(1, RingTuning.FLIGHT_TRAIL.ticks());
		RandomSource r = mc.level.getRandom();
		long time = mc.level.getGameTime();
		for (Trail t : TRAILS.values()) t.seen = false;
		for (AbstractClientPlayer p : mc.level.players()) {
			Vec3 now = p.position();
			Vec3 move = now.subtract(p.xo, p.yo, p.zo);
			double speed = move.length();
			Trail t = TRAILS.get(p.getId());
			boolean gliding = FlightPoses.fast(p) > 0.5f && speed > MIN;
			if (gliding) {
				if (t == null) TRAILS.put(p.getId(), t = new Trail());
				t.corps = ringCorps(p);
				t.speed = amount(speed);
				Vec3 fist = MovePoses.fist(p, 1f);
				t.points.addFirst(new Point(fist != null ? fist : now.add(0, 0.9, 0), clock, t.speed));
				Vec3 dir = move.normalize();
				// Wind streaking past the body.
				if (speed > WIND) {
					for (int i = 0; i < 2; i++) {
						Vec3 side = randomPerp(dir, r).scale(0.6 + r.nextDouble() * 0.7);
						STREAKS.add(new Streak(now.add(0, 0.9, 0).add(side).add(dir.scale(r.nextDouble() * 1.5)), dir.scale(-1),
								(float) (1.2 + speed * 1.5 * r.nextDouble()), clock));
					}
				}
				// A ring of light every so often at speed (the sonic boom's own ring takes its place).
				if (speed > RING && --t.nextRing <= 0 && !SonicBoom.recent(p.getId(), time)) {
					t.nextRing = RING_EVERY;
					RINGS.add(new SpeedRing(now.add(0, 0.9, 0), dir, clock, t.corps));
				}
			}
			if (t == null) continue;
			// Faster leaves a longer ribbon: a third of the fade time at the slowest, all of it at full speed.
			float keep = life * (0.35f + 0.65f * t.speed);
			while (!t.points.isEmpty() && clock - t.points.peekLast().tick() > keep) t.points.removeLast();
			t.seen = !t.points.isEmpty();
		}
		TRAILS.values().removeIf(t -> !t.seen);
		STREAKS.removeIf(s -> clock - s.tick > STREAK_LIFE);
		RINGS.removeIf(s -> clock - s.tick > RING_LIFE);
	}

	private static Vec3 randomPerp(Vec3 dir, RandomSource r) {
		Vec3 up = Math.abs(dir.y) > 0.95 ? new Vec3(1, 0, 0) : new Vec3(0, 1, 0);
		Vec3 a = dir.cross(up).normalize(), b = a.cross(dir).normalize();
		double ang = r.nextDouble() * Math.PI * 2;
		return a.scale(Math.cos(ang)).add(b.scale(Math.sin(ang)));
	}

	private static Corps ringCorps(Player p) {
		for (ItemStack stack : List.of(p.getMainHandItem(), p.getOffhandItem())) {
			if (stack.is(ModRegistry.POWER_RING)) return Corps.of(stack);
		}
		var inventory = p.getInventory();
		for (int i = 0; i < inventory.getContainerSize(); i++) {
			if (inventory.getItem(i).is(ModRegistry.POWER_RING)) return Corps.of(inventory.getItem(i));
		}
		return Corps.GREEN;
	}

	public static void render(LevelRenderContext context) {
		if (TRAILS.isEmpty() && STREAKS.isEmpty() && RINGS.isEmpty()) return;
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float partial = mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
		Vec3 camera = context.levelState().cameraRenderState.pos;
		float life = Math.max(1, RingTuning.FLIGHT_TRAIL.ticks());
		boolean firstPerson = mc.options.getCameraType().isFirstPerson();
		RenderType type = RenderTypes.entityTranslucentEmissive(TEXTURE);
		int frame = Math.floorMod(clock, FRAMES);
		for (Int2ObjectMap.Entry<Trail> e : TRAILS.int2ObjectEntrySet()) {
			Trail t = e.getValue();
			if (!(mc.level.getEntity(e.getIntKey()) instanceof Player p)) continue;
			float own = p == mc.player && firstPerson ? OWN : 1f;
			List<Vec3> pos = new ArrayList<>();
			List<Float> fade = new ArrayList<>();
			List<Float> width = new ArrayList<>();
			// The newest point follows the fist smoothly; older ones fade with age.
			Vec3 fist = FlightPoses.fast(p) > 0.5f ? MovePoses.fist(p, partial) : null;
			if (fist != null) {
				pos.add(fist);
				fade.add(1f);
				width.add(t.speed);
			}
			float keep = life * (0.35f + 0.65f * t.speed) + 1;
			for (Point pt : t.points) {
				if (fist != null && pt.pos().distanceToSqr(fist) < 0.01) continue;
				float age = clock + partial - pt.tick();
				float a = 1f - age / keep;
				if (a <= 0) break;
				pos.add(pt.pos());
				fade.add(a);
				width.add(pt.speed());
			}
			if (pos.size() < 2) continue;
			float r = t.corps.red(), g = t.corps.green(), b = t.corps.blue();
			float alpha = own;
			context.submitNodeCollector().submitCustomGeometry(context.poseStack(), type,
					(pose, buffer) -> ribbon(pose, buffer, pos, fade, width, camera, frame, r, g, b, alpha));
		}
		if (!STREAKS.isEmpty()) {
			List<Streak> streaks = List.copyOf(STREAKS);
			context.submitNodeCollector().submitCustomGeometry(context.poseStack(), type, (pose, buffer) -> {
				for (Streak s : streaks) {
					float a = 0.3f * (1f - (clock + partial - s.tick) / (STREAK_LIFE + 1));
					if (a <= 0) continue;
					List<Vec3> line = List.of(s.pos, s.pos.add(s.back.scale(s.length)));
					ribbon(pose, buffer, line, List.of(1f, 0f), List.of(0.08f, 0.08f), camera, frame, 0.9f, 0.95f, 1f, a);
				}
			});
		}
		for (SpeedRing ring : RINGS) {
			float age = clock + partial - ring.tick;
			float k = Mth.clamp(age / RING_LIFE, 0f, 1f);
			SonicBoom.ring(context, camera, ring.pos, ring.dir, 0.8f + 1.2f * k, Math.min(7, 2 + (int) (k * 6)), 8, ring.corps, 0.5f * (1f - k));
		}
	}

	/** A camera-facing strip of the light texture through the points, tapering and fading toward its tail. */
	private static void ribbon(PoseStack.Pose pose, VertexConsumer buffer, List<Vec3> pos, List<Float> fade, List<Float> amount, Vec3 camera,
			int frame, float r, float g, float b, float alpha) {
		int n = pos.size();
		Vec3[] side = new Vec3[n];
		for (int i = 0; i < n; i++) {
			Vec3 dir = pos.get(Math.min(i + 1, n - 1)).subtract(pos.get(Math.max(i - 1, 0)));
			Vec3 s = dir.cross(camera.subtract(pos.get(i)));
			float taper = 1f - 0.6f * i / (n - 1);
			float half = (0.03f + MAX_HALF_WIDTH * amount.get(i)) * taper;
			side[i] = s.lengthSqr() < 1e-8 ? Vec3.ZERO : s.normalize().scale(half);
		}
		float v0 = frame / (float) FRAMES, v1 = (frame + 1) / (float) FRAMES;
		for (int i = 0; i + 1 < n; i++) {
			float bright0 = 0.15f + 0.85f * amount.get(i), bright1 = 0.15f + 0.85f * amount.get(i + 1);
			float a0 = alpha * fade.get(i) * bright0 * near(pos.get(i), camera), a1 = alpha * fade.get(i + 1) * bright1 * near(pos.get(i + 1), camera);
			if (a0 < 0.02f && a1 < 0.02f) continue;
			Vec3 p0 = pos.get(i), p1 = pos.get(i + 1);
			// One seamless tile a segment (a tick of travel); the frames scroll the light along it.
			vertex(pose, buffer, p0.subtract(side[i]), camera, 0, v1, r, g, b, a0);
			vertex(pose, buffer, p0.add(side[i]), camera, 0, v0, r, g, b, a0);
			vertex(pose, buffer, p1.add(side[i + 1]), camera, 1, v0, r, g, b, a1);
			vertex(pose, buffer, p1.subtract(side[i + 1]), camera, 1, v1, r, g, b, a1);
		}
	}

	/** Fades the trail out right at the camera, so your own doesn't flash across the screen. */
	private static float near(Vec3 p, Vec3 camera) {
		return Mth.clamp((float) (p.distanceTo(camera) - 1.5) / 1.5f, 0f, 1f);
	}

	private static void vertex(PoseStack.Pose pose, VertexConsumer buffer, Vec3 p, Vec3 camera, float u, float v,
			float r, float g, float b, float a) {
		buffer.addVertex(pose, (float) (p.x - camera.x), (float) (p.y - camera.y), (float) (p.z - camera.z))
				.setColor(r, g, b, a)
				.setUv(u, v)
				.setOverlay(NO_OVERLAY)
				.setLight(ShaderGlow.light(0.8f))
				.setNormal(pose, 0, 1, 0);
	}
}
