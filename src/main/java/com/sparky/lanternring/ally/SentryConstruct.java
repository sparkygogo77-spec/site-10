package com.sparky.lanternring.ally;

import com.sparky.lanternring.ModParticles;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The Sentry construct: a spiked hard-light eye that guards the spot it was summoned. It drifts
 * in a slow loop around that spot, and shoots any hostile mob that comes near with a beam that
 * hits lightly but knocks the mob flying. It never breaks blocks and stays put when its owner
 * leaves, so it can watch a base or a farm while you do something else.
 */
public class SentryConstruct extends FlyingConstruct {
	private static final float BEAM_DAMAGE = 4f;
	/** How far from its post it looks for mobs. */
	public static final double GUARD_RANGE = 20;

	/** Client side: spikes out while it has a target, and its tail sways. */
	public float spikes;
	public float oSpikes;
	public float tail;
	public float oTail;

	public SentryConstruct(EntityType<? extends SentryConstruct> type, Level level) {
		super(type, level);
		xpReward = 0;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Mob.createMobAttributes()
				.add(Attributes.MAX_HEALTH, 200)
				.add(Attributes.MOVEMENT_SPEED, 0.4)
				.add(Attributes.FLYING_SPEED, 0.4)
				.add(Attributes.FOLLOW_RANGE, GUARD_RANGE);
	}

	@Override
	protected Vec3 goal(@Nullable LivingEntity target) {
		// A slow loop around its post, bobbing gently; it speeds up a little while it fights.
		orbit += target != null ? 0.03 : 0.018;
		return home.add(Math.cos(orbit) * 4, Math.sin(tickCount * 0.06) * 0.6, Math.sin(orbit) * 4);
	}

	@Override
	public boolean canAttack(LivingEntity target) {
		return super.canAttack(target) && (home == null || target.distanceToSqr(home) < GUARD_RANGE * GUARD_RANGE);
	}

	@Override
	protected double maxSpeed() {
		return 0.25;
	}

	@Override
	protected double shotRange() {
		return GUARD_RANGE;
	}

	@Override
	protected int shotInterval() {
		return 20;
	}

	@Override
	protected void shoot(ServerLevel level, LivingEntity target, Vec3 from) {
		playSound(SoundEvents.GUARDIAN_ATTACK, 1f, 1.6f);
		playSound(SoundEvents.BEACON_ACTIVATE, 0.6f, 2f);
		Vec3 at = target.position().add(0, target.getBbHeight() * 0.5, 0);
		level.sendParticles(ModParticles.SPARK, at.x, at.y, at.z, 10, 0.3, 0.3, 0.3, 0.25);
		if (target.hurtServer(level, level.damageSources().indirectMagic(this, owner() != null ? owner() : this), BEAM_DAMAGE)) {
			// Knocks it flying, away from the sentry.
			Vec3 dir = at.subtract(from).multiply(1, 0, 1).normalize();
			target.push(dir.x * 1.9, 0.8, dir.z * 1.9);
			WardenConstruct.knock(target);
		}
	}

	@Override
	public void tick() {
		super.tick();
		if (level().isClientSide()) {
			oSpikes = spikes;
			oTail = tail;
			spikes += ((aimed() != null ? 1f : 0.25f) - spikes) * 0.15f;
			tail += 0.12f;
		}
	}
}
