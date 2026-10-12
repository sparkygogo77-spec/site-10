package com.sparky.lanternring.ally;

import com.sparky.lanternring.RingFx;
import com.sparky.lanternring.RingPowers;
import com.sparky.lanternring.net.RingFxPayload;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.AnimationState;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

/**
 * The Warden construct: a hard-light warden that walks with its owner and smashes hostile mobs.
 * Up close it swings (big damage, big knockback); at range it charges a sonic boom that goes
 * through armor and knocks the mob flying. Neither breaks any blocks.
 */
public class WardenConstruct extends ConstructAlly {
	private static final byte ATTACK_EVENT = 4;
	private static final byte BOOM_EVENT = 62;
	/** Ticks the sonic boom charges before it goes off (the warden's own windup is 34). */
	private static final int BOOM_WINDUP = 20;
	private static final int BOOM_COOLDOWN = 60;
	private static final float BOOM_DAMAGE = 10f;

	public final AnimationState attackAnimationState = new AnimationState();
	public final AnimationState sonicBoomAnimationState = new AnimationState();
	private int boomCooldown = 40;
	private int boomCharge = -1;

	public WardenConstruct(EntityType<? extends WardenConstruct> type, Level level) {
		super(type, level);
		xpReward = 0;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Mob.createMobAttributes()
				.add(Attributes.MAX_HEALTH, 200)
				.add(Attributes.MOVEMENT_SPEED, 0.33)
				.add(Attributes.ATTACK_DAMAGE, 16)
				.add(Attributes.ATTACK_KNOCKBACK, 1.6)
				.add(Attributes.KNOCKBACK_RESISTANCE, 1)
				.add(Attributes.FOLLOW_RANGE, 24)
				.add(Attributes.STEP_HEIGHT, 1.1);
	}

	@Override
	protected void registerGoals() {
		super.registerGoals();
		goalSelector.addGoal(0, new FloatGoal(this));
		goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.25, true));
		goalSelector.addGoal(3, new FollowOwnerGoal(this, 1.1));
		goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 8f));
		goalSelector.addGoal(9, new RandomLookAroundGoal(this));
	}

	@Override
	public boolean doHurtTarget(ServerLevel level, Entity target) {
		level.broadcastEntityEvent(this, ATTACK_EVENT);
		boolean hit = super.doHurtTarget(level, target);
		if (hit) {
			playSound(SoundEvents.WARDEN_ATTACK_IMPACT, 1f, 1.1f);
			target.push(0, 0.35, 0);
		}
		return hit;
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		LivingEntity target = getTarget();
		if (boomCharge >= 0) {
			if (target == null || !target.isAlive()) {
				boomCharge = -1;
			} else {
				getLookControl().setLookAt(target);
				if (--boomCharge < 0) sonicBoom(level, target);
			}
			return;
		}
		if (boomCooldown > 0) {
			boomCooldown--;
			return;
		}
		if (target != null && distanceToSqr(target) > 4 * 4 && distanceToSqr(target) < 16 * 16 && hasLineOfSight(target)) {
			boomCharge = BOOM_WINDUP;
			level.broadcastEntityEvent(this, BOOM_EVENT);
			playSound(SoundEvents.WARDEN_SONIC_CHARGE, 2f, 1.1f);
		}
	}

	private void sonicBoom(ServerLevel level, LivingEntity target) {
		boomCooldown = BOOM_COOLDOWN;
		Vec3 from = position().add(0, 1.6, 0);
		Vec3 to = target.getEyePosition().subtract(0, target.getBbHeight() * 0.3, 0);
		Vec3 d = to.subtract(from);
		Vec3 dir = d.normalize();
		for (int i = 2; i < Math.floor(d.length()) + 2; i += 2) {
			Vec3 p = from.add(dir.scale(i));
			level.sendParticles(ParticleTypes.SONIC_BOOM, p.x, p.y, p.z, 1, 0, 0, 0, 0);
		}
		RingFx.send(level, RingFxPayload.Kind.ALLY_SHOT, from, to);
		RingPowers.lightShot(level, from, to);
		playSound(SoundEvents.WARDEN_SONIC_BOOM, 3f, 1.1f);
		if (target.hurtServer(level, level.damageSources().sonicBoom(this), BOOM_DAMAGE)) {
			target.push(dir.x * 2.2, 0.5 + dir.y * 0.5, dir.z * 2.2);
			knock(target);
		}
	}

	static void knock(Entity entity) {
		RingPowers.syncVelocity(entity);
	}

	@Override
	public void handleEntityEvent(byte id) {
		if (id == ATTACK_EVENT) {
			attackAnimationState.start(tickCount);
		} else if (id == BOOM_EVENT) {
			sonicBoomAnimationState.start(tickCount);
		} else {
			super.handleEntityEvent(id);
		}
	}

	@Override
	protected void playStepSound(net.minecraft.core.BlockPos pos, net.minecraft.world.level.block.state.BlockState state) {
		playSound(SoundEvents.WARDEN_STEP, 0.6f, 1.3f);
		level().playSound(null, getX(), getY(), getZ(), SoundEvents.AMETHYST_BLOCK_STEP, SoundSource.NEUTRAL, 0.5f, 1.4f);
	}
}
