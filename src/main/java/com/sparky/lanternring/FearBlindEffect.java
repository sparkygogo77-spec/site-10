package com.sparky.lanternring;

import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;

/**
 * Fear Blind, from standing in the Dread Runner's fear (corps/DreadTrails): a player's screen goes
 * dark with sickly yellow light at its edges (the client's FearBlind), fading as the effect runs out.
 * It does nothing on its own; mobs also get plain Blindness.
 */
public class FearBlindEffect extends MobEffect {
	FearBlindEffect() {
		super(MobEffectCategory.HARMFUL, 0x6B5A12);
	}
}
