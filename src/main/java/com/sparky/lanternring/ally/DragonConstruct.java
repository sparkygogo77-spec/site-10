package com.sparky.lanternring.ally;

import com.sparky.lanternring.ModParticles;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.boss.enderdragon.DragonFlightHistory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The Dragon construct: an ender dragon about a third the size, made of hard light. It circles
 * above its owner, and when a hostile mob shows up it wheels around it and breathes bolts of
 * green fire at it. The breath hits only that mob and leaves the ground alone.
 */
public class DragonConstruct extends FlyingConstruct {
	private static final float BREATH_DAMAGE = 7f;

	/** Client side: the wing beat and the recent heights and headings, as the ender dragon keeps them for its model. */
	public final DragonFlightHistory flightHistory = new DragonFlightHistory();
	public float flapTime;
	public float oFlapTime;

	public DragonConstruct(EntityType<? extends DragonConstruct> type, Level level) {
		super(type, level);
		xpReward = 0;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Mob.createMobAttributes()
				.add(Attributes.MAX_HEALTH, 200)
				.add(Attributes.MOVEMENT_SPEED, 0.6)
				.add(Attributes.FLYING_SPEED, 0.6)
				.add(Attributes.FOLLOW_RANGE, 28);
	}

	@Override
	protected Vec3 goal(@Nullable LivingEntity target) {
		if (target != null) {
			// Wheel around the mob, a little above it.
			orbit += 0.07;
			return target.position().add(Math.cos(orbit) * 6, 4.5, Math.sin(orbit) * 6);
		}
		orbit += 0.035;
		Player owner = owner();
		Vec3 center = owner != null && owner.distanceToSqr(this) < 64 * 64 ? owner.position() : home;
		return center.add(Math.cos(orbit) * 7, 5 + Math.sin(tickCount * 0.05) * 0.8, Math.sin(orbit) * 7);
	}

	@Override
	protected double maxSpeed() {
		return getTarget() != null ? 0.75 : 0.55;
	}

	@Override
	protected double shotRange() {
		return 20;
	}

	@Override
	protected int shotInterval() {
		return 25;
	}

	@Override
	protected Vec3 muzzle() {
		return position().add(getLookAngle().scale(2.2)).add(0, 0.6, 0);
	}

	@Override
	protected void shoot(ServerLevel level, LivingEntity target, Vec3 from) {
		playSound(SoundEvents.ENDER_DRAGON_SHOOT, 1.5f, 1.3f);
		Vec3 at = target.position().add(0, target.getBbHeight() * 0.5, 0);
		level.sendParticles(ModParticles.SPARK, at.x, at.y, at.z, 16, 0.4, 0.4, 0.4, 0.2);
		if (target.hurtServer(level, level.damageSources().indirectMagic(this, owner() != null ? owner() : this), BREATH_DAMAGE)) {
			Vec3 dir = at.subtract(from).normalize();
			target.push(dir.x * 0.9, 0.35, dir.z * 0.9);
			WardenConstruct.knock(target);
		}
	}

	@Override
	public void tick() {
		super.tick();
		if (level().isClientSide()) {
			oFlapTime = flapTime;
			Vec3 v = getDeltaMovement();
			float flap = 0.2f / ((float) v.horizontalDistance() * 10f + 1f);
			flapTime += flap * (float) Math.pow(2.0, v.y) * 0.9f;
			// The ender dragon's model faces the other way round from other mobs.
			flightHistory.record(getY(), getYRot() + 180f);
		}
		if (!level().isClientSide() && tickCount % 40 == 0) playSound(SoundEvents.ENDER_DRAGON_FLAP, 0.6f, 1.6f);
	}
}
