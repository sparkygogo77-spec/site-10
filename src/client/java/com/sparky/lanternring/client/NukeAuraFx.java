package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import net.minecraft.client.Minecraft;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.Vec3;

/**
 * The Fear Nuke's yellow aura (server side: corps/FearNuke's Burn): a shell of yellow light sweeps out
 * from the blast, and everything inside it burns. The server turns the blocks it reaches into yellow
 * hard light and then air; this draws the shell itself and the fire, all on the client so a nuke
 * costs no particle packets.
 */
public final class NukeAuraFx {
	private record Aura(Vec3 centre, double radius, int sweep, int burn, long start) {
	}

	private static final List<Aura> AURAS = new ArrayList<>();

	private NukeAuraFx() {
	}

	static void start(Vec3 centre, double radius, int sweep, int burn) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		AURAS.add(new Aura(centre, radius, Math.max(1, sweep), burn, mc.level.getGameTime()));
		// The flash, and the ground shakes for everyone near.
		mc.level.addParticle(ParticleTypes.EXPLOSION_EMITTER, centre.x, centre.y, centre.z, 0, 0, 0);
		if (mc.player != null) {
			double d = mc.player.position().distanceTo(centre);
			if (d < radius * 6) RingShake.kick((float) (3.0 * (1 - d / (radius * 6))));
		}
	}

	static void clear() {
		AURAS.clear();
	}

	static void tick(Minecraft mc) {
		if (AURAS.isEmpty()) return;
		long now = mc.level.getGameTime();
		RandomSource r = mc.level.getRandom();
		Corps before = CorpsTint.enter(Corps.YELLOW);
		try {
			for (Iterator<Aura> it = AURAS.iterator(); it.hasNext(); ) {
				Aura a = it.next();
				long age = now - a.start;
				if (age > a.sweep + a.burn + 30 || age < 0) {
					it.remove();
					continue;
				}
				double front = a.radius * Math.min(1.0, (age + 1) / (double) a.sweep);
				if (age <= a.sweep + a.burn) {
					// The shell of the aura, the eviscerating front.
					int shell = LabFx.count(140 + (float) (front * 12));
					for (int i = 0; i < shell; i++) {
						Vec3 d = onSphere(r);
						Vec3 at = a.centre.add(d.scale(front));
						LabFx.spawn(ModParticles.MOTE, at, d.scale(0.08), 2.2f);
					}
				}
				// Everything inside it burns.
				double inside = Math.min(front, a.radius);
				int fire = LabFx.count(age < a.sweep + a.burn ? 70 : 25);
				for (int i = 0; i < fire; i++) {
					Vec3 at = a.centre.add(onSphere(r).scale(inside * Math.cbrt(r.nextDouble())));
					mc.level.addParticle(r.nextInt(3) == 0 ? ParticleTypes.FLAME : ParticleTypes.FLAME,
							at.x, at.y, at.z, r.nextGaussian() * 0.05, 0.05 + r.nextDouble() * 0.15, r.nextGaussian() * 0.05);
					if (i % 4 == 0) mc.level.addParticle(ParticleTypes.LARGE_SMOKE, at.x, at.y, at.z, 0, 0.12, 0);
					if (i % 3 == 0) LabFx.spawn(ModParticles.SPARK, at, onSphere(r).scale(0.25), 1.4f);
				}
			}
		} finally {
			CorpsTint.restore(before);
		}
	}

	private static Vec3 onSphere(RandomSource r) {
		double z = r.nextDouble() * 2 - 1, a = r.nextDouble() * Math.PI * 2, s = Math.sqrt(1 - z * z);
		return new Vec3(s * Math.cos(a), z, s * Math.sin(a));
	}
}
