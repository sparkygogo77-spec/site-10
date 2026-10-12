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
 * Draws Lasso bubbles (see the server's Lasso) as glowing spheres of cracked jade hard light, with a
 * twisted rope of light from the holder's ring that pulses towards the bubble. Both are drawn every
 * frame, so they follow the mob smoothly, with the translucent emissive entity render type so they
 * stay bright at night and under shader packs. Each bubble also gets its sounds (LassoSound). Also
 * sends the bearer's left-click (every tick it is held) and space to the server while they are
 * holding something.
 */
public final class LassoFx {
	private static final Identifier SHELL = LanternRing.id("textures/entity/lasso_bubble.png");
	private static final Identifier STRING = LanternRing.id("textures/entity/lasso_rope.png");
	private static final int FULL_BRIGHT = 0xF000F0;
	/** OverlayTexture.NO_OVERLAY: no hurt-red or white flash. */
	private static final int NO_OVERLAY = 10 << 16;
	private static final int LONGITUDES = 32;
	private static final int LATITUDES = 18;
	private static final int STRING_SIDES = 8;
	private static final double STRING_RADIUS = 0.07;
	/** The soft glow around the rope and the bubble, as a fraction of their size. */
	private static final double STRING_GLOW = 2.2;
	private static final double SHELL_GLOW = 1.08;
	/** Rope length of one turn of the texture. */
	private static final double STRING_TILE = 0.6;

	static final class Bubble {
		int holder;
		float radius;
		boolean holding;
		int lastSeen;
		LassoSound hum;
		LassoSound wind;
	}

	/** Live bubbles, by the id of the mob inside. */
	private static final Map<Integer, Bubble> BUBBLES = new HashMap<>();
	private static int clock;
	private static boolean jumpWasDown;
	/** Vanilla's double-tap window for starting to fly, and the ticks left before a single tap counts. */
	private static final int DOUBLE_TAP_TICKS = 7;
	private static int reelTap;

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
			// A bubble caught again in mid-air gets its hum back.
			if (b.holder != -1 && (b.hum == null || b.hum.isStopped())) b.hum = LassoSound.start(mc, e.getKey(), true);
			if (b.wind == null || b.wind.isStopped()) b.wind = LassoSound.start(mc, e.getKey(), false);
			Vec3 center = target.getBoundingBox().getCenter();
			if (mc.level.getRandom().nextFloat() < 0.5f) {
				var r = mc.level.getRandom();
				Vec3 out = new Vec3(r.nextDouble() - 0.5, r.nextDouble() - 0.5, r.nextDouble() - 0.5).normalize();
				LabFx.spawn(ModParticles.MOTE, center.add(out.scale(b.radius)), out.scale(0.02), 0.6f);
			}
		}
	}

	/**
	 * While holding a catch: left-click goes to the server every tick it is held, and a single tap of
	 * space toggles the reel. Space belongs to flight while flying (it rises), and a double tap that
	 * starts flying isn't a reel toggle, so with ring flight a tap only counts once the double-tap
	 * window has passed.
	 */
	private static void input(Minecraft mc) {
		boolean jump = mc.options.keyJump.isDown();
		Bubble mine = null;
		for (Bubble b : BUBBLES.values()) {
			if (b.holder == mc.player.getId()) mine = b;
		}
		boolean holding = mine != null && mc.player.isUsingItem() && ClientPlayNetworking.canSend(LassoInputPayload.TYPE);
		var abilities = mc.player.getAbilities();
		if (!holding || abilities.flying) {
			reelTap = 0;
		} else if (reelTap > 0 && --reelTap == 0) {
			ClientPlayNetworking.send(new LassoInputPayload(Lasso.INPUT_HOLD));
		}
		if (holding) {
			if (mc.options.keyAttack.isDown()) ClientPlayNetworking.send(new LassoInputPayload(Lasso.INPUT_SEND));
			if (jump && !jumpWasDown && !abilities.flying) {
				if (!abilities.mayfly) {
					ClientPlayNetworking.send(new LassoInputPayload(Lasso.INPUT_HOLD));
				} else {
					// A second tap inside the window is the double tap that starts flying.
					reelTap = reelTap > 0 ? 0 : DOUBLE_TAP_TICKS;
				}
			}
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

	/** The bubble around this mob, or null once it popped. */
	static Bubble bubble(int target) {
		return BUBBLES.get(target);
	}

	public static void render(LevelRenderContext context) {
		if (BUBBLES.isEmpty()) return;
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float partial = mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
		Vec3 camera = context.levelState().cameraRenderState.pos;
		RenderType shell = RenderTypes.entityTranslucentEmissive(SHELL);
		RenderType string = RenderTypes.entityTranslucentEmissive(STRING);
		double time = clock + partial;
		for (Map.Entry<Integer, Bubble> e : BUBBLES.entrySet()) {
			Entity target = mc.level.getEntity(e.getKey());
			if (target == null) continue;
			Bubble b = e.getValue();
			Vec3 center = target.getPosition(partial).add(0, target.getBbHeight() / 2, 0);
			double spin = time * 0.02;
			context.submitNodeCollector().submitCustomGeometry(context.poseStack(), shell,
					(pose, buffer) -> sphere(pose, buffer, center, b.radius, spin, camera, b.holding, time));
			if (mc.level.getEntity(b.holder) instanceof Player holder) {
				Vec3 ring = LabFx.ringPos(mc, holder, holder.getMainArm());
				context.submitNodeCollector().submitCustomGeometry(context.poseStack(), string,
						(pose, buffer) -> string(pose, buffer, ring, center, b.radius, camera, time));
			}
		}
	}

	/**
	 * A sphere of cracked jade glass, solid enough to see clearly but still showing the mob inside,
	 * brighter towards its outline like a soap bubble, with a soft glow shell around it. The inside
	 * of the far wall is drawn too, so the cracks wrap all the way round. It breathes slowly, and
	 * glows brighter while it is held in place.
	 */
	private static void sphere(PoseStack.Pose pose, VertexConsumer buffer, Vec3 center, double r, double spin,
			Vec3 camera, boolean holding, double time) {
		float pulse = (float) (0.9 + 0.1 * Math.sin(time * 0.15));
		float base = (holding ? 0.6f : 0.5f) * pulse;
		shell(pose, buffer, center, r, spin, camera, base, 0.45f, false);
		shell(pose, buffer, center, r, spin, camera, base, 0.45f, true);
		// The glow: only its rim shows, a halo just outside the outline.
		shell(pose, buffer, center, r * SHELL_GLOW, -spin, camera, 0f, 0.5f * pulse, false);
	}

	private static void shell(PoseStack.Pose pose, VertexConsumer buffer, Vec3 center, double r, double spin,
			Vec3 camera, float base, float rim, boolean inside) {
		for (int lat = 0; lat < LATITUDES; lat++) {
			double t0 = Math.PI * lat / LATITUDES;
			double t1 = Math.PI * (lat + 1) / LATITUDES;
			float v0 = lat / (float) LATITUDES, v1 = (lat + 1) / (float) LATITUDES;
			for (int lon = 0; lon < LONGITUDES; lon++) {
				double p0 = Math.PI * 2 * lon / LONGITUDES + spin;
				double p1 = Math.PI * 2 * (lon + 1) / LONGITUDES + spin;
				float u0 = lon / (float) LONGITUDES, u1 = (lon + 1) / (float) LONGITUDES;
				Vec3 a = unit(t0, p0), bb = unit(t0, p1), c = unit(t1, p1), d = unit(t1, p0);
				if (inside) {
					sphereVertex(pose, buffer, center, d, r, camera, u0, v1, base, rim, true);
					sphereVertex(pose, buffer, center, c, r, camera, u1, v1, base, rim, true);
					sphereVertex(pose, buffer, center, bb, r, camera, u1, v0, base, rim, true);
					sphereVertex(pose, buffer, center, a, r, camera, u0, v0, base, rim, true);
				} else {
					sphereVertex(pose, buffer, center, a, r, camera, u0, v0, base, rim, false);
					sphereVertex(pose, buffer, center, bb, r, camera, u1, v0, base, rim, false);
					sphereVertex(pose, buffer, center, c, r, camera, u1, v1, base, rim, false);
					sphereVertex(pose, buffer, center, d, r, camera, u0, v1, base, rim, false);
				}
			}
		}
	}

	private static Vec3 unit(double theta, double phi) {
		return new Vec3(Math.sin(theta) * Math.cos(phi), Math.cos(theta), Math.sin(theta) * Math.sin(phi));
	}

	private static void sphereVertex(PoseStack.Pose pose, VertexConsumer buffer, Vec3 center, Vec3 n, double r,
			Vec3 camera, float u, float v, float base, float rim, boolean inside) {
		Vec3 p = center.add(n.scale(r));
		Vec3 view = camera.subtract(p);
		double facing = Math.abs(n.dot(view.normalize()));
		float edge = (float) Math.pow(1 - facing, 2);
		// The render type drops anything under 10% alpha, so a glow shell fades out before its middle.
		float alpha = Math.min(1f, (inside ? base * 0.6f : base) + rim * edge);
		if (alpha < 0.1f) alpha = 0f;
		float glow = Math.min(1f, 0.75f + 0.25f * edge);
		Vec3 normal = inside ? n.scale(-1) : n;
		vertex(pose, buffer, p, camera, u, v, 0.55f * glow + 0.3f * edge, glow, 0.7f * glow + 0.2f * edge, alpha, normal);
	}

	/**
	 * A twisted rope of light from the ring to the bubble's surface, sagging a little, with a soft
	 * glowing sheath around it and pulses of light running out towards the bubble.
	 */
	private static void string(PoseStack.Pose pose, VertexConsumer buffer, Vec3 from, Vec3 center, double radius,
			Vec3 camera, double time) {
		Vec3 d = center.subtract(from);
		double len = d.length();
		if (len <= radius + 0.05) return;
		Vec3 to = center.subtract(d.scale(radius / len));
		double span = len - radius;
		double sag = Math.min(0.6, span * 0.04);
		tube(pose, buffer, from, to, span, sag, STRING_RADIUS, camera, time, false);
		tube(pose, buffer, from, to, span, sag, STRING_RADIUS * STRING_GLOW, camera, time, true);
	}

	private static void tube(PoseStack.Pose pose, VertexConsumer buffer, Vec3 from, Vec3 to, double span, double sag,
			double radius, Vec3 camera, double time, boolean glow) {
		int segments = Math.max(4, (int) Math.ceil(span / STRING_TILE * 2));
		Vec3[] prev = null;
		Vec3[] prevNormals = null;
		float prevBright = 0;
		for (int i = 0; i <= segments; i++) {
			double f = i / (double) segments;
			Vec3 at = point(from, to, sag, f);
			Vec3 tangent = point(from, to, sag, Math.min(1, f + 0.01)).subtract(point(from, to, sag, Math.max(0, f - 0.01))).normalize();
			Vec3 side = tangent.cross(new Vec3(0, 1, 0));
			side = side.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : side.normalize();
			Vec3 up = side.cross(tangent).normalize();
			Vec3[] ring = new Vec3[STRING_SIDES];
			Vec3[] normals = new Vec3[STRING_SIDES];
			for (int j = 0; j < STRING_SIDES; j++) {
				double th = j * Math.PI * 2 / STRING_SIDES;
				normals[j] = side.scale(Math.cos(th)).add(up.scale(Math.sin(th)));
				ring[j] = at.add(normals[j].scale(radius));
			}
			// Pulses travel out along the rope, a few blocks apart.
			double wave = Math.sin(f * span * 1.2 - time * 0.9);
			float bright = (float) (0.78 + 0.22 * Math.max(0, wave));
			if (prev != null) {
				// Each segment shows half a turn of the texture, so the strands twist along the rope.
				float v0 = (i - 1) % 2 * 0.5f, v1 = v0 + 0.5f;
				for (int j = 0; j < STRING_SIDES; j++) {
					int k = (j + 1) % STRING_SIDES;
					float u0 = j / (float) STRING_SIDES, u1 = (j + 1) / (float) STRING_SIDES;
					stringVertex(pose, buffer, prev[j], prevNormals[j], camera, u0, v0, prevBright, glow);
					stringVertex(pose, buffer, prev[k], prevNormals[k], camera, u1, v0, prevBright, glow);
					stringVertex(pose, buffer, ring[k], normals[k], camera, u1, v1, bright, glow);
					stringVertex(pose, buffer, ring[j], normals[j], camera, u0, v1, bright, glow);
				}
			}
			prev = ring;
			prevNormals = normals;
			prevBright = bright;
		}
	}

	private static void stringVertex(PoseStack.Pose pose, VertexConsumer buffer, Vec3 p, Vec3 n, Vec3 camera, float u,
			float v, float bright, boolean glow) {
		float alpha;
		if (glow) {
			// Only the sheath's outline shows, as a soft halo either side of the rope.
			double facing = Math.abs(n.dot(camera.subtract(p).normalize()));
			alpha = (float) (0.45 * Math.pow(1 - facing, 1.5) * bright);
			if (alpha < 0.1f) alpha = 0f;
		} else {
			alpha = 1f;
		}
		vertex(pose, buffer, p, camera, u, v, 0.6f * bright, bright, 0.72f * bright, alpha, n);
	}

	private static Vec3 point(Vec3 from, Vec3 to, double sag, double f) {
		return from.lerp(to, f).subtract(0, sag * 4 * f * (1 - f), 0);
	}

	private static void vertex(PoseStack.Pose pose, VertexConsumer buffer, Vec3 p, Vec3 camera, float u, float v,
			float r, float g, float b, float a, Vec3 n) {
		buffer.addVertex(pose, (float) (p.x - camera.x), (float) (p.y - camera.y), (float) (p.z - camera.z))
				.setColor(r, g, b, a)
				.setUv(u, v)
				.setOverlay(NO_OVERLAY)
				.setLight(FULL_BRIGHT)
				.setNormal(pose, (float) n.x, (float) n.y, (float) n.z);
	}
}
