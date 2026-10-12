package com.sparky.lanternring;

import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.item.alchemy.Potion;

/** The Yellow Lantern's Fear effect, and a Potion of Fear (brewed from an awkward potion and a wither rose). */
public final class ModEffects {
	public static final Holder<MobEffect> FEAR = Registry.registerForHolder(BuiltInRegistries.MOB_EFFECT, LanternRing.id("fear"), new FearEffect());
	public static final Holder<Potion> FEAR_POTION = Registry.registerForHolder(BuiltInRegistries.POTION, LanternRing.id("fear"),
			new Potion("fear", new MobEffectInstance(FEAR, 20 * 30), new MobEffectInstance(MobEffects.WEAKNESS, 20 * 30)));

	static void init() {
	}

	private ModEffects() {
	}
}
