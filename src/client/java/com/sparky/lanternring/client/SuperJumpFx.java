package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.SuperJumps;
import com.sparky.lanternring.net.RingFxPayload;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * What every client draws for a super jump (server side: SuperJumps). Take-off: the ring flares hard
 * and the jumper's camera kicks. On the way the ring glows low, then builds up as the ground comes up
 * (J's Blender flare levels: wind-up 40, take-off 420, rising 30, falling 20 + 150 u^2.2, touchdown
 * 300; the ribbon and fist glow are SuperJumpAir).
 * Landing: the hard-light pad and wall form under the jumper (SuperLandConstruct), a few dim motes
 * rise, and each camera nearby rumbles as the wave gets to it (the jumper's dips hard first). The
 * poses are in SuperJumpPoses.
 */
public final class SuperJumpFx {
	/** How far past the quake's own reach cameras still feel it, as a multiple of the reach. */
	private static final double FELT = 2.5;
	/** The ring's flare, as a flash size (Blender level / 100): take-off, touchdown, and the glow on the way and winding up. */
	private static final float TAKE_OFF = 4.2f, TOUCHDOWN = 3f, AIR_RISE = 0.3f, WIND_UP = 0.4f;

	private SuperJumpFx() {
	}

	static void handle(RingFxPayload fx, @Nullable Player bearer) {
		Minecraft mc = Minecraft.getInstance();
		LocalPlayer me = mc.player;
		if (me == null) return;
		boolean mine = fx.bearer() >= 0 && fx.bearer() == me.getId();
		if (fx.kind() == RingFxPayload.Kind.SUPER_JUMP) {
			float charge = fx.value();
			if (fx.bearer() >= 0) SuperJumpPoses.jumped(fx.bearer(), charge, fx.from().y);
			if (bearer != null) RingEmit.flash(bearer, TAKE_OFF * (0.6f + 0.4f * charge));
			if (mine) RingShake.kick(0.5f + 0.7f * charge);
			return;
		}
		// SUPER_LAND
		float strength = fx.value();
		double reach = fx.to().distanceTo(fx.from());
		boolean deep = (fx.variant() & SuperJumps.DEEP_BIT) != 0;
		// A power landing (PowerLandingFx) has its own pose, pad and blocks.
		boolean power = (fx.variant() & SuperJumps.POWER_BIT) != 0;
		if (fx.bearer() >= 0 && !power) SuperJumpPoses.landed(fx.bearer(), deep);
		if (bearer != null) RingEmit.flash(bearer, TOUCHDOWN);
		if (!power) SuperLandConstruct.land(fx);
		motes(fx.from());
		if (mine) {
			RingShake.kick(0.8f + 0.8f * strength, true);
			RingShake.quake(0.8f + 0.6f * strength, 0f);
			return;
		}
		double d = me.position().distanceTo(fx.from());
		if (d > reach * FELT) return;
		float falloff = (float) (1 - d / (reach * FELT));
		RingShake.quake((0.5f + 0.7f * strength) * falloff, (float) (d / SuperJumps.WAVE_SPEED / 20));
	}

	/** The ring's low glow while winding up and in the air, a spark on it every few ticks. */
	static void tick(Minecraft mc) {
		if (mc.level == null || mc.player == null || mc.isPaused() || mc.level.getGameTime() % 3 != 0) return;
		float charge = SuperJumpInput.charge();
		if (charge >= 0f && mc.player.onGround() && mc.player.isSprinting()) glint(mc, mc.player, WIND_UP * Math.max(0.35f, charge));
		for (Player p : mc.level.players()) {
			if (!SuperJumpPoses.airborne(p.getId()) || p.onGround()) continue;
			// Rising: a low glow. Falling: the build-up, low at the top to bright just before touchdown (Blender 20 + 150 u^2.2).
			float u = SuperJumpAir.fall(p.getId());
			glint(mc, p, u < 0 ? AIR_RISE : (20 + 150 * (float) Math.pow(u, 2.2)) / 100f);
		}
	}

	private static void glint(Minecraft mc, Player p, float size) {
		float near = p == mc.player && mc.options.getCameraType().isFirstPerson() ? 0.45f : 1f;
		Corps before = CorpsTint.enter(Corps.held(p));
		try {
			LabFx.spawn(ModParticles.SPARK, RingEmit.ringNow(p, 1f), Vec3.ZERO, 1.2f * size * near);
		} finally {
			CorpsTint.restore(before);
		}
	}

	/** A few dim motes where you land (J's Blender pass: about 8). */
	private static void motes(Vec3 at) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		RandomSource r = mc.level.getRandom();
		float[] dim = CorpsTint.apply(CorpsTint.current(), 0.3f, 0.75f, 0.45f);
		for (int i = 0; i < 8; i++) {
			double a = r.nextDouble() * Math.PI * 2;
			Vec3 v = new Vec3(Math.cos(a) * 0.08, 0.05 + r.nextDouble() * 0.1, Math.sin(a) * 0.08);
			ConstructParticle p = LabFx.spawn(ModParticles.MOTE, at.add(0, 0.3, 0), v, 0.6f);
			if (p == null) continue;
			p.tinted(dim[0], dim[1], dim[2]);
			p.lasting(20 + r.nextInt(20));
		}
	}
}
