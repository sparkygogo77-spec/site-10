package com.sparky.lanternring;

import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.entity.LivingEntity;

/**
 * Dread, from the Yellow Lantern's Fear Nuke (see corps/FearNuke): fear that slowly kills. A
 * player's hearts turn yellow while they have it (the client's HeartTypeMixin); a mob shows yellow
 * motes over its head. Every 1.5 s it takes an 18th of its full health, so whatever it caught dies
 * by the end of RingTuning.FEAR_DREAD unless it is healed or drinks milk.
 */
public class DreadEffect extends MobEffect {
	/** Ticks between hits. */
	static final int EVERY = 30;
	private static final DustParticleOptions YELLOW = new DustParticleOptions(0xFFD21A, 1.1f);

	DreadEffect() {
		super(MobEffectCategory.HARMFUL, 0xFFD21A);
	}

	@Override
	public boolean shouldApplyEffectTickThisTick(int remaining, int amplifier) {
		return true;
	}

	@Override
	public boolean applyEffectTick(ServerLevel level, LivingEntity entity, int amplifier) {
		if (entity.tickCount % 6 == 0) {
			level.sendParticles(YELLOW, entity.getX(), entity.getY() + entity.getBbHeight() + 0.3, entity.getZ(),
					2, entity.getBbWidth() * 0.4, 0.15, entity.getBbWidth() * 0.4, 0.01);
		}
		if (entity.tickCount % EVERY == 0) {
			entity.hurtServer(level, level.damageSources().magic(), Math.max(1f, entity.getMaxHealth() / 18f));
		}
		return true;
	}
}
