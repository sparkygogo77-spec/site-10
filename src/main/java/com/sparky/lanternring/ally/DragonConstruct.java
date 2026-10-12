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
	public Formation.Stance stance() {
		return Formation.Stance.CANOPY;
	}

	/** Owner speed (blocks a tick) above which the dragons stop circling and fly as wingmen. */
	private static final double WINGMAN_SPEED = 0.45;

	@Override
	protected Vec3 goal(@Nullable LivingEntity target) {
		Formation.Place place = place();
		if (target != null) {
			// Wheel around the mob, a little above it; several dragons spread round it.
			orbit += 0.07;
			double a = orbit + place.phase();
			return target.position().add(Math.cos(a) * 6, 4.5 + (place.index() % 2) * 2, Math.sin(a) * 6);
		}
		Player owner = owner();
		if (owner == null || owner.distanceToSqr(this) > 64 * 64) {
			orbit += 0.035;
			return home.add(Math.cos(orbit) * 7, 5 + Math.sin(tickCount * 0.05) * 0.8, Math.sin(orbit) * 7);
		}
		Vec3 motion = ownerMotion();
		if (motion.horizontalDistance() > WINGMAN_SPEED) {
			// You're flying (or riding) fast: they fall in behind and above you in a V, a lone one
			// on your tail, and lead your path a little so they keep up.
			Vec3 facing = motion.multiply(1, 0, 1).normalize();
			int rank = place.count() == 1 ? 0 : place.index() / 2 + 1;
			double side = place.count() == 1 ? 0 : (place.index() % 2 == 0 ? 1 : -1) * 3.5 * rank;
			return Formation.around(owner, facing, side, -4 - 3 * rank, 2.5 + rank * 0.8).add(motion.scale(6));
		}
		// Circling overhead: the group shares one circle, evenly spaced and at two heights,
		// and the circle opens up the more there are.
		double a = level().getGameTime() * 0.035 + place.phase();
		double radius = 7 + 1.5 * (place.count() - 1);
		double up = 5 + (place.index() % 2) * 2.5 + Math.sin(tickCount * 0.05) * 0.8;
		return owner.position().add(Math.cos(a) * radius, up, Math.sin(a) * radius);
	}

	@Override
	protected double maxSpeed() {
		if (getTarget() != null) return 0.75;
		return Math.min(2.5, Math.max(0.55, ownerMotion().length() * 1.5));
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
