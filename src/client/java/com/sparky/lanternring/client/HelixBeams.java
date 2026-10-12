package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.Vec3;

/**
 * The twin helix beam: two translucent hard-light tubes, textured and lit like a beacon beam, that
 * twist around the line from the ring to the target. A beam grows out of the ring, holds on the
 * target, then undoes itself, either shooting off into the target or snapping back into the ring.
 * The tubes are drawn every frame (so the motion is smooth); the sparks, burst and glow around
 * them are particles spawned each tick.
 */
final class HelixBeams {
	private static final Vec3 UP = new Vec3(0, 1, 0);
	private static final Identifier TEXTURE = LanternRing.id("textures/misc/helix_beam.png");
	private static final int FULL_BRIGHT = 0xF000F0;
	/** OverlayTexture.NO_OVERLAY: no hurt-red or white flash. */
	private static final int NO_OVERLAY = 10 << 16;

	private static final int GROW = 3;
	private static final int HOLD = 2;
	private static final int FADE = 3;
	/** How far apart the strands sit from the center line, and how fast they wind and spin. */
	private static final double RADIUS = 0.22;
	private static final double TWIST = 2.2;
	private static final double SPIN = 1.3;
	/** How far from the ring the two strands take to open out to their full radius. */
	private static final double EMERGE = 2.5;
	/** The two tube layers: a bright core and a wide faint shell, like a beacon beam. */
	private static final float CORE = 0.065f;
	private static final float SHELL = 0.15f;
	private static final int SIDES = 6;
	private static final double STEP = 0.12;

	private static final List<Beam> BEAMS = new ArrayList<>();

	private static final class Beam {
		Vec3 from;
		final Vec3 to;
		/** Fired by this client's player: the beam stays attached to the ring they see. */
		final boolean mine;
		/** Unravel back into the ring instead of shooting off into the target. */
		final boolean recall;
		final boolean burstAtEnd;
		/** 1 for a tap; the charged beam is fatter, with a wider, slower twist. */
		final float size;
		int age;

		Beam(Vec3 from, Vec3 to, boolean mine, boolean recall, boolean burstAtEnd, float size) {
			this.from = from;
			this.to = to;
			this.mine = mine;
			this.recall = recall;
			this.burstAtEnd = burstAtEnd;
			this.size = size;
		}

		/** How far along the line the tip and the tail are (0 = ring, 1 = target), at time t in ticks. */
		double head(double t) {
			if (t < GROW) return easeOut(t / GROW);
			return recall ? 1 - undo(t) : 1;
		}

		double tail(double t) {
			return recall ? 0 : undo(t);
		}

		/** 0 while the beam is whole, rising to 1 as it finishes undoing itself. */
		static double undo(double t) {
			return easeOut((t - GROW - HOLD) / FADE);
		}
	}

	private HelixBeams() {
	}

	static void fire(Vec3 from, Vec3 to, boolean recall, boolean burstAtEnd, float size) {
		Minecraft mc = Minecraft.getInstance();
		boolean mine = mc.player != null && mc.player.getEyePosition().distanceToSqr(from) < 2.5 * 2.5;
		BEAMS.add(new Beam(from, to, mine, recall, burstAtEnd, size));
	}

	static void clear() {
		BEAMS.clear();
	}

	private static double easeOut(double x) {
		x = Mth.clamp(x, 0, 1);
		return 1 - (1 - x) * (1 - x);
	}

	private static void anchor(Minecraft mc, Beam b) {
		if (b.mine && mc.player != null) b.from = LabFx.ringPos(mc, mc.player, mc.player.getMainArm());
	}

	// ---- every tick: sparks at the tip, the hit, and the glow around the beam --------------------

	static void tick(Minecraft mc) {
		RandomSource r = mc.level.getRandom();
		for (Iterator<Beam> it = BEAMS.iterator(); it.hasNext(); ) {
			Beam b = it.next();
			anchor(mc, b);
			Vec3 d = b.to.subtract(b.from);
			double len = d.length();
			if (len < 0.01 || b.age >= GROW + HOLD + FADE) {
				it.remove();
				continue;
			}
			Vec3 dir = d.scale(1 / len);
			double t = b.age + 1;
			double head = b.head(t) * len;
			double tail = b.tail(t) * len;
			Vec3 tip = b.from.add(dir.scale(head));

			if (b.age < GROW) LabFx.spawn(ModParticles.SPARK, tip, Vec3.ZERO, 2.4f);
			if (b.age == GROW - 1 && b.burstAtEnd) LabFx.burst(b.to, 12, 0.18);
			// A few motes of light drift off the lit part of the beam, kept clear of the ring.
			double near = Math.max(tail, Math.min(head, EMERGE));
			for (int i = 0; i < LabFx.count((float) (len / 4)); i++) {
				Vec3 c = b.from.add(dir.scale(Mth.lerp(r.nextDouble(), near, head)));
				LabFx.spawn(ModParticles.MOTE, c.add(LabFx.jitter(r, 0.5)), LabFx.jitter(r, 0.02), 0.8f);
			}
			if (b.age >= GROW + HOLD) {
				Vec3 fading = b.recall ? tip : b.from.add(dir.scale(tail));
				LabFx.spawn(ModParticles.SPARK, fading, Vec3.ZERO, 1.6f);
				for (int i = 0; i < LabFx.count(4); i++) {
					LabFx.spawn(ModParticles.MOTE, fading.add(LabFx.jitter(r, 0.3)), LabFx.jitter(r, 0.06), 0.6f);
				}
			}
			b.age++;
		}
	}

	// ---- every frame: the tubes ------------------------------------------------------------------

	static void render(LevelRenderContext context) {
		if (BEAMS.isEmpty()) return;
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float partial = mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
		Vec3 camera = context.levelState().cameraRenderState.pos;
		RenderType type = RenderTypes.beaconBeam(TEXTURE, true);
		for (Beam b : BEAMS) {
			anchor(mc, b);
			double t = b.age + partial;
			if (t >= GROW + HOLD + FADE) continue;
			double undo = Beam.undo(t);
			// Unravelling, the strands loosen, swell and thin out as the light dissipates.
			double radius = RADIUS * b.size * (1 + 0.6 * undo);
			float swell = (float) (1 + 0.8 * undo) * b.size;
			float fade = (float) (1 - 0.7 * undo);
			context.submitNodeCollector().submitCustomGeometry(context.poseStack(), type, (pose, buffer) -> {
				for (int strand = 0; strand < 2; strand++) {
					tube(pose, buffer, b, t, strand, radius, camera, SHELL * swell, 0.30f * fade, 0.5f);
					tube(pose, buffer, b, t, strand, radius, camera, CORE * swell, 0.85f * fade, 1f);
				}
			});
		}
	}

	/** One strand as a six-sided tube along its helix, from the beam's tail to its tip. */
	private static void tube(PoseStack.Pose pose, VertexConsumer buffer, Beam b, double t, int strand, double radius,
			Vec3 camera, float thickness, float alpha, float whiteness) {
		Vec3 d = b.to.subtract(b.from);
		double len = d.length();
		if (len < 0.01) return;
		Vec3 dir = d.scale(1 / len);
		Vec3 right = dir.cross(UP);
		right = right.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : right.normalize();
		Vec3 up = right.cross(dir).normalize();
		double start = b.tail(t) * len;
		double end = b.head(t) * len;
		if (end - start < 0.02) return;

		// Green core fading to a paler green: the shell is deeper green, the core almost white-green.
		float red = 0.25f + 0.35f * whiteness;
		float green = 1f;
		float blue = 0.35f + 0.25f * whiteness;
		double spin = t * SPIN + strand * Math.PI;
		double scroll = -t * 0.35;

		Vec3[] prev = null;
		double prevS = 0;
		for (double s = start; ; s += STEP) {
			boolean last = s >= end;
			if (last) s = end;
			double a = s * TWIST / b.size + spin;
			Vec3 radial = right.scale(Math.cos(a)).add(up.scale(Math.sin(a)));
			// The strands leave the ring together and open out into the helix.
			Vec3 center = b.from.add(dir.scale(s)).add(radial.scale(radius * Math.min(1, s / EMERGE)));
			Vec3 tangent = dir.add(right.scale(-Math.sin(a)).add(up.scale(Math.cos(a))).scale(radius * TWIST / b.size)).normalize();
			Vec3 n1 = radial.subtract(tangent.scale(radial.dot(tangent))).normalize();
			Vec3 n2 = tangent.cross(n1);
			// Taper the very ends so the tip reads as a point of light, not a cut-off pipe.
			// They also start as thin threads at the ring, so the beam doesn't fill a first-person view.
			double taper = Math.min(1, Math.min(s - start, end - s) / 0.3 + 0.35) * (0.25 + 0.75 * Math.min(1, s / EMERGE));
			Vec3[] ring = new Vec3[SIDES];
			for (int j = 0; j < SIDES; j++) {
				double th = j * Math.PI * 2 / SIDES;
				ring[j] = center.add(n1.scale(Math.cos(th) * thickness * taper)).add(n2.scale(Math.sin(th) * thickness * taper));
			}
			if (prev != null) {
				float v0 = pingPong(prevS * 0.5 + scroll);
				float v1 = pingPong(s * 0.5 + scroll);
				for (int j = 0; j < SIDES; j++) {
					int k = (j + 1) % SIDES;
					vertex(pose, buffer, prev[j], camera, 0, v0, red, green, blue, alpha);
					vertex(pose, buffer, prev[k], camera, 1, v0, red, green, blue, alpha);
					vertex(pose, buffer, ring[k], camera, 1, v1, red, green, blue, alpha);
					vertex(pose, buffer, ring[j], camera, 0, v1, red, green, blue, alpha);
				}
			}
			prev = ring;
			prevS = s;
			if (last) break;
		}
	}

	/** Runs 0..1..0 so the texture flows along the beam without needing to wrap. */
	private static float pingPong(double v) {
		double m = v - 2 * Math.floor(v / 2);
		return (float) (m < 1 ? m : 2 - m);
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
