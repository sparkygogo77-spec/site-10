package com.sparky.lanternring;

import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

/**
 * Red Lantern rage on you (J, 2026-10-13: 38c), from being hurt by a Red Lantern or its constructs
 * (corps/RedRage). A dark red aura hangs round you and blood drips, very slowly, from your mouth;
 * on your own screen the edges glow red (the client's RageTint). A Blue Lantern rescue squad seeing
 * it offers to fly with you against the Red Lanterns.
 */
public class RageEffect extends MobEffect {
	private static final DustParticleOptions AURA = new DustParticleOptions(0x8A0A0A, 1.1f);
	private static final BlockParticleOption BLOOD = new BlockParticleOption(ParticleTypes.FALLING_DUST, Blocks.REDSTONE_BLOCK.defaultBlockState());

	RageEffect() {
		super(MobEffectCategory.HARMFUL, 0xB01010);
	}

	@Override
	public boolean shouldApplyEffectTickThisTick(int duration, int amplifier) {
		return duration % 10 == 0;
	}

	@Override
	public boolean applyEffectTick(ServerLevel level, LivingEntity e, int amplifier) {
		// The aura: a few dark red motes drifting round the body.
		level.sendParticles(AURA, e.getX(), e.getY() + e.getBbHeight() * 0.55, e.getZ(), 3, e.getBbWidth() * 0.6, e.getBbHeight() * 0.35, e.getBbWidth() * 0.6, 0.0);
		// A slow drop of blood from the mouth, every couple of seconds.
		if (e.tickCount % 40 < 10) {
			Vec3 face = Vec3.directionFromRotation(0, e.getYHeadRot()).scale(e.getBbWidth() * 0.5 + 0.05);
			Vec3 mouth = e.getEyePosition().add(face).subtract(0, 0.22, 0);
			level.sendParticles(BLOOD, mouth.x, mouth.y, mouth.z, 1, 0.03, 0, 0.03, 0);
		}
		return true;
	}
}
