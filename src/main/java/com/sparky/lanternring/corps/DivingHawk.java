package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.ally.ConstructAlly;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.PathfinderMob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * An armored diving hawk of the Blue Lantern city: a big raptor with a blue armour lance over its
 * beak. Hawks live on their city's flier highway ({@link FlierHighway}): they rest on the pads,
 * fly the lanes hoop to hoop between districts, and when a monster or a Red raider comes near the
 * city they climb above it, fold their wings and stoop onto it, stabbing with the lance, then pull
 * up and climb back to the lanes.
 *
 * <p>Anyone can ride one (use it with an empty hand): look where to fly, hold forward to speed up,
 * jump to climb, sneak to get off. Look steeply down at speed and it stoops: much faster, and
 * whatever the lance hits is stabbed. A riderless hawk flies home to its pad.
 */
public class DivingHawk extends PathfinderMob {
	/** Whether it is sitting (on a pad, a perch or the ground), for the folded-wing pose. */
	private static final EntityDataAccessor<Boolean> PERCHED = SynchedEntityData.defineId(DivingHawk.class, EntityDataSerializers.BOOLEAN);

	private enum Mode { PERCH, ROUTE, HUNT, STOOP, CLIMB }

	/** How far a sitting hawk leans back: raptors perch upright. */
	public static final float PERCH_PITCH = -30f;
	/** Stoop damage at full speed, and the speeds it flies at (blocks a tick). */
	static final float STAB_DAMAGE = 14f;
	static final double CRUISE = 0.75, LANE_SPEED = 0.6, STOOP_SPEED = 2.1, RIDE_SPEED = 1.05;

	/** Its city's anchor (null for a wild hawk from an egg) and home pad. */
	@Nullable
	private BlockPos anchor;
	private int homePad = -1;
	@Nullable
	private Vec3 wildHome;
	private Mode mode = Mode.PERCH;
	private int restTimer = 100, modeTicks, stabCooldown;
	/** The way it is flying: points still to pass through, and the pad it is bound for. */
	private final List<Vec3> route = new ArrayList<>();
	private int bound = -1;
	@Nullable
	private LivingEntity prey;
	@Nullable
	private Vec3 lastServerPos;

	// Client side: what the animation reads (see DivingHawkModel).
	public float flapPhase, oFlapPhase, flap, oFlap, stoop, oStoop, perch, oPerch, pitch, oPitch, bank, oBank;
	/** Client side, for tests: {flap, stoop, perch, pitch} to hold instead of what it's doing. */
	public float @Nullable [] previewPose;

	public DivingHawk(EntityType<? extends DivingHawk> type, Level level) {
		super(type, level);
		setPersistenceRequired();
		xpReward = 0;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Mob.createMobAttributes()
				.add(Attributes.MAX_HEALTH, 40)
				.add(Attributes.ARMOR, 8)
				.add(Attributes.MOVEMENT_SPEED, 0.3)
				.add(Attributes.FLYING_SPEED, 0.8)
				.add(Attributes.FOLLOW_RANGE, 40)
				.add(Attributes.ATTACK_DAMAGE, STAB_DAMAGE);
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(PERCHED, true);
	}

	public boolean perched() {
		return entityData.get(PERCHED);
	}

	/** A hawk hatched on a highway pad. */
	void settle(BlockPos anchor, int pad) {
		this.anchor = anchor.immutable();
		this.homePad = pad;
		this.mode = Mode.PERCH;
		this.restTimer = 60 + random.nextInt(200);
	}

	private FlierHighway.@Nullable Network network(ServerLevel level) {
		return anchor == null ? null : FlierHighway.network(level, anchor);
	}

	// ---- riding ---------------------------------------------------------------------------------

	@Override
	public InteractionResult mobInteract(Player player, InteractionHand hand) {
		if (player.isSecondaryUseActive() || isVehicle() || !player.getItemInHand(hand).isEmpty()) return super.mobInteract(player, hand);
		if (!level().isClientSide()) {
			player.startRiding(this);
			takeOff();
			playSound(SoundEvents.PARROT_FLY, 1f, 0.6f);
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public @Nullable LivingEntity getControllingPassenger() {
		return getFirstPassenger() instanceof Player p ? p : null;
	}

	@Override
	protected void tickRidden(Player rider, Vec3 input) {
		super.tickRidden(rider, input);
		setYRot(rider.getYRot());
		yRotO = getYRot();
		setXRot(rider.getXRot() * 0.5f);
		yBodyRot = getYRot();
		yHeadRot = getYRot();
	}

	@Override
	protected Vec3 getRiddenInput(Player rider, Vec3 input) {
		return new Vec3(rider.xxa, rider.isJumping() ? 1 : 0, rider.zza);
	}

	@Override
	protected float getRiddenSpeed(Player rider) {
		return (float) RIDE_SPEED;
	}

	/**
	 * Ridden flight (runs where the rider is, like a horse): fly where the rider looks, faster when
	 * holding forward, a slow forward glide with a gentle sink when not, jump to climb, and a stoop
	 * when looking steeply down at speed.
	 */
	private void rideTravel(Player rider, Vec3 input) {
		Vec3 look = rider.getLookAngle();
		Vec3 v = getDeltaMovement();
		double speed = v.length();
		boolean steep = rider.getXRot() > 35f;
		Vec3 want;
		double ease = 0.12;
		if (input.z > 0) {
			want = look.scale(steep ? STOOP_SPEED : RIDE_SPEED);
			if (steep) ease = 0.06; // a stoop builds up speed rather than snapping to it
		} else if (input.z < 0) {
			want = Vec3.ZERO; // brake into a hover
		} else {
			want = look.multiply(1, 0, 1).normalize().scale(Math.max(0.2, Math.min(speed, 0.4))).add(0, -0.03, 0);
		}
		if (input.y > 0) want = want.add(0, 0.55, 0);
		// Sidestep with strafe keys, banking round.
		if (input.x != 0) want = want.add(new Vec3(look.z, 0, -look.x).normalize().scale(input.x * 0.35));
		v = v.lerp(want, ease);
		setDeltaMovement(v);
		move(MoverType.SELF, v);
		if (onGround() && input.y <= 0 && v.horizontalDistance() < 0.15) setDeltaMovement(Vec3.ZERO);
	}

	@Override
	public void travel(Vec3 input) {
		if (getControllingPassenger() instanceof Player rider) {
			setNoGravity(true);
			rideTravel(rider, input);
			return;
		}
		if (!perched()) {
			move(MoverType.SELF, getDeltaMovement());
			return;
		}
		super.travel(input);
	}

	@Override
	protected void removePassenger(Entity passenger) {
		super.removePassenger(passenger);
		// Left alone in the air: go home.
		if (!level().isClientSide() && passenger instanceof LivingEntity rider) {
			rider.resetFallDistance();
			mode = Mode.CLIMB;
			modeTicks = 0;
		}
	}

	// ---- the wild hawk --------------------------------------------------------------------------

	private void takeOff() {
		entityData.set(PERCHED, false);
		setNoGravity(true);
		route.clear();
		mode = Mode.ROUTE;
		modeTicks = 0;
		setDeltaMovement(getDeltaMovement().add(0, 0.35, 0));
	}

	private void land() {
		entityData.set(PERCHED, true);
		mode = Mode.PERCH;
		modeTicks = 0;
		restTimer = 200 + random.nextInt(400);
		route.clear();
		setDeltaMovement(Vec3.ZERO);
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		super.customServerAiStep(level);
		if (wildHome == null) wildHome = position();
		modeTicks++;
		if (stabCooldown > 0) stabCooldown--;
		if (getControllingPassenger() instanceof Player rider) {
			entityData.set(PERCHED, false);
			riderStoop(level, rider);
			lastServerPos = position();
			return;
		}
		lastServerPos = position();
		if (mode != Mode.HUNT && mode != Mode.STOOP && tickCount % 10 == 0) {
			LivingEntity found = findPrey(level);
			if (found != null) {
				prey = found;
				if (perched()) takeOff();
				mode = Mode.HUNT;
				modeTicks = 0;
				playSound(SoundEvents.PARROT_IMITATE_PHANTOM, 1.2f, 0.5f);
			}
		}
		switch (mode) {
			case PERCH -> perchStep(level);
			case ROUTE -> routeStep(level);
			case HUNT -> huntStep(level);
			case STOOP -> stoopStep(level);
			case CLIMB -> climbStep(level);
		}
	}

	/** A monster or Red raider near its city (or near itself, for a wild hawk), in sight. */
	@Nullable
	private LivingEntity findPrey(ServerLevel level) {
		Vec3 centre = anchor != null ? Vec3.atCenterOf(anchor) : wildHome;
		double range = anchor != null ? FlierHighway.PORT_RADIUS + 24 : 20;
		LivingEntity best = null;
		double bestD = Double.MAX_VALUE;
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(BlockPos.containing(centre)).inflate(range),
				e -> (ConstructAlly.isBadMob(e) || e instanceof SkyRaider) && e.isAlive())) {
			double d = e.distanceToSqr(this);
			if (d < bestD && d < 48 * 48) {
				bestD = d;
				best = e;
			}
		}
		return best;
	}

	private void perchStep(ServerLevel level) {
		FlierHighway.Network hw = network(level);
		if (hw != null && homePad >= 0 && homePad < hw.pads.size()) {
			Vec3 seat = Vec3.atBottomCenterOf(hw.pads.get(homePad).perch().above());
			if (distanceToSqr(seat) > 4) {
				takeOff();
				return;
			}
			setNoGravity(true);
			setPos(seat.x, seat.y, seat.z);
			setDeltaMovement(Vec3.ZERO);
		} else {
			setNoGravity(false);
			entityData.set(PERCHED, onGround());
			if (!onGround()) return;
		}
		// Look about now and then, as raptors do.
		if (random.nextInt(60) == 0) setYRot(getYRot() + (random.nextFloat() - 0.5f) * 90f);
		yBodyRot = getYRot();
		if (--restTimer <= 0) takeOff();
	}

	/** Flies the highway to another district: a random pad, or home when it has flown a while. */
	private void routeStep(ServerLevel level) {
		FlierHighway.Network hw = network(level);
		if (hw == null) {
			// A wild hawk circles over where it was let go, then comes down.
			double a = tickCount * 0.04;
			fly(wildHome.add(Math.cos(a) * 10, 9 + Math.sin(tickCount * 0.05), Math.sin(a) * 10), CRUISE);
			if (modeTicks > 600) {
				mode = Mode.CLIMB;
				modeTicks = 0;
			}
			return;
		}
		if (route.isEmpty()) {
			int from = hw.nearestPad(position());
			// Back home after a while out: rest. Otherwise on to another district (home now and then).
			if (from == homePad && (bound == homePad && modeTicks > 300 || modeTicks > 2400)) {
				land();
				return;
			}
			int n = hw.pads.size();
			int to = modeTicks > 1600 || random.nextInt(3) == 0 ? homePad : random.nextInt(n);
			if (to == from && n > 1) to = (from + 1 + random.nextInt(n - 1)) % n;
			bound = to;
			route.addAll(hw.route(from, to));
		}
		Vec3 next = route.getFirst();
		double near = route.size() == 1 ? 0.8 : 2.5;
		if (position().distanceToSqr(next) < near * near) {
			route.removeFirst();
			if (route.isEmpty() && bound == homePad && modeTicks > 200) land();
			return;
		}
		fly(next, route.size() == 1 ? 0.35 : LANE_SPEED);
	}

	/** Gets above its prey, then folds and stoops. */
	private void huntStep(ServerLevel level) {
		if (prey == null || !prey.isAlive() || modeTicks > 400 || prey.distanceToSqr(this) > 56 * 56) {
			prey = null;
			mode = Mode.CLIMB;
			modeTicks = 0;
			return;
		}
		// Come at it from the side it's on, well above it, so the dive is steep.
		Vec3 off = position().subtract(prey.position()).multiply(1, 0, 1);
		off = off.lengthSqr() < 1 ? new Vec3(1, 0, 0) : off.normalize();
		Vec3 above = prey.position().add(off.scale(6)).add(0, 14, 0);
		fly(above, CRUISE * 1.4);
		if (position().distanceToSqr(above) < 9 || modeTicks > 160 && getY() > prey.getY() + 8) {
			mode = Mode.STOOP;
			modeTicks = 0;
			playSound(SoundEvents.PHANTOM_SWOOP, 1.5f, 0.8f);
		}
	}

	/** The stoop: straight down the line to the prey, speeding up all the way; the lance hits first. */
	private void stoopStep(ServerLevel level) {
		if (prey == null || !prey.isAlive() || modeTicks > 80) {
			mode = Mode.CLIMB;
			modeTicks = 0;
			return;
		}
		Vec3 aim = prey.position().add(0, prey.getBbHeight() * 0.6, 0);
		Vec3 to = aim.subtract(position());
		double speed = Math.min(STOOP_SPEED, 0.6 + modeTicks * 0.09);
		setDeltaMovement(getDeltaMovement().lerp(to.normalize().scale(speed), 0.35));
		face(position().add(getDeltaMovement()));
		if (tickCount % 2 == 0) {
			level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), getX(), getY() + 0.6, getZ(), 2, 0.2, 0.2, 0.2, 0.01);
		}
		if (stab(level, getDeltaMovement().length(), null) || to.length() < 1.2) {
			mode = Mode.CLIMB;
			modeTicks = 0;
		}
	}

	/** Pulls out of a stoop and climbs back up to the lanes (or home, when it has no city). */
	private void climbStep(ServerLevel level) {
		FlierHighway.Network hw = network(level);
		Vec3 back;
		if (hw != null) {
			back = Vec3.atCenterOf(hw.pads.get(hw.nearestPad(position())).perch()).add(0, 4, 0);
		} else {
			BlockPos ground = level.getHeightmapPos(net.minecraft.world.level.levelgen.Heightmap.Types.MOTION_BLOCKING, BlockPos.containing(wildHome));
			back = Vec3.atBottomCenterOf(ground);
		}
		fly(back, CRUISE);
		if (position().distanceToSqr(back) < 4 || modeTicks > 300) {
			if (hw == null) {
				setNoGravity(false);
				land();
			} else {
				mode = Mode.ROUTE;
				modeTicks = 0;
				route.clear();
				bound = -1;
			}
		}
	}

	/** Steers toward a point, easing in, and faces the way it flies. */
	private void fly(Vec3 at, double maxSpeed) {
		setNoGravity(true);
		entityData.set(PERCHED, false);
		Vec3 to = at.subtract(position());
		double dist = to.length();
		Vec3 want = dist < 0.01 ? Vec3.ZERO : to.scale(Math.min(maxSpeed, dist * 0.15) / dist);
		setDeltaMovement(getDeltaMovement().lerp(want, 0.1));
		if (getDeltaMovement().lengthSqr() > 1e-4) face(position().add(getDeltaMovement().scale(10)));
	}

	private void face(Vec3 at) {
		Vec3 d = at.subtract(position());
		float yaw = (float) (Mth.atan2(d.z, d.x) * Mth.RAD_TO_DEG) - 90f;
		float pitch = (float) -(Mth.atan2(d.y, d.horizontalDistance()) * Mth.RAD_TO_DEG);
		setYRot(Mth.approachDegrees(getYRot(), yaw, 9f));
		setXRot(Mth.approachDegrees(getXRot(), pitch, 6f));
		yBodyRot = getYRot();
		yHeadRot = getYRot();
	}

	/** The rider's stoop: stab whatever the lance meets when diving fast. */
	private void riderStoop(ServerLevel level, Player rider) {
		if (lastServerPos == null) return;
		Vec3 moved = position().subtract(lastServerPos);
		if (moved.length() > 0.9 && moved.y < -0.3) {
			if (tickCount % 2 == 0) {
				level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), getX(), getY() + 0.6, getZ(), 2, 0.2, 0.2, 0.2, 0.01);
			}
			stab(level, moved.length(), rider);
		}
	}

	/**
	 * The lance: anything (but its rider, Blue villagers and golems, and other hawks) just ahead of
	 * the beak is stabbed, harder the faster the stoop. Returns whether it hit.
	 */
	private boolean stab(ServerLevel level, double speed, @Nullable Player rider) {
		if (stabCooldown > 0) return false;
		Vec3 dir = getDeltaMovement().lengthSqr() > 1e-4 ? getDeltaMovement().normalize() : getLookAngle();
		Vec3 tip = position().add(0, getBbHeight() * 0.5, 0).add(dir.scale(1.6));
		AABB box = new AABB(tip, tip).inflate(0.9);
		boolean hit = false;
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box, e -> e != this && e != rider && e.isAlive()
				&& !(e instanceof DivingHawk) && !(e instanceof CorpsVillager v && v.corps() == Corps.BLUE)
				&& !(e instanceof CorpsGolem g && g.corps() == Corps.BLUE) && !(rider != null && e.isPassengerOfSameVehicle(rider)))) {
			float damage = (float) (STAB_DAMAGE * Mth.clamp(speed / STOOP_SPEED, 0.4, 1.2));
			DamageSource src = rider != null ? level.damageSources().playerAttack(rider) : level.damageSources().mobAttack(this);
			if (e.hurtServer(level, src, damage)) {
				e.push(dir.x * 1.2, 0.4, dir.z * 1.2);
				hit = true;
			}
		}
		if (hit) {
			stabCooldown = 12;
			level.playSound(null, tip.x, tip.y, tip.z, SoundEvents.TRIDENT_HIT, SoundSource.NEUTRAL, 1.4f, 0.8f);
			level.sendParticles(ModParticles.of(ModParticles.SPARK, Corps.BLUE), tip.x, tip.y, tip.z, 14, 0.3, 0.3, 0.3, 0.25);
		}
		return hit;
	}

	// ---- every tick -----------------------------------------------------------------------------

	@Override
	public void tick() {
		boolean wildFlight = !level().isClientSide() && getControllingPassenger() == null && !perched();
		if (wildFlight) noPhysics = true;
		super.tick();
		noPhysics = false;
		// A stoop that would carry it into the ground pulls up instead.
		if (wildFlight && mode == Mode.STOOP && !level().getBlockState(blockPosition()).getCollisionShape(level(), blockPosition()).isEmpty()) {
			Vec3 v = getDeltaMovement();
			setDeltaMovement(v.x * 0.3, 0.6, v.z * 0.3);
			mode = Mode.CLIMB;
			modeTicks = 0;
		}
		if (level().isClientSide()) animate();
	}

	/** Client side: eases the pose values toward what the hawk is doing now. */
	private void animate() {
		oFlapPhase = flapPhase;
		oFlap = flap;
		oStoop = stoop;
		oPerch = perch;
		oPitch = pitch;
		oBank = bank;
		if (previewPose != null) {
			flap = previewPose[0];
			stoop = previewPose[1];
			perch = previewPose[2];
			pitch = previewPose[3];
			bank = 0;
			flapPhase += 0.6f;
			return;
		}
		Vec3 moved = new Vec3(getX() - xo, getY() - yo, getZ() - zo);
		double speed = moved.length();
		double h = moved.horizontalDistance();
		float travelPitch = speed > 0.08 ? (float) -(Mth.atan2(moved.y, h) * Mth.RAD_TO_DEG) : 0f;
		boolean sitting = perched() && !isVehicle() || onGround() && speed < 0.05;
		boolean stooping = travelPitch > 30f && speed > 0.7;
		perch += ((sitting ? 1f : 0f) - perch) * 0.15f;
		stoop += ((stooping ? 1f : 0f) - stoop) * 0.2f;
		// Flaps hard to climb, hover or get going; glides when level and fast, with a beat now and then.
		float wantFlap;
		if (sitting || stooping) {
			wantFlap = 0f;
		} else if (moved.y > 0.04 || speed < 0.35) {
			wantFlap = 1f;
		} else {
			wantFlap = Mth.sin(tickCount * 0.045f) > 0.55f ? 0.8f : 0.15f;
		}
		flap += (wantFlap - flap) * 0.12f;
		flapPhase += 0.32f + 0.28f * flap + (moved.y > 0.04 ? 0.12f : 0f);
		float wantPitch = sitting ? PERCH_PITCH : Mth.clamp(travelPitch, -35f, 80f);
		pitch += (wantPitch - pitch) * 0.2f;
		float turn = Mth.wrapDegrees(getYRot() - yRotO);
		bank += (Mth.clamp(turn * 3.5f, -50f, 50f) * (sitting ? 0f : 1f) - bank) * 0.15f;
	}

	@Override
	public boolean causeFallDamage(double fallDistance, float multiplier, DamageSource source) {
		return false;
	}

	@Override
	protected void checkFallDamage(double y, boolean onGround, net.minecraft.world.level.block.state.BlockState state, BlockPos pos) {
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		Entity by = source.getEntity();
		if (source.is(DamageTypes.IN_WALL) || source.is(DamageTypes.FALL) || by != null && hasPassenger(by)
				|| by instanceof CorpsVillager v && v.corps() == Corps.BLUE || by instanceof CorpsGolem) {
			return false;
		}
		return super.hurtServer(level, source, amount);
	}

	@Override
	public boolean removeWhenFarAway(double distance) {
		return false;
	}

	@Override
	protected @Nullable SoundEvent getAmbientSound() {
		return perched() ? SoundEvents.PARROT_AMBIENT : null;
	}

	@Override
	public float getVoicePitch() {
		return 0.55f;
	}

	@Override
	protected @Nullable SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.PARROT_HURT;
	}

	@Override
	protected @Nullable SoundEvent getDeathSound() {
		return SoundEvents.PARROT_DEATH;
	}

	// ---- saving ---------------------------------------------------------------------------------

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
		super.addAdditionalSaveData(output);
		if (anchor != null) output.store("HawkCity", BlockPos.CODEC, anchor);
		output.putInt("HawkPad", homePad);
		output.putBoolean("HawkPerched", perched());
		if (wildHome != null) output.store("HawkHome", Vec3.CODEC, wildHome);
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
		super.readAdditionalSaveData(input);
		anchor = input.read("HawkCity", BlockPos.CODEC).orElse(null);
		homePad = input.getIntOr("HawkPad", -1);
		wildHome = input.read("HawkHome", Vec3.CODEC).orElse(null);
		boolean sat = input.getBooleanOr("HawkPerched", true);
		entityData.set(PERCHED, sat);
		mode = sat ? Mode.PERCH : Mode.CLIMB;
		setNoGravity(!sat || anchor != null);
	}
}
