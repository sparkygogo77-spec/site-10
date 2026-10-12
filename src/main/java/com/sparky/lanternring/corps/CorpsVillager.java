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
	/** How many Blue Lantern villagers build together, in a wide U round the construct. */
	static final int CREW = 3;

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
	private boolean islandBuilt;
	private int buildTimer = 100, golemTimer = 60, shotCooldown, rivalTimer = -1;
	private SkyBuilds.@Nullable Job job;
	/** Where it's flying to, and whether it lands there. */
	@Nullable
	private Vec3 flyTo;
	private boolean landAtEnd;
	/** The founder's building crew (Blue Lantern): not saved, gathered again when it next builds. */
	private final List<CorpsVillager> crew = new ArrayList<>();
	/** Crew: ticks left holding its place in the formation, and what it faces there. */
	private int formationTicks;
	@Nullable
	private Vec3 formationLook;
	/** Client: eased pose blends for the renderer (see BlueVillagerRenderer). */
	private float fly, oFly, build, oBuild, fwd, oFwd, side, oSide;

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
	}

	public boolean flying() {
		return entityData.get(FLYING);
	}

	public boolean building() {
		return entityData.get(BUILDING);
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
		setCorps(corps());
		return out;
	}

	// ---- every tick -----------------------------------------------------------------------------

	@Override
	protected void customServerAiStep(ServerLevel level) {
		if (home == null) home = blockPosition();
		if (formationTicks > 0 && --formationTicks == 0) {
			// The build it was helping with is done: come down.
			entityData.set(BUILDING, false);
			formationLook = null;
			flyTo(safeSpot(), true);
		}
		if (flying()) {
			flyStep(level);
		} else {
			super.customServerAiStep(level);
			// Fell (off the island, off a cliff): catch itself on its ring and fly back up.
			if (fallDistance > 3 && getDeltaMovement().y < -0.3) flyTo(safeSpot(), true);
		}
		Corps corps = corps();
		if (getMainHandItem().isEmpty() && !isTrading()) setItemSlot(EquipmentSlot.MAINHAND, corps.ring());
		if (tickCount % 12 == 0) {
			level.sendParticles(ModParticles.of(ModParticles.MOTE, corps), getX(), getY() + 1.1, getZ(), 1, 0.3, 0.5, 0.3, 0.01);
		}
		defend(level, corps);
		if (founder < 0 && tickCount > 20) decide(level);
		if (founder == 1) work(level, corps);
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
		if (SkyBuilds.running(job)) {
			if (corps == Corps.BLUE) formation(level, job);
			else if (flying() || stage == RISING) hoverOver(job.current());
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
				if (rivalTimer > 0 && --rivalTimer == 0) {
					rivalTimer = -2;
					SkyRaider.rivalsArrive(level, island, corps);
				}
			}
			default -> {
			}
		}
	}

	// ---- the Blue Lantern's building crew ----------------------------------------------------------

	/** Starts a build; a Blue founder first gathers two more Blue villagers (calling them in if needed). */
	private SkyBuilds.Job startJob(ServerLevel level, java.util.Map<BlockPos, BlockState> blocks, int ticks, Corps corps, boolean force, CorpsVillager builder) {
		SkyBuilds.Job started = SkyBuilds.start(level, blocks, ticks, corps, force, builder);
		if (corps == Corps.BLUE) {
			gatherCrew(level, corps);
			started.crew(crew);
		}
		return started;
	}

	private void gatherCrew(ServerLevel level, Corps corps) {
		crew.removeIf(v -> !v.isAlive());
		for (CorpsVillager v : near(level, blockPosition(), 48)) {
			if (crew.size() >= CREW - 1) break;
			if (v != this && v.corps() == corps && v.founder != 1 && !v.isBaby() && !crew.contains(v)) crew.add(v);
		}
		while (crew.size() < CREW - 1) {
			CorpsVillager v = CorpsMobs.CORPS_VILLAGER.create(level, EntitySpawnReason.MOB_SUMMONED);
			if (v == null) return;
			v.setCorps(corps);
			v.founder = 0;
			v.home = home;
			double a = random.nextDouble() * Math.PI * 2;
			v.snapTo(getX() + Math.cos(a) * 2, getY() + 0.5, getZ() + Math.sin(a) * 2, random.nextFloat() * 360f, 0f);
			level.addFreshEntity(v);
			CorpsShots.summon(level, v.position(), v.getBbHeight(), 1f, corps);
			crew.add(v);
		}
	}

	/**
	 * The crew of three hover in a wide U round the build, rising with it as it goes up: the founder
	 * at the bottom of the U (on the village's side) and one at each arm, all facing the construct
	 * with their arms out, pouring light into it.
	 */
	private void formation(ServerLevel level, SkyBuilds.Job job) {
		Vec3 c = job.center;
		double r = Math.max(6, job.radius + 4);
		double y = Math.max(job.current().getY() + 3.5, c.y + 2);
		Vec3 toHome = home == null ? Vec3.ZERO : new Vec3(home.getX() + 0.5 - c.x, 0, home.getZ() + 0.5 - c.z);
		Vec3 back = toHome.lengthSqr() < 1 ? new Vec3(0, 0, 1) : toHome.normalize();
		Vec3 across = new Vec3(-back.z, 0, back.x);
		Vec3 look = new Vec3(c.x, y - 1.5, c.z);
		holdSlot(new Vec3(c.x, y, c.z).add(back.scale(r)), look);
		for (int i = 0; i < crew.size(); i++) {
			CorpsVillager v = crew.get(i);
			if (!v.isAlive()) continue;
			// The arms of the U reach a little past the middle, and stand a block higher.
			Vec3 arm = across.scale(i == 0 ? r : -r).subtract(back.scale(r * 0.45));
			v.holdSlot(new Vec3(c.x, y + 1, c.z).add(arm), look);
		}
	}

	/** Flies to (and hovers at) its place in the formation for the next few ticks, facing {@code look}. */
	void holdSlot(Vec3 at, Vec3 look) {
		formationTicks = 20;
		formationLook = look;
		entityData.set(BUILDING, true);
		if (!flying() || flyTo == null || flyTo.distanceToSqr(at) > 0.25) flyTo(at, false);
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

	private void rise(ServerLevel level, Corps corps) {
		if (island == null) return;
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

	public void flyTo(Vec3 to, boolean land) {
		flyTo = to;
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
		Vec3 to = flyTo.subtract(position());
		double dist = to.length();
		if (dist < 0.6) {
			if (landAtEnd) land();
			setDeltaMovement(getDeltaMovement().scale(0.5));
			if (formationLook != null) face(formationLook);
			return;
		}
		Vec3 want = to.scale(Math.min(0.45, dist * 0.1) / dist);
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
		home = input.read("CorpsHome", BlockPos.CODEC).orElse(null);
		island = input.read("CorpsIsland", BlockPos.CODEC).orElse(null);
		// A step that was half built when the game closed is built again (jobs aren't saved).
		if (stage == RISING && islandHouses == 0) islandBuilt = false;
	}

	static List<CorpsVillager> near(ServerLevel level, BlockPos at, double r) {
		return level.getEntitiesOfClass(CorpsVillager.class, new AABB(at).inflate(r), LivingEntity::isAlive);
	}
}
