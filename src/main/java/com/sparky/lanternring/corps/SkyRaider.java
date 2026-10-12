package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.Hope;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.designs.Blueprint;
import java.util.List;
import java.util.Map;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.animal.golem.IronGolem;
import net.minecraft.world.entity.monster.illager.Pillager;
import net.minecraft.world.entity.npc.villager.AbstractVillager;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A Red Lantern sky raider: a pillager with a red ring who flies and fires bolts of burning red
 * light. Raiders live in a band round a floating red outpost. The first raider in an area is its
 * captain: it flies up and builds the outpost (a red island with a pillager watchtower on it),
 * calls more raiders until the band is five strong, and every so often leads the band down on the
 * nearest corps village (any colour but red) or ordinary village to burn it.
 */
public class SkyRaider extends Pillager {
	private static final EntityDataAccessor<Boolean> CAPTAIN = SynchedEntityData.defineId(SkyRaider.class, EntityDataSerializers.BOOLEAN);

	static final int OUTPOST_RADIUS = 11, BAND = 5;

	/** The top middle of its outpost island. */
	@Nullable
	private BlockPos outpost;
	private boolean outpostBuilt;
	/** -1 not decided, 0 a band member, 1 the captain. */
	private int rank = -1;
	/** The village it's raiding, and how long it has left there. */
	@Nullable
	private BlockPos raid;
	private int raidTicks;
	private int raidTimer = -1, callTimer = 200, shotCooldown = 30;
	private double orbit;
	private SkyBuilds.@Nullable Job job;

	public SkyRaider(EntityType<? extends SkyRaider> type, Level level) {
		super(type, level);
		setNoGravity(true);
		setPersistenceRequired();
		orbit = random.nextDouble() * Math.PI * 2;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Pillager.createAttributes().add(Attributes.MAX_HEALTH, 36).add(Attributes.FOLLOW_RANGE, 40).add(Attributes.ARMOR, 4);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(CAPTAIN, false);
	}

	@Override
	protected void registerGoals() {
		// No crossbow or walking goals: it flies and shoots on its own (customServerAiStep).
		targetSelector.addGoal(1, new HurtByTargetGoal(this, SkyRaider.class).setAlertOthers());
		targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
		targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, AbstractVillager.class, false));
		targetSelector.addGoal(3, new NearestAttackableTargetGoal<>(this, IronGolem.class, true));
	}

	@Override
	protected void populateDefaultEquipmentSlots(RandomSource rng, DifficultyInstance difficulty) {
		setItemSlot(EquipmentSlot.MAINHAND, Corps.RED.ring());
	}

	public boolean captain() {
		return entityData.get(CAPTAIN);
	}

	private void setCaptain(boolean captain) {
		rank = captain ? 1 : 0;
		entityData.set(CAPTAIN, captain);
		setCustomName(Component.translatable(captain ? "entity.lanternring.sky_raider.captain" : "entity.lanternring.sky_raider.named")
				.withStyle(ChatFormatting.RED));
	}

	// ---- every tick -----------------------------------------------------------------------------

	@Override
	public void tick() {
		setNoGravity(true);
		super.tick();
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (getMainHandItem().isEmpty()) setItemSlot(EquipmentSlot.MAINHAND, Corps.RED.ring());
		if (rank < 0 && tickCount > 5) decide(level);
		if (rank == 1) lead(level);
		LivingEntity target = getTarget();
		if (target != null && (!target.isAlive() || distanceToSqr(target) > 48 * 48)) {
			setTarget(null);
			target = null;
		}
		if (raid != null && --raidTicks <= 0) raid = null;
		fly(level, target);
		if (target != null && --shotCooldown <= 0 && distanceToSqr(target) < 26 * 26 && hasLineOfSight(target)) {
			shotCooldown = 25 + random.nextInt(15);
			CorpsShots.shoot(level, this, target, Corps.RED, 5);
		}
		if (tickCount % 3 == 0) {
			level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.RED), getX(), getY() - 0.1, getZ(), 1, 0.2, 0.1, 0.2, 0.01);
		}
	}

	/** Joins the nearest captain's band, or becomes a captain and picks a spot in the sky. */
	private void decide(ServerLevel level) {
		SkyRaider captain = nearestCaptain(level, blockPosition(), 96);
		if (captain != null && captain != this && captain.outpost != null) {
			setCaptain(false);
			outpost = captain.outpost;
			return;
		}
		setCaptain(true);
		BlockPos ground = blockPosition();
		outpost = SkyBuilds.skySpot(level, ground, OUTPOST_RADIUS, 22);
	}

	@Nullable
	private static SkyRaider nearestCaptain(ServerLevel level, BlockPos at, double r) {
		SkyRaider best = null;
		double bestD = Double.MAX_VALUE;
		for (SkyRaider s : level.getEntitiesOfClass(SkyRaider.class, new AABB(at).inflate(r), e -> e.isAlive() && e.captain())) {
			double d = s.distanceToSqr(Vec3.atCenterOf(at));
			if (d < bestD) {
				bestD = d;
				best = s;
			}
		}
		return best;
	}

	private void lead(ServerLevel level) {
		if (outpost == null) return;
		if (SkyBuilds.running(job)) return;
		job = null;
		if (!outpostBuilt) {
			if (distanceToSqr(Vec3.atCenterOf(outpost)) > 24 * 24) return;
			Map<BlockPos, BlockState> blocks = SkyBuilds.island(outpost, OUTPOST_RADIUS, Corps.RED, random, false);
			Blueprint tower = SkyBuilds.structure(level, "minecraft:pillager_outpost/watchtower");
			if (tower != null) {
				Rotation rot = Rotation.values()[random.nextInt(4)];
				int w = SkyBuilds.footW(tower, rot), d = SkyBuilds.footD(tower, rot);
				blocks.putAll(SkyBuilds.place(tower, outpost.getX() - w / 2, outpost.getY(), outpost.getZ() - d / 2, rot));
			}
			job = SkyBuilds.start(level, blocks, RingTuning.CORPS_BUILD_TIME.ticks() * 2, Corps.RED, true, this);
			outpostBuilt = true;
			raidTimer = RingTuning.CORPS_RAID.ticks();
			for (ServerPlayer p : level.players()) {
				if (p.distanceToSqr(this) < 128 * 128) {
					p.sendSystemMessage(Component.translatable("message.lanternring.red_outpost").withStyle(ChatFormatting.RED, ChatFormatting.ITALIC));
				}
			}
			return;
		}
		// Call more raiders, one at a time.
		if (--callTimer <= 0) {
			callTimer = RingTuning.CORPS_RAIDER_CALL.ticks();
			List<SkyRaider> band = band(level);
			if (band.size() < BAND) {
				SkyRaider r = CorpsMobs.SKY_RAIDER.create(level, EntitySpawnReason.MOB_SUMMONED);
				if (r != null) {
					r.setCaptain(false);
					r.outpost = outpost;
					r.setItemSlot(EquipmentSlot.MAINHAND, Corps.RED.ring());
					r.snapTo(outpost.getX() + 0.5, outpost.getY() + 3, outpost.getZ() + 0.5, random.nextFloat() * 360f, 0f);
					level.addFreshEntity(r);
					CorpsShots.summon(level, r.position(), r.getBbHeight(), 1f, Corps.RED);
				}
			}
		}
		// Lead the band on a raid.
		if (raidTimer <= 0) raidTimer = RingTuning.CORPS_RAID.ticks();
		if (--raidTimer == 0) {
			raidTimer = RingTuning.CORPS_RAID.ticks();
			BlockPos village = village(level);
			if (village != null) {
				int ticks = 60 * 20;
				for (SkyRaider r : band(level)) {
					r.raid = village;
					r.raidTicks = ticks;
				}
				level.playSound(null, village.getX(), village.getY(), village.getZ(), SoundEvents.RAID_HORN, SoundSource.HOSTILE, 64f, 1f);
				for (ServerPlayer p : level.players()) {
					if (p.distanceToSqr(Vec3.atCenterOf(village)) < 96 * 96) {
						p.sendSystemMessage(Component.translatable("message.lanternring.red_raid").withStyle(ChatFormatting.RED, ChatFormatting.BOLD));
					}
				}
			}
		}
	}

	private List<SkyRaider> band(ServerLevel level) {
		BlockPos home = outpost;
		return level.getEntitiesOfClass(SkyRaider.class, new AABB(home).inflate(96), r -> r.isAlive() && home.equals(r.outpost));
	}

	/** The nearest corps village of another colour, or failing that the nearest villagers. */
	@Nullable
	private BlockPos village(ServerLevel level) {
		AbstractVillager best = null;
		double bestD = Double.MAX_VALUE;
		for (AbstractVillager v : level.getEntitiesOfClass(AbstractVillager.class, new AABB(outpost).inflate(160), LivingEntity::isAlive)) {
			if (v instanceof CorpsVillager cv && cv.corps() == Corps.RED) continue;
			// Corps villages and the Blue Lantern's villages first: they count as much nearer.
			boolean corps = v instanceof CorpsVillager || v.hasAttached(Hope.MARK);
			double d = v.distanceToSqr(Vec3.atCenterOf(outpost)) * (corps ? 0.25 : 1);
			if (d < bestD) {
				bestD = d;
				best = v;
			}
		}
		return best == null ? null : best.blockPosition();
	}

	// ---- flying ---------------------------------------------------------------------------------

	private void fly(ServerLevel level, @Nullable LivingEntity target) {
		orbit += 0.03;
		Vec3 goal;
		double speed = 0.5;
		if (target != null) {
			// Circle the target just out of reach, above it.
			goal = target.position().add(Math.cos(orbit) * 7, 5 + Math.sin(orbit * 2) * 1.5, Math.sin(orbit) * 7);
		} else if (raid != null) {
			goal = Vec3.atCenterOf(raid).add(Math.cos(orbit) * 10, 12, Math.sin(orbit) * 10);
			speed = 0.6;
		} else if (outpost != null) {
			goal = Vec3.atCenterOf(outpost).add(Math.cos(orbit) * (OUTPOST_RADIUS + 4), 8 + Math.sin(orbit * 3) * 2, Math.sin(orbit) * (OUTPOST_RADIUS + 4));
			if (rank == 1 && (!outpostBuilt || SkyBuilds.running(job))) goal = Vec3.atCenterOf(outpost).add(OUTPOST_RADIUS + 3, 10, 0);
		} else {
			goal = position();
		}
		Vec3 to = goal.subtract(position());
		double dist = to.length();
		Vec3 want = dist < 0.01 ? Vec3.ZERO : to.scale(Math.min(speed, dist * 0.08) / dist);
		setDeltaMovement(getDeltaMovement().lerp(want, 0.1));
		Vec3 face = target != null ? target.position().subtract(position()) : getDeltaMovement();
		if (face.horizontalDistanceSqr() > 1.0e-4) {
			float yaw = (float) (Mth.atan2(face.z, face.x) * Mth.RAD_TO_DEG) - 90f;
			setYRot(Mth.approachDegrees(getYRot(), yaw, 12f));
			yBodyRot = getYRot();
			yHeadRot = getYRot();
		}
	}

	@Override
	public void travel(Vec3 input) {
		move(MoverType.SELF, getDeltaMovement());
	}

	@Override
	public boolean causeFallDamage(double fallDistance, float multiplier, DamageSource source) {
		return false;
	}

	@Override
	public boolean onClimbable() {
		return false;
	}

	@Override
	public boolean canJoinRaid() {
		return false;
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		if (source.getEntity() instanceof SkyRaider || source.is(DamageTypes.IN_WALL)) return false;
		return super.hurtServer(level, source, amount);
	}

	// ---- the Red Lantern Corps answers a floating village ----------------------------------------

	/** A raid captain arrives 70 to 90 blocks from a new floating village and builds its outpost there. */
	static void rivalsArrive(ServerLevel level, @Nullable BlockPos island, Corps rival) {
		if (island == null || nearestCaptain(level, island, 200) != null) return;
		double a = level.getRandom().nextDouble() * Math.PI * 2;
		double d = 70 + level.getRandom().nextDouble() * 20;
		BlockPos ground = island.offset((int) (Math.cos(a) * d), 0, (int) (Math.sin(a) * d));
		if (!level.isLoaded(ground)) return;
		SkyRaider captain = CorpsMobs.SKY_RAIDER.create(level, EntitySpawnReason.EVENT);
		if (captain == null) return;
		captain.setCaptain(true);
		captain.outpost = SkyBuilds.skySpot(level, ground, OUTPOST_RADIUS, 22).atY(Math.max(island.getY(),
				SkyBuilds.skySpot(level, ground, OUTPOST_RADIUS, 22).getY()));
		captain.setItemSlot(EquipmentSlot.MAINHAND, Corps.RED.ring());
		captain.snapTo(ground.getX() + 0.5, captain.outpost.getY() + 6, ground.getZ() + 0.5, 0f, 0f);
		level.addFreshEntity(captain);
		CorpsShots.summon(level, captain.position(), captain.getBbHeight(), 1f, Corps.RED);
		for (ServerPlayer p : level.players()) {
			if (p.distanceToSqr(Vec3.atCenterOf(island)) < 160 * 160) {
				p.sendSystemMessage(Component.translatable("message.lanternring.red_rivals", rival.ring().getHoverName())
						.withStyle(ChatFormatting.RED, ChatFormatting.ITALIC));
			}
		}
	}

	// ---- saving ---------------------------------------------------------------------------------

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putInt("RaiderRank", rank);
		output.putBoolean("OutpostBuilt", outpostBuilt);
		output.putInt("RaidTimer", raidTimer);
		if (outpost != null) output.store("Outpost", BlockPos.CODEC, outpost);
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		rank = input.getIntOr("RaiderRank", -1);
		entityData.set(CAPTAIN, rank == 1);
		outpostBuilt = input.getBooleanOr("OutpostBuilt", false);
		raidTimer = input.getIntOr("RaidTimer", -1);
		outpost = input.read("Outpost", BlockPos.CODEC).orElse(null);
	}
}
