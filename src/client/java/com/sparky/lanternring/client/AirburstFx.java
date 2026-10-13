package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.Vec3;

/**
 * The Fear Nuke's airburst, drawn by each client (J, 2026-10-13: "it should realistically explode
 * and incinerate around it"): a white-yellow flash that floods the screen of anyone looking, a
 * fireball where it burst, a shock ring that races out along the ground past the crater's rim, and
 * a mushroom of yellow smoke whose cap rolls up over a rising stem. The crater itself is the yellow
 * aura's (NukeAuraFx, corps/FearNuke.Burn).
 */
public final class AirburstFx {
	/** How long the cloud keeps rolling, in ticks. */
	private static final int LIFE = 160;
	private static final int FIREBALL = 30, SHOCK = 28;
	private static final DustParticleOptions GOLD = new DustParticleOptions(0xE8C040, 4f);
	private static final DustParticleOptions AMBER = new DustParticleOptions(0x9C7418, 4f);
	private static final DustParticleOptions WHITE_HOT = new DustParticleOptions(0xFFF6C8, 4f);

	private record Burst(Vec3 at, Vec3 ground, double radius, long start) {
	}

	private static final List<Burst> BURSTS = new ArrayList<>();
	private static float flash, prevFlash;

	private AirburstFx() {
	}

	static void start(Vec3 at, Vec3 ground, float radius) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		BURSTS.add(new Burst(at, ground, Math.max(4, radius), mc.level.getGameTime()));
		if (mc.player != null) {
			Vec3 eye = mc.player.getEyePosition();
			double d = eye.distanceTo(at);
			// Blinding if you are looking anywhere near it, and close enough.
			double facing = mc.player.getViewVector(1f).dot(at.subtract(eye).normalize());
			float near = (float) Mth.clamp(1.0 - d / (radius * 8), 0, 1);
			flash = Math.max(flash, near * (float) Mth.clamp((facing + 0.3) / 1.0, 0.25, 1.0));
			if (d < radius * 6) RingShake.kick((float) (4.0 * (1 - d / (radius * 6))));
		}
	}

	public static void register() {
		HudElementRegistry.addFirst(LanternRing.id("airburst_flash"), AirburstFx::extract);
	}

	static void clear() {
		BURSTS.clear();
		flash = prevFlash = 0;
	}

	/** Test hook: how bright the flash is right now. */
	public static float flash() {
		return flash;
	}

	static void tick(Minecraft mc) {
		prevFlash = flash;
		flash = Math.max(0f, flash - 0.045f);
		if (BURSTS.isEmpty()) return;
		long now = mc.level.getGameTime();
		RandomSource r = mc.level.getRandom();
		Corps before = CorpsTint.enter(Corps.YELLOW);
		try {
			for (Iterator<Burst> it = BURSTS.iterator(); it.hasNext(); ) {
				Burst b = it.next();
				long age = now - b.start;
				if (age > LIFE || age < 0) {
					it.remove();
					continue;
				}
				fireball(mc, b, age, r);
				shock(mc, b, age, r);
				mushroom(mc, b, age, r);
			}
		} finally {
			CorpsTint.restore(before);
		}
	}

	private static void add(Minecraft mc, ParticleOptions p, Vec3 at, double vx, double vy, double vz) {
		mc.level.addParticle(p, true, true, at.x, at.y, at.z, vx, vy, vz);
	}

	/** A ball of white-hot fire where it burst, swelling and going dull gold. */
	private static void fireball(Minecraft mc, Burst b, long age, RandomSource r) {
		if (age > FIREBALL) return;
		float k = age / (float) FIREBALL;
		double rad = b.radius * (0.08 + 0.22 * Math.sqrt(k));
		int n = LabFx.count(70 * (1 - k * 0.6f));
		for (int i = 0; i < n; i++) {
			Vec3 d = onSphere(r);
			Vec3 at = b.at.add(d.scale(rad * Math.cbrt(r.nextDouble())));
			add(mc, k < 0.3f ? WHITE_HOT : r.nextBoolean() ? GOLD : ParticleTypes.FLAME, at, d.x * 0.15, d.y * 0.15, d.z * 0.15);
			if (i % 3 == 0) LabFx.spawn(ModParticles.SPARK, at, d.scale(0.6), 2.4f);
		}
		if (age == 0) {
			for (int i = 0; i < 6; i++) add(mc, ParticleTypes.EXPLOSION_EMITTER, b.at.add(onSphere(r).scale(rad)), 0, 0, 0);
		}
	}

	/** The shock ring racing out along the ground. */
	private static void shock(Minecraft mc, Burst b, long age, RandomSource r) {
		if (age > SHOCK) return;
		float k = age / (float) SHOCK;
		double rad = b.radius * 1.4 * (1 - (1 - k) * (1 - k));
		int pts = LabFx.count(40 + (float) rad * 2.5f);
		for (int i = 0; i < pts; i++) {
			double a = r.nextDouble() * Math.PI * 2;
			Vec3 at = new Vec3(b.ground.x + Math.cos(a) * rad, b.ground.y + 0.6 + r.nextDouble() * 1.5, b.ground.z + Math.sin(a) * rad);
			add(mc, i % 2 == 0 ? ParticleTypes.CLOUD : GOLD, at, Math.cos(a) * 0.3, 0.02, Math.sin(a) * 0.3);
		}
	}

	/** The mushroom: a stem of smoke climbing from the crater and a cap rolling up and out over it. */
	private static void mushroom(Minecraft mc, Burst b, long age, RandomSource r) {
		if (age < 6) return;
		float k = Math.min(1f, (age - 6) / (float) (LIFE - 40));
		float fade = age > LIFE - 40 ? (LIFE - age) / 40f : 1f;
		double h = b.at.y - b.ground.y;
		double capY = b.at.y + b.radius * 0.7 * (1 - (1 - k) * (1 - k));
		double capR = b.radius * (0.18 + 0.3 * Math.sqrt(k));
		double tube = capR * 0.35;
		// The cap: a rolling ring (torus) with a dome over it.
		int n = LabFx.count(95 * fade);
		for (int i = 0; i < n; i++) {
			double a = r.nextDouble() * Math.PI * 2, t = r.nextDouble() * Math.PI * 2;
			double ring = capR - tube + tube * Math.cos(t);
			Vec3 at = new Vec3(b.at.x + Math.cos(a) * ring, capY + tube * Math.sin(t) * 0.8, b.at.z + Math.sin(a) * ring);
			// It rolls: up on the outside, in over the top, down on the inside.
			double roll = 0.06;
			add(mc, r.nextInt(3) == 0 ? AMBER : r.nextInt(4) == 0 ? ParticleTypes.LARGE_SMOKE : GOLD, at,
					-Math.sin(t) * Math.cos(a) * roll, Math.cos(t) * roll + 0.05, -Math.sin(t) * Math.sin(a) * roll);
		}
		int dome = LabFx.count(30 * fade);
		for (int i = 0; i < dome; i++) {
			double a = r.nextDouble() * Math.PI * 2, d = Math.sqrt(r.nextDouble()) * (capR - tube);
			Vec3 at = new Vec3(b.at.x + Math.cos(a) * d, capY + tube * (0.6 + 0.4 * r.nextDouble()), b.at.z + Math.sin(a) * d);
			add(mc, r.nextBoolean() ? GOLD : AMBER, at, 0, 0.04, 0);
		}
		// The stem, from the ground up into the cap, narrower in the middle.
		int stem = LabFx.count(45 * fade);
		double base = b.ground.y, top = capY - tube * 0.5;
		for (int i = 0; i < stem; i++) {
			double y = base + r.nextDouble() * Math.max(1, top - base);
			double along = (y - base) / Math.max(1, top - base);
			double w = b.radius * (0.05 + 0.06 * Math.abs(along - 0.45) * 2) + (along < 0.1 ? b.radius * 0.15 * (0.1 - along) * 10 : 0);
			double a = r.nextDouble() * Math.PI * 2, d = Math.sqrt(r.nextDouble()) * w;
			Vec3 at = new Vec3(b.ground.x + Math.cos(a) * d, y, b.ground.z + Math.sin(a) * d);
			add(mc, r.nextInt(3) == 0 ? ParticleTypes.LARGE_SMOKE : r.nextBoolean() ? AMBER : GOLD, at, 0, 0.12 + 0.1 * r.nextDouble(), 0);
		}
		// Fire still licking round the burst point early on.
		if (age < 50 && h > 0) {
			int fire = LabFx.count(12);
			for (int i = 0; i < fire; i++) {
				Vec3 at = b.at.add(onSphere(r).scale(capR * 0.4 * r.nextDouble()));
				add(mc, ParticleTypes.FLAME, at, 0, 0.08, 0);
			}
		}
	}

	private static Vec3 onSphere(RandomSource r) {
		double z = r.nextDouble() * 2 - 1, a = r.nextDouble() * Math.PI * 2, s = Math.sqrt(1 - z * z);
		return new Vec3(s * Math.cos(a), z, s * Math.sin(a));
	}

	/** The flash floods the screen white-yellow, then fades. */
	private static void extract(GuiGraphicsExtractor graphics, DeltaTracker delta) {
		float f = Mth.lerp(delta.getGameTimeDeltaPartialTick(false), prevFlash, flash);
		if (f <= 0.004f) return;
		float alpha = Mth.clamp(f * 0.95f, 0f, 0.95f);
		int rgb = f > 0.6f ? 0xFFFBE8 : 0xFFE680;
		graphics.fill(0, 0, graphics.guiWidth(), graphics.guiHeight(), Math.round(255 * alpha) << 24 | rgb);
	}
}
