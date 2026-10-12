package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.designs.Blueprint;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import com.sparky.lanternring.ally.ConstructAlly;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.DifficultyInstance;
import net.minecraft.world.entity.SpawnGroupData;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.entity.npc.villager.Villager;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A Lantern Corps villager: a villager who took the oath at a lantern (or was born to it). It
 * trades like any villager, wears its corps' ring and fights off monsters and Red raiders with it.
 * The first one in an area is the village's founder and builds, step by step:
 * <ol>
 * <li>on the ground, corps golems (two at a time) and three new houses round the village,</li>
 * <li>then flies up and raises a floating island over the village, four houses on it and a
 * lantern in the middle, and calls two more corps villagers and a golem to live there,</li>
 * <li>and once the floating village stands, the Red Lantern Corps notices: a raid captain arrives
 * and builds a sky outpost within sight (see {@link SkyRaider}).</li>
 * </ol>
 * Corps villagers take no fall damage: one that falls off the island flies back up on its ring.
 */
public class CorpsVillager extends Villager {
	private static final EntityDataAccessor<Integer> CORPS = SynchedEntityData.defineId(CorpsVillager.class, EntityDataSerializers.INT);
	private static final EntityDataAccessor<Boolean> FLYING = SynchedEntityData.defineId(CorpsVillager.class, EntityDataSerializers.BOOLEAN);
	/** Hovering in the building formation, pouring light into a construct. */
	private static final EntityDataAccessor<Boolean> BUILDING = SynchedEntityData.defineId(CorpsVillager.class, EntityDataSerializers.BOOLEAN);
	/**
	 * Whether it wears its suit. Blue Lantern villagers always do (J, 2026-10-12: a bearer, not a
	 * construct); the renderer only draws a see-through construct for an unsuited one.
	 */
	private static final EntityDataAccessor<Boolean> SUITED = SynchedEntityData.defineId(CorpsVillager.class, EntityDataSerializers.BOOLEAN);
	/** Blue Lantern in a fight: the entity its ring arm points at (-1 none), and a count of shots so the ring flares on each. */
	private static final EntityDataAccessor<Integer> AIM_AT = SynchedEntityData.defineId(CorpsVillager.class, EntityDataSerializers.INT);
	private static final EntityDataAccessor<Integer> SHOTS = SynchedEntityData.defineId(CorpsVillager.class, EntityDataSerializers.INT);
	/** Where the ring sits on the right hand: shoulder height and offsets, and the arm's length (the player's, at this model's 0.9375 scale). */
	private static final double SHOULDER = 1.289, SHOULDER_SIDE = 0.347, SHOULDER_FORWARD = 0.075, ARM = 0.69;

	public static final int GROUND = 0, RISING = 1, SKY = 2;
	static final int GROUND_HOUSES = 3, ISLAND_HOUSES = 4, ISLAND_RADIUS = 16, ISLAND_HEIGHT = 30;

	@Nullable
	private BlockPos home;
	/** The top middle of the floating island (null until the founder picks it). */
	@Nullable
	private BlockPos island;
	private int stage = GROUND;
	/** -1 not decided yet, 0 a villager of someone else's village, 1 the founder. */
	private int founder = -1;
	private int houses, islandHouses;
	/** Blue: the sky city has nothing left to build (checked again after a restart). */
	private boolean cityComplete;
	private boolean islandBuilt;
	private int buildTimer = 100, golemTimer = 60, shotCooldown, rivalTimer = -1;
	private SkyBuilds.@Nullable Job job;
	/** Where it's flying to, and whether it lands there. */
	@Nullable
	private Vec3 flyTo;
	private boolean landAtEnd;
	/** Blue Lantern: the crew it leads (founders only), and the crew it belongs to. See BlueCrew. */
	@Nullable
	private BlueCrew ownCrew;
	@Nullable
	private BlueCrew memberOf;
	/** The rest of the route to flyTo (see SkyPath). */
	private java.util.Deque<Vec3> path = new java.util.ArrayDeque<>();
	/** Ticks left following a crew order (holding a place, following the leader); then it goes home. */
	private int formationTicks;
	@Nullable
	private Vec3 formationLook;
	/** Client: eased pose blends for the renderer (see BlueVillagerRenderer). */
	private float fly, oFly, build, oBuild, fwd, oFwd, side, oSide, aim, oAim, flash, oFlash;
	private int seenShots;
	/** Client: where the ring arm last pointed, relative to the body (radians), so it eases down from there. */
	private float aimYaw, aimPitch;
	/** Blue Lantern: how it fights (see BlueCombat). */
	private final BlueCombat combat = new BlueCombat(this);

	public CorpsVillager(EntityType<? extends CorpsVillager> type, Level level) {
		super(type, level);
		setPersistenceRequired();
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Villager.createAttributes().add(Attributes.MAX_HEALTH, 40).add(Attributes.ARMOR, 6);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(CORPS, 0);
		builder.define(FLYING, false);
		builder.define(BUILDING, false);
		builder.define(SUITED, false);
		builder.define(AIM_AT, -1);
		builder.define(SHOTS, 0);
	}

	public Corps corps() {
		Corps[] all = Corps.values();
		int i = entityData.get(CORPS);
		return i >= 0 && i < all.length ? all[i] : Corps.GREEN;
	}

	public void setCorps(Corps corps) {
		entityData.set(CORPS, corps.ordinal());
		setCustomName(Component.translatable("entity.lanternring.corps_villager.named",
				Component.translatable("corps.lanternring." + corps.getSerializedName())).withStyle(corps.chat));
		setItemSlot(EquipmentSlot.MAINHAND, corps.ring());
		// Blue Lantern bearers wear the blue suit from the start, never a see-through construct (J, 2026-10-12).
		if (corps == Corps.BLUE) entityData.set(SUITED, true);
	}

	public boolean flying() {
		return entityData.get(FLYING);
	}

	public boolean building() {
		return entityData.get(BUILDING);
	}

	public boolean suited() {
		return entityData.get(SUITED);
	}

	/** The suit forms on it in a flash of its corps' light. */
	public void suitUp(ServerLevel level) {
		if (suited()) return;
		entityData.set(SUITED, true);
		CorpsShots.summon(level, position(), getBbHeight(), 1f, corps());
		level.playSound(null, blockPosition(), SoundEvents.BEACON_ACTIVATE, SoundSource.NEUTRAL, 1f, 1.4f);
	}

	public float flyAnim(float partialTick) {
		return Mth.lerp(partialTick, oFly, fly);
	}

	public float buildAnim(float partialTick) {
		return Mth.lerp(partialTick, oBuild, build);
	}

	public float leanForward(float partialTick) {
		return Mth.lerp(partialTick, oFwd, fwd);
	}

	public float leanSide(float partialTick) {
		return Mth.lerp(partialTick, oSide, side);
	}

	/** 0..1 how far the ring arm is raised at what it's fighting. */
	public float aimAnim(float partialTick) {
		return Mth.lerp(partialTick, oAim, aim);
	}

	/** 1 the moment its ring fires, fading to 0: how bright the ring flares. */
	public float flashAnim(float partialTick) {
		return Mth.lerp(partialTick, oFlash, flash);
	}

	/** Client: the ring arm's aim relative to the body, in radians (yaw, then pitch, down positive). */
	public float aimYaw() {
		return aimYaw;
	}

	public float aimPitch() {
		return aimPitch;
	}

	/** What its ring arm points at (client and server), or null. */
	public net.minecraft.world.entity.@Nullable Entity aimTarget() {
		int id = entityData.get(AIM_AT);
		return id < 0 ? null : level().getEntity(id);
	}

	void aimAt(@Nullable LivingEntity target) {
		entityData.set(AIM_AT, target == null ? -1 : target.getId());
	}

	/** Its ring just fired: the clients flare it. */
	void fired() {
		entityData.set(SHOTS, entityData.get(SHOTS) + 1);
	}

	/**
	 * Where its ring is when the right arm points at {@code at}: the end of the arm, as
	 * BlueVillagerModel poses it. Used for where beams and the lasso's string start.
	 */
	public static Vec3 ringPos(LivingEntity v, float partial, Vec3 at) {
		float yaw = Mth.rotLerp(partial, v.yBodyRotO, v.yBodyRot) * Mth.DEG_TO_RAD;
		Vec3 forward = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
		Vec3 right = new Vec3(-Mth.cos(yaw), 0, -Mth.sin(yaw));
		Vec3 shoulder = v.getPosition(partial).add(right.scale(SHOULDER_SIDE)).add(forward.scale(SHOULDER_FORWARD)).add(0, SHOULDER, 0);
		Vec3 d = at.subtract(shoulder);
		return d.lengthSqr() < 1e-4 ? shoulder : shoulder.add(d.normalize().scale(ARM));
	}

	@Override
	public void tick() {
		super.tick();
		if (level().isClientSide()) animate();
	}

	/** Client: eases into the flight and building poses and leans with the way it's flying. */
	private void animate() {
		oFly = fly;
		oBuild = build;
		oFwd = fwd;
		oSide = side;
		oAim = aim;
		oFlash = flash;
		aim = approach(aim, entityData.get(AIM_AT) >= 0 ? 1 : 0, 0.25f);
		int shots = entityData.get(SHOTS);
		flash = shots != seenShots ? 1f : Math.max(0f, flash - 0.125f);
		seenShots = shots;
		net.minecraft.world.entity.Entity t = aimTarget();
		if (t != null) {
			Vec3 d = t.getBoundingBox().getCenter().subtract(getX(), getY() + SHOULDER, getZ());
			float yaw = (float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90f;
			aimYaw = Mth.wrapDegrees(yaw - yBodyRot) * Mth.DEG_TO_RAD;
			aimPitch = (float) -Mth.atan2(d.y, Math.sqrt(d.x * d.x + d.z * d.z));
		}
		fly = approach(fly, flying() ? 1 : 0, 0.2f);
		build = approach(build, building() ? 1 : 0, 0.2f);
		float yaw = yBodyRot * Mth.DEG_TO_RAD;
		double vx = getX() - xo, vz = getZ() - zo;
		float forward = (float) (vx * -Mth.sin(yaw) + vz * Mth.cos(yaw));
		float right = (float) (vx * -Mth.cos(yaw) + vz * -Mth.sin(yaw));
		fwd = approach(fwd, flying() ? Mth.clamp(forward / 0.45f, -1, 1) : 0, 0.2f);
		side = approach(side, flying() ? Mth.clamp(right / 0.45f, -1, 1) : 0, 0.2f);
	}

	private static float approach(float from, float to, float rate) {
		float next = from + (to - from) * rate;
		return Math.abs(to - next) < 0.002f ? to : next;
	}

	public int stage() {
		return stage;
	}

	@Nullable
	public BlockPos island() {
		return islandBuilt ? island : null;
	}

	/** A villager called to live in a finished floating village. */
	void joinIsland(BlockPos island) {
		this.island = island;
		this.islandBuilt = true;
		this.home = island.above();
		this.stage = SKY;
		this.founder = 0;
	}

	@Override
	public @Nullable SpawnGroupData finalizeSpawn(ServerLevelAccessor level, DifficultyInstance difficulty, EntitySpawnReason reason,
			@Nullable SpawnGroupData data) {
		SpawnGroupData out = super.finalizeSpawn(level, difficulty, reason, data);
		// The spawn egg makes a Blue Lantern villager.
		setCorps(reason == EntitySpawnReason.SPAWN_ITEM_USE ? Corps.BLUE : corps());
		return out;
	}

	// ---- every tick -----------------------------------------------------------------------------

	@Override
	protected void customServerAiStep(ServerLevel level) {
		if (home == null) home = blockPosition();
		if (formationTicks > 0 && --formationTicks == 0) {
			// Its crew stopped giving it places (done, or the leader's gone): come down.
			goHome();
		}
		boolean blue = corps() == Corps.BLUE;
		if (blue) calm();
		if (flying()) {
			flyStep(level);
		} else {
			super.customServerAiStep(level);
			if (blue) {
				calm();
				// Facing a monster it holds its ground instead of wandering off.
				if (combat.fighting()) {
					getBrain().eraseMemory(net.minecraft.world.entity.ai.memory.MemoryModuleType.WALK_TARGET);
					getNavigation().stop();
				}
			}
			// Fell (off the island, off a cliff): catch itself on its ring and fly back up.
			if (fallDistance > 3 && getDeltaMovement().y < -0.3) flyTo(safeSpot(), true);
		}
		Corps corps = corps();
		if (getMainHandItem().isEmpty() && !isTrading()) setItemSlot(EquipmentSlot.MAINHAND, corps.ring());
		if (tickCount % 12 == 0) {
			level.sendParticles(ModParticles.of(ModParticles.MOTE, corps), getX(), getY() + 1.1, getZ(), 1, 0.3, 0.5, 0.3, 0.01);
		}
		if (corps == Corps.BLUE) combat.tick(level);
		else defend(level, corps);
		if (founder < 0 && tickCount > 20) decide(level);
		if (founder == 1) work(level, corps);
	}

	/**
	 * Blue Lantern villagers are confident: monsters and being hit don't send them running (no
	 * panic), they turn and fight with their ring (see BlueCombat).
	 */
	private void calm() {
		var brain = getBrain();
		brain.eraseMemory(net.minecraft.world.entity.ai.memory.MemoryModuleType.HURT_BY);
		brain.eraseMemory(net.minecraft.world.entity.ai.memory.MemoryModuleType.HURT_BY_ENTITY);
		brain.eraseMemory(net.minecraft.world.entity.ai.memory.MemoryModuleType.NEAREST_HOSTILE);
		if (brain.isActive(net.minecraft.world.entity.schedule.Activity.PANIC)) {
			brain.eraseMemory(net.minecraft.world.entity.ai.memory.MemoryModuleType.WALK_TARGET);
			brain.useDefaultActivity();
		}
	}

	/** The first corps villager of a colour in an area founds its village; the rest live in it. */
	private void decide(ServerLevel level) {
		AABB box = getBoundingBox().inflate(64);
		Corps corps = corps();
		boolean taken = !level.getEntitiesOfClass(CorpsVillager.class, box, v -> v != this && v.founder == 1 && v.corps() == corps).isEmpty();
		founder = taken ? 0 : 1;
	}

	/** Shoots monsters and Red raiders that come near. */
	private void defend(ServerLevel level, Corps corps) {
		if (--shotCooldown > 0) return;
		shotCooldown = 10;
		LivingEntity target = null;
		double best = 20 * 20;
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, getBoundingBox().inflate(20),
				ConstructAlly::isBadMob)) {
			double d = distanceToSqr(e);
			if (d < best && hasLineOfSight(e)) {
				best = d;
				target = e;
			}
		}
		if (target == null) return;
		shotCooldown = 30;
		lookAt(target, 30f, 30f);
		CorpsShots.shoot(level, this, target, corps, 6);
	}

	// ---- building the village -------------------------------------------------------------------

	private void work(ServerLevel level, Corps corps) {
		if (stage == GROUND || stage == SKY) golems(level, corps);
		if (corps == Corps.BLUE) {
			// The Blue Lantern's founder plans; its crew of three builds (see BlueCrew).
			BlueCrew c = crew();
			c.tick(level);
			if (c.busy()) return;
		} else if (SkyBuilds.running(job)) {
			if (flying() || stage == RISING) hoverOver(job.current());
			return;
		}
		job = null;
		switch (stage) {
			case GROUND -> {
				if (--buildTimer > 0) return;
				buildTimer = RingTuning.CORPS_BUILD.ticks();
				if (houses < GROUND_HOUSES) {
					buildGroundHouse(level, corps);
				} else {
					stage = RISING;
					BlockPos sky = SkyBuilds.skySpot(level, home, ISLAND_RADIUS, 14);
					island = sky.atY(Math.min(Math.max(home.getY() + ISLAND_HEIGHT, sky.getY()), level.getMaxY() - 24));
					announce(level, Component.translatable("message.lanternring.corps_rising", corps.ring().getHoverName()));
				}
			}
			case RISING -> rise(level, corps);
			case SKY -> {
				// The Blue Lantern goes on to raise its sky city over the village, a piece at a time.
				if (corps == Corps.BLUE && !cityComplete && --buildTimer <= 0) {
					buildTimer = RingTuning.CORPS_BUILD.ticks();
					crew().order(cityOrder());
				}
				if (rivalTimer > 0 && --rivalTimer == 0) {
					rivalTimer = -2;
					SkyRaider.rivalsArrive(level, island, corps);
				}
			}
			default -> {
			}
		}
	}

	// ---- the Blue Lantern's building crew (see BlueCrew) -----------------------------------------

	/** The crew this founder leads (made on first use). Other features queue builds on it with {@link BlueCrew#order}. */
	public BlueCrew crew() {
		if (ownCrew == null) ownCrew = new BlueCrew(this);
		return ownCrew;
	}

	/** The crew it's a member of, while that crew's leader is alive. */
	@Nullable
	public BlueCrew crewOf() {
		return memberOf != null && memberOf.leader().isAlive() ? memberOf : null;
	}

	/** Whether it founded (and leads) its village. */
	public boolean leads() {
		return founder == 1;
	}

	public BlockPos homePos() {
		return home != null ? home : blockPosition();
	}

	void joinCrew(BlueCrew crew) {
		memberOf = crew;
	}

	/** A villager called to live in someone else's village. */
	void settle(BlockPos home) {
		founder = 0;
		this.home = home;
	}

	/** A build: Blue founders queue it for their crew (returns null), others start it themselves. */
	private SkyBuilds.@Nullable Job startJob(ServerLevel level, Map<BlockPos, BlockState> blocks, int ticks, Corps corps, boolean force, CorpsVillager builder) {
		if (corps == Corps.BLUE) {
			crew().order(BuildOrder.fixed("build", blocks, ticks, force));
			return null;
		}
		return SkyBuilds.start(level, blocks, ticks, corps, force, builder);
	}

	/**
	 * Crew order: fly to (and hover at) {@code at} for the next second, facing {@code look}, with arms
	 * out pouring light if {@code building}. Call it every tick to keep it there.
	 */
	public void holdSlot(Vec3 at, Vec3 look, boolean building) {
		formationTicks = 20;
		formationLook = look;
		entityData.set(BUILDING, building);
		if (!flying() || flyTo == null || flyTo.distanceToSqr(at) > 0.25) flyTo(at, false);
	}

	/** Crew order: fly to {@code at} (re-aimed only when it moves a block or more). Call it every tick. */
	public void follow(Vec3 at) {
		formationTicks = 20;
		formationLook = null;
		entityData.set(BUILDING, false);
		if (!flying() || flyTo == null || flyTo.distanceToSqr(at) > 1) flyTo(at, false);
	}

	/** Leaves whatever it was doing for its crew and flies home to land. */
	public void goHome() {
		formationTicks = 0;
		formationLook = null;
		entityData.set(BUILDING, false);
		flyTo(safeSpot(), true);
	}

	private void golems(ServerLevel level, Corps corps) {
		if (--golemTimer > 0) return;
		golemTimer = RingTuning.CORPS_GOLEM.ticks();
		BlockPos guard = stage == SKY && island != null ? island.above() : home;
		int want = stage == SKY ? 1 : 2;
		int have = level.getEntitiesOfClass(CorpsGolem.class, new AABB(guard).inflate(32), g -> g.isAlive() && g.corps() == corps).size();
		if (have >= want) return;
		BlockPos at = guard;
		if (stage != SKY) {
			double a = random.nextDouble() * Math.PI * 2;
			int x = guard.getX() + (int) (Math.cos(a) * 4), z = guard.getZ() + (int) (Math.sin(a) * 4);
			at = new BlockPos(x, level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z), z);
		} else {
			at = island.offset(random.nextBoolean() ? 3 : -3, 1, 0);
		}
		lookAt(net.minecraft.commands.arguments.EntityAnchorArgument.Anchor.EYES, Vec3.atCenterOf(at));
		CorpsGolem.forge(level, at, corps, guard);
	}

	private void buildGroundHouse(ServerLevel level, Corps corps) {
		if (corps == Corps.BLUE) {
			crew().order(houseOrder());
			houses++;
			return;
		}
		Blueprint b = SkyBuilds.house(level, random, 13);
		if (b == null) {
			houses++;
			return;
		}
		Rotation rot = Rotation.values()[random.nextInt(4)];
		BlockPos corner = SkyBuilds.groundSpot(level, home, SkyBuilds.footW(b, rot), SkyBuilds.footD(b, rot), random);
		if (corner == null) {
			// No room left round here: count it and move on, so it still gets to the sky.
			houses++;
			return;
		}
		// Turn it to face the village.
		Vec3 mid = new Vec3(corner.getX() + SkyBuilds.footW(b, rot) / 2.0, 0, corner.getZ() + SkyBuilds.footD(b, rot) / 2.0);
		Direction toward = Direction.getApproximateNearest(home.getX() - mid.x, 0, home.getZ() - mid.z);
		rot = SkyBuilds.facing(toward);
		corner = SkyBuilds.groundSpot(level, home, SkyBuilds.footW(b, rot), SkyBuilds.footD(b, rot), random);
		if (corner == null) {
			houses++;
			return;
		}
		Map<BlockPos, BlockState> blocks = SkyBuilds.groundHouse(level, b, corner, rot);
		job = startJob(level, blocks, RingTuning.CORPS_BUILD_TIME.ticks(), corps, true, this);
		houses++;
		getNavigation().moveTo(corner.getX(), corner.getY() + 1, corner.getZ(), 0.6);
	}

	/**
	 * A Blue house: the blueprint and its site are picked when the crew gets to it (BlueSites scores
	 * the ground round the village), turned so its door faces the village centre.
	 */
	private BuildOrder houseOrder() {
		return new BuildOrder() {
			@Override
			public String name() {
				return "house";
			}

			@Override
			public BuildOrder.@Nullable Site plan(ServerLevel level, BlueCrew crew) {
				Blueprint b = SkyBuilds.house(level, random, 13);
				if (b == null) return null;
				BlockPos h = homePos();
				// Try each way round; keep the site whose door would face home.
				for (int attempt = 0; attempt < 3; attempt++) {
					Rotation rot = Rotation.values()[random.nextInt(4)];
					BlockPos corner = BlueSites.ground(level, h, SkyBuilds.footW(b, rot), SkyBuilds.footD(b, rot), random);
					if (corner == null) continue;
					Vec3 mid = new Vec3(corner.getX() + SkyBuilds.footW(b, rot) / 2.0, 0, corner.getZ() + SkyBuilds.footD(b, rot) / 2.0);
					Rotation facing = SkyBuilds.facing(Direction.getApproximateNearest(h.getX() - mid.x, 0, h.getZ() - mid.z));
					if (SkyBuilds.footW(b, facing) != SkyBuilds.footW(b, rot)) {
						// Turned it no longer fits the same patch: find one for it that way round.
						corner = BlueSites.ground(level, h, SkyBuilds.footW(b, facing), SkyBuilds.footD(b, facing), random);
						if (corner == null) continue;
					}
					return new BuildOrder.Site(SkyBuilds.groundHouse(level, b, corner, facing), RingTuning.CORPS_BUILD_TIME.ticks(), true);
				}
				return null;
			}
		};
	}

	/** The next piece of the sky city (see city.BlueCity): the crew forms its U round it and the city's own job builds it. */
	private BuildOrder cityOrder() {
		return new BuildOrder() {
			private com.sparky.lanternring.city.CityBuilds.@Nullable Job job;

			@Override
			public String name() {
				return "sky city";
			}

			@Override
			public BuildOrder.@Nullable Site plan(ServerLevel level, BlueCrew crew) {
				return null;
			}

			@Override
			public @Nullable AABB area(ServerLevel level, BlueCrew crew) {
				var city = com.sparky.lanternring.city.BlueCity.cityFor(level, homePos());
				job = com.sparky.lanternring.city.BlueCity.buildNext(level, city, List.of());
				if (job == null) {
					cityComplete = true;
					return null;
				}
				Vec3 f = job.focus();
				return new AABB(f.x - 7, job.current().getY(), f.z - 7, f.x + 7, f.y + 1, f.z + 7);
			}

			@Override
			public BuildOrder.@Nullable Started start(ServerLevel level, BlueCrew crew, List<CorpsVillager> builders) {
				var j = job;
				if (j == null) return null;
				j.attach(builders);
				return new BuildOrder.Started() {
					@Override
					public Vec3 focus() {
						return j.focus();
					}

					@Override
					public BlockPos current() {
						return j.current();
					}

					@Override
					public boolean running() {
						return com.sparky.lanternring.city.CityBuilds.running(j);
					}
				};
			}
		};
	}

	private void rise(ServerLevel level, Corps corps) {
		if (island == null) return;
		if (!islandBuilt && corps == Corps.BLUE) {
			// The crew flies up there together (see BlueCrew).
			startJob(level, SkyBuilds.island(island, ISLAND_RADIUS, corps, random, true), RingTuning.CORPS_BUILD_TIME.ticks() * 2, corps, false, this);
			islandBuilt = true;
			return;
		}
		if (!islandBuilt) {
			Vec3 over = Vec3.atBottomCenterOf(island).add(0, 3, 0);
			if (distanceToSqr(over) > 3 * 3) {
				if (!flying() || flyTo == null || flyTo.distanceToSqr(over) > 1) flyTo(over, false);
				return;
			}
			job = startJob(level, SkyBuilds.island(island, ISLAND_RADIUS, corps, random, true),
					RingTuning.CORPS_BUILD_TIME.ticks() * 2, corps, false, this);
			islandBuilt = true;
			return;
		}
		if (islandHouses < ISLAND_HOUSES) {
			// One house in each quarter of the island, its door toward the lantern in the middle.
			int q = islandHouses++;
			int sx = (q & 1) == 0 ? -1 : 1, sz = (q & 2) == 0 ? -1 : 1;
			Blueprint b = SkyBuilds.house(level, random, 8);
			if (b == null) return;
			Direction toward = Math.abs(sx) >= Math.abs(sz) && random.nextBoolean()
					? (sx < 0 ? Direction.EAST : Direction.WEST) : (sz < 0 ? Direction.SOUTH : Direction.NORTH);
			Rotation rot = SkyBuilds.facing(toward);
			int w = SkyBuilds.footW(b, rot), d = SkyBuilds.footD(b, rot);
			int cx = island.getX() + sx * 6, cz = island.getZ() + sz * 6;
			int x = cx - w / 2, z = cz - d / 2;
			job = startJob(level, SkyBuilds.place(b, x, island.getY(), z, rot), RingTuning.CORPS_BUILD_TIME.ticks(), corps, true, this);
			return;
		}
		// Done: land in the middle, and the village fills up.
		stage = SKY;
		home = island.above();
		flyTo(Vec3.atBottomCenterOf(island).add(1.5, 1, 1.5), true);
		for (int i = 0; i < 2; i++) {
			CorpsVillager v = CorpsMobs.CORPS_VILLAGER.create(level, EntitySpawnReason.MOB_SUMMONED);
			if (v == null) continue;
			v.setCorps(corps);
			v.joinIsland(island);
			v.snapTo(island.getX() + 0.5 + (i == 0 ? -3 : 3), island.getY() + 1, island.getZ() + 0.5, random.nextFloat() * 360f, 0f);
			level.addFreshEntity(v);
			CorpsShots.summon(level, v.position(), v.getBbHeight(), 1f, corps);
		}
		golemTimer = 1;
		if (corps != Corps.RED) rivalTimer = Math.max(1, RingTuning.CORPS_RIVAL.ticks());
		announce(level, Component.translatable("message.lanternring.corps_floating", corps.ring().getHoverName()));
	}

	private void announce(ServerLevel level, Component text) {
		for (ServerPlayer p : level.players()) {
			if (p.distanceToSqr(this) < 128 * 128) p.sendSystemMessage(text.copy().withStyle(ChatFormatting.ITALIC));
		}
		level.playSound(null, blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.NEUTRAL, 1.5f, 1f);
	}

	// ---- flying ---------------------------------------------------------------------------------

	private Vec3 safeSpot() {
		if (island != null && islandBuilt && stage != GROUND) return Vec3.atBottomCenterOf(island).add(2.5, 1, 0.5);
		BlockPos h = home == null ? blockPosition() : home;
		int y = level().getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, h.getX(), h.getZ());
		return new Vec3(h.getX() + 0.5, y, h.getZ() + 0.5);
	}

	/** Flies to {@code to} over whatever's in the way (see SkyPath), landing there if {@code land}. */
	public void flyTo(Vec3 to, boolean land) {
		flyTo = to;
		path = SkyPath.plan(level(), position(), to);
		landAtEnd = land;
		entityData.set(FLYING, true);
		setNoGravity(true);
		getNavigation().stop();
	}

	private void hoverOver(BlockPos at) {
		Vec3 over = new Vec3(at.getX() + 0.5, Math.max(at.getY() + 4, island != null && stage == RISING ? island.getY() + 4 : 0), at.getZ() + 0.5);
		Vec3 here = flyTo == null ? position() : flyTo;
		if (here.distanceToSqr(over) > 36 || !flying()) flyTo(over.add(3, 0, 0), false);
	}

	/** Turns body and head toward a point (hovering in the formation). */
	private void face(Vec3 at) {
		Vec3 d = at.subtract(getEyePosition());
		float yaw = (float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90f;
		setYRot(Mth.approachDegrees(getYRot(), yaw, 12f));
		yBodyRot = getYRot();
		yHeadRot = getYRot();
		setXRot((float) -(Mth.atan2(d.y, Math.sqrt(d.x * d.x + d.z * d.z)) * Mth.RAD_TO_DEG));
	}

	private void land() {
		entityData.set(FLYING, false);
		setNoGravity(false);
		flyTo = null;
		resetFallDistance();
	}

	private void flyStep(ServerLevel level) {
		if (flyTo == null) {
			land();
			return;
		}
		// Waypoints first, then the destination itself.
		while (path.size() > 1 && path.peek().distanceToSqr(position()) < 1.5 * 1.5) path.poll();
		Vec3 aim = path.size() > 1 ? path.peek() : flyTo;
		Vec3 to = aim.subtract(position());
		double dist = to.length();
		if (aim == flyTo && dist < 0.6) {
			if (landAtEnd) land();
			setDeltaMovement(getDeltaMovement().scale(0.5));
			if (formationLook != null) face(formationLook);
			return;
		}
		Vec3 want = to.scale(Math.min(0.45, Math.max(aim == flyTo ? 0 : 0.3, dist * 0.1)) / dist);
		// Ran into something the route missed: climb over it.
		if (horizontalCollision) want = want.add(0, 0.25, 0);
		setDeltaMovement(getDeltaMovement().lerp(want, 0.15));
		float yaw = (float) (Mth.atan2(to.z, to.x) * Mth.RAD_TO_DEG) - 90f;
		setYRot(Mth.approachDegrees(getYRot(), yaw, 10f));
		yBodyRot = getYRot();
		yHeadRot = getYRot();
		if (tickCount % 2 == 0) {
			level.sendParticles(ModParticles.of(ModParticles.MOTE, corps()), getX(), getY() - 0.1, getZ(), 2, 0.15, 0.1, 0.15, 0.01);
		}
		resetFallDistance();
	}

	@Override
	public void travel(Vec3 input) {
		if (flying()) {
			move(MoverType.SELF, getDeltaMovement());
		} else {
			super.travel(input);
		}
	}

	@Override
	public boolean causeFallDamage(double fallDistance, float multiplier, DamageSource source) {
		return false;
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		// Its own corps' light doesn't hurt it.
		if (source.getEntity() instanceof CorpsGolem || source.getEntity() instanceof CorpsVillager || source.is(DamageTypes.IN_WALL)) return false;
		return super.hurtServer(level, source, amount);
	}

	// ---- saving ---------------------------------------------------------------------------------

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		output.putInt("Corps", entityData.get(CORPS));
		output.putInt("CorpsStage", stage);
		output.putInt("CorpsFounder", founder);
		output.putInt("CorpsHouses", houses);
		output.putInt("CorpsIslandHouses", islandHouses);
		output.putBoolean("CorpsIslandBuilt", islandBuilt);
		output.putInt("CorpsRival", rivalTimer);
		output.putBoolean("CorpsSuited", suited());
		if (ownCrew != null) output.store("CorpsCrew", net.minecraft.core.UUIDUtil.CODEC.listOf(), ownCrew.memberIds());
		if (home != null) output.store("CorpsHome", BlockPos.CODEC, home);
		if (island != null) output.store("CorpsIsland", BlockPos.CODEC, island);
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		entityData.set(CORPS, input.getIntOr("Corps", 0));
		stage = input.getIntOr("CorpsStage", GROUND);
		founder = input.getIntOr("CorpsFounder", -1);
		houses = input.getIntOr("CorpsHouses", 0);
		islandHouses = input.getIntOr("CorpsIslandHouses", 0);
		islandBuilt = input.getBooleanOr("CorpsIslandBuilt", false);
		rivalTimer = input.getIntOr("CorpsRival", -1);
		entityData.set(SUITED, input.getBooleanOr("CorpsSuited", false) || corps() == Corps.BLUE);
		input.read("CorpsCrew", net.minecraft.core.UUIDUtil.CODEC.listOf()).ifPresent(ids -> crew().load(ids));
		home = input.read("CorpsHome", BlockPos.CODEC).orElse(null);
		island = input.read("CorpsIsland", BlockPos.CODEC).orElse(null);
		// A step that was half built when the game closed is built again (jobs aren't saved).
		if (stage == RISING && islandHouses == 0) islandBuilt = false;
	}

	static List<CorpsVillager> near(ServerLevel level, BlockPos at, double r) {
		return level.getEntitiesOfClass(CorpsVillager.class, new AABB(at).inflate(r), LivingEntity::isAlive);
	}
}
