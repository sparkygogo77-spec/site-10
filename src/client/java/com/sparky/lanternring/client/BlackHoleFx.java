package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.BlackHoles;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.Vec3;

/**
 * Draws the Black Hole (see BlackHoles): a black core, a spinning accretion disk of streaky green
 * gas tipped toward the bearer, the bright photon ring and smeared halo of light round the core
 * (the light from the far side of the disk, bent round the hole), a dark shadow just outside the
 * core, and streaks of matter spiralling in faster and faster. The side of the disk coming toward
 * you is brighter, like a real one.
 *
 * <p>The light is one translucent mesh on one texture sheet (black_hole.png, drawn by
 * tools/black_hole_textures.py), so the game sorts it back to front: the far side of the disk
 * goes behind the core and the near side crosses in front of it. The core is a separate solid
 * ball and its shadow a plain (unlit, not emissive) translucent ring: shader packs treat emissive
 * entity layers as added light, so black drawn there vanished and you could see straight through
 * the hole. Solid, it hides whatever is inside it.
 *
 * <p>The longer a hole lives and the more it eats (BLACK_HOLE_FEED from the server), the hungrier
 * it gets: the disk and photon ring burn brighter and whiter, arms of light spiral in from well
 * outside the disk, and more matter streams in faster. Up close the rest of the screen sinks into
 * darkness round it (BlackHoleDark).
 */
public final class BlackHoleFx {
	private static final RenderType SHEET = RenderTypes.entityTranslucentEmissive(LanternRing.id("textures/entity/black_hole.png"));
	/** The core: solid, so it hides what's inside it and stays black under shader packs. */
	private static final RenderType CORE = RenderTypes.entitySolid(LanternRing.id("textures/entity/black_hole.png"));
	/** The shadow round the core: ordinary translucent, so it darkens rather than adding light. */
	private static final RenderType SHADOW = RenderTypes.entityTranslucent(LanternRing.id("textures/entity/black_hole.png"));
	/** Lightmap for the core and shadow: none at all. */
	private static final int NO_LIGHT = 0;
	private static final float TEX_W = 512, TEX_H = 256;
	/** Areas of the sheet: the disk (u 0-1, v DISK_V0-DISK_V1), the glow dot, the ring line and black. */
	private static final float DISK_V0 = 1 / TEX_H, DISK_V1 = 127 / TEX_H;
	private static final float[] GLOW = {1 / TEX_W, 129 / TEX_H, 63 / TEX_W, 191 / TEX_H};
	private static final float[] LINE = {66 / TEX_W, 129 / TEX_H, 94 / TEX_W, 191 / TEX_H};
	private static final float BLACK_U = 104 / TEX_W, BLACK_V = 136 / TEX_H;
	/** Ticks the flash lasts after it collapses. */
	private static final int FLASH = 12;
	/** Disk radii, in core radii. */
	private static final float DISK_IN = 1.4f, DISK_OUT = 5f;

	private static final class Bit {
		float r, angle, h, pr, pa, ph;
		float size;

		void save() {
			pr = r;
			pa = angle;
			ph = h;
		}
	}

	static final class Hole {
		final Vec3 center;
		/** The disk's axis and two directions in its plane. */
		final Vec3 n, e1, e2;
		final long start;
		final int pullTicks;
		final int size;
		final float core;
		final List<Bit> bits = new ArrayList<>();
		boolean burst;
		/** Things it has swallowed (from the server), and that count eased in so it brightens smoothly. */
		int fed;
		float shownFed, prevShownFed;
		/** A flare of the photon ring each time it swallows something, fading. */
		float gulp, prevGulp;

		Hole(Vec3 center, Vec3 axis, long start, int pullTicks, int size) {
			this.center = center;
			this.n = axis.lengthSqr() < 1.0e-4 ? new Vec3(0, 1, 0) : axis.normalize();
			Vec3 side = Math.abs(n.y) < 0.9 ? new Vec3(0, 1, 0) : new Vec3(1, 0, 0);
			this.e1 = side.cross(n).normalize();
			this.e2 = n.cross(e1).normalize();
			this.start = start;
			this.pullTicks = pullTicks;
			this.size = size;
			this.core = (float) BlackHoles.coreRadius(size);
		}

		float collapseAt() {
			return BlackHoles.GROW + pullTicks;
		}

		float end() {
			return collapseAt() + BlackHoles.COLLAPSE;
		}

		/** The hole's size from 0 to 1 at this age: swelling open, a slow throb, then crushed down. */
		float scale(float age) {
			if (age < BlackHoles.GROW) {
				float x = age / BlackHoles.GROW;
				// Ease out with a little overshoot.
				float c = 1.7f;
				float y = x - 1;
				return Math.max(0, 1 + (c + 1) * y * y * y + c * y * y);
			}
			if (age < collapseAt()) return 1 + 0.04f * Mth.sin(age * 0.45f);
			float x = Math.min(1, (age - collapseAt()) / BlackHoles.COLLAPSE);
			// It swells a touch before it is crushed to nothing.
			return (1 - x * x) * (1 + 0.25f * Mth.sin(x * Mth.PI));
		}

		/** How fast the disk turns at radius r (in blocks), radians per tick: faster near the core, and as it collapses. */
		float spin(float r, float age) {
			float base = 0.32f * (float) Math.pow(core / Math.max(r, core), 1.5);
			if (age > collapseAt()) base *= 1 + 3 * (age - collapseAt()) / BlackHoles.COLLAPSE;
			return base;
		}

		/**
		 * How hungry it looks, 0 to 1: rising through its life and with everything it eats. Drives
		 * the brightness of its light and how hard matter flows in.
		 */
		float hunger(float age, float partial) {
			float life = Mth.clamp((age - BlackHoles.GROW) / Math.max(1f, pullTicks), 0, 1);
			float eaten = Mth.lerp(partial, prevShownFed, shownFed);
			return Mth.clamp(0.55f * life + 0.06f * eaten, 0, 1);
		}

		float gulp(float partial) {
			return Mth.lerp(partial, prevGulp, gulp);
		}

		Vec3 at(float r, float angle, float h) {
			return center.add(e1.scale(r * Mth.cos(angle))).add(e2.scale(r * Mth.sin(angle))).add(n.scale(h));
		}
	}

	private static final List<Hole> HOLES = new ArrayList<>();

	private BlackHoleFx() {
	}

	public static void register() {
		LevelRenderEvents.COLLECT_SUBMITS.register(BlackHoleFx::submit);
		ClientTickEvents.END_CLIENT_TICK.register(BlackHoleFx::tick);
		BlackHoleDark.register();
	}

	/** From the server: a hole opened at center with its disk round axis; it stays open pullTicks. */
	public static void open(Vec3 center, Vec3 axis, int pullTicks, int size) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		Hole hole = new Hole(center, axis, mc.level.getGameTime(), pullTicks, size);
		HOLES.add(hole);
		LabFx.spawn(ModParticles.SPARK, center, Vec3.ZERO, 3f + 2f * size);
		RandomSource r = mc.level.getRandom();
		// A ring of light snaps inward as it opens.
		int n = LabFx.count(30 + 15 * size);
		for (int i = 0; i < n; i++) {
			double a = i * Math.PI * 2 / n;
			Vec3 out = hole.e1.scale(Math.cos(a)).add(hole.e2.scale(Math.sin(a)));
			double far = BlackHoles.pullRadius(size) * 0.5;
			ConstructParticle p = LabFx.spawn(ModParticles.MOTE, center.add(out.scale(far)), out.scale(-far / 14).add(LabFx.jitter(r, 0.02)), 1.4f);
			if (p != null) p.lasting(14);
		}
	}

	/** From the server: the hole at center has now eaten count things. */
	public static void fed(Vec3 center, int count) {
		Hole best = null;
		double bestDist = 1;
		for (Hole hole : HOLES) {
			double d = hole.center.distanceToSqr(center);
			if (d < bestDist) {
				best = hole;
				bestDist = d;
			}
		}
		if (best == null || count <= best.fed) return;
		best.fed = count;
		best.gulp = 1;
	}

	/** The open hole nearest the camera, for BlackHoleDark: null if none. */
	static Hole nearest(Vec3 cam) {
		Hole best = null;
		double bestDist = Double.MAX_VALUE;
		for (Hole hole : HOLES) {
			double d = hole.center.distanceToSqr(cam);
			if (d < bestDist) {
				best = hole;
				bestDist = d;
			}
		}
		return best;
	}

	/**
	 * How dark the screen round this hole gets, 0 to 1, for a camera at cam: nothing from well
	 * outside its pull, deepening the closer you come and the longer it lives and feeds, gone as
	 * it collapses. At 1 its green is the only light left (J, 2026-10-13).
	 */
	static float darkness(Hole hole, Vec3 cam, float now) {
		float age = now - hole.start;
		if (age >= hole.end()) return 0;
		float scale = Mth.clamp(hole.scale(age), 0, 1);
		float reach = (float) BlackHoles.pullRadius(hole.size);
		float far = reach * 3f, near = hole.core * 3f;
		float d = (float) cam.distanceTo(hole.center);
		float x = Mth.clamp((far - d) / (far - near), 0, 1);
		x = x * x * (3 - 2 * x);
		float h = hole.hunger(age, 0);
		return x * scale * (0.55f + 0.45f * h);
	}

	/** How dark the world is at cam from the nearest open hole, 0 to 1 (SunDim turns the light down by it). */
	public static float darknessAt(Vec3 cam, float now) {
		Hole hole = nearest(cam);
		return hole == null ? 0 : darkness(hole, cam, now);
	}

	/** The centre of the open hole nearest from (null if none), for tests. */
	public static Vec3 nearestCenter(Vec3 from) {
		Hole hole = nearest(from);
		return hole == null ? null : hole.center;
	}

	static Vec3 center(Hole hole) {
		return hole.center;
	}

	/**
	 * How far round the core the screen stays clear, in blocks, at this darkness: well past the
	 * disk while you're far off, pulling in to the bright inner swirl as the dark deepens. The
	 * world inside it goes dark by its lighting (SunDim), so the green is left shining alone.
	 */
	static float clearRadius(Hole hole, float now, float dark) {
		float age = now - hole.start;
		float core = hole.core * Mth.clamp(hole.scale(age), 0, 1.2f);
		return core * Mth.lerp(dark * dark, DISK_OUT * 1.5f, DISK_OUT * 0.75f);
	}

	/** From the server while the bearer aims: a small whirl of light where it will open, and its reach traced faintly. */
	public static void marker(Vec3 center, float reach, int size) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		RandomSource r = mc.level.getRandom();
		float core = (float) BlackHoles.coreRadius(size);
		double t = mc.level.getGameTime() * 0.35;
		for (int i = 0; i < 6; i++) {
			double a = t + i * Math.PI / 3;
			Vec3 out = new Vec3(Math.cos(a), 0, Math.sin(a));
			Vec3 tangent = new Vec3(-Math.sin(a), 0, Math.cos(a));
			ConstructParticle p = LabFx.spawn(ModParticles.MOTE, center.add(out.scale(core * 2.4)),
					out.scale(-core * 0.12).add(tangent.scale(core * 0.18)), 0.9f + 0.2f * size);
			if (p != null) p.lasting(8);
		}
		LabFx.spawn(ModParticles.SPARK, center, Vec3.ZERO, 0.6f + 0.3f * size);
		// The edge of its pull, a few dots at a time going round.
		for (int i = 0; i < LabFx.count(3 + size); i++) {
			double a = r.nextDouble() * Math.PI * 2;
			ConstructParticle p = LabFx.spawn(ModParticles.MOTE, center.add(Math.cos(a) * reach, (r.nextDouble() - 0.5) * 0.4, Math.sin(a) * reach),
					Vec3.ZERO, 0.6f);
			if (p != null) p.lasting(10);
		}
	}

	// ---- every tick: the matter falling in ---------------------------------------------------

	private static void tick(Minecraft mc) {
		if (mc.level == null) {
			HOLES.clear();
			return;
		}
		if (mc.isPaused()) return;
		long now = mc.level.getGameTime();
		RandomSource r = mc.level.getRandom();
		for (Iterator<Hole> it = HOLES.iterator(); it.hasNext(); ) {
			Hole hole = it.next();
			float age = now - hole.start;
			if (age > hole.end() + FLASH || age < -2) {
				it.remove();
				continue;
			}
			if (age >= hole.end() && !hole.burst) {
				hole.burst = true;
				collapseBurst(hole, r);
			}
			float scale = hole.scale(age);
			float reach = (float) BlackHoles.pullRadius(hole.size);
			hole.prevShownFed = hole.shownFed;
			hole.shownFed += (hole.fed - hole.shownFed) * 0.12f;
			hole.prevGulp = hole.gulp;
			hole.gulp *= 0.8f;
			float hunger = hole.hunger(age, 1);
			// Keep a crowd of bits spiralling in while it's open: more, and faster, the hungrier it is.
			int want = age < hole.collapseAt() ? (int) ((40 + 50 * hole.size) * (1 + 1.5f * hunger) * Math.min(1, age / 10f) * LabSettings.get().amount()) : 0;
			for (int i = 0; hole.bits.size() < want && i < 12; i++) {
				Bit b = new Bit();
				b.r = hole.core * 2.2f + r.nextFloat() * (reach * 0.85f - hole.core * 2.2f);
				b.angle = r.nextFloat() * Mth.TWO_PI;
				b.h = (r.nextFloat() - 0.5f) * b.r * 0.7f;
				b.size = 0.05f + r.nextFloat() * 0.09f;
				b.save();
				hole.bits.add(b);
			}
			float pullIn = (age >= hole.collapseAt() ? 2.5f : 1f) * (1 + 1.4f * hunger);
			for (Iterator<Bit> bi = hole.bits.iterator(); bi.hasNext(); ) {
				Bit b = bi.next();
				b.save();
				b.angle += hole.spin(b.r, age) * 1.3f;
				b.r -= pullIn * (0.03f + 0.9f * hole.core / Math.max(b.r, 0.1f) * 0.25f) * (0.6f + 0.4f * hole.size);
				b.h *= 0.9f;
				if (b.r < hole.core * Math.max(0.2f, scale) * 1.05f) {
					// Swallowed: a last flick of light at the edge.
					if (r.nextInt(4) == 0) LabFx.spawn(ModParticles.SPARK, hole.at(b.r, b.angle, b.h), Vec3.ZERO, 0.5f);
					bi.remove();
				}
			}
			// Now and then a spark is flung off the inner edge of the disk.
			if (age < hole.collapseAt() && r.nextFloat() < (0.4f + 0.6f * hunger) * LabSettings.get().amount()) {
				float a = r.nextFloat() * Mth.TWO_PI;
				float rr = hole.core * DISK_IN * scale;
				Vec3 p = hole.at(rr, a, 0);
				Vec3 tangent = hole.e1.scale(-Mth.sin(a)).add(hole.e2.scale(Mth.cos(a)));
				ConstructParticle c = LabFx.spawn(ModParticles.MOTE, p, tangent.scale(0.25).add(hole.n.scale((r.nextFloat() - 0.5) * 0.3)), 0.8f);
				if (c != null) c.lasting(8);
			}
		}
	}

	/** It's gone: a white flash, a ring of light racing out along the disk, and shards everywhere. */
	private static void collapseBurst(Hole hole, RandomSource r) {
		LabFx.spawn(ModParticles.SPARK, hole.center, Vec3.ZERO, 6f + 3f * hole.size);
		int n = LabFx.count(50 + 25 * hole.size);
		for (int i = 0; i < n; i++) {
			double a = i * Math.PI * 2 / n;
			Vec3 out = hole.e1.scale(Math.cos(a)).add(hole.e2.scale(Math.sin(a)));
			ConstructParticle p = LabFx.spawn(ModParticles.MOTE, hole.center.add(out.scale(0.5)), out.scale(0.45 + 0.15 * hole.size), 1.8f);
			if (p != null) p.lasting(16);
		}
		for (int i = 0; i < LabFx.count(30 + 15 * hole.size); i++) {
			LabFx.spawn(ModParticles.SHARD, hole.center.add(LabFx.jitter(r, 1)), LabFx.jitter(r, 1.1), 1.4f);
		}
	}

	// ---- drawing ----------------------------------------------------------------------------

	private static void submit(LevelRenderContext ctx) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null || HOLES.isEmpty()) return;
		float partial = ctx.levelState().worldPartialTicks;
		float now = mc.level.getGameTime() + partial;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		for (Hole hole : HOLES) {
			float age = now - hole.start;
			PoseStack pose = ctx.poseStack();
			pose.pushPose();
			pose.translate(hole.center.x - cam.x, hole.center.y - cam.y, hole.center.z - cam.z);
			Vec3 eye = cam.subtract(hole.center);
			if (age < hole.end()) {
				float core = hole.core * hole.scale(age);
				if (core > 0.01f) {
					ctx.submitNodeCollector().submitCustomGeometry(pose, CORE, (p, vc) -> sphere(p, vc, core));
					ctx.submitNodeCollector().submitCustomGeometry(pose, SHADOW, (p, vc) -> shadow(p, vc, eye, core));
				}
			}
			ctx.submitNodeCollector().submitCustomGeometry(pose, SHEET, (p, vc) -> draw(p, vc, hole, age, partial, eye));
			pose.popPose();
		}
	}

	/** Everything for one hole, in its own space (the centre at 0,0,0); eye is the camera. */
	private static void draw(PoseStack.Pose pose, VertexConsumer vc, Hole hole, float age, float partial, Vec3 eye) {
		if (age >= hole.end()) {
			flash(pose, vc, hole, age - hole.end(), eye);
			return;
		}
		float scale = hole.scale(age);
		if (scale <= 0.01f) return;
		float core = hole.core * scale;
		Vec3 toEye = eye.normalize();
		// Directions across the screen, for things drawn facing the camera.
		Vec3 right = new Vec3(0, 1, 0).cross(toEye);
		right = right.lengthSqr() < 1.0e-4 ? new Vec3(1, 0, 0) : right.normalize();
		Vec3 up = toEye.cross(right).normalize();

		float hunger = hole.hunger(age, partial);
		float gulp = hole.gulp(partial);
		int light = ShaderGlow.light(0.55f + 0.45f * Math.min(1, hunger + gulp * 0.5f));
		// Arms of light spiralling in from well outside the disk, stronger the hungrier it is.
		arms(pose, vc, hole, age, scale, eye, hunger, light);
		// The disk, its inner edges spinning faster than its outer ones.
		disk(pose, vc, hole, age, scale, eye, hunger, light);
		// The light from the far side of the disk, bent up over the core and down under it.
		float spin = age * hole.spin(core * 1.6f, age);
		billboardRing(pose, vc, right, up, core * 1.05f, core * (2.2f + 0.4f * hunger), 1f, 1f, 1f, 0f, 0.6f + 0.4f * hunger, DISK_UV, spin, light);
		// The photon ring: a thin bright line hugging the core, flaring each time it swallows something.
		float throb = 0.85f + 0.15f * Mth.sin(age * (0.7f + 0.5f * hunger));
		billboardRing(pose, vc, right, up, core * 0.97f, core * (1.2f + 0.3f * hunger + 0.25f * gulp), 1f, 1f, 1f, 0f,
				Math.min(1, throb * (0.7f + 0.3f * hunger) + gulp), LINE, 0, light);
		// Matter spiralling in, drawn as streaks along the way it moves.
		for (Bit b : hole.bits) {
			float r = Mth.lerp(partial, b.pr, b.r);
			float a = Mth.lerp(partial, b.pa, b.angle);
			float h = Mth.lerp(partial, b.ph, b.h);
			Vec3 at = hole.at(r, a, h).subtract(hole.center);
			if (hidden(at, eye, core) || inFront(at, eye, core) < 0.05f) continue;
			Vec3 along = hole.e1.scale(-Mth.sin(a)).add(hole.e2.scale(Mth.cos(a)));
			float speed = hole.spin(r, age) * r;
			float near = Mth.clamp(1 - (r - core) / (float) (BlackHoles.pullRadius(hole.size) * 0.85), 0, 1);
			float bright = 0.35f + 0.65f * near * near;
			streak(pose, vc, at, along, eye, b.size * (0.8f + near), b.size + speed * (2.5f + 2f * hunger), Math.min(1, bright * (0.8f + 0.5f * hunger)), light);
		}
	}

	/** The disk's area of the sheet as {u0, v0, u1, v1}, for the halo of bent light. */
	private static final float[] DISK_UV = {0, DISK_V0, 1, DISK_V1};

	private static final int DISK_BANDS = 9;
	private static final int DISK_SEGS = 72;

	private static void disk(PoseStack.Pose pose, VertexConsumer vc, Hole hole, float age, float scale, Vec3 eye, float hunger, int light) {
		float core = hole.core * scale;
		float in = core * DISK_IN, out = core * DISK_OUT;
		boolean above = eye.dot(hole.n) >= 0;
		// Young, it's a dimmer green; fed, it burns brighter and whiter.
		float fadeIn = Math.min(1, age / 8f) * (0.7f + 0.3f * hunger);
		float hot = 0.3f * hunger;
		for (int band = 0; band < DISK_BANDS; band++) {
			float t0 = band / (float) DISK_BANDS, t1 = (band + 1) / (float) DISK_BANDS;
			// Bands crowd toward the inner edge, where it's brightest and turns fastest.
			float r0 = in + (out - in) * t0 * t0, r1 = in + (out - in) * t1 * t1;
			float v0 = DISK_V0 + (DISK_V1 - DISK_V0) * t0 * t0, v1 = DISK_V0 + (DISK_V1 - DISK_V0) * t1 * t1;
			// Each band turns at the speed of its middle: the gas shears into a spiral.
			float turn = age * hole.spin((r0 + r1) / 2, age);
			for (int seg = 0; seg < DISK_SEGS; seg++) {
				float a0 = seg * Mth.TWO_PI / DISK_SEGS + turn, a1 = (seg + 1) * Mth.TWO_PI / DISK_SEGS + turn;
				float u0 = seg / (float) DISK_SEGS, u1 = (seg + 1) / (float) DISK_SEGS;
				if (above) {
					diskVertex(pose, vc, hole, eye, core, r0, a0, u0, v0, fadeIn, hot, light);
					diskVertex(pose, vc, hole, eye, core, r1, a0, u0, v1, fadeIn, hot, light);
					diskVertex(pose, vc, hole, eye, core, r1, a1, u1, v1, fadeIn, hot, light);
					diskVertex(pose, vc, hole, eye, core, r0, a1, u1, v0, fadeIn, hot, light);
				} else {
					diskVertex(pose, vc, hole, eye, core, r0, a1, u1, v0, fadeIn, hot, light);
					diskVertex(pose, vc, hole, eye, core, r1, a1, u1, v1, fadeIn, hot, light);
					diskVertex(pose, vc, hole, eye, core, r1, a0, u0, v1, fadeIn, hot, light);
					diskVertex(pose, vc, hole, eye, core, r0, a0, u0, v0, fadeIn, hot, light);
				}
			}
		}
	}

	private static void diskVertex(PoseStack.Pose pose, VertexConsumer vc, Hole hole, Vec3 eye, float core,
			float r, float a, float u, float v, float fade, float hot, int light) {
		Vec3 p = hole.e1.scale(r * Mth.cos(a)).add(hole.e2.scale(r * Mth.sin(a)));
		Vec3 toEye = eye.subtract(p).normalize();
		// The side turning toward you glows brighter and whiter; the side turning away dims.
		Vec3 moving = hole.e1.scale(-Mth.sin(a)).add(hole.e2.scale(Mth.cos(a)));
		float doppler = (float) moving.dot(toEye);
		float bright = Mth.clamp(0.95f + 0.45f * doppler, 0.35f, 1.4f) * fade * inFront(p, eye, core);
		float white = Math.max(0, doppler) * 0.25f + hot;
		vc.addVertex(pose, (float) p.x, (float) p.y, (float) p.z)
				.setColor(Math.min(1, 0.85f + white), 1f, Math.min(1, 0.9f + white), Math.min(1, bright))
				.setUv(u, v)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(light)
				.setNormal(pose, (float) hole.n.x, (float) hole.n.y, (float) hole.n.z);
	}

	/**
	 * How much of a point of the disk (relative to the centre) to show: none where it crosses in
	 * front of the core, so the core stays pure black and you can't see what is going into it.
	 */
	private static float inFront(Vec3 p, Vec3 eye, float core) {
		double eyeDist = eye.length();
		if (eyeDist < 1.0e-4) return 1;
		Vec3 axis = eye.scale(1 / eyeDist);
		double along = p.dot(axis);
		// Only the part nearer the eye than the centre covers it.
		if (along <= 0) return 1;
		double off = p.subtract(axis.scale(along)).length();
		// Seen from the eye, the point's offset from the core's middle shrinks as it comes nearer the core.
		double seen = off * eyeDist / Math.max(0.1, eyeDist - along);
		return Mth.clamp((float) ((seen - core * 0.95) / (core * 0.5)), 0, 1);
	}

	/** True if the core is between the eye and this point (both relative to the centre). */
	private static boolean hidden(Vec3 p, Vec3 eye, float core) {
		Vec3 d = p.subtract(eye);
		double len = d.length();
		if (len < 1.0e-4) return false;
		d = d.scale(1 / len);
		double t = -eye.dot(d);
		if (t < 0 || t > len) return false;
		return eye.add(d.scale(t)).lengthSqr() < core * core;
	}

	private static final int SPHERE_SEGS = 28, SPHERE_RINGS = 16;

	/** The core: a solid black ball, both sides drawn so it is black from inside too. */
	private static void sphere(PoseStack.Pose pose, VertexConsumer vc, float radius) {
		for (int ring = 0; ring < SPHERE_RINGS; ring++) {
			float p0 = -Mth.HALF_PI + Mth.PI * ring / SPHERE_RINGS, p1 = -Mth.HALF_PI + Mth.PI * (ring + 1) / SPHERE_RINGS;
			for (int seg = 0; seg < SPHERE_SEGS; seg++) {
				float y0 = seg * Mth.TWO_PI / SPHERE_SEGS, y1 = (seg + 1) * Mth.TWO_PI / SPHERE_SEGS;
				blackVertex(pose, vc, radius, y0, p0);
				blackVertex(pose, vc, radius, y1, p0);
				blackVertex(pose, vc, radius, y1, p1);
				blackVertex(pose, vc, radius, y0, p1);
				blackVertex(pose, vc, radius, y0, p1);
				blackVertex(pose, vc, radius, y1, p1);
				blackVertex(pose, vc, radius, y1, p0);
				blackVertex(pose, vc, radius, y0, p0);
			}
		}
	}

	/** The shadow: the core's darkness spilling past its edge, where light is bent away. */
	private static void shadow(PoseStack.Pose pose, VertexConsumer vc, Vec3 eye, float core) {
		Vec3 toEye = eye.normalize();
		Vec3 right = new Vec3(0, 1, 0).cross(toEye);
		right = right.lengthSqr() < 1.0e-4 ? new Vec3(1, 0, 0) : right.normalize();
		Vec3 up = toEye.cross(right).normalize();
		billboardRing(pose, vc, right, up, core * 0.98f, core * 1.6f, 0, 0, 0, 0.9f, 0f, null, 0, NO_LIGHT);
	}

	private static final int ARMS = 4, ARM_STEPS = 48;

	/**
	 * Arms of green light winding in from well outside the disk to the core, flat in the disk's
	 * plane, with bright pulses running down them toward the hole. Faint while it's young; strong
	 * once it has lived a while and eaten.
	 */
	private static void arms(PoseStack.Pose pose, VertexConsumer vc, Hole hole, float age, float scale, Vec3 eye, float hunger, int light) {
		float strength = (0.12f + 0.8f * hunger) * Math.min(1, age / 12f);
		if (strength < 0.02f) return;
		float core = hole.core * scale;
		float rOut = core * DISK_OUT * 1.9f, rIn = core * 1.05f;
		float logSpan = (float) Math.log(rOut / rIn);
		float turn = age * (0.05f + 0.07f * hunger);
		float flow = age * (0.35f + 0.55f * hunger);
		for (int arm = 0; arm < ARMS; arm++) {
			float base = arm * Mth.TWO_PI / ARMS + turn;
			for (int i = 0; i < ARM_STEPS; i++) {
				float t0 = i / (float) ARM_STEPS, t1 = (i + 1) / (float) ARM_STEPS;
				float r0 = rIn * (float) Math.exp(logSpan * (1 - t0)), r1 = rIn * (float) Math.exp(logSpan * (1 - t1));
				armQuad(pose, vc, hole, eye, core, base, r0, r1, rOut, logSpan, flow, strength, light);
			}
		}
	}

	private static void armQuad(PoseStack.Pose pose, VertexConsumer vc, Hole hole, Vec3 eye, float core, float base, float r0, float r1, float rOut,
			float logSpan, float flow, float strength, int light) {
		float[] alpha = new float[2];
		Vec3[] in = new Vec3[2], out = new Vec3[2];
		float[] rs = {r0, r1};
		for (int k = 0; k < 2; k++) {
			float r = rs[k];
			float lr = (float) Math.log(rOut / r);
			// A log spiral: the angle winds on as it falls in.
			float a = base + 2.2f * lr;
			Vec3 radial = hole.e1.scale(Mth.cos(a)).add(hole.e2.scale(Mth.sin(a)));
			Vec3 mid = radial.scale(r);
			float w = r * 0.16f;
			in[k] = mid.subtract(radial.scale(w));
			out[k] = mid.add(radial.scale(w));
			// Pulses that run inward: constant phase moves to smaller r as time goes on.
			float pulse = 0.5f + 0.5f * Mth.sin(5f * lr + flow);
			float t = lr / logSpan;
			// Fades in from nothing at the outer end and brightens toward the core.
			float edge = Mth.clamp(t * 4, 0, 1) * Mth.clamp((1 - t) * 10, 0, 1);
			alpha[k] = Math.min(1, strength * edge * (0.35f + 0.65f * pulse * pulse) * (0.5f + 0.7f * t)) * inFront(mid, eye, core);
		}
		float u0 = LINE[0], u1 = LINE[2];
		// Both windings, so it shows from above and below.
		armVertex(pose, vc, hole, in[0], u0, LINE[1], alpha[0], light);
		armVertex(pose, vc, hole, out[0], u1, LINE[1], alpha[0], light);
		armVertex(pose, vc, hole, out[1], u1, LINE[3], alpha[1], light);
		armVertex(pose, vc, hole, in[1], u0, LINE[3], alpha[1], light);
		armVertex(pose, vc, hole, in[1], u0, LINE[3], alpha[1], light);
		armVertex(pose, vc, hole, out[1], u1, LINE[3], alpha[1], light);
		armVertex(pose, vc, hole, out[0], u1, LINE[1], alpha[0], light);
		armVertex(pose, vc, hole, in[0], u0, LINE[1], alpha[0], light);
	}

	private static void armVertex(PoseStack.Pose pose, VertexConsumer vc, Hole hole, Vec3 p, float u, float v, float alpha, int light) {
		vc.addVertex(pose, (float) p.x, (float) p.y, (float) p.z)
				.setColor(0.8f, 1f, 0.85f, alpha)
				.setUv(u, v)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(light)
				.setNormal(pose, (float) hole.n.x, (float) hole.n.y, (float) hole.n.z);
	}

	private static void blackVertex(PoseStack.Pose pose, VertexConsumer vc, float radius, float yaw, float pitch) {
		float nx = Mth.cos(yaw) * Mth.cos(pitch), ny = Mth.sin(pitch), nz = Mth.sin(yaw) * Mth.cos(pitch);
		vc.addVertex(pose, nx * radius, ny * radius, nz * radius)
				.setColor(0f, 0f, 0f, 1f)
				.setUv(BLACK_U, BLACK_V)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(NO_LIGHT)
				.setNormal(pose, nx, ny, nz);
	}

	private static final int RING_SEGS = 64;

	/**
	 * A flat ring facing the camera from r0 to r1. With no texture area it is plain black, alpha
	 * going from a0 at its inner edge to a1 at its outer; with one, the area's u runs round the ring
	 * (turned by spin) and v from inner to outer, at strength a1.
	 */
	private static void billboardRing(PoseStack.Pose pose, VertexConsumer vc, Vec3 right, Vec3 up, float r0, float r1,
			float red, float green, float blue, float a0, float a1, float[] area, float spin, int light) {
		int steps = area == null ? 3 : 1;
		for (int s = 0; s < steps; s++) {
			float t0 = s / (float) steps, t1 = (s + 1) / (float) steps;
			float ri = r0 + (r1 - r0) * t0, ro = r0 + (r1 - r0) * t1;
			for (int seg = 0; seg < RING_SEGS; seg++) {
				float b0 = seg * Mth.TWO_PI / RING_SEGS + spin, b1 = (seg + 1) * Mth.TWO_PI / RING_SEGS + spin;
				if (area == null) {
					// The shadow fades off smoothly (squared, so most of the dark hugs the core).
					float ai = a0 * (1 - t0) * (1 - t0), ao = a0 * (1 - t1) * (1 - t1);
					ringVertex(pose, vc, right, up, ri, b0, 0, 0, 0, ai, BLACK_U, BLACK_V, light);
					ringVertex(pose, vc, right, up, ri, b1, 0, 0, 0, ai, BLACK_U, BLACK_V, light);
					ringVertex(pose, vc, right, up, ro, b1, 0, 0, 0, ao, BLACK_U, BLACK_V, light);
					ringVertex(pose, vc, right, up, ro, b0, 0, 0, 0, ao, BLACK_U, BLACK_V, light);
				} else {
					float u0 = area[0] + (area[2] - area[0]) * seg / RING_SEGS, u1 = area[0] + (area[2] - area[0]) * (seg + 1) / RING_SEGS;
					ringVertex(pose, vc, right, up, ri, b0, red, green, blue, a1, u0, area[1], light);
					ringVertex(pose, vc, right, up, ri, b1, red, green, blue, a1, u1, area[1], light);
					ringVertex(pose, vc, right, up, ro, b1, red, green, blue, a1, u1, area[3], light);
					ringVertex(pose, vc, right, up, ro, b0, red, green, blue, a1, u0, area[3], light);
				}
			}
		}
	}

	private static void ringVertex(PoseStack.Pose pose, VertexConsumer vc, Vec3 right, Vec3 up, float r, float angle,
			float red, float green, float blue, float alpha, float u, float v, int light) {
		Vec3 p = right.scale(r * Mth.cos(angle)).add(up.scale(r * Mth.sin(angle)));
		Vec3 normal = right.cross(up);
		vc.addVertex(pose, (float) p.x, (float) p.y, (float) p.z)
				.setColor(red, green, blue, alpha)
				.setUv(u, v)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(light)
				.setNormal(pose, (float) normal.x, (float) normal.y, (float) normal.z);
	}

	/** A glowing streak at p, stretched along dir, facing the camera as well as it can. */
	private static void streak(PoseStack.Pose pose, VertexConsumer vc, Vec3 p, Vec3 dir, Vec3 eye, float width, float length, float bright, int light) {
		Vec3 toEye = eye.subtract(p).normalize();
		Vec3 side = dir.cross(toEye);
		side = side.lengthSqr() < 1.0e-4 ? new Vec3(0, 1, 0) : side.normalize();
		Vec3 l = dir.scale(length / 2);
		Vec3 w = side.scale(width / 2);
		float g = Math.min(1, bright);
		glowVertex(pose, vc, p.subtract(l).subtract(w), GLOW[0], GLOW[3], g, toEye, light);
		glowVertex(pose, vc, p.add(l).subtract(w), GLOW[2], GLOW[3], g, toEye, light);
		glowVertex(pose, vc, p.add(l).add(w), GLOW[2], GLOW[1], g, toEye, light);
		glowVertex(pose, vc, p.subtract(l).add(w), GLOW[0], GLOW[1], g, toEye, light);
	}

	private static void glowVertex(PoseStack.Pose pose, VertexConsumer vc, Vec3 p, float u, float v, float alpha, Vec3 normal, int light) {
		vc.addVertex(pose, (float) p.x, (float) p.y, (float) p.z)
				.setColor(0.75f, 1f, 0.82f, alpha)
				.setUv(u, v)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(light)
				.setNormal(pose, (float) normal.x, (float) normal.y, (float) normal.z);
	}

	/** Just after it collapses: a bright flash that swells and fades. */
	private static void flash(PoseStack.Pose pose, VertexConsumer vc, Hole hole, float t, Vec3 eye) {
		float x = Mth.clamp(t / FLASH, 0, 1);
		Vec3 toEye = eye.normalize();
		Vec3 right = new Vec3(0, 1, 0).cross(toEye);
		right = right.lengthSqr() < 1.0e-4 ? new Vec3(1, 0, 0) : right.normalize();
		Vec3 up = toEye.cross(right).normalize();
		float r = hole.core * (2 + 6 * x);
		float a = (1 - x) * (1 - x);
		Vec3 l = right.scale(r), w = up.scale(r);
		int light = ShaderGlow.light();
		glowVertex(pose, vc, l.scale(-1).subtract(w), GLOW[0], GLOW[3], a, toEye, light);
		glowVertex(pose, vc, l.subtract(w), GLOW[2], GLOW[3], a, toEye, light);
		glowVertex(pose, vc, l.add(w), GLOW[2], GLOW[1], a, toEye, light);
		glowVertex(pose, vc, l.scale(-1).add(w), GLOW[0], GLOW[1], a, toEye, light);
		// And the photon ring, thrown outward as it fades.
		billboardRing(pose, vc, right, up, hole.core * (1 + 9 * x), hole.core * (1.6f + 11 * x), 0.55f, 1f, 0.65f, 0f, a, LINE, 0, light);
	}
}
