package com.sparky.lanternring.ally;

import com.sparky.lanternring.RingFx;
import com.sparky.lanternring.RingPowers;
import com.sparky.lanternring.net.RingFxPayload;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A construct that flies: it steers itself toward a point each tick and passes through blocks
 * like the rest of the ring's hard light. Subclasses pick the point (see goal) and when to shoot.
 */
public abstract class FlyingConstruct extends ConstructAlly {
	/** The entity id it is shooting at (0 for none), so clients can turn its eye to it. */
	private static final EntityDataAccessor<Integer> AIM = SynchedEntityData.defineId(FlyingConstruct.class, EntityDataSerializers.INT);

	/** Where it was summoned: the Sentry guards around here. */
	protected Vec3 home;
	/** How far around its orbit it is, in radians. */
	protected double orbit;
	protected int shotCooldown = 20;

	protected FlyingConstruct(EntityType<? extends FlyingConstruct> type, Level level) {
		super(type, level);
		setNoGravity(true);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(AIM, 0);
	}

	public void setHome(Vec3 home) {
		this.home = home;
		orbit = random.nextDouble() * Math.PI * 2;
	}

	@Nullable
	public Entity aimed() {
		int id = entityData.get(AIM);
		return id == 0 ? null : level().getEntity(id);
	}

	/** Where to fly this tick. */
	protected abstract Vec3 goal(@Nullable LivingEntity target);

	protected abstract double maxSpeed();

	/** Range it shoots from, and ticks between shots. */
	protected abstract double shotRange();

	protected abstract int shotInterval();

	protected abstract void shoot(ServerLevel level, LivingEntity target, Vec3 from);

	/** A point to look at while it has nothing to shoot, or null to face the way it flies. */
	@Nullable
	protected Vec3 idleLook() {
		return null;
	}

	protected Vec3 muzzle() {
		return position().add(0, getBbHeight() * 0.5, 0);
	}

	@Override
	public void tick() {
		noPhysics = true;
		super.tick();
		noPhysics = false;
		setNoGravity(true);
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (home == null) setHome(position());
		LivingEntity target = getTarget();
		Vec3 goal = goal(target);
		Vec3 to = goal.subtract(position());
		double dist = to.length();
		// Ease toward the point and slow down as it arrives, so it glides rather than jitters.
		Vec3 want = dist < 0.01 ? Vec3.ZERO : to.scale(Math.min(maxSpeed(), dist * 0.12) / dist);
		setDeltaMovement(getDeltaMovement().lerp(want, 0.12));

		int aim = 0;
		if (target != null && target.isAlive() && distanceToSqr(target) < shotRange() * shotRange()) {
			aim = target.getId();
			face(target.getEyePosition().subtract(0, target.getBbHeight() * 0.25, 0));
			if (--shotCooldown <= 0 && hasLineOfSight(target)) {
				shotCooldown = shotInterval();
				Vec3 from = muzzle();
				Vec3 hit = target.position().add(0, target.getBbHeight() * 0.5, 0);
				RingFx.send(level, RingFxPayload.Kind.ALLY_SHOT, from, hit);
				RingPowers.lightShot(level, from, hit);
				shoot(level, target, from);
			}
		} else if (idleLook() != null) {
			face(idleLook());
		} else if (getDeltaMovement().horizontalDistanceSqr() > 1.0e-4) {
			face(position().add(getDeltaMovement().scale(10)));
		}
		if (entityData.get(AIM) != aim) entityData.set(AIM, aim);
	}

	protected void face(Vec3 at) {
		Vec3 d = at.subtract(position().add(0, getEyeHeight(), 0));
		float yaw = (float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90f;
		float pitch = (float) -(Mth.atan2(d.y, d.horizontalDistance()) * Mth.RAD_TO_DEG);
		setYRot(Mth.approachDegrees(getYRot(), yaw, 12f));
		setXRot(Mth.approachDegrees(getXRot(), pitch, 8f));
		yBodyRot = getYRot();
		yHeadRot = getYRot();
	}

	@Override
	public void travel(Vec3 input) {
		move(MoverType.SELF, getDeltaMovement());
	}

	@Override
	public boolean onClimbable() {
		return false;
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		if (home != null) output.store("ConstructHome", Vec3.CODEC, home);
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		input.read("ConstructHome", Vec3.CODEC).ifPresent(this::setHome);
	}
}
