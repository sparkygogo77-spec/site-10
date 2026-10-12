package com.sparky.lanternring.ally;

import com.sparky.lanternring.ModParticles;
import java.util.List;
import java.util.UUID;
import net.minecraft.core.UUIDUtil;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.NeutralMob;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A hard-light ally summoned in Army mode (see ConstructArmy). It runs on the charge it was given:
 * that is its life in ticks, counting down every tick, and every hit it takes burns some more.
 * When it runs out the construct shatters. It only ever goes for hostile mobs (see isBadMob):
 * never players, pets, villagers or animals, and its owner can't hurt it by accident.
 */
public abstract class ConstructAlly extends PathfinderMob {
	private static final EntityDataAccessor<Integer> LIFE = SynchedEntityData.defineId(ConstructAlly.class, EntityDataSerializers.INT);
	private static final EntityDataAccessor<Integer> MAX_LIFE = SynchedEntityData.defineId(ConstructAlly.class, EntityDataSerializers.INT);
	/** Ticks of life a hit takes per point of damage. */
	private static final int DRAIN_PER_DAMAGE = 10;

	@Nullable
	private UUID owner;
	/** Its place in its formation (see Formation), refreshed every half second on the server. */
	private Formation.Place place = Formation.Place.ALONE;
	/** How fast the owner has been moving lately, in blocks per tick (server side). */
	private Vec3 ownerMotion = Vec3.ZERO;
	@Nullable
	private Vec3 ownerLast;

	protected ConstructAlly(EntityType<? extends ConstructAlly> type, Level level) {
		super(type, level);
		setPersistenceRequired();
	}

	/** Hostile mobs only: no players, no pets, no passive or calm neutral mobs, no other constructs. */
	public static boolean isBadMob(LivingEntity e) {
		if (!(e instanceof Enemy) || e instanceof ConstructAlly || !e.isAlive()) return false;
		if (e instanceof OwnableEntity pet && pet.getOwnerReference() != null) return false;
		// Endermen, zombified piglins and the like are left alone until something makes them angry.
		if (e instanceof NeutralMob neutral && !neutral.isAngry()) return false;
		return true;
	}

	public void setup(Player owner, int lifeTicks) {
		this.owner = owner.getUUID();
		entityData.set(MAX_LIFE, Math.max(1, lifeTicks));
		entityData.set(LIFE, Math.max(1, lifeTicks));
	}

	@Nullable
	public UUID ownerId() {
		return owner;
	}

	@Nullable
	public Player owner() {
		return owner == null ? null : level().getPlayerByUUID(owner);
	}

	/** Which formation it takes around its owner (see Formation). */
	public Formation.Stance stance() {
		return Formation.Stance.FLANK;
	}

	/** Whether {@code other}, an ally of the same owner and stance, forms up with this one. */
	protected boolean sameGroup(ConstructAlly other) {
		return true;
	}

	/** Called with its group (itself included, oldest first) each time the formation is worked out. */
	protected void formed(List<ConstructAlly> group) {}

	public Formation.Place place() {
		return place;
	}

	public Vec3 ownerMotion() {
		return ownerMotion;
	}

	public int life() {
		return entityData.get(LIFE);
	}

	/** How much of its charge is left, 1 when summoned down to 0. */
	public float lifeFraction() {
		return Math.min(1f, entityData.get(LIFE) / (float) Math.max(1, entityData.get(MAX_LIFE)));
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(LIFE, 20 * 60);
		builder.define(MAX_LIFE, 20 * 60);
	}

	@Override
	protected void registerGoals() {
		targetSelector.addGoal(1, new DefendOwnerGoal(this));
		targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Mob.class, 5, false, false, (target, level) -> isBadMob(target)));
	}

	@Override
	public boolean canAttack(LivingEntity target) {
		return isBadMob(target) && super.canAttack(target);
	}

	@Override
	public void tick() {
		super.tick();
		if (level() instanceof ServerLevel level) {
			LivingEntity target = getTarget();
			if (target != null && !isBadMob(target)) setTarget(null);
			Player owner = owner();
			if (owner != null) {
				// Players move on their own client, so the server's velocity for them is no good: track it here.
				Vec3 now = owner.position();
				if (ownerLast != null) ownerMotion = ownerMotion.lerp(now.subtract(ownerLast), 0.25);
				ownerLast = now;
			}
			if ((tickCount + getId()) % 10 == 0) {
				List<ConstructAlly> group = Formation.group(level, this);
				int index = group.indexOf(this);
				place = index < 0 ? Formation.Place.ALONE : new Formation.Place(index, group.size());
				formed(group);
			}
			int life = entityData.get(LIFE) - 1;
			entityData.set(LIFE, life);
			if (life <= 0) shatter(level);
		} else if (random.nextInt(3) == 0) {
			// A little light drifting off it all the time, more as it runs low.
			Vec3 at = position().add((random.nextDouble() - 0.5) * getBbWidth(), random.nextDouble() * getBbHeight(),
					(random.nextDouble() - 0.5) * getBbWidth());
			level().addParticle(lifeFraction() < 0.15f && random.nextBoolean() ? ModParticles.SHARD : ModParticles.MOTE,
					at.x, at.y, at.z, 0, 0.02, 0);
		}
	}

	/** Out of charge (or dismissed): bursts into shards of light and is gone. */
	public void shatter(ServerLevel level) {
		level.sendParticles(ModParticles.SHARD, getX(), getY() + getBbHeight() / 2, getZ(), 40,
				getBbWidth() / 2, getBbHeight() / 2, getBbWidth() / 2, 0.08);
		level.sendParticles(ModParticles.MOTE, getX(), getY() + getBbHeight() / 2, getZ(), 25,
				getBbWidth() / 2, getBbHeight() / 2, getBbWidth() / 2, 0.04);
		level.playSound(null, getX(), getY(), getZ(), SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.NEUTRAL, 1.2f, 0.8f);
		discard();
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		if (source.is(DamageTypeTags.BYPASSES_INVULNERABILITY)) {
			// /kill and the void.
			shatter(level);
			return true;
		}
		if (isInvulnerableTo(level, source)) return false;
		Entity attacker = source.getEntity();
		// The owner's own powers and the other constructs don't hurt it.
		if (attacker instanceof ConstructAlly || (attacker != null && owner != null && owner.equals(attacker.getUUID()))) return false;
		// Hits burn charge instead of health.
		int life = entityData.get(LIFE) - Math.max(1, Math.round(amount * DRAIN_PER_DAMAGE));
		entityData.set(LIFE, life);
		level.sendParticles(ModParticles.SPARK, getX(), getY() + getBbHeight() * 0.6, getZ(), 8,
				getBbWidth() / 3, getBbHeight() / 4, getBbWidth() / 3, 0.15);
		playSound(SoundEvents.AMETHYST_BLOCK_HIT, 1f, 1.2f);
		if (attacker instanceof LivingEntity living && isBadMob(living) && getTarget() == null) setTarget(living);
		if (life <= 0) shatter(level);
		return true;
	}

	@Override
	public boolean removeWhenFarAway(double distance) {
		return false;
	}

	@Override
	public boolean isPushable() {
		return false;
	}

	@Override
	public boolean canBeLeashed() {
		return false;
	}

	@Override
	public boolean causeFallDamage(double distance, float multiplier, DamageSource source) {
		return false;
	}

	@Override
	public boolean canBreatheUnderwater() {
		return true;
	}

	@Override
	public boolean shouldDropExperience() {
		return false;
	}

	@Override
	protected @Nullable SoundEvent getHurtSound(DamageSource source) {
		return null;
	}

	@Override
	protected @Nullable SoundEvent getDeathSound() {
		return null;
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putInt("ConstructLife", entityData.get(LIFE));
		output.putInt("ConstructMaxLife", entityData.get(MAX_LIFE));
		output.storeNullable("ConstructOwner", UUIDUtil.CODEC, owner);
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		entityData.set(LIFE, input.getIntOr("ConstructLife", 20 * 60));
		entityData.set(MAX_LIFE, input.getIntOr("ConstructMaxLife", 20 * 60));
		owner = input.read("ConstructOwner", UUIDUtil.CODEC).orElse(null);
	}
}
