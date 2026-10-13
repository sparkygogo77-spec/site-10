package com.sparky.lanternring.corps;

import com.sparky.lanternring.ally.ConstructAlly;
import java.util.function.Predicate;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.MoveTowardsRestrictionGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import org.jspecify.annotations.Nullable;

/**
 * The Blue Lantern rescue squad's mount (J, 2026-10-13): a ravager on the Blue Lantern's side,
 * ridden by the squad's rider (see BlueSquad). It isn't a monster or a raider, so golems and
 * other Blue villagers leave it alone; it charges and gores the monsters round its squad's
 * lantern and never touches players, villagers or animals. The rider steers nothing: the beast
 * picks its own fights while the rider fires its ring from its back.
 *
 * <p>Its look is a placeholder (the vanilla ravager tinted blue, BlueRavagerRenderer) until the
 * Blender skin is ready.
 */
public class BlueRavager extends PathfinderMob {
	/** How long the head-butt animation runs (as the vanilla ravager). */
	public static final int ATTACK_TICKS = 10;

	@Nullable
	private BlockPos post;
	private int attackTick;

	public BlueRavager(EntityType<? extends BlueRavager> type, Level level) {
		super(type, level);
		setPersistenceRequired();
		xpReward = 0;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return PathfinderMob.createMobAttributes()
				.add(Attributes.MAX_HEALTH, 100)
				.add(Attributes.MOVEMENT_SPEED, 0.3)
				.add(Attributes.KNOCKBACK_RESISTANCE, 0.75)
				.add(Attributes.ATTACK_DAMAGE, 12)
				.add(Attributes.ATTACK_KNOCKBACK, 1.5)
				.add(Attributes.FOLLOW_RANGE, BlueSquad.CLEAR_RADIUS)
				.add(Attributes.STEP_HEIGHT, 1.0);
	}

	@Override
	protected void registerGoals() {
		goalSelector.addGoal(0, new FloatGoal(this));
		goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.1, true));
		goalSelector.addGoal(4, new MoveTowardsRestrictionGoal(this, 0.9));
		goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.5));
		goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 6f));
		goalSelector.addGoal(7, new RandomLookAroundGoal(this));
		targetSelector.addGoal(1, new NearestAttackableTargetGoal<>(this, LivingEntity.class, 5, true, false,
				(e, level) -> inClearing().test(e)));
	}

	/** Monsters inside its squad's clearing (anywhere near it, before it has a post). */
	private Predicate<LivingEntity> inClearing() {
		return e -> ConstructAlly.isBadMob(e) && (post == null || e.distanceToSqr(Vec3.atCenterOf(post)) < BlueSquad.CLEAR_RADIUS * BlueSquad.CLEAR_RADIUS);
	}

	/** Keeps it round the squad's lantern. */
	public void guard(BlockPos lantern) {
		post = lantern;
		setHomeTo(lantern, (int) BlueSquad.CLEAR_RADIUS);
	}

	/** Once the rescue spot is picked it prowls round it (still fighting anything in the clearing). */
	public void prowl(BlockPos centre) {
		if (getHomePosition() == null || !getHomePosition().equals(centre)) setHomeTo(centre, (int) BlueRescue.WALLS + 4);
	}

	/** Its rider rides; the beast picks its own path and fights. */
	@Override
	public @Nullable LivingEntity getControllingPassenger() {
		return null;
	}

	@Override
	public void aiStep() {
		super.aiStep();
		if (attackTick > 0) attackTick--;
		// Drop a target that left the clearing, so it comes back instead of chasing off.
		LivingEntity t = getTarget();
		if (!level().isClientSide() && t != null && !inClearing().test(t)) setTarget(null);
	}

	@Override
	public boolean doHurtTarget(ServerLevel level, Entity target) {
		attackTick = ATTACK_TICKS;
		level.broadcastEntityEvent(this, (byte) 4);
		playSound(SoundEvents.RAVAGER_ATTACK, 1f, 1f);
		return super.doHurtTarget(level, target);
	}

	@Override
	public void handleEntityEvent(byte event) {
		if (event == 4) {
			attackTick = ATTACK_TICKS;
			playSound(SoundEvents.RAVAGER_ATTACK, 1f, 1f);
		} else {
			super.handleEntityEvent(event);
		}
	}

	/** Ticks left of the head-butt (client: for the model). */
	public int attackTick() {
		return attackTick;
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		// Its own side's light, and its rider's, never hurt it.
		Entity by = source.getEntity();
		if (by instanceof CorpsVillager || by instanceof CorpsGolem || source.is(DamageTypes.IN_WALL)) return false;
		return super.hurtServer(level, source, amount);
	}

	@Override
	protected SoundEvent getAmbientSound() {
		return SoundEvents.RAVAGER_AMBIENT;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.RAVAGER_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.RAVAGER_DEATH;
	}

	@Override
	protected void playStepSound(BlockPos pos, BlockState state) {
		playSound(SoundEvents.RAVAGER_STEP, 0.15f, 1f);
	}

	@Override
	public int getMaxHeadYRot() {
		return 45;
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		if (post != null) output.store("SquadPost", BlockPos.CODEC, post);
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		input.read("SquadPost", BlockPos.CODEC).ifPresent(this::guard);
	}
}
