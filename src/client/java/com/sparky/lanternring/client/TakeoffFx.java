package com.sparky.lanternring.client;

import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.net.RingFxPayload;
import net.minecraft.client.Minecraft;
import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.Vec3;

/**
 * Everyone's view of the pass 403 take-off and soft landing (TakeoffMoves moves the flyer; the server passes each
 * move on as FLIGHT_TAKEOFF or SOFT_LANDING): the poses (MovePoses) and the construct rings, drawn with the
 * construct pixels every power uses, in the flyer's corps colour.
 * <ul>
 * <li>the standing puff: a burst ring under the feet, 28 pixels flung out from 0.3 to 2.6 blocks over 10 ticks;
 * <li>the R3 dart: the same ring out to 1.8 blocks, trailing back about 0.12 blocks a tick;
 * <li>the L2 touchdown: a cushion ring out to 1.4 blocks.
 * </ul>
 */
final class TakeoffFx {
	/** Pixels in a ring, and the ticks they take to reach its edge. */
	private static final int PIXELS = 28, RING_TICKS = 10;
	/** Where the pixels start out from the middle. */
	private static final double START = 0.3;
	/** How far a pixel coasts over RING_TICKS for each block a tick it starts with (motes keep 92% a tick). */
	private static final double COAST = (1 - Math.pow(0.92, RING_TICKS)) / 0.08;

	private TakeoffFx() {
	}

	/** FLIGHT_TAKEOFF with value 1-3 (the standing puff, S1/S2a/S2b) or 4 (the dart). */
	static void takeoff(RingFxPayload fx) {
		int code = Math.round(fx.value());
		Vec3 dir = flat(fx.to().subtract(fx.from()));
		if (code == 4) {
			MovePoses.dart(fx.variant());
			ring(fx.from(), 1.8, dir.scale(-0.17));
		} else {
			MovePoses.hop(fx.variant());
			ring(fx.from(), 2.6, Vec3.ZERO);
		}
	}

	/** SOFT_LANDING: value 3 + take (L5, L4, L6) the pass 405 drop starts (1: an older client's, as L5), 2 touchdown, 0 cancelled. */
	static void landing(RingFxPayload fx) {
		int code = Math.round(fx.value());
		if (code == 1 || code >= 3) {
			LabSettings.SoftLanding[] takes = LabSettings.SoftLanding.values();
			MovePoses.land(fx.variant(), code == 1 ? LabSettings.SoftLanding.L5 : takes[Math.min(code - 3, takes.length - 1)]);
		} else if (code == 2) {
			MovePoses.touchdown(fx.variant());
			ring(fx.from(), 1.4, Vec3.ZERO);
		} else {
			MovePoses.landCancelled(fx.variant());
		}
	}

	/** A construct ring round "at", flat on the ground, reaching radius blocks over 10 ticks as it fades; drift is added to every pixel. */
	static void ring(Vec3 at, double radius, Vec3 drift) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		RandomSource r = mc.level.getRandom();
		double speed = (radius - START) / COAST;
		double spin = r.nextDouble() * Math.PI * 2;
		for (int i = 0; i < PIXELS; i++) {
			double a = spin + i * Math.PI * 2 / PIXELS;
			Vec3 out = new Vec3(Math.cos(a), 0, Math.sin(a));
			Vec3 v = out.scale(speed * (0.92 + 0.16 * r.nextDouble())).add(drift);
			ConstructParticle p = LabFx.spawn(ModParticles.MOTE, at.add(out.scale(START)).add(0, 0.06, 0), v, 1.2f);
			if (p != null) p.lasting(RING_TICKS + r.nextInt(3));
		}
		LabFx.spawn(ModParticles.SPARK, at.add(0, 0.1, 0), Vec3.ZERO, 2f);
	}

	private static Vec3 flat(Vec3 v) {
		Vec3 h = new Vec3(v.x, 0, v.z);
		return h.lengthSqr() < 1e-6 ? Vec3.ZERO : h.normalize();
	}
}
