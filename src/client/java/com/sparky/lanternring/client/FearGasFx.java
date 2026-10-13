package com.sparky.lanternring.client;

import com.sparky.lanternring.client.mixin.FogRendererAccessor;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import net.minecraft.client.Camera;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.fog.FogData;
import net.minecraft.client.renderer.fog.environment.FogEnvironment;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.material.FogType;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;
import org.joml.Vector3fc;

/**
 * The Fear Nuke's yellow gas, lingering where it burst for RingTuning.FEAR_GAS (corps/FearFrenzy):
 * inside it the view closes in to a yellow fog that darkens toward amber as it goes on, and low
 * drifts of yellow smoke roll over the ground round you. Shader packs draw their own fog; the
 * smoke still shows.
 */
public final class FearGasFx extends FogEnvironment {
	/** How far you can still see in the thick of it. */
	private static final float NEAR = 30f;
	private static final DustParticleOptions SMOKE = new DustParticleOptions(0xD9B428, 3f);
	private static final DustParticleOptions DARK = new DustParticleOptions(0x7A5A10, 3f);

	private record Gas(Vec3 centre, double radius, int life, long start) {
	}

	private static final List<Gas> GASES = new ArrayList<>();
	private static float strength, prevStrength, dark;

	public static void register() {
		FogRendererAccessor.lanternring$environments().add(0, new FearGasFx());
	}

	static void start(Vec3 centre, double radius, int life) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		GASES.add(new Gas(centre, radius, Math.max(1, life), mc.level.getGameTime()));
	}

	static void clear() {
		GASES.clear();
		strength = prevStrength = 0;
	}

	/** Test hook: how thick the gas is round you now, 0..1. */
	public static float strength() {
		return strength;
	}

	static void tick(Minecraft mc) {
		prevStrength = strength;
		long now = mc.level.getGameTime();
		float target = 0f, darkest = 0f;
		Vec3 eye = mc.player.position();
		RandomSource r = mc.level.getRandom();
		for (Iterator<Gas> it = GASES.iterator(); it.hasNext(); ) {
			Gas g = it.next();
			long age = now - g.start;
			if (age > g.life || age < -1) {
				it.remove();
				continue;
			}
			float k = age / (float) g.life;
			// It thickens fast, then thins out over its last stretch.
			float life = Math.min(1f, age / 20f) * Math.min(1f, (g.life - age) / 60f);
			double dx = eye.x - g.centre.x, dz = eye.z - g.centre.z;
			double d = Math.sqrt(dx * dx + dz * dz);
			float inside = (float) Mth.clamp((g.radius - d) / 8.0, 0, 1);
			if (inside * life > target) {
				target = inside * life;
				darkest = k;
			}
			// Low drifts of smoke round you while you're in it, and over the crater for anyone watching.
			if (inside > 0) {
				int n = LabFx.count(6 * life);
				for (int i = 0; i < n; i++) {
					double a = r.nextDouble() * Math.PI * 2, rr = 2 + r.nextDouble() * 14;
					double x = eye.x + Math.cos(a) * rr, z = eye.z + Math.sin(a) * rr;
					mc.level.addParticle(r.nextFloat() < k ? DARK : SMOKE, x, eye.y + r.nextDouble() * 2.5, z,
							0.02 * r.nextGaussian(), 0.004, 0.02 * r.nextGaussian());
				}
			}
			if (age % 3 == 0) {
				int n = LabFx.count(8 * life);
				for (int i = 0; i < n; i++) {
					double a = r.nextDouble() * Math.PI * 2, rr = Math.sqrt(r.nextDouble()) * g.radius;
					double x = g.centre.x + Math.cos(a) * rr, z = g.centre.z + Math.sin(a) * rr;
					mc.level.addParticle(r.nextFloat() < k ? DARK : SMOKE, true, true, x, g.centre.y + r.nextDouble() * 6, z, 0, 0.01, 0);
				}
			}
		}
		strength = target > strength ? Math.min(target, strength + 0.05f) : Math.max(target, strength - 0.03f);
		dark = darkest;
	}

	@Override
	public boolean isApplicable(FogType type, Entity entity) {
		return type == FogType.ATMOSPHERIC && Math.max(strength, prevStrength) > 0.01f;
	}

	@Override
	public void setupFog(FogData fog, Camera camera, ClientLevel level, float renderDistance, DeltaTracker delta) {
		float s = Mth.lerp(delta.getGameTimeDeltaPartialTick(false), prevStrength, strength);
		float end = Mth.lerp(s, Math.max(renderDistance, 32f), NEAR);
		fog.environmentalStart = end * 0.25f;
		fog.environmentalEnd = end;
		fog.skyEnd = end;
		fog.cloudEnd = end;
	}

	@Override
	public Vector3fc getBaseColor(ClientLevel level, Camera camera, int renderDistance, float partialTick) {
		// Gold at first, darkening toward a murky amber as the gas goes on.
		float k = Mth.clamp(dark, 0f, 1f);
		return new Vector3f(Mth.lerp(k, 0.72f, 0.24f), Mth.lerp(k, 0.58f, 0.17f), Mth.lerp(k, 0.16f, 0.03f));
	}

	@Override
	public boolean providesColor() {
		return true;
	}
}
