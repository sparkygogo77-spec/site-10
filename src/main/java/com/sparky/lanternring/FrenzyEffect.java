package com.sparky.lanternring;

import com.sparky.lanternring.corps.FearFrenzy;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;

/**
 * Fear Frenzy, the Fear Nuke's poison (J, 2026-10-13: "it causes fear in every mob the radius
 * poisons ... and they go crazy and start killing each other"). It does no damage itself: a
 * frenzied mob turns on the nearest other living thing with whatever yellow construct weapon the
 * gas handed it (see corps/FearFrenzy). Players aren't forced to fight.
 */
public class FrenzyEffect extends MobEffect {
	FrenzyEffect() {
		super(MobEffectCategory.HARMFUL, 0xF2C81E);
	}

	@Override
	public boolean shouldApplyEffectTickThisTick(int remaining, int amplifier) {
		return true;
	}

	@Override
	public boolean applyEffectTick(ServerLevel level, LivingEntity entity, int amplifier) {
		if (entity instanceof Mob mob) FearFrenzy.frenzyTick(level, mob);
		return true;
	}
}
