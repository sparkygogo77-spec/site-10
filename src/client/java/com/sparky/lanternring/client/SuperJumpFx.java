package com.sparky.lanternring.client;

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
 * What every client draws for a super jump (server side: SuperJumps). Take-off: the ring flares, a
 * small ring of hard light skims out over the ground and the jumper's camera kicks. Landing: a low
 * wall of light rolls out along the ground as far as the quake reaches, and each camera nearby
 * rumbles as the wave gets to it (the jumper's dips hard first). The poses are in SuperJumpPoses.
 */
public final class SuperJumpFx {
	/** How far past the quake's own reach cameras still feel it, as a multiple of the reach. */
	private static final double FELT = 2.5;

	private SuperJumpFx() {
	}

	static void handle(RingFxPayload fx, @Nullable Player bearer) {
		Minecraft mc = Minecraft.getInstance();
		LocalPlayer me = mc.player;
		if (me == null) return;
		boolean mine = fx.bearer() >= 0 && fx.bearer() == me.getId();
		if (fx.kind() == RingFxPayload.Kind.SUPER_JUMP) {
			float charge = fx.value();
			if (fx.bearer() >= 0) SuperJumpPoses.jumped(fx.bearer(), charge);
			if (bearer != null) RingEmit.flash(bearer, 1.2f + charge);
			groundRing(fx.from(), 1.5 + 2 * charge, 1);
			if (mine) RingShake.kick(0.5f + 0.7f * charge);
			return;
		}
		// SUPER_LAND
		float strength = fx.value();
		double reach = fx.to().distanceTo(fx.from());
		if (fx.bearer() >= 0) SuperJumpPoses.landed(fx.bearer());
		if (bearer != null) RingEmit.flash(bearer, 1.5f + strength);
		boolean primed = fx.variant() == 1;
		groundRing(fx.from(), reach, primed ? 5 : 3);
		burst(fx.from(), strength * (primed ? 2f : 1f));
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

	/** A low wall of hard-light panes skimming out along the ground to radius blocks, rows high. */
	static void groundRing(Vec3 at, double radius, int rows) {
		double step = 0.08, r0 = 0.4;
		float size = (float) (0.53 * r0 * step);
		float growth = (float) (0.53 * SuperJumps.WAVE_SPEED * step);
		int life = (int) Math.ceil((radius - r0) / SuperJumps.WAVE_SPEED) + 2;
		Vec3 base = at.add(0, 0.15, 0);
		for (int row = 0; row < rows; row++) {
			double pitch = row * step;
			int n = Math.max(1, (int) Math.round(Math.PI * 2 * Math.cos(pitch) / step));
			double shift = (row % 2) * 0.5;
			for (int i = 0; i < n; i++) {
				double yaw = (i + shift) * Math.PI * 2 / n;
				Vec3 out = new Vec3(Math.cos(yaw) * Math.cos(pitch), Math.sin(pitch), Math.sin(yaw) * Math.cos(pitch));
				ConstructParticle p = LabFx.spawn(ModParticles.PANE, base.add(out.scale(r0)), out.scale(SuperJumps.WAVE_SPEED), 1f);
				// The top row fades sooner, so the wall sinks as it spreads.
				if (p != null) p.tinted(0.4f, 1f, 0.6f).paned(size, growth, row == rows - 1 && rows > 1 ? life * 2 / 3 : life);
			}
		}
	}

	/** Shards and motes thrown up and out where you land. */
	private static void burst(Vec3 at, float strength) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		RandomSource r = mc.level.getRandom();
		int n = LabFx.count(20 + 20 * strength);
		for (int i = 0; i < n; i++) {
			double a = r.nextDouble() * Math.PI * 2;
			double out = 0.15 + r.nextDouble() * 0.25 * strength;
			Vec3 v = new Vec3(Math.cos(a) * out, 0.15 + r.nextDouble() * 0.35, Math.sin(a) * out);
			ConstructParticle p = LabFx.spawn(i % 3 == 0 ? ModParticles.SHARD : ModParticles.MOTE, at.add(0, 0.2, 0), v, 0.9f + 0.4f * r.nextFloat());
			if (p != null) p.lasting(20 + r.nextInt(20));
		}
		LabFx.spawn(ModParticles.SPARK, at.add(0, 0.6, 0), Vec3.ZERO, 2f + strength * 2f);
	}
}
