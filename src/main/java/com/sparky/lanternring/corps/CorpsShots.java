package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RingFx;
import com.sparky.lanternring.RingPowers;
import com.sparky.lanternring.net.RingFxPayload;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;

/** The ring bolts corps villagers, their golems and the sky raiders fire, and their summoning flash. */
final class CorpsShots {
	/** A bolt of the corps' light from the shooter's hand to the target. Red bolts set it alight. */
	static void shoot(ServerLevel level, LivingEntity shooter, LivingEntity target, Corps corps, float damage) {
		Vec3 from = shooter.position().add(0, shooter.getBbHeight() * 0.6, 0);
		Vec3 hit = target.position().add(0, target.getBbHeight() * 0.5, 0);
		Corps before = Corps.enter(corps);
		try {
			RingFx.send(level, RingFxPayload.Kind.ALLY_SHOT, from, hit);
			RingPowers.lightShot(level, from, hit);
		} finally {
			Corps.restore(before);
		}
		level.playSound(null, shooter.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.HOSTILE, 0.9f,
				corps == Corps.RED ? 0.7f : 1.4f);
		if (target.hurtServer(level, level.damageSources().mobAttack(shooter), damage) && corps == Corps.RED) {
			target.igniteForSeconds(3);
		}
	}

	/** The pillar of light a golem or a new villager forms in. */
	static void summon(ServerLevel level, Vec3 foot, float height, float width, Corps corps) {
		Corps before = Corps.enter(corps);
		try {
			RingFx.send(level, RingFxPayload.Kind.ALLY_SUMMON, foot, foot.add(0, height, 0), width);
		} finally {
			Corps.restore(before);
		}
		level.sendParticles(ModParticles.of(ModParticles.MOTE, corps), foot.x, foot.y + height * 0.5, foot.z, 30, width * 0.4,
				height * 0.4, width * 0.4, 0.05);
		level.playSound(null, foot.x, foot.y, foot.z, SoundEvents.BEACON_ACTIVATE, SoundSource.NEUTRAL, 1f, 1.3f);
	}

	private CorpsShots() {
	}
}
