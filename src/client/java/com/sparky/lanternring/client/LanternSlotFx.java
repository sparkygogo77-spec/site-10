package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternSlot;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RingTuning;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.phys.Vec3;

/**
 * The lantern summoned from its slot (key R, see LanternSlot), on this client: how far it has
 * floated in (0 = gone, 1 = at rest), and the light it gathers from as it forms and breaks up into
 * as it's dismissed. Drawn by {@link LanternFirstPerson#renderSlot}.
 */
public final class LanternSlotFx {
	private static float appear;
	private static float prevAppear;
	private static boolean wasOut;
	private static Corps corps = Corps.GREEN;

	private LanternSlotFx() {
	}

	public static void tick(Minecraft mc) {
		prevAppear = appear;
		LocalPlayer player = mc.player;
		boolean out = player != null && LanternSlot.out(player);
		if (out) corps = Corps.ofLantern(LanternSlot.lantern(player));
		float step = 1f / Math.max(1, RingTuning.LANTERN_SUMMON.ticks());
		appear = Mth.clamp(appear + (out ? step : -step), 0f, 1f);
		if (player != null && mc.level != null && !mc.isPaused()) {
			if (out != wasOut) burst(mc, player, out);
			else if (out && appear < 1f) gather(mc, player);
		}
		wasOut = out;
	}

	/** 0..1: how far the summoned lantern has floated in. */
	static float appear(float partialTick) {
		return Mth.lerp(partialTick, prevAppear, appear);
	}

	/** True while the summoned lantern is (even partly) on screen. */
	static boolean visible() {
		return appear > 0f || prevAppear > 0f;
	}

	static Corps corps() {
		return corps;
	}

	/** Roughly where the lantern rests in the world: low, ahead and to the off-hand side of the eyes. */
	private static Vec3 rest(LocalPlayer player) {
		Vec3 look = player.getViewVector(1f);
		Vec3 side = look.cross(new Vec3(0, 1, 0)).normalize();
		float f = player.getMainArm() == HumanoidArm.RIGHT ? -1f : 1f;
		return player.getEyePosition().add(look.scale(1.3)).add(side.scale(0.4 * f)).add(0, -0.45, 0);
	}

	/** Motes drawn in to where it's forming. */
	private static void gather(Minecraft mc, LocalPlayer player) {
		RandomSource r = mc.level.getRandom();
		Vec3 at = rest(player);
		Corps before = CorpsTint.enter(corps);
		for (int i = 0; i < 2; i++) {
			Vec3 from = at.add(r.nextGaussian() * 0.5, r.nextGaussian() * 0.5, r.nextGaussian() * 0.5);
			LabFx.spawn(ModParticles.MOTE, from, at.subtract(from).scale(0.2), 0.3f);
		}
		CorpsTint.restore(before);
	}

	/** A puff of light as it's summoned, and a burst as it breaks up when dismissed. */
	private static void burst(Minecraft mc, LocalPlayer player, boolean summoned) {
		RandomSource r = mc.level.getRandom();
		Vec3 at = rest(player);
		Corps before = CorpsTint.enter(corps);
		int count = summoned ? 8 : 18;
		double speed = summoned ? 0.03 : 0.09;
		for (int i = 0; i < count; i++) {
			Vec3 v = new Vec3(r.nextGaussian(), r.nextGaussian() + 0.3, r.nextGaussian()).scale(speed);
			LabFx.spawn(summoned ? ModParticles.MOTE : ModParticles.SHARD, at, v, 0.35f);
		}
		CorpsTint.restore(before);
	}
}
