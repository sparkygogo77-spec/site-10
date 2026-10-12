package com.sparky.lanternring.ally;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.Terror;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LeapAtTargetGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.ai.navigation.WallClimberNavigation;
import net.minecraft.world.level.Level;
import org.jspecify.annotations.Nullable;

/**
 * The Yellow Lantern's Brood (see Terror): a giant hard-light spider or one of its spiderlings.
 * They crawl out of the darkness round a mob their owner frightened and hunt it, climbing walls
 * to get at it; the giant's bite pins it down, the spiderlings' poisons it. When their prey is
 * dead they go for anything else their owner frightened, then any hostile mob nearby, and with
 * nothing left to hunt they fade back into the dark.
 */
public class BroodSpider extends ConstructAlly {
	/** Ticks with nothing to hunt before it fades away. */
	private static final int IDLE_FADE = 60;
	@Nullable
	private LivingEntity prey;
	private int idle;

	public BroodSpider(EntityType<? extends BroodSpider> type, Level level) {
		super(type, level);
		xpReward = 0;
	}

	public static AttributeSupplier.Builder createAttributes(boolean giant) {
		return Mob.createMobAttributes()
				.add(Attributes.MAX_HEALTH, giant ? 60 : 8)
				.add(Attributes.MOVEMENT_SPEED, giant ? 0.36 : 0.42)
				.add(Attributes.ATTACK_DAMAGE, giant ? 9 : 2.5)
				.add(Attributes.ATTACK_KNOCKBACK, giant ? 1.0 : 0)
				.add(Attributes.KNOCKBACK_RESISTANCE, giant ? 1 : 0)
				.add(Attributes.FOLLOW_RANGE, 32)
				.add(Attributes.STEP_HEIGHT, giant ? 1.6 : 1.0);
	}

	public boolean isGiant() {
		return getType() == ModEntities.BROOD_SPIDER;
	}

	public void setPrey(LivingEntity prey) {
		this.prey = prey;
		setTarget(prey);
	}

	@Override
	protected Corps corps() {
		return Corps.YELLOW;
	}

	@Override
	protected void registerGoals() {
		super.registerGoals();
		targetSelector.addGoal(1, new NearestAttackableTargetGoal<>(this, LivingEntity.class, 5, false, false,
				(target, level) -> Terror.isPreyOf(target, ownerId())));
		goalSelector.addGoal(0, new FloatGoal(this));
		goalSelector.addGoal(2, new LeapAtTargetGoal(this, 0.45f));
		goalSelector.addGoal(3, new MeleeAttackGoal(this, 1.3, true));
		goalSelector.addGoal(9, new RandomLookAroundGoal(this));
	}

	@Override
	protected boolean canHunt(LivingEntity target) {
		if (target.getUUID().equals(ownerId())) return false;
		return target == prey && target.isAlive() || Terror.isPreyOf(target, ownerId()) || isBadMob(target);
	}

	@Override
	protected PathNavigation createNavigation(Level level) {
		return new WallClimberNavigation(this, level);
	}

	@Override
	public boolean onClimbable() {
		return horizontalCollision;
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (prey != null && !prey.isAlive()) prey = null;
		if (prey != null && getTarget() != prey && distanceToSqr(prey) < 40 * 40) setTarget(prey);
		if (getTarget() == null) {
			if (++idle > IDLE_FADE) shatter(level);
		} else {
			idle = 0;
		}
	}

	@Override
	public boolean doHurtTarget(ServerLevel level, Entity target) {
		boolean hit = super.doHurtTarget(level, target);
		if (hit && target instanceof LivingEntity living) {
			if (isGiant()) {
				// Pinned in place by the bite.
				living.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 40, 3), this);
				playSound(SoundEvents.SPIDER_HURT, 1.5f, 0.5f);
			} else {
				living.addEffect(new MobEffectInstance(MobEffects.POISON, 60, 0), this);
			}
		}
		return hit;
	}

	@Override
	protected void playStepSound(net.minecraft.core.BlockPos pos, net.minecraft.world.level.block.state.BlockState state) {
		playSound(SoundEvents.SPIDER_STEP, isGiant() ? 0.4f : 0.1f, isGiant() ? 0.6f : 1.6f);
	}
}
