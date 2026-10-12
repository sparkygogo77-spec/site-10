package com.sparky.lanternring;

import com.sparky.lanternring.ally.ConstructAlly;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectCategory;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.util.DefaultRandomPos;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

/**
 * Fear: darkness closes in around whoever has it. A feared mob gives up on whoever frightened it
 * and runs from them; a feared player's view closes in to a few blocks (see the client's FearFog
 * and FearVignette). Its attack drops too. Mobs don't see, so their darkness is drawn round them
 * for everyone else to watch: a ring of black smoke that tightens round the mob, with pairs of
 * yellow eyes blinking in it (where the Brood comes from; see Terror).
 */
public class FearEffect extends MobEffect {
	private static final Identifier ATTACK_ID = LanternRing.id("fear_attack");
	/** How far a feared mob runs before it looks for somewhere further. */
	private static final int FLEE = 16;

	FearEffect() {
		super(MobEffectCategory.HARMFUL, 0xD8B020);
		addAttributeModifier(Attributes.ATTACK_DAMAGE, ATTACK_ID, -0.25, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
	}

	@Override
	public boolean shouldApplyEffectTickThisTick(int remaining, int amplifier) {
		return true;
	}

	@Override
	public boolean applyEffectTick(ServerLevel level, LivingEntity entity, int amplifier) {
		if (entity instanceof Player || entity instanceof ConstructAlly) return true;
		Player fearer = Terror.fearer(level, entity);
		if (entity instanceof Mob mob && fearer != null) {
			// It won't go for whoever frightened it.
			if (mob.getTarget() == fearer) mob.setTarget(null);
			if (mob instanceof PathfinderMob runner && fearer.distanceToSqr(runner) < FLEE * FLEE
					&& (runner.getNavigation().isDone() || runner.tickCount % 20 == 0)) {
				Vec3 away = DefaultRandomPos.getPosAway(runner, FLEE, 7, fearer.position());
				if (away != null) runner.getNavigation().moveTo(away.x, away.y, away.z, 1.35);
			}
		}
		if (entity.tickCount % 3 == 0) darkness(level, entity);
		return true;
	}

	/** The ring of black smoke round a feared mob, closing in over the first 2 seconds, with yellow eyes in it. */
	private static void darkness(ServerLevel level, LivingEntity entity) {
		float closing = Mth.clamp(Terror.fearedFor(level, entity) / 40f, 0f, 1f);
		double radius = Mth.lerp(closing, 5.5, 1.6) + entity.getBbWidth() / 2;
		Vec3 c = entity.position();
		var random = entity.getRandom();
		for (int i = 0; i < 10; i++) {
			double a = random.nextDouble() * Mth.TWO_PI;
			double r = radius * (0.85 + 0.3 * random.nextDouble());
			double y = random.nextDouble() * (entity.getBbHeight() + 1.2);
			double in = -0.04 * (1 - closing) - 0.01;
			level.sendParticles(random.nextInt(6) == 0 ? ParticleTypes.SQUID_INK : ParticleTypes.LARGE_SMOKE,
					c.x + Math.cos(a) * r, c.y + y, c.z + Math.sin(a) * r, 0, Math.cos(a) * in, 0.005, Math.sin(a) * in, 1);
		}
		if (random.nextInt(6) == 0) {
			// A pair of eyes opens in the dark, looking in.
			double a = random.nextDouble() * Mth.TWO_PI;
			double r = radius * 1.1;
			double y = c.y + 0.3 + random.nextDouble() * 1.4;
			double px = -Math.sin(a) * 0.12, pz = Math.cos(a) * 0.12;
			var eye = ModParticles.of(ModParticles.SPARK, Corps.YELLOW);
			for (int s = -1; s <= 1; s += 2) {
				level.sendParticles(eye, c.x + Math.cos(a) * r + px * s, y, c.z + Math.sin(a) * r + pz * s, 1, 0, 0, 0, 0);
			}
		}
	}
}
