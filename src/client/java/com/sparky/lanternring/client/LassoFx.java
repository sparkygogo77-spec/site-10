package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.Lasso;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.net.LassoInputPayload;
import com.sparky.lanternring.net.LassoPayload;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

/**
 * Draws Lasso bubbles (see the server's Lasso) as solid see-through spheres of hard light, using
 * the construct texture, with a thin glowing string from the holder's ring. Both are drawn every
 * frame, so they follow the mob smoothly. Also sends the bearer's left-click (every tick it is
 * held) and space to the server while they are holding something.
 */
public final class LassoFx {
	private static final Identifier SHELL = LanternRing.id("textures/block/construct_inner.png");
	private static final Identifier STRING = LanternRing.id("textures/block/construct_rim.png");
	private static final int FULL_BRIGHT = 0xF000F0;
	/** OverlayTexture.NO_OVERLAY: no hurt-red or white flash. */
	private static final int NO_OVERLAY = 10 << 16;
	private static final int LONGITUDES = 28;
	private static final int LATITUDES = 16;
	private static final int STRING_SIDES = 5;
	private static final double STRING_RADIUS = 0.035;

	private static final class Bubble {
		int holder;
		float radius;
		boolean holding;
		int lastSeen;
	}

	/** Live bubbles, by the id of the mob inside. */
	private static final Map<Integer, Bubble> BUBBLES = new HashMap<>();
	private static int clock;
	private static boolean jumpWasDown;

	private LassoFx() {
	}

	public static void handle(LassoPayload payload) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		if (payload.radius() <= 0) {
			Bubble gone = BUBBLES.remove(payload.target());
			if (gone != null) pop(mc, payload.target(), gone);
			return;
		}
		Bubble b = BUBBLES.computeIfAbsent(payload.target(), id -> new Bubble());
		b.holder = payload.holder();
		b.radius = payload.radius();
		b.holding = payload.holding();
		b.lastSeen = clock;
	}

	public static void tick(Minecraft mc) {
		clock++;
		if (mc.level == null || mc.player == null) {
			BUBBLES.clear();
			return;
		}
		input(mc);
		if (mc.isPaused()) return;
		for (Iterator<Map.Entry<Integer, Bubble>> it = BUBBLES.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<Integer, Bubble> e = it.next();
			Entity target = mc.level.getEntity(e.getKey());
			if (target == null || clock - e.getValue().lastSeen > 5) {
				it.remove();
				continue;
			}
			// A few motes drift off the surface so the shell feels alive.
			Bubble b = e.getValue();
			Vec3 center = target.getBoundingBox().getCenter();
			if (mc.level.getRandom().nextFloat() < 0.5f) {
				var r = mc.level.getRandom();
				Vec3 out = new Vec3(r.nextDouble() - 0.5, r.nextDouble() - 0.5, r.nextDouble() - 0.5).normalize();
				LabFx.spawn(ModParticles.MOTE, center.add(out.scale(b.radius)), out.scale(0.02), 0.6f);
			}
		}
	}

	/** While holding a catch: left-click goes to the server every tick it is held, space on press. */
	private static void input(Minecraft mc) {
		boolean jump = mc.options.keyJump.isDown();
		Bubble mine = null;
		for (Bubble b : BUBBLES.values()) {
			if (b.holder == mc.player.getId()) mine = b;
		}
		if (mine != null && mc.player.isUsingItem() && ClientPlayNetworking.canSend(LassoInputPayload.TYPE)) {
			if (mc.options.keyAttack.isDown()) ClientPlayNetworking.send(new LassoInputPayload(Lasso.INPUT_SEND));
			if (jump && !jumpWasDown) ClientPlayNetworking.send(new LassoInputPayload(Lasso.INPUT_HOLD));
		}
		jumpWasDown = jump;
	}

	/** The bubble bursts into shards and motes. */
	private static void pop(Minecraft mc, int targetId, Bubble b) {
		Entity target = mc.level.getEntity(targetId);
		if (target == null) return;
		Vec3 center = target.getBoundingBox().getCenter();
		double golden = Math.PI * (3 - Math.sqrt(5));
		for (int i = 0; i < 40; i++) {
			double y = 1 - (i + 0.5) * 2 / 40;
			double ring = Math.sqrt(1 - y * y);
			double a = i * golden;
			Vec3 out = new Vec3(Math.cos(a) * ring, y, Math.sin(a) * ring);
			LabFx.spawn(i % 3 == 0 ? ModParticles.SHARD : ModParticles.MOTE, center.add(out.scale(b.radius)), out.scale(0.12));
		}
	}

	// ---- every frame: the spheres and strings ----------------------------------------------------

	public static void render(LevelRenderContext context) {
		if (BUBBLES.isEmpty()) return;
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float partial = mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
		Vec3 camera = context.levelState().cameraRenderState.pos;
		RenderType shell = RenderTypes.beaconBeam(SHELL, true);
		RenderType string = RenderTypes.beaconBeam(STRING, true);
		for (Map.Entry<Integer, Bubble> e : BUBBLES.entrySet()) {
			Entity target = mc.level.getEntity(e.getKey());
			if (target == null) continue;
			Bubble b = e.getValue();
			Vec3 center = target.getPosition(partial).add(0, target.getBbHeight() / 2, 0);
			double spin = (clock + partial) * 0.02;
			context.submitNodeCollector().submitCustomGeometry(context.poseStack(), shell,
					(pose, buffer) -> sphere(pose, buffer, center, b.radius, spin, camera, b.holding));
			if (mc.level.getEntity(b.holder) instanceof Player holder) {
				Vec3 ring = LabFx.ringPos(mc, holder, holder.getMainArm());
				context.submitNodeCollector().submitCustomGeometry(context.poseStack(), string,
						(pose, buffer) -> string(pose, buffer, ring, center, b.radius, camera));
			}
		}
	}

	/**
	 * A see-through sphere, faint where you look straight through it and brighter towards its
	 * outline, like a soap bubble. It glows a little brighter while it is held in place.
	 */
	private static void sphere(PoseStack.Pose pose, VertexConsumer buffer, Vec3 center, double r, double spin,
			Vec3 camera, boolean holding) {
		float base = holding ? 0.4f : 0.28f;
		for (int lat = 0; lat < LATITUDES; lat++) {
			double t0 = Math.PI * lat / LATITUDES;
			double t1 = Math.PI * (lat + 1) / LATITUDES;
			for (int lon = 0; lon < LONGITUDES; lon++) {
				double p0 = Math.PI * 2 * lon / LONGITUDES + spin;
				double p1 = Math.PI * 2 * (lon + 1) / LONGITUDES + spin;
				Vec3 a = unit(t0, p0), bb = unit(t0, p1), c = unit(t1, p1), d = unit(t1, p0);
				sphereVertex(pose, buffer, center, a, r, camera, 0, 0, base);
				sphereVertex(pose, buffer, center, bb, r, camera, 1, 0, base);
				sphereVertex(pose, buffer, center, c, r, camera, 1, 1, base);
				sphereVertex(pose, buffer, center, d, r, camera, 0, 1, base);
			}
		}
	}

	private static Vec3 unit(double theta, double phi) {
		return new Vec3(Math.sin(theta) * Math.cos(phi), Math.cos(theta), Math.sin(theta) * Math.sin(phi));
	}

	private static void sphereVertex(PoseStack.Pose pose, VertexConsumer buffer, Vec3 center, Vec3 n, double r,
			Vec3 camera, float u, float v, float base) {
		Vec3 p = center.add(n.scale(r));
		Vec3 view = camera.subtract(p);
		double facing = Math.abs(n.dot(view.normalize()));
		float edge = (float) Math.pow(1 - facing, 2);
		float alpha = Math.min(1f, base + 0.65f * edge);
		vertex(pose, buffer, p, camera, u, v, 0.45f + 0.4f * edge, 1f, 0.55f + 0.3f * edge, alpha);
	}

	/** A thin glowing tube from the ring to the bubble's surface, sagging a little like a rope. */
	private static void string(PoseStack.Pose pose, VertexConsumer buffer, Vec3 from, Vec3 center, double radius, Vec3 camera) {
		Vec3 d = center.subtract(from);
		double len = d.length();
		if (len <= radius + 0.05) return;
		Vec3 to = center.subtract(d.scale(radius / len));
		double span = len - radius;
		double sag = Math.min(0.6, span * 0.04);
		int segments = Math.max(4, (int) (span / 0.25));
		Vec3[] prev = null;
		for (int i = 0; i <= segments; i++) {
			double f = i / (double) segments;
			Vec3 at = point(from, to, sag, f);
			Vec3 tangent = point(from, to, sag, Math.min(1, f + 0.01)).subtract(point(from, to, sag, Math.max(0, f - 0.01))).normalize();
			Vec3 side = tangent.cross(new Vec3(0, 1, 0));
			side = side.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : side.normalize();
			Vec3 up = side.cross(tangent).normalize();
			Vec3[] ring = new Vec3[STRING_SIDES];
			for (int j = 0; j < STRING_SIDES; j++) {
				double th = j * Math.PI * 2 / STRING_SIDES;
				ring[j] = at.add(side.scale(Math.cos(th) * STRING_RADIUS)).add(up.scale(Math.sin(th) * STRING_RADIUS));
			}
			if (prev != null) {
				for (int j = 0; j < STRING_SIDES; j++) {
					int k = (j + 1) % STRING_SIDES;
					vertex(pose, buffer, prev[j], camera, 0, 0, 0.5f, 1f, 0.55f, 0.95f);
					vertex(pose, buffer, prev[k], camera, 1, 0, 0.5f, 1f, 0.55f, 0.95f);
					vertex(pose, buffer, ring[k], camera, 1, 1, 0.5f, 1f, 0.55f, 0.95f);
					vertex(pose, buffer, ring[j], camera, 0, 1, 0.5f, 1f, 0.55f, 0.95f);
				}
			}
			prev = ring;
		}
	}

	private static Vec3 point(Vec3 from, Vec3 to, double sag, double f) {
		return from.lerp(to, f).subtract(0, sag * 4 * f * (1 - f), 0);
	}

	private static void vertex(PoseStack.Pose pose, VertexConsumer buffer, Vec3 p, Vec3 camera, float u, float v,
			float r, float g, float b, float a) {
		buffer.addVertex(pose, (float) (p.x - camera.x), (float) (p.y - camera.y), (float) (p.z - camera.z))
				.setColor(r, g, b, a)
				.setUv(u, v)
				.setOverlay(NO_OVERLAY)
				.setLight(FULL_BRIGHT)
				.setNormal(pose, 0, 1, 0);
	}
}
