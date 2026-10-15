package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

/**
 * The ring lasers from Blender pass 836 (docs/handoff/2026-10-15-laser-test-picks): a straight core, glow and haze, each a
 * camera-facing ribbon from the ring to the hit, a flare at both ends, and per look a braid (H3), sparks (P1), an animated
 * construct texture (C1, C2) or a see-through hex tube (C3). Only the Beam's look: damage, range and the hit stay as they are.
 * The textures are white (intensity), tinted with the corps colour, and drawn additive (energy swirl), or under a shader
 * pack as see-through emissive, so the glow stays coloured and never turns white.
 */
final class LaserBeams {
	private static final Vec3 UP = new Vec3(0, 1, 0);
	/** The ring green (8, 255, 56); CorpsTint turns it into the other corps' colours. */
	private static final float GREEN_R = 8 / 255f, GREEN_G = 1f, GREEN_B = 56 / 255f;

	/** Full length in GROW ticks, held, then every width shrinks to 5% over FADE ticks. */
	private static final int GROW = 2;
	private static final int HOLD = 4;
	private static final int HOLD_CHARGED = 10;
	private static final int FADE = 4;
	/** The beam starts this far off the ring's face. */
	private static final double LIFT = 0.02;
	/** The fewest screen pixels (half widths) the core and the glow get, so a far beam stays a solid line (as OmegaFx). */
	private static final float CORE_PX = 1.0f, GLOW_PX = 2.5f;
	/** A charged shot is this much wider. */
	private static final float CHARGED = 1.6f;
	/** Ribbons are cut at least this often, so the minimum width follows the distance. */
	private static final double MAX_PIECE = 2.0;

	private static Identifier tex(String name) {
		return LanternRing.id("textures/misc/laser/" + name + ".png");
	}

	private static final Identifier CORE = tex("laser_core");
	private static final Identifier HAZE = tex("laser_haze");
	private static final Identifier FLARE = tex("laser_flare");
	private static final Identifier STRAND = tex("laser_strand");
	private static final Identifier SHEATH = tex("laser_strand_sheath");
	private static final Identifier TUBE = tex("laser_tube_hex");

	/** One textured layer: full width (blocks), flow (blocks a tick toward the hit), blocks a texture repeat, frames (1 = still). */
	private record Layer(Identifier texture, float width, double flow, double tile, int frames) {
		static Layer streak(String name, float width, double flow, double tile) {
			return new Layer(tex(name), width, flow, tile, 1);
		}

		/** A construct strip: 24 frames of 1 block, a frame every 4 ticks. */
		static Layer animated(String name, float width, double flow) {
			return new Layer(tex(name), width, flow, 1, 24);
		}
	}

	/** One look of the table in the hand-off: core width and wobble, its glow layers, haze width. */
	private record Look(float core, float wobble, List<Layer> glows, float haze) {
	}

	static Look look(LabSettings.BeamLook look) {
		return switch (look) {
			case H3_BRAID -> new Look(0.04f, 0.15f, List.of(Layer.streak("laser_glow_streak", 0.26f, 0.6, 9)), 0.75f);
			case N1_NEEDLE -> new Look(0.036f, 0.15f, List.of(Layer.streak("laser_glow_needle", 0.24f, 1.4, 25)), 0.5f);
			case N2_LAYERED -> new Look(0.064f, 0.15f, List.of(Layer.streak("laser_glow_layer_outer", 0.75f, 0.35, 6),
					Layer.streak("laser_glow_layer_inner", 0.30f, 1.3, 9)), 0.75f);
			case N3_CRACKLE -> new Look(0.064f, 0.4f, List.of(Layer.streak("laser_glow_crackle", 0.42f, 1.0, 3)), 0.75f);
			case P1_PULSES -> new Look(0.064f, 0.15f, List.of(Layer.streak("laser_glow_pulse", 0.42f, 2.0, 1)), 0.75f);
			case C1_WEAVE -> new Look(0.064f, 0.15f, List.of(Layer.animated("laser_glow_weave", 0.55f, 0.6)), 0.75f);
			case C2_BRICK -> new Look(0.064f, 0.15f, List.of(Layer.animated("laser_glow_brick", 0.55f, 0.6)), 0.75f);
			case C3_HEX_TUBE -> new Look(0.064f, 0.15f, List.of(Layer.streak("laser_glow_streak", 0.5f, 0.6, 9)), 0.75f);
			case HELIX -> throw new IllegalArgumentException("HELIX is drawn by HelixBeams / LabFx.useLine");
		};
	}

	private static final List<Beam> BEAMS = new ArrayList<>();

	private static final class Beam {
		Vec3 from;
		final Vec3 to;
		final int bearer;
		final LabSettings.BeamLook kind;
		final Look look;
		final float size;
		final int hold;
		final boolean burstAtEnd;
		final Corps corps = CorpsTint.current();
		int age;

		Beam(Vec3 from, Vec3 to, int bearer, LabSettings.BeamLook kind, boolean charged, boolean burstAtEnd) {
			this.from = from;
			this.to = to;
			this.bearer = bearer;
			this.kind = kind;
			this.look = look(kind);
			this.size = charged ? CHARGED : 1f;
			this.hold = charged ? HOLD_CHARGED : HOLD;
			this.burstAtEnd = burstAtEnd;
		}

		int life() {
			return GROW + hold + FADE;
		}

		/** How far along the line the tip is (0 = ring, 1 = hit). */
		static double reach(double t) {
			return Mth.clamp(t / GROW, 0, 1);
		}

		/** Width scale: 1 while it holds, down to 5% over the fade. */
		double width(double t) {
			double f = Mth.clamp((t - GROW - hold) / FADE, 0, 1);
			return size * (1 - 0.95 * f);
		}
	}

	private LaserBeams() {
	}

	static void fire(Vec3 from, Vec3 to, LabSettings.BeamLook look, boolean charged, boolean burstAtEnd, Player bearer) {
		if (look == LabSettings.BeamLook.HELIX) return;
		BEAMS.add(new Beam(from, to, bearer == null ? -1 : bearer.getId(), look, charged, burstAtEnd));
	}

	static void clear() {
		BEAMS.clear();
	}

	private static void anchor(Minecraft mc, Beam b) {
		Player bearer = RingEmit.bearer(b.bearer);
		if (bearer != null) b.from = RingEmit.ringFiring(bearer, mc.getDeltaTracker().getGameTimeDeltaPartialTick(false));
	}

	// ---- every tick: the hit burst and P1's sparks ----------------------------------------------

	static void tick(Minecraft mc) {
		RandomSource r = mc.level.getRandom();
		for (Iterator<Beam> it = BEAMS.iterator(); it.hasNext(); ) {
			Beam b = it.next();
			anchor(mc, b);
			Vec3 d = b.to.subtract(b.from);
			if (d.lengthSqr() < 1e-4 || b.age >= b.life()) {
				it.remove();
				continue;
			}
			Vec3 dir = d.normalize();
			Corps before = CorpsTint.enter(b.corps);
			if (b.age == GROW - 1 && b.burstAtEnd) LabFx.burst(b.to, 12, 0.18);
			// P1: four small sparks every 2 ticks while it holds, flying back and up off the hit, then falling.
			if (b.kind == LabSettings.BeamLook.P1_PULSES && b.age >= GROW - 1 && b.age < GROW + b.hold && b.age % 2 == 1) {
				for (int i = 0; i < 4; i++) {
					Vec3 v = dir.scale(-0.06).add(0, 0.05, 0).add(LabFx.jitter(r, 0.06));
					ConstructParticle p = LabFx.spawn(ModParticles.SPARK, b.to.add(LabFx.jitter(r, 0.15)), v, 0.7f);
					if (p != null) p.lasting(12).falling(0.2f);
				}
			}
			CorpsTint.restore(before);
			b.age++;
		}
	}

	// ---- every frame: the ribbons ---------------------------------------------------------------

	static void render(LevelRenderContext context) {
		if (BEAMS.isEmpty()) return;
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float partial = mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
		Vec3 camera = context.levelState().cameraRenderState.pos;
		float px = pixel(mc);
		boolean pack = SoulSight.shaderPackOn();
		for (Beam b : BEAMS) {
			anchor(mc, b);
			double t = b.age + partial;
			if (t >= b.life()) continue;
			Vec3 d = b.to.subtract(b.from);
			double len = d.length();
			if (len < 0.05) continue;
			Vec3 dir = d.scale(1 / len);
			Vec3 start = b.from.add(dir.scale(LIFT));
			double reach = Beam.reach(t) * (len - LIFT);
			if (reach < 0.02) continue;
			double w = b.width(t);
			float[] c = CorpsTint.apply(b.corps, GREEN_R, GREEN_G, GREEN_B);
			Look look = b.look;
			Strip line = new Strip(start, dir, reach);

			// Back to front: the tube and the braid (off the axis, so before the flat layers fill the depth), haze, glows, core, flares.
			if (b.kind == LabSettings.BeamLook.C3_HEX_TUBE) {
				submit(context, TUBE, pack, (pose, buf) -> line.tube(pose, buf, camera, 0.1 * w, 0.6 * t, (int) (t / 4), c, 0.8f, pack));
			}
			if (b.kind == LabSettings.BeamLook.H3_BRAID) {
				List<Vec3> braid0 = braid(start, dir, reach, t, 0, w), braid1 = braid(start, dir, reach, t, 1, w),
						braid2 = braid(start, dir, reach, t, 2, w);
				submit(context, SHEATH, pack, (pose, buf) -> {
					for (List<Vec3> s : List.of(braid0, braid1, braid2)) path(pose, buf, s, camera, (float) (0.07 * w), 0, 0.6 * t, c, 0.6f, pack);
				});
				submit(context, STRAND, pack, (pose, buf) -> {
					for (List<Vec3> s : List.of(braid0, braid1, braid2)) path(pose, buf, s, camera, (float) (0.032 * w), 0.5f * px, 0.6 * t, c, 1f, pack);
				});
			}
			submit(context, HAZE, pack, (pose, buf) -> line.ribbon(pose, buf, camera, (float) (look.haze * w), 0, 0, 1, 1, c, 0.35f, pack, true));
			for (Layer g : look.glows) {
				submit(context, g.texture, pack, (pose, buf) -> line.ribbon(pose, buf, camera, (float) (g.width * w), GLOW_PX * px,
						g.flow * t, g.tile, g.frames, c, 0.9f, pack, true, (int) (t / 4)));
			}
			float wobble = 1 + look.wobble * Mth.sin((float) (2.3 * Math.floor(t)));
			submit(context, CORE, pack, (pose, buf) -> line.ribbon(pose, buf, camera, (float) (look.core * w * wobble), CORE_PX * px,
					0, 1, 1, c, 1f, pack, false));
			float pulse = 0.85f + 0.15f * Mth.sin((float) (1.9 * t));
			submit(context, FLARE, pack, (pose, buf) -> {
				flare(pose, buf, start, camera, (float) (0.42 * w * pulse), c, 0.9f, pack);
				if (t >= GROW) flare(pose, buf, start.add(dir.scale(reach)), camera, (float) (0.9 * w * pulse), c, 1f, pack);
			});
		}
	}

	private static void submit(LevelRenderContext context, Identifier texture, boolean pack, Geometry geometry) {
		// Additive like BeamChargeGlow; under a shader pack (Iris) additive draws black, so see-through emissive there.
		RenderType type = pack ? RenderTypes.entityTranslucentEmissive(texture) : RenderTypes.energySwirl(texture, 0, 0);
		context.submitNodeCollector().submitCustomGeometry(context.poseStack(), type, geometry::draw);
	}

	@FunctionalInterface
	private interface Geometry {
		void draw(PoseStack.Pose pose, VertexConsumer buffer);
	}

	/** H3: one of three strands round the axis, 120° apart, opening out over the first 1.5 blocks. */
	private static List<Vec3> braid(Vec3 start, Vec3 dir, double reach, double t, int strand, double w) {
		Vec3 right = dir.cross(UP);
		right = right.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : right.normalize();
		Vec3 up = right.cross(dir).normalize();
		List<Vec3> pts = new ArrayList<>();
		double step = 0.1;
		for (double s = 0; ; s += step) {
			boolean last = s >= reach;
			if (last) s = reach;
			double a = 4.5 * s + 0.25 * t + strand * Math.PI * 2 / 3;
			double radius = 0.07 * w * Math.min(1, s / 1.5);
			pts.add(start.add(dir.scale(s)).add(right.scale(Math.cos(a) * radius)).add(up.scale(Math.sin(a) * radius)));
			if (last) break;
		}
		return pts;
	}

	/** A camera-facing ribbon along a bent path (the braid's strands), its texture flowing along it. */
	private static void path(PoseStack.Pose pose, VertexConsumer buffer, List<Vec3> pts, Vec3 camera, float width, float minPerBlock,
			double shift, float[] c, float strength, boolean pack) {
		int n = pts.size();
		if (n < 2) return;
		Vec3[] side = new Vec3[n];
		for (int i = 0; i < n; i++) side[i] = side(pts.get(Math.min(i + 1, n - 1)).subtract(pts.get(Math.max(i - 1, 0))), pts.get(i), camera, width, minPerBlock);
		double run = 0;
		for (int i = 0; i + 1 < n; i++) {
			Vec3 p0 = pts.get(i), p1 = pts.get(i + 1);
			double seg = p0.distanceTo(p1);
			// Each piece is under a block, so its v stays inside one repeat of the 1-block strand texture.
			double v0 = frac(run - shift);
			double v1 = v0 + seg;
			if (v1 > 1) {
				v0 = 0;
				v1 = seg;
			}
			quad(pose, buffer, p0, p1, side[i], side[i + 1], camera, (float) v0, (float) v1, 0, 1, c, strength, strength, pack);
			run += seg;
		}
	}

	/** The straight line from the ring to the hit, cut so each piece stays in one texture repeat. */
	private record Strip(Vec3 start, Vec3 dir, double reach) {
		void ribbon(PoseStack.Pose pose, VertexConsumer buffer, Vec3 camera, float width, float minPerBlock, double shift, double tile,
				int frames, float[] c, float strength, boolean pack, boolean fadeNear) {
			ribbon(pose, buffer, camera, width, minPerBlock, shift, tile, frames, c, strength, pack, fadeNear, 0);
		}

		/**
		 * A camera-facing strip of the given full width (never thinner on screen than minPerBlock x distance), texture u across it
		 * and v along it, one repeat every tile blocks, shifted shift blocks toward the hit. With frames > 1 the texture is a
		 * strip of frames and frame (mod frames) is the one shown.
		 */
		void ribbon(PoseStack.Pose pose, VertexConsumer buffer, Vec3 camera, float width, float minPerBlock, double shift, double tile,
				int frames, float[] c, float strength, boolean pack, boolean fadeNear, int frame) {
			if (width <= 0) return;
			double f = Math.floorMod(frame, frames);
			double s = 0;
			while (s < reach - 1e-4) {
				double phase = (s - shift) / tile;
				double next = Math.min(reach, Math.min(s + MAX_PIECE, (Math.floor(phase) + 1) * tile + shift));
				if (next <= s + 1e-5) next = Math.min(reach, s + 1e-3);
				double v0 = frac(phase);
				double v1 = v0 + (next - s) / tile;
				if (v1 > 1) v1 = 1;
				Vec3 p0 = start.add(dir.scale(s)), p1 = start.add(dir.scale(next));
				float a0 = strength * (fadeNear ? near(p0, camera) : 1), a1 = strength * (fadeNear ? near(p1, camera) : 1);
				quad(pose, buffer, p0, p1, side(dir, p0, camera, width, minPerBlock), side(dir, p1, camera, width, minPerBlock), camera,
						(float) ((f + v0) / frames), (float) ((f + v1) / frames), 0, 1, c, a0, a1, pack);
				s = next;
			}
		}

		/** C3: a see-through eight-sided tube round the core, wearing the hex texture twice round, cut like ribbon(). */
		void tube(PoseStack.Pose pose, VertexConsumer buffer, Vec3 camera, double radius, double shift, int frame, float[] c, float strength,
				boolean pack) {
			Vec3 right = dir.cross(UP);
			right = right.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : right.normalize();
			Vec3 up = right.cross(dir).normalize();
			int sides = 8;
			double f = Math.floorMod(frame, 24);
			double s = 0;
			while (s < reach - 1e-4) {
				double phase = s - shift;
				double next = Math.min(reach, Math.floor(phase) + 1 + shift);
				if (next <= s + 1e-5) next = Math.min(reach, s + 1e-3);
				double v0 = frac(phase), v1 = Math.min(1, v0 + (next - s));
				Vec3 c0 = start.add(dir.scale(s)), c1 = start.add(dir.scale(next));
				float a0 = strength * near(c0, camera), a1 = strength * near(c1, camera);
				// Far faces first, so the near ones (see-through) draw over them.
				Vec3 view = camera.subtract(c0);
				Vec3 r = right, u = up;
				List<Integer> order = new ArrayList<>();
				for (int j = 0; j < sides; j++) order.add(j);
				order.sort(java.util.Comparator.comparingDouble(j -> {
					double th = (j + 0.5) * Math.PI * 2 / sides;
					return r.scale(Math.cos(th)).add(u.scale(Math.sin(th))).dot(view);
				}));
				for (int j : order) {
					double th0 = j * Math.PI * 2 / sides, th1 = (j + 1) * Math.PI * 2 / sides;
					Vec3 o0 = right.scale(Math.cos(th0) * radius).add(up.scale(Math.sin(th0) * radius));
					Vec3 o1 = right.scale(Math.cos(th1) * radius).add(up.scale(Math.sin(th1) * radius));
					// Twice round: each half of the sides takes the texture's full width.
					float u0 = (j % (sides / 2)) / (sides / 2f), u1 = (j % (sides / 2) + 1) / (sides / 2f);
					float vv0 = (float) ((f + v0) / 24), vv1 = (float) ((f + v1) / 24);
					vertex(pose, buffer, c0.add(o0), camera, u0, vv0, c, a0, pack);
					vertex(pose, buffer, c0.add(o1), camera, u1, vv0, c, a0, pack);
					vertex(pose, buffer, c1.add(o1), camera, u1, vv1, c, a1, pack);
					vertex(pose, buffer, c1.add(o0), camera, u0, vv1, c, a1, pack);
					// The energy swirl draws both sides already; the emissive one culls, so it gets the other winding too.
					if (!pack) continue;
					vertex(pose, buffer, c1.add(o0), camera, u0, vv1, c, a1, pack);
					vertex(pose, buffer, c1.add(o1), camera, u1, vv1, c, a1, pack);
					vertex(pose, buffer, c0.add(o1), camera, u1, vv0, c, a0, pack);
					vertex(pose, buffer, c0.add(o0), camera, u0, vv0, c, a0, pack);
				}
				s = next;
			}
		}
	}

	/** Half of the ribbon's width, sideways to both the line and the view. */
	private static Vec3 side(Vec3 along, Vec3 at, Vec3 camera, float width, float minPerBlock) {
		Vec3 toCam = camera.subtract(at);
		Vec3 s = along.cross(toCam);
		if (s.lengthSqr() < 1e-10) return Vec3.ZERO;
		return s.normalize().scale(Math.max(width / 2, minPerBlock * toCam.length()));
	}

	/** One ribbon piece, wound as OmegaFx's ribbons so it faces the camera. */
	private static void quad(PoseStack.Pose pose, VertexConsumer buffer, Vec3 p0, Vec3 p1, Vec3 s0, Vec3 s1, Vec3 camera, float v0, float v1,
			float uIn, float uOut, float[] c, float a0, float a1, boolean pack) {
		if (a0 < 0.01f && a1 < 0.01f) return;
		vertex(pose, buffer, p0.subtract(s0), camera, uIn, v0, c, a0, pack);
		vertex(pose, buffer, p0.add(s0), camera, uOut, v0, c, a0, pack);
		vertex(pose, buffer, p1.add(s1), camera, uOut, v1, c, a1, pack);
		vertex(pose, buffer, p1.subtract(s1), camera, uIn, v1, c, a1, pack);
	}

	/** A camera-facing square flare of the given full width. */
	private static void flare(PoseStack.Pose pose, VertexConsumer buffer, Vec3 at, Vec3 camera, float width, float[] c, float strength,
			boolean pack) {
		Vec3 toCam = camera.subtract(at);
		if (toCam.lengthSqr() < 1e-6) return;
		Vec3 view = toCam.normalize();
		Vec3 right = view.cross(UP);
		right = right.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : right.normalize();
		Vec3 up = right.cross(view).normalize();
		// The ring's flare sits right in front of a first-person camera: keep it from filling the screen.
		float a = strength * Math.max(0.3f, near(at, camera));
		Vec3 r = right.scale(width / 2), u = up.scale(width / 2);
		vertex(pose, buffer, at.subtract(r).subtract(u), camera, 0, 1, c, a, pack);
		vertex(pose, buffer, at.add(r).subtract(u), camera, 1, 1, c, a, pack);
		vertex(pose, buffer, at.add(r).add(u), camera, 1, 0, c, a, pack);
		vertex(pose, buffer, at.subtract(r).add(u), camera, 0, 0, c, a, pack);
	}

	/**
	 * Additive: the brightness rides in the colour (so the glow stays saturated). Under a shader pack: the colour stays, and the
	 * brightness becomes how see-through it is, as BeamChargeGlow.glow does.
	 */
	private static void vertex(PoseStack.Pose pose, VertexConsumer buffer, Vec3 p, Vec3 camera, float u, float v, float[] c, float strength,
			boolean pack) {
		float k = pack ? 1f : strength;
		float a = pack ? Mth.clamp(strength * 0.6f, 0f, 1f) : 1f;
		buffer.addVertex(pose, (float) (p.x - camera.x), (float) (p.y - camera.y), (float) (p.z - camera.z))
				.setColor(c[0] * k, c[1] * k, c[2] * k, a)
				.setUv(u, v)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(ShaderGlow.light())
				.setNormal(pose, 0, 1, 0);
	}

	/** Fades the wide layers right at the camera, so your own beam doesn't fill the screen as it leaves your hand. */
	private static float near(Vec3 p, Vec3 camera) {
		return Mth.clamp((float) (p.distanceTo(camera) - 0.5) / 1.5f, 0f, 1f);
	}

	private static double frac(double x) {
		return x - Math.floor(x);
	}

	private static float pixel(Minecraft mc) {
		float fov = mc.options.fov().get();
		return 2f * (float) Math.tan(Math.toRadians(fov) / 2) / Math.max(240, mc.getWindow().getHeight());
	}
}
