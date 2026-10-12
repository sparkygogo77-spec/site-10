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
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/**
 * A thin streak of essence light behind a player in the fast ring glide: a bright core with a soft
 * glow around it, in the ring's corps colour, that fades within a fraction of a second (the Ring
 * Lab's "Flight trail fade" duration). Each client draws it for every player it sees gliding.
 */
public final class FlightTrail {
	private static final Identifier TEXTURE = LanternRing.id("textures/entity/flight_trail.png");
	/** Blocks per tick the glide must reach before it leaves a streak (its top speed is about 1). */
	private static final double MIN_SPEED = 0.45;
	/** Height of the body's middle, where the streak comes from (the glide lies the body flat). */
	private static final double MIDDLE = 0.9;
	/** The streak starts this far behind the middle, about where the feet trail. */
	private static final double FEET = 0.9;
	private static final float CORE = 0.035f;
	private static final float GLOW = 0.14f;
	private static final int NO_OVERLAY = 0xA0000;

	private record Point(Vec3 pos, int tick) {
	}

	private static final class Trail {
		final ArrayDeque<Point> points = new ArrayDeque<>();
		Corps corps = Corps.GREEN;
		boolean seen;
	}

	private static final Int2ObjectMap<Trail> TRAILS = new Int2ObjectOpenHashMap<>();
	private static int clock;

	private FlightTrail() {
	}

	static void tick(Minecraft mc) {
		if (mc.level == null) {
			TRAILS.clear();
			return;
		}
		clock++;
		int life = Math.max(1, RingTuning.FLIGHT_TRAIL.ticks());
		for (Trail t : TRAILS.values()) t.seen = false;
		for (AbstractClientPlayer p : mc.level.players()) {
			Vec3 now = p.position();
			double speed = now.distanceTo(new Vec3(p.xo, p.yo, p.zo));
			Trail t = TRAILS.get(p.getId());
			if (FlightPoses.fast(p) > 0.5f && speed > MIN_SPEED) {
				if (t == null) TRAILS.put(p.getId(), t = new Trail());
				t.corps = ringCorps(p);
				t.points.addFirst(new Point(now.add(0, MIDDLE, 0), clock));
			}
			if (t == null) continue;
			while (!t.points.isEmpty() && clock - t.points.peekLast().tick() > life) t.points.removeLast();
			t.seen = !t.points.isEmpty();
		}
		TRAILS.values().removeIf(t -> !t.seen);
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
		if (TRAILS.isEmpty()) return;
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float partial = mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
		Vec3 camera = context.levelState().cameraRenderState.pos;
		float life = Math.max(1, RingTuning.FLIGHT_TRAIL.ticks());
		RenderType type = RenderTypes.entityTranslucentEmissive(TEXTURE);
		for (Int2ObjectMap.Entry<Trail> e : TRAILS.int2ObjectEntrySet()) {
			Trail t = e.getValue();
			if (!(mc.level.getEntity(e.getIntKey()) instanceof Player p)) continue;
			// The newest point follows the player smoothly; older ones fade with age.
			Vec3 middle = p.getPosition(partial).add(0, MIDDLE, 0);
			List<Vec3> pos = new ArrayList<>();
			List<Float> fade = new ArrayList<>();
			Vec3 back = null;
			for (Point pt : t.points) {
				if (back == null) {
					Vec3 dir = middle.subtract(pt.pos());
					if (dir.lengthSqr() < 1e-4) continue;
					back = dir.normalize();
					// Start at the feet, so the streak leaves the body rather than poking through it.
					if (FlightPoses.fast(p) > 0.5f) {
						pos.add(middle.subtract(back.scale(FEET)));
						fade.add(1f);
					}
				}
				if (pt.pos().distanceTo(middle) < FEET) continue;
				float age = clock + partial - pt.tick();
				float a = 1f - age / (life + 1);
				if (a <= 0) break;
				pos.add(pt.pos());
				fade.add(a);
			}
			if (pos.size() < 2) continue;
			float r = t.corps.red(), g = t.corps.green(), b = t.corps.blue();
			context.submitNodeCollector().submitCustomGeometry(context.poseStack(), type, (pose, buffer) -> {
				ribbon(pose, buffer, pos, fade, camera, GLOW, r, g, b, 0.45f);
				ribbon(pose, buffer, pos, fade, camera, CORE, Mth.lerp(0.6f, r, 1f), Mth.lerp(0.6f, g, 1f), Mth.lerp(0.6f, b, 1f), 1f);
			});
		}
	}

	/** A camera-facing strip through the points, tapering and fading toward its tail. */
	private static void ribbon(PoseStack.Pose pose, VertexConsumer buffer, List<Vec3> pos, List<Float> fade, Vec3 camera,
			float halfWidth, float r, float g, float b, float alpha) {
		int n = pos.size();
		Vec3[] side = new Vec3[n];
		for (int i = 0; i < n; i++) {
			Vec3 along = pos.get(Math.min(i + 1, n - 1)).subtract(pos.get(Math.max(i - 1, 0)));
			Vec3 s = along.cross(camera.subtract(pos.get(i)));
			float taper = 1f - 0.7f * i / (n - 1);
			side[i] = s.lengthSqr() < 1e-8 ? Vec3.ZERO : s.normalize().scale(halfWidth * taper);
		}
		for (int i = 0; i + 1 < n; i++) {
			float a0 = alpha * fade.get(i) * near(pos.get(i), camera), a1 = alpha * fade.get(i + 1) * near(pos.get(i + 1), camera);
			if (a0 < 0.1f && a1 < 0.1f) continue;
			Vec3 p0 = pos.get(i), p1 = pos.get(i + 1);
			vertex(pose, buffer, p0.subtract(side[i]), camera, 0, 1, r, g, b, a0);
			vertex(pose, buffer, p0.add(side[i]), camera, 0, 0, r, g, b, a0);
			vertex(pose, buffer, p1.add(side[i + 1]), camera, 1, 0, r, g, b, a1);
			vertex(pose, buffer, p1.subtract(side[i + 1]), camera, 1, 1, r, g, b, a1);
		}
	}

	/** Fades the streak out right at the camera, so your own doesn't flash across the screen. */
	private static float near(Vec3 p, Vec3 camera) {
		return Mth.clamp((float) (p.distanceTo(camera) - 1.2) / 1.5f, 0f, 1f);
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
