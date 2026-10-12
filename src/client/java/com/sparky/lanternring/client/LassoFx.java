package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.Lasso;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.LassoInputPayload;
import com.sparky.lanternring.net.LassoPayload;
import com.sparky.lanternring.RingTuning;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Iterator;
import java.util.Map;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.corps.CorpsVillager;
import net.minecraft.world.phys.Vec3;

/**
 * Draws Lasso bubbles (see the server's Lasso) as glowing spheres of cracked jade hard light, with a
 * smooth tube of light from the holder's ring that pulses towards the bubble. Both are drawn every
 * frame, so they follow the mob smoothly, with the translucent emissive entity render type so they
 * stay bright at night and under shader packs. Each bubble also gets its sounds (LassoSound). Also
 * sends the bearer's left-click (every tick it is held) and space to the server while they are
 * holding something, and left-click in Lasso mode without a catch to pick mobs.
 */
public final class LassoFx {
	private static final Identifier SHELL = LanternRing.id("textures/entity/lasso_bubble.png");
	private static final Identifier STRING = LanternRing.id("textures/entity/lasso_rope.png");
	/** OverlayTexture.NO_OVERLAY: no hurt-red or white flash. */
	private static final int NO_OVERLAY = 10 << 16;
	private static final int LONGITUDES = 32;
	private static final int LATITUDES = 18;
	private static final int STRING_SIDES = 8;
	private static final double STRING_RADIUS = 0.07;
	/** The soft glow around the rope and the bubble, as a fraction of their size. */
	private static final double STRING_GLOW = 1.6;
	private static final double SHELL_GLOW = 1.08;
	/** Rope length of one band of the texture. */
	private static final double STRING_TILE = 0.6;

	static final class Bubble {
		int holder;
		float radius;
		boolean holding;
		/** The bearer's ring colour (player or corps villager): drawn in it, and keeps it in flight. */
		Corps corps = Corps.GREEN;
		int lastSeen;
		LassoSound hum;
		LassoSound wind;
	}

	/** Live bubbles, by the id of the mob inside. */
	private static final Map<Integer, Bubble> BUBBLES = new HashMap<>();

	/** A let-go bubble coming apart from its far side, its light and then its rope going back into the ring. */
	private static final class Dismissing {
		Vec3 center;
		float radius;
		int holder;
		Corps corps;
		boolean holding;
		float start;
		float ticks;
		/** How far from the ring the dissolving front was last tick. */
		double lastFront = Double.NaN;
	}

	private static final List<Dismissing> DISMISSING = new ArrayList<>();
	/** Shares of the dismissal: the shell is gone by SHELL_END, the rope starts pulling in at ROPE_START. */
	private static final float SHELL_END = 0.7f;
	private static final float ROPE_START = 0.45f;
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
			if (gone == null) return;
			Entity holder = payload.holder() >= 0 ? mc.level.getEntity(payload.holder()) : null;
			if (holder == null || !dismiss(mc, payload.target(), gone, holder)) pop(mc, payload.target(), gone);
			return;
		}
		Bubble b = BUBBLES.computeIfAbsent(payload.target(), id -> new Bubble());
		b.holder = payload.holder();
		b.corps = payload.corps();
		b.radius = payload.radius();
		b.holding = payload.holding();
		b.lastSeen = clock;
	}

	public static void tick(Minecraft mc) {
		clock++;
		if (mc.level == null || mc.player == null) {
			BUBBLES.clear();
			DISMISSING.clear();
			return;
		}
		input(mc);
		if (mc.isPaused()) return;
		tickDismissing(mc);
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
				Corps before = CorpsTint.enter(b.corps);
				LabFx.spawn(ModParticles.MOTE, center.add(out.scale(b.radius)), out.scale(0.02), 0.6f);
				CorpsTint.restore(before);
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
		if (picking(mc) && mc.options.keyAttack.isDown() && ClientPlayNetworking.canSend(LassoInputPayload.TYPE)) {
			ClientPlayNetworking.send(new LassoInputPayload(Lasso.INPUT_SELECT));
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

	/**
	 * Lasso mode with the ring in the main hand and right-click up: left-click picks mobs (see the
	 * server's Lasso.pick) instead of hitting or mining (see MinecraftMixin).
	 */
	public static boolean picking(Minecraft mc) {
		return mc.player != null && !mc.player.isUsingItem() && !mc.options.keyUse.isDown()
				&& mc.player.getMainHandItem().getItem() instanceof PowerRingItem
				&& PowerRingItem.getMode(mc.player.getMainHandItem()) == RingMode.TETHER;
	}

	/**
	 * The holder let go: the bubble stays where it was and comes apart quickly from the side
	 * furthest from their ring, each piece's light streaming back into the ring (DismissFx), then
	 * the rope pulls back in. False when there's no time set for it (the bubble pops instead).
	 */
	private static boolean dismiss(Minecraft mc, int targetId, Bubble b, Entity holder) {
		Entity target = mc.level.getEntity(targetId);
		int ticks = RingTuning.DISMISS_TIME.ticks();
		if (target == null || ticks <= 0 || holder.distanceToSqr(target) > 96 * 96) return false;
		Dismissing d = new Dismissing();
		d.center = target.getBoundingBox().getCenter();
		d.radius = b.radius;
		d.holder = holder.getId();
		d.corps = b.corps;
		d.holding = b.holding;
		d.start = clock;
		d.ticks = ticks;
		DISMISSING.add(d);
		return true;
	}

	/** Each tick, the pieces the front just passed send their light home. */
	private static void tickDismissing(Minecraft mc) {
		var r = mc.level.getRandom();
		for (Iterator<Dismissing> it = DISMISSING.iterator(); it.hasNext(); ) {
			Dismissing d = it.next();
			Entity holder = mc.level.getEntity(d.holder);
			float t = (clock - d.start) / d.ticks;
			if (holder == null || t > 1) {
				it.remove();
				continue;
			}
			Vec3 ring = DismissFx.ringOf(holder, 1f, d.center);
			double front = front(d, ring, t);
			double last = Double.isNaN(d.lastFront) ? d.center.distanceTo(ring) + d.radius : d.lastFront;
			d.lastFront = front;
			if (front >= last) continue;
			// A dozen points on the shell between last tick's front and this one's.
			int n = 0;
			for (int tries = 0; tries < 80 && n < 12; tries++) {
				Vec3 out = new Vec3(r.nextGaussian(), r.nextGaussian(), r.nextGaussian());
				if (out.lengthSqr() < 1e-6) continue;
				Vec3 p = d.center.add(out.normalize().scale(d.radius));
				double dist = p.distanceTo(ring);
				if (dist > last || dist < front) continue;
				DismissFx.streak(d.holder, d.corps, p, -r.nextFloat(), 0.8f);
				n++;
			}
		}
	}

	/** How far from the ring the dissolving front is: from the far side of the shell at t 0 to its near side at SHELL_END. */
	private static double front(Dismissing d, Vec3 ring, float t) {
		double mid = d.center.distanceTo(ring);
		float f = Mth.clamp(t / SHELL_END, 0f, 1f);
		return mid + d.radius - 2 * d.radius * f;
	}

	/** The bubble bursts into shards and motes. */
	private static void pop(Minecraft mc, int targetId, Bubble b) {
		Entity target = mc.level.getEntity(targetId);
		if (target == null) return;
		Vec3 center = target.getBoundingBox().getCenter();
		double golden = Math.PI * (3 - Math.sqrt(5));
		Corps before = CorpsTint.enter(b.corps);
		for (int i = 0; i < 40; i++) {
			double y = 1 - (i + 0.5) * 2 / 40;
			double ring = Math.sqrt(1 - y * y);
			double a = i * golden;
			Vec3 out = new Vec3(Math.cos(a) * ring, y, Math.sin(a) * ring);
			LabFx.spawn(i % 3 == 0 ? ModParticles.SHARD : ModParticles.MOTE, center.add(out.scale(b.radius)), out.scale(0.12));
		}
		CorpsTint.restore(before);
	}

	// ---- every frame: the spheres and strings ----------------------------------------------------

	/** Shoulder height above the feet, arm length to the ring, and the shoulder's offsets (third person). */
	private static final double SHOULDER = 1.375;
	private static final double CROUCH_DROP = 0.14;
	private static final double ARM = 0.735;
	private static final double SHOULDER_SIDE = 0.37;
	private static final double SHOULDER_FORWARD = 0.08;

	/**
	 * Exactly where the ring is this frame, so the rope comes out of it. In first person that is the
	 * ring as drawn on the fist (LabFx.ringPos), already relative to this frame's camera. In third person
	 * the holder's ring arm is raised to point where they look (see FlightPoses), so the ring is at the
	 * end of that arm.
	 */
	private static Vec3 ropeStart(Minecraft mc, Player holder, float partial) {
		HumanoidArm arm = FlightPoses.isRing(holder.getMainHandItem()) || !FlightPoses.isRing(holder.getOffhandItem())
				? holder.getMainArm() : holder.getMainArm().getOpposite();
		if (holder == mc.player && mc.options.getCameraType().isFirstPerson()) {
			return LabFx.ringPos(mc, holder, arm);
		}
		float side = arm == HumanoidArm.RIGHT ? 1 : -1;
		float yaw = Mth.rotLerp(partial, holder.yBodyRotO, holder.yBodyRot) * Mth.DEG_TO_RAD;
		Vec3 forward = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
		Vec3 right = new Vec3(-Mth.cos(yaw), 0, -Mth.sin(yaw));
		double height = SHOULDER - (holder.isCrouching() ? CROUCH_DROP : 0);
		Vec3 shoulder = holder.getPosition(partial).add(right.scale(side * SHOULDER_SIDE)).add(forward.scale(SHOULDER_FORWARD)).add(0, height, 0);
		float aim = FlightPoses.aim(holder, partial);
		Vec3 dir = new Vec3(0, -1, 0).lerp(holder.getViewVector(partial), aim);
		dir = dir.lengthSqr() < 1e-4 ? holder.getViewVector(partial) : dir.normalize();
		return shoulder.add(dir.scale(ARM));
	}

	/** The bubble around this mob, or null once it popped. */
	static Bubble bubble(int target) {
		return BUBBLES.get(target);
	}

	public static void render(LevelRenderContext context) {
		if (BUBBLES.isEmpty() && DISMISSING.isEmpty()) return;
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float partial = mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
		Vec3 camera = context.levelState().cameraRenderState.pos;
		double time = clock + partial;
		for (Map.Entry<Integer, Bubble> e : BUBBLES.entrySet()) {
			Entity target = mc.level.getEntity(e.getKey());
			if (target == null) continue;
			Bubble b = e.getValue();
			Vec3 center = target.getPosition(partial).add(0, target.getBbHeight() / 2, 0);
			double spin = time * 0.02;
			Corps corps = b.corps;
			context.submitNodeCollector().submitCustomGeometry(context.poseStack(), RenderTypes.entityTranslucentEmissive(CorpsTint.texture(SHELL, corps)),
					(pose, buffer) -> sphere(pose, tinted(buffer, corps), center, b.radius, spin, camera, b.holding, time, null, 0));
			Entity holder = mc.level.getEntity(b.holder);
			Vec3 ring = holder instanceof Player p ? ropeStart(mc, p, partial)
					: holder instanceof CorpsVillager v ? CorpsVillager.ringPos(v, partial, center) : null;
			if (ring != null) {
				context.submitNodeCollector().submitCustomGeometry(context.poseStack(), RenderTypes.entityTranslucentEmissive(CorpsTint.texture(STRING, corps)),
						(pose, buffer) -> string(pose, tinted(buffer, corps), ring, center, b.radius, camera, time));
			}
		}
		for (Dismissing d : DISMISSING) {
			Entity holder = mc.level.getEntity(d.holder);
			if (holder == null) continue;
			float t = (float) ((time - d.start) / d.ticks);
			if (t < 0 || t > 1) continue;
			Vec3 ring = DismissFx.ringOf(holder, partial, d.center);
			double front = front(d, ring, t);
			Corps corps = d.corps;
			if (t < SHELL_END) {
				double spin = time * 0.02;
				context.submitNodeCollector().submitCustomGeometry(context.poseStack(), RenderTypes.entityTranslucentEmissive(CorpsTint.texture(SHELL, corps)),
						(pose, buffer) -> sphere(pose, tinted(buffer, corps), d.center, d.radius, spin, camera, d.holding, time, ring, front));
			}
			// The rope runs to the shell's near side, and pulls back into the ring once the shell is nearly gone.
			Vec3 dir = d.center.subtract(ring);
			double span = dir.length() - d.radius;
			if (span <= 0.1) continue;
			float pull = Mth.clamp((t - ROPE_START) / (1 - ROPE_START), 0f, 1f);
			double left = span * (1 - pull * pull * (3 - 2 * pull));
			if (left < 0.1) continue;
			Vec3 end = ring.add(dir.normalize().scale(left + d.radius));
			context.submitNodeCollector().submitCustomGeometry(context.poseStack(), RenderTypes.entityTranslucentEmissive(CorpsTint.texture(STRING, corps)),
					(pose, buffer) -> string(pose, tinted(buffer, corps), ring, end, d.radius, camera, time));
		}
	}

	/**
	 * A sphere of cracked jade glass, solid enough to see clearly but still showing the mob inside,
	 * brighter towards its outline like a soap bubble, with a soft glow shell around it. The inside
	 * of the far wall is drawn too, so the cracks wrap all the way round. It breathes slowly, and
	 * glows brighter while it is held in place.
	 */
	private static void sphere(PoseStack.Pose pose, VertexConsumer buffer, Vec3 center, double r, double spin,
			Vec3 camera, boolean holding, double time, Vec3 cutRing, double front) {
		float pulse = (float) (0.9 + 0.1 * Math.sin(time * 0.15));
		float base = (holding ? 0.6f : 0.5f) * pulse;
		shell(pose, buffer, center, r, spin, camera, base, 0.45f, false, cutRing, front);
		shell(pose, buffer, center, r, spin, camera, base, 0.45f, true, cutRing, front);
		// The glow: only its rim shows, a halo just outside the outline.
		shell(pose, buffer, center, r * SHELL_GLOW, -spin, camera, 0f, 0.5f * pulse, false, cutRing, front);
	}

	/**
	 * One layer of the sphere. While it is being dismissed (cutRing not null) only the part nearer
	 * the ring than {@code front} is left, and the band just behind the front glows bright as it comes apart.
	 */
	private static void shell(PoseStack.Pose pose, VertexConsumer buffer, Vec3 center, double r, double spin,
			Vec3 camera, float base, float rim, boolean inside, Vec3 cutRing, double front) {
		double edge = Math.max(0.3, r * 0.35);
		for (int lat = 0; lat < LATITUDES; lat++) {
			double t0 = Math.PI * lat / LATITUDES;
			double t1 = Math.PI * (lat + 1) / LATITUDES;
			float v0 = lat / (float) LATITUDES, v1 = (lat + 1) / (float) LATITUDES;
			for (int lon = 0; lon < LONGITUDES; lon++) {
				double p0 = Math.PI * 2 * lon / LONGITUDES + spin;
				double p1 = Math.PI * 2 * (lon + 1) / LONGITUDES + spin;
				float u0 = lon / (float) LONGITUDES, u1 = (lon + 1) / (float) LONGITUDES;
				Vec3 a = unit(t0, p0), bb = unit(t0, p1), c = unit(t1, p1), d = unit(t1, p0);
				float qb = base, qr = rim;
				if (cutRing != null) {
					double dist = center.add(unit((t0 + t1) / 2, (p0 + p1) / 2).scale(r)).distanceTo(cutRing);
					if (dist > front) continue;
					float hot = (float) Math.max(0, 1 - (front - dist) / edge);
					qb = Math.min(1f, base + 0.5f * hot);
					qr = rim + 0.5f * hot;
				}
				if (inside) {
					sphereVertex(pose, buffer, center, d, r, camera, u0, v1, qb, qr, true);
					sphereVertex(pose, buffer, center, c, r, camera, u1, v1, qb, qr, true);
					sphereVertex(pose, buffer, center, bb, r, camera, u1, v0, qb, qr, true);
					sphereVertex(pose, buffer, center, a, r, camera, u0, v0, qb, qr, true);
				} else {
					sphereVertex(pose, buffer, center, a, r, camera, u0, v0, qb, qr, false);
					sphereVertex(pose, buffer, center, bb, r, camera, u1, v0, qb, qr, false);
					sphereVertex(pose, buffer, center, c, r, camera, u1, v1, qb, qr, false);
					sphereVertex(pose, buffer, center, d, r, camera, u0, v1, qb, qr, false);
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
	 * A smooth tube of light from the ring to the bubble's surface, sagging a little, with a soft
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
		// The rope starts right at the ring, a hand's length from the eye, so it is thin there and
		// grows to full width over its first block; otherwise it would fill the view.
		double taper = Math.min(1, span);
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
				double width = 0.35 + 0.65 * Math.min(1, f * span / taper);
				ring[j] = at.add(normals[j].scale(radius * width));
			}
			// Pulses travel out along the rope, a few blocks apart.
			double wave = Math.sin(f * span * 1.2 - time * 0.9);
			float bright = (float) (0.78 + 0.22 * Math.max(0, wave));
			if (prev != null) {
				// Each segment shows half a band of the texture.
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
			vertex(pose, buffer, p, camera, u, v, 0.6f * bright, bright, 0.72f * bright, alpha, n);
			return;
		}
		// A round tube: brightest down the middle facing you, a little deeper green towards its sides.
		double facing = Math.abs(n.dot(camera.subtract(p).normalize()));
		float shade = (float) (0.7 + 0.3 * facing) * bright;
		vertex(pose, buffer, p, camera, u, v, 0.55f * shade + 0.1f * (float) facing, shade, 0.7f * shade, 1f, n);
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
				.setLight(ShaderGlow.light(0.8f))
				.setNormal(pose, (float) n.x, (float) n.y, (float) n.z);
	}

	private static VertexConsumer tinted(VertexConsumer buffer, Corps corps) {
		return corps == Corps.GREEN ? buffer : new Tinted(buffer, corps);
	}

	/** Turns the bubble's and string's green vertex colours into the bearer's corps colour. */
	private record Tinted(VertexConsumer to, Corps corps) implements VertexConsumer {
		@Override
		public VertexConsumer addVertex(float x, float y, float z) {
			to.addVertex(x, y, z);
			return this;
		}

		@Override
		public VertexConsumer setColor(int r, int g, int b, int a) {
			int rgb = CorpsTint.apply(corps, r << 16 | g << 8 | b);
			to.setColor(rgb >> 16 & 0xFF, rgb >> 8 & 0xFF, rgb & 0xFF, a);
			return this;
		}

		@Override
		public VertexConsumer setColor(int argb) {
			to.setColor(CorpsTint.apply(corps, argb));
			return this;
		}

		@Override
		public VertexConsumer setUv(float u, float v) {
			to.setUv(u, v);
			return this;
		}

		@Override
		public VertexConsumer setUv1(int u, int v) {
			to.setUv1(u, v);
			return this;
		}

		@Override
		public VertexConsumer setUv2(int u, int v) {
			to.setUv2(u, v);
			return this;
		}

		@Override
		public VertexConsumer setUv3(float u, float v) {
			to.setUv3(u, v);
			return this;
		}

		@Override
		public VertexConsumer setNormal(float x, float y, float z) {
			to.setNormal(x, y, z);
			return this;
		}

		@Override
		public VertexConsumer setLineWidth(float width) {
			to.setLineWidth(width);
			return this;
		}
	}
}
