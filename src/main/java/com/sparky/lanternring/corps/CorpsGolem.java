package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.animal.golem.IronGolem;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A corps golem: an iron golem forged by a corps villager's ring, half again as big, five times as
 * tough, and able to throw bolts of its corps' light at things it can't reach (like the flying Red
 * raiders). It guards the village it was made for and leaps back to it if it strays.
 */
public class CorpsGolem extends IronGolem {
	private static final EntityDataAccessor<Integer> CORPS = SynchedEntityData.defineId(CorpsGolem.class, EntityDataSerializers.INT);

	@Nullable
	private BlockPos home;
	private int shotCooldown = 40;

	public CorpsGolem(EntityType<? extends CorpsGolem> type, Level level) {
		super(type, level);
		setPlayerCreated(true);
		setPersistenceRequired();
	}

	@Override
	protected void registerGoals() {
		super.registerGoals();
		// A red golem living in a sanctuary also guards it from anyone without a red ring.
		targetSelector.addGoal(3, new net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal<>(this,
				net.minecraft.world.entity.player.Player.class, 10, true, false,
				(target, level) -> corps() == Corps.RED && entityTags().contains(RedSanctuary.TAG) && !RedSanctuary.friend(target)));
	}

	public static AttributeSupplier.Builder createAttributes() {
		return IronGolem.createAttributes()
				.add(Attributes.MAX_HEALTH, 250)
				.add(Attributes.ATTACK_DAMAGE, 30)
				.add(Attributes.ARMOR, 12)
				.add(Attributes.KNOCKBACK_RESISTANCE, 1)
				.add(Attributes.FOLLOW_RANGE, 40)
				.add(Attributes.SCALE, 1.5);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(CORPS, 0);
	}

	public Corps corps() {
		Corps[] all = Corps.values();
		int i = entityData.get(CORPS);
		return i >= 0 && i < all.length ? all[i] : Corps.GREEN;
	}

	public void setup(Corps corps, BlockPos home) {
		entityData.set(CORPS, corps.ordinal());
		this.home = home;
		setCustomName(Component.translatable("entity.lanternring.corps_golem.named", Component.translatable("corps.lanternring." + corps.getSerializedName()))
				.withStyle(corps.chat));
	}

	@Override
	public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
			@Nullable SpawnGroupData data) {
		SpawnGroupData out = super.finalizeSpawn(level, difficulty, reason, data);
		if (home == null) setup(corps(), blockPosition());
		return out;
	}

	@Nullable
	public BlockPos home() {
		return home;
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		Corps corps = corps();
		if (tickCount % 8 == 0) {
			level.sendParticles(ModParticles.of(ModParticles.MOTE, corps), getX(), getY() + getBbHeight() * 0.6, getZ(), 2,
					getBbWidth() * 0.4, getBbHeight() * 0.3, getBbWidth() * 0.4, 0.01);
		}
		if (tickCount % 40 == 0 && getHealth() < getMaxHealth()) heal(2);
		// Strayed (knocked off its island, chased something away): a leap of light back home.
		if (home != null && tickCount % 20 == 0 && distanceToSqr(Vec3.atBottomCenterOf(home)) > 40 * 40 && getTarget() == null) {
			CorpsShots.summon(level, position(), getBbHeight(), getBbWidth(), corps);
			teleportTo(home.getX() + 0.5, home.getY(), home.getZ() + 0.5);
			CorpsShots.summon(level, position(), getBbHeight(), getBbWidth(), corps);
		}
		LivingEntity target = getTarget();
		if (--shotCooldown <= 0 && target != null && target.isAlive()) {
			double dist = distanceToSqr(target);
			if (dist > 4 * 4 && dist < 24 * 24 && hasLineOfSight(target)) {
				shotCooldown = 40;
				CorpsShots.shoot(level, this, target, corps, 10);
			}
		}
	}

	@Override
	public boolean causeFallDamage(double fallDistance, float multiplier, DamageSource source) {
		return false;
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putInt("Corps", entityData.get(CORPS));
		if (home != null) output.store("CorpsHome", BlockPos.CODEC, home);
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		entityData.set(CORPS, input.getIntOr("Corps", 0));
		home = input.read("CorpsHome", BlockPos.CODEC).orElse(null);
	}

	static void forge(ServerLevel level, BlockPos at, Corps corps, BlockPos home) {
		CorpsGolem golem = CorpsMobs.CORPS_GOLEM.create(level, EntitySpawnReason.MOB_SUMMONED);
		if (golem == null) return;
		golem.setup(corps, home);
		golem.snapTo(at.getX() + 0.5, at.getY(), at.getZ() + 0.5, level.getRandom().nextFloat() * 360f, 0f);
		level.addFreshEntity(golem);
		CorpsShots.summon(level, golem.position(), golem.getBbHeight(), golem.getBbWidth(), corps);
		level.playSound(null, at, SoundEvents.IRON_GOLEM_REPAIR, SoundSource.NEUTRAL, 1.2f, 0.7f);
	}
}
