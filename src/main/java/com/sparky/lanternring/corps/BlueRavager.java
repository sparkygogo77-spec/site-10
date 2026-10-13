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
	/**
	 * Flight with its lance rider (J, 2026-10-13: 23): where it's flying this tick (set by the
	 * rider every tick, null to come down), the current lance pass's far end, and the lance's
	 * cooldown. It flies faster than the villagers.
	 */
	@Nullable
	private Vec3 skyTo, passEnd;
	private int skyTicks, lanceRest;
	private static final double SKY_SPEED = 0.75, PASS_OVER = 7, LANCE_REACH = 2.6;
	private static final float LANCE_DAMAGE = 11f;

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
		// On the ground only: in the air its rider steers (lead).
		goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.1, true) {
			@Override
			public boolean canUse() {
				return !soaring() && super.canUse();
			}

			@Override
			public boolean canContinueToUse() {
				return !soaring() && super.canContinueToUse();
			}
		});
		goalSelector.addGoal(4, new MoveTowardsRestrictionGoal(this, 0.9) {
			@Override
			public boolean canUse() {
				return !soaring() && super.canUse();
			}
		});
		goalSelector.addGoal(5, new WaterAvoidingRandomStrollGoal(this, 0.5) {
			@Override
			public boolean canUse() {
				return !soaring() && super.canUse();
			}
		});
		goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 6f));
		goalSelector.addGoal(7, new RandomLookAroundGoal(this));
		targetSelector.addGoal(1, new NearestAttackableTargetGoal<>(this, LivingEntity.class, 5, true, false,
				(e, level) -> inClearing().test(e)));
	}

	/** Monsters inside its squad's clearing (anywhere near it, before it has a post). */
	private Predicate<LivingEntity> inClearing() {
		return e -> (ConstructAlly.isBadMob(e) || RedRage.red(e) && !(e instanceof Player)) && (post == null || e.distanceToSqr(Vec3.atCenterOf(post)) < BlueSquad.CLEAR_RADIUS * BlueSquad.CLEAR_RADIUS);
	}

	/** Keeps it round the squad's lantern. */
	public void guard(BlockPos lantern) {
		post = lantern;
		setHomeTo(lantern, (int) BlueSquad.CLEAR_RADIUS);
	}

	/** Recruited: it goes with the squad's leader (or ahead of them), fighting what threatens them. */
	public void follow(Vec3 at, @Nullable LivingEntity threat) {
		if (tickCount % 20 == 0) guard(BlockPos.containing(at));
		if (threat != null && getTarget() == null) setTarget(threat);
		double d = distanceToSqr(at);
		// Left far behind (the squad flies): it catches up.
		if (d > 48 * 48) teleportTo(at.x + 2, at.y, at.z + 2);
		else if (getTarget() == null && d > 6 * 6 && (getNavigation().isDone() || tickCount % 20 == 0)) getNavigation().moveTo(at.x, at.y, at.z, 1.2);
	}

	/**
	 * Its lance rider leads it (every tick while mounted): with a monster about it flies lance
	 * passes through it, the rider's lance of light striking as they go by; with none, it flies
	 * back to {@code home} when it's far, and walks once it's close.
	 */
	void lead(CorpsVillager rider, @Nullable LivingEntity threat, Vec3 home) {
		if (threat != null && threat.isAlive()) {
			Vec3 hit = threat.getBoundingBox().getCenter();
			if (passEnd == null || position().distanceToSqr(passEnd) < 2.5 * 2.5 || hit.distanceToSqr(passEnd) > (PASS_OVER + 6) * (PASS_OVER + 6)) {
				// A new pass: from here, straight through it and out the other side.
				Vec3 dir = new Vec3(hit.x - getX(), 0, hit.z - getZ());
				dir = dir.lengthSqr() < 1 ? Vec3.directionFromRotation(0, getYRot()) : dir.normalize();
				passEnd = hit.add(dir.scale(PASS_OVER)).add(0, 2.5, 0);
			}
			// Low through the monster, then up and out to the pass's end.
			boolean before = position().distanceToSqr(passEnd) > hit.distanceToSqr(passEnd);
			skyTo = before ? hit.subtract(0, 0.6, 0) : passEnd;
			skyTicks = 3;
			if (lanceRest == 0 && getBoundingBox().getCenter().distanceTo(hit) < LANCE_REACH + getBbWidth() / 2 && level() instanceof ServerLevel level) {
				lanceRest = 16;
				Vec3 push = getDeltaMovement().lengthSqr() < 1e-3 ? hit.subtract(position()).normalize() : getDeltaMovement().normalize();
				threat.hurtServer(level, level.damageSources().indirectMagic(rider, rider), LANCE_DAMAGE);
				threat.push(push.x * 1.4, 0.5, push.z * 1.4);
				com.sparky.lanternring.RingPowers.syncVelocity(threat);
				rider.fired();
				level.playSound(null, threat.blockPosition(), SoundEvents.TRIDENT_HIT, net.minecraft.sounds.SoundSource.NEUTRAL, 1.2f, 0.8f);
				level.playSound(null, threat.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, net.minecraft.sounds.SoundSource.NEUTRAL, 1f, 1.4f);
			}
			return;
		}
		passEnd = null;
		if (distanceToSqr(home) > 16 * 16) {
			skyTo = home.add(0, 4, 0);
			skyTicks = 3;
		}
	}

	/** Whether it's in the air with its rider. */
	public boolean soaring() {
		return skyTo != null;
	}

	private void skyStep(ServerLevel level) {
		if (--skyTicks <= 0 || getPassengers().isEmpty()) {
			// Nothing leading it up there: it glides down and walks again.
			skyTo = null;
			passEnd = null;
			setNoGravity(false);
			return;
		}
		setNoGravity(true);
		getNavigation().stop();
		Vec3 to = skyTo.subtract(position());
		double dist = to.length();
		Vec3 want = dist < 1e-3 ? Vec3.ZERO : to.scale(Math.min(SKY_SPEED, dist * 0.2) / dist);
		if (horizontalCollision) want = want.add(0, 0.3, 0);
		setDeltaMovement(getDeltaMovement().lerp(want, 0.2));
		float yaw = (float) (Math.atan2(to.z, to.x) * 180 / Math.PI) - 90f;
		setYRot(net.minecraft.util.Mth.approachDegrees(getYRot(), yaw, 14f));
		yBodyRot = getYRot();
		yHeadRot = getYRot();
		resetFallDistance();
		var mote = com.sparky.lanternring.ModParticles.of(com.sparky.lanternring.ModParticles.MOTE, com.sparky.lanternring.Corps.BLUE);
		if (tickCount % 2 == 0) level.sendParticles(mote, getX(), getY() + 0.2, getZ(), 3, 0.6, 0.15, 0.6, 0.01);
		// The rider's lance of light, held out ahead.
		Vec3 fwd = Vec3.directionFromRotation(0, getYRot());
		Vec3 grip = position().add(0, getBbHeight() + 0.9, 0).add(fwd.scale(0.3)).add(new Vec3(-fwd.z, 0, fwd.x).scale(0.45));
		for (int i = 1; i <= 7; i++) {
			Vec3 q = grip.add(fwd.scale(i * 0.5)).subtract(0, i * 0.06, 0);
			level.sendParticles(mote, q.x, q.y, q.z, 1, 0, 0, 0, 0);
		}
	}

	@Override
	public boolean causeFallDamage(double fallDistance, float multiplier, DamageSource source) {
		return false;
	}

	/** Once the rescue spot is picked it prowls round it (still fighting anything in the clearing). */
	public void prowl(BlockPos centre) {
		if (getHomePosition() == null || !getHomePosition().equals(centre)) setHomeTo(centre, (int) BlueRescue.WALLS + 4);
	}

	/** Room for its rider and one more behind (a player who asked the rider for a lift, J: 33a). */
	@Override
	protected boolean canAddPassenger(Entity passenger) {
		return getPassengers().size() < 2;
	}

	@Override
	protected Vec3 getPassengerAttachmentPoint(Entity passenger, net.minecraft.world.entity.EntityDimensions dims, float scale) {
		Vec3 seat = super.getPassengerAttachmentPoint(passenger, dims, scale);
		if (getPassengers().indexOf(passenger) <= 0) return seat;
		// The second seat is behind the rider.
		return seat.add(new Vec3(0, -0.1, -1.0).yRot((float) Math.toRadians(-getYRot())));
	}

	/**
	 * Dying with a player on its back (J, 2026-10-13: 34): sometimes the rider's ring chooses them,
	 * like a totem going off, and flies onto their finger.
	 */
	@Override
	public void die(DamageSource source) {
		if (level() instanceof ServerLevel level) {
			// Its rider splits off and fights on with its ring as a flyer (J: 23).
			for (CorpsVillager v : level.getEntitiesOfClass(CorpsVillager.class, getBoundingBox().inflate(40), v -> v.ridesOn(getUUID()))) v.loseMount();
			for (Entity e : getPassengers()) {
				if (e instanceof net.minecraft.server.level.ServerPlayer p && getRandom().nextFloat() < CHOSEN_CHANCE) chosen(level, p);
			}
		}
		super.die(source);
	}

	/** Chance a player riding a dying beast is chosen by the rider's ring. */
	private static final float CHOSEN_CHANCE = 0.35f;

	private void chosen(ServerLevel level, net.minecraft.server.level.ServerPlayer p) {
		for (net.minecraft.world.item.ItemStack held : p.getInventory()) {
			if (held.getItem() instanceof com.sparky.lanternring.item.PowerRingItem && com.sparky.lanternring.Corps.of(held) == com.sparky.lanternring.Corps.BLUE) return;
		}
		net.minecraft.world.item.ItemStack ring = com.sparky.lanternring.Corps.BLUE.ring();
		if (p.getMainHandItem().isEmpty()) p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND, ring);
		else if (!p.getInventory().add(ring)) p.spawnAtLocation(level, ring);
		level.sendParticles(net.minecraft.core.particles.ParticleTypes.TOTEM_OF_UNDYING, p.getX(), p.getY() + 1, p.getZ(), 60, 0.5, 0.8, 0.5, 0.4);
		level.sendParticles(com.sparky.lanternring.ModParticles.of(com.sparky.lanternring.ModParticles.MOTE, com.sparky.lanternring.Corps.BLUE), p.getX(), p.getY() + 1, p.getZ(), 30, 0.4, 0.6, 0.4, 0.05);
		level.playSound(null, p.blockPosition(), SoundEvents.TOTEM_USE, net.minecraft.sounds.SoundSource.PLAYERS, 1f, 1.2f);
		p.sendSystemMessage(net.minecraft.network.chat.Component.translatable("message.lanternring.blue_ring_chooses").withStyle(net.minecraft.ChatFormatting.AQUA));
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
		if (lanceRest > 0) lanceRest--;
		if (skyTo != null && level() instanceof ServerLevel level) skyStep(level);
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
