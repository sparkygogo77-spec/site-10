package com.sparky.lanternring.ally;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.HeldConstructs;
import com.sparky.lanternring.RingPowers;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.block.BlastGlowBlock;
import com.sparky.lanternring.corps.DreadTrails;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The Yellow Lantern's biggest Blast (level 4, see BlastDrills): the Dread Runner, a gaunt fear
 * construct that bursts out of the ring and sprints, ground-hugging, at whatever its owner is aiming
 * at. It turns to follow their aim for its whole run, breaks a body-sized tunnel
 * ({@link #WIDTH} wide, {@link #HEIGHT} high) through anything in its way, batters and throws mobs
 * aside, and leaves fear on the ground behind it (see DreadTrails) that blinds whoever stands in it,
 * its owner included. When its run is over it stops and fades.
 *
 * <p>The client draws it from the Blender rig (DreadRunnerRenderer, dread_runner_*.bbmodel).
 */
public class DreadRunner extends Mob {
	/** How much bigger than its Blockbench model (about 46 px tall) it is drawn: some 4 blocks. */
	public static final float SCALE = 1.35f;
	/** The tunnel it breaks: blocks across and blocks high from its feet. */
	public static final int WIDTH = 3;
	public static final int HEIGHT = 4;
	/** A run reaches from MIN_RUN (a tap) to MAX_RUN (fully charged) blocks. */
	public static final double MIN_RUN = 20;
	public static final double MAX_RUN = 64;
	private static final float DAMAGE = 9f;
	/** How far ahead of its middle it breaks blocks. */
	private static final double REACH = 1.6;
	/** How far it looks for what its owner is aiming at. */
	private static final double AIM_RANGE = 96;
	/** The sharpest it turns in a tick, in radians: about 9 degrees. */
	private static final double TURN = 0.16;
	/** Ticks it takes to fade once it has stopped. */
	public static final int FADE = 14;
	/** Only some broken blocks throw debris. */
	private static final float DEBRIS_SHARE = 0.35f;

	/** Most mobs it stops to kill in one run (Blender pass 420); the rest are trampled as before. */
	private static final int MAX_KILLS = 3;
	/**
	 * The kill animation the Ring Lab picked (RANDOM, K1-K4 or OFF). The client sets it; in singleplayer
	 * that is the server this runs on, and a dedicated server keeps RANDOM.
	 */
	public static volatile String killPick = "RANDOM";

	/** Ticks since it stopped, or -1 while it is still running (the client fades it by this). */
	private static final EntityDataAccessor<Integer> STOPPED = SynchedEntityData.defineId(DreadRunner.class, EntityDataSerializers.INT);
	/** The kill clip playing (index into RunnerKills.clips()), or -1. */
	private static final EntityDataAccessor<Integer> KILL = SynchedEntityData.defineId(DreadRunner.class, EntityDataSerializers.INT);
	/** The tickCount the kill clip started at. */
	private static final EntityDataAccessor<Integer> KILL_START = SynchedEntityData.defineId(DreadRunner.class, EntityDataSerializers.INT);

	@Nullable
	private Player owner;
	/** Its heading, flat. */
	private Vec3 dir = new Vec3(0, 0, 1);
	private double run;
	private double travelled;
	private double speed;
	/** Where the fear was last dropped on the ground. */
	private Vec3 lastFear = Vec3.ZERO;
	private final Map<UUID, Long> hit = new HashMap<>();
	private Corps corps = Corps.YELLOW;
	/** The mob being killed, where the runner was and which way it faced when the clip started. */
	@Nullable
	private Mob victim;
	private Vec3 killFrom = Vec3.ZERO;
	private Vec3 killDir = new Vec3(0, 0, 1);
	private Vec3 victimLast = Vec3.ZERO;
	private Vec3 victimVel = Vec3.ZERO;
	private boolean held;
	private boolean struck;
	private int kills;

	public DreadRunner(EntityType<? extends DreadRunner> type, Level level) {
		super(type, level);
		noPhysics = true;
		setNoGravity(true);
		xpReward = 0;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Mob.createMobAttributes()
				.add(Attributes.MAX_HEALTH, 100)
				.add(Attributes.KNOCKBACK_RESISTANCE, 1);
	}

	/** How long a run charged this far (0 to 1) is. */
	public static double run(float fraction) {
		return MIN_RUN + (MAX_RUN - MIN_RUN) * Mth.clamp(fraction, 0f, 1f);
	}

	/** Blocks per tick, from the Durations menu's time for a full run. */
	public static double speed() {
		return MAX_RUN / Math.max(1, RingTuning.DREAD_RUN.ticks());
	}

	/** Lets the runner loose from in front of the player, heading for what they aim at. */
	public static boolean start(ServerLevel level, Player player, float fraction) {
		DreadRunner runner = ModEntities.DREAD_RUNNER.create(level, EntitySpawnReason.MOB_SUMMONED);
		if (runner == null) return false;
		Vec3 dir = Vec3.directionFromRotation(0, player.getYRot());
		runner.owner = player;
		runner.corps = Corps.current();
		runner.dir = dir;
		runner.run = run(fraction);
		runner.speed = speed();
		Vec3 at = new Vec3(player.getX(), Math.floor(player.getY() + 0.01), player.getZ()).add(dir.scale(1.5));
		runner.snapTo(at.x, at.y, at.z, player.getYRot(), 0);
		runner.face();
		runner.lastFear = at;
		level.addFreshEntity(runner);
		level.playSound(null, at.x, at.y, at.z, SoundEvents.WARDEN_ROAR, SoundSource.PLAYERS, 2f, 1.4f);
		level.playSound(null, at.x, at.y, at.z, SoundEvents.PHANTOM_SWOOP, SoundSource.PLAYERS, 2f, 0.6f);
		// Where it bursts out goes at once, so it never stands inside rock.
		runner.carve(runner.position(), runner.position().add(dir.scale(REACH)));
		return true;
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(STOPPED, -1);
		builder.define(KILL, -1);
		builder.define(KILL_START, 0);
	}

	/** Ticks since it stopped, or -1 while running. */
	public int stopped() {
		return entityData.get(STOPPED);
	}

	/** The kill clip playing (index into RunnerKills.clips()), or -1. */
	public int killClip() {
		return entityData.get(KILL);
	}

	/** The tickCount the kill clip started at. */
	public int killStart() {
		return entityData.get(KILL_START);
	}

	@Override
	public void tick() {
		noPhysics = true;
		super.tick();
		if (!(level() instanceof ServerLevel level)) return;
		if (owner == null || !owner.isAlive()) {
			// Loaded from a save or lost its owner: nothing to run for.
			discard();
			return;
		}
		int stopped = stopped();
		if (stopped >= 0) {
			entityData.set(STOPPED, stopped + 1);
			if (stopped + 1 >= FADE) {
				level.sendParticles(ParticleTypes.LARGE_SMOKE, getX(), getY() + 2, getZ(), 30, 0.8, 1.5, 0.8, 0.02);
				discard();
			}
			return;
		}
		if (tickCount % 5 == 0) {
			level.playSound(null, getX(), getY(), getZ(), SoundEvents.SKELETON_STEP, SoundSource.PLAYERS, 1.6f, 0.5f);
		}
		if (tickCount % 30 == 15) {
			level.playSound(null, getX(), getY(), getZ(), SoundEvents.PHANTOM_AMBIENT, SoundSource.PLAYERS, 1.6f, 0.5f);
		}
		if (travelled >= run) {
			entityData.set(STOPPED, 0);
			level.playSound(null, getX(), getY(), getZ(), SoundEvents.WARDEN_SONIC_CHARGE, SoundSource.PLAYERS, 1.5f, 1.6f);
		}
	}

	/** Steers for its owner's aim and sprints on (the server moves it; clients follow). */
	@Override
	public void travel(Vec3 input) {
		if (stopped() >= 0 || owner == null || !(level() instanceof ServerLevel level)) return;
		Corps before = Corps.enter(corps);
		try {
			if (killClip() >= 0) {
				stepKill(level);
				return;
			}
			Vec3 target = aim(level);
			steer(target);
			Vec3 from = position();
			// Ground-hugging: it climbs or drops toward what it is aimed at, at most a block for every
			// two it runs, and falls when there's nothing under it and nothing higher to aim for.
			double dy = 0;
			if (target != null) dy = Mth.clamp(target.y - from.y, -speed * 0.5, speed * 0.5);
			if (dy > -0.05 && !supported(level, from) && (target == null || target.y <= from.y + 0.5)) dy = -speed * 0.6;
			Vec3 to = from.add(dir.scale(speed)).add(0, dy, 0);
			carve(from, to.add(dir.scale(REACH)));
			setPos(to);
			travelled += speed;
			face();
			trample(level);
			dropFear(level);
		} finally {
			Corps.restore(before);
		}
	}

	/** What its owner is aiming at: the block they look at, or a point far off along their look. */
	@Nullable
	private Vec3 aim(ServerLevel level) {
		Vec3 eye = owner.getEyePosition();
		Vec3 end = eye.add(owner.getLookAngle().scale(AIM_RANGE));
		HitResult hit = level.clip(new ClipContext(eye, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, owner));
		return hit.getType() == HitResult.Type.MISS ? null : hit.getLocation();
	}

	/** Turns its heading toward the target (or the owner's flat look), no faster than TURN a tick. */
	private void steer(@Nullable Vec3 target) {
		Vec3 want = target == null ? Vec3.directionFromRotation(0, owner.getYRot()) : target.subtract(position()).multiply(1, 0, 1);
		// Once it has reached (or passed) what it was aimed at, it runs straight on through it
		// rather than wheeling round to come back.
		if (target != null && (want.lengthSqr() < 16 || want.dot(dir) < 0)) return;
		if (want.lengthSqr() < 0.25) return;
		double have = Math.atan2(dir.z, dir.x);
		double goal = Math.atan2(want.z, want.x);
		double turn = Mth.clamp(Mth.wrapDegrees(Math.toDegrees(goal - have)) * Mth.DEG_TO_RAD, -TURN, TURN);
		double a = have + turn;
		dir = new Vec3(Math.cos(a), 0, Math.sin(a));
	}

	private void face() {
		float yaw = (float) Math.toDegrees(Math.atan2(-dir.x, dir.z));
		setYRot(yaw);
		yBodyRot = yaw;
		setYHeadRot(yaw);
	}

	private static boolean supported(ServerLevel level, Vec3 at) {
		BlockPos below = BlockPos.containing(at.x, at.y - 0.5, at.z);
		return !level.getBlockState(below).getCollisionShape(level, below).isEmpty();
	}

	/** Breaks the body-sized tunnel from {@code from} to {@code to}, feet level up. */
	private void carve(Vec3 from, Vec3 to) {
		if (!(level() instanceof ServerLevel level) || owner == null) return;
		Vec3 side = new Vec3(-dir.z, 0, dir.x);
		double length = to.subtract(from).length();
		BlockState loudest = null;
		for (double t = 0; t <= length + 1e-3; t += 0.5) {
			Vec3 c = length < 1e-3 ? from : from.add(to.subtract(from).scale(t / length));
			for (int a = -(WIDTH / 2); a <= WIDTH / 2; a++) {
				for (int h = 0; h < HEIGHT; h++) {
					BlockPos pos = BlockPos.containing(c.x + side.x * a, Math.floor(c.y + 0.01) + h + 0.5, c.z + side.z * a);
					if (!level.isLoaded(pos)) continue;
					BlockState state = level.getBlockState(pos);
					if (state.isAir() || !state.getFluidState().isEmpty() || state.getBlock() instanceof BlastGlowBlock
							|| state.getDestroySpeed(level, pos) < 0 || state.hasBlockEntity() || !level.mayInteract(owner, pos)) {
						continue;
					}
					level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
					if (level.getRandom().nextFloat() < DEBRIS_SHARE) HeldConstructs.debris(level, pos, state);
					if (loudest == null || state.getDestroySpeed(level, pos) > loudest.getDestroySpeed(level, pos)) loudest = state;
				}
			}
		}
		if (loudest != null) {
			level.playSound(null, to.x, to.y + 1.5, to.z, loudest.getSoundType().getBreakSound(), SoundSource.PLAYERS, 1.5f, 0.6f);
		}
	}

	/** Batters and throws aside anything alive it runs into. */
	private void trample(ServerLevel level) {
		Vec3 side = new Vec3(-dir.z, 0, dir.x);
		AABB box = new AABB(position(), position().add(dir.scale(REACH + 0.5))).inflate(WIDTH / 2.0 + 0.5, 0, WIDTH / 2.0 + 0.5).expandTowards(0, HEIGHT, 0);
		long now = level.getGameTime();
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box, e -> e != owner && e != this && e.isAlive() && !e.isSpectator())) {
			Long until = hit.get(e.getUUID());
			if (until != null && now < until) continue;
			hit.put(e.getUUID(), now + 10);
			if (killClip() < 0 && e instanceof Mob mob && startKill(level, mob)) continue;
			e.hurtServer(level, level.damageSources().indirectMagic(this, owner), DAMAGE);
			Vec3 rel = e.position().subtract(position());
			double out = rel.x * side.x + rel.z * side.z >= 0 ? 1 : -1;
			e.setDeltaMovement(dir.scale(0.8).add(side.scale(out * 1.1)).add(0, 0.55, 0));
			RingPowers.syncVelocity(e);
		}
	}

	/** Stops to kill this mob with the Ring Lab's kill clip; false (trample it) if kills are off or used up. */
	private boolean startKill(ServerLevel level, Mob mob) {
		List<RunnerKills.Clip> clips = RunnerKills.clips();
		String pick = killPick;
		if (clips.isEmpty() || "OFF".equals(pick) || kills >= MAX_KILLS) return false;
		int clip = switch (pick) {
			case "K1" -> 0;
			case "K2" -> 1;
			case "K3" -> 2;
			case "K4" -> 3;
			default -> level.getRandom().nextInt(clips.size());
		};
		if (clip >= clips.size()) clip = 0;
		kills++;
		victim = mob;
		killFrom = position();
		killDir = dir;
		victimLast = mob.position();
		victimVel = Vec3.ZERO;
		held = true;
		struck = false;
		entityData.set(KILL_START, tickCount);
		entityData.set(KILL, clip);
		level.playSound(null, getX(), getY() + 2, getZ(), SoundEvents.WARDEN_ROAR, SoundSource.PLAYERS, 1.6f, 1.2f);
		return true;
	}

	/**
	 * One tick of the kill clip: the runner moves by the clip's root, the victim is held where its target
	 * says (thrown on with its last speed when let go mid-air, else dropped), and it dies on the hit frame.
	 */
	private void stepKill(ServerLevel level) {
		RunnerKills.Clip clip = RunnerKills.clips().get(killClip());
		float f = (tickCount - killStart()) * RunnerKills.FPS / 20f;
		if (f >= clip.length() - 1) {
			entityData.set(KILL, -1);
			victim = null;
			return;
		}
		int i = (int) f;
		float t = f - i;
		double s = SCALE / 16.0;
		Vec3 side = new Vec3(-killDir.z, 0, killDir.x);
		float[] r0 = clip.root()[i], r1 = clip.root()[i + 1];
		Vec3 from = position();
		Vec3 to = killFrom.add(side.scale(Mth.lerp(t, r0[0], r1[0]) * s)).add(killDir.scale(Mth.lerp(t, r0[1], r1[1]) * s));
		carve(from, to.add(killDir.scale(REACH)));
		setPos(to);
		if (victim == null || victim.isRemoved()) return;
		float[] a = clip.target()[i], b = clip.target()[i + 1];
		if (a != null && held) {
			float[] p = b == null ? a : new float[] {Mth.lerp(t, a[0], b[0]), Mth.lerp(t, a[1], b[1]), Mth.lerp(t, a[2], b[2])};
			Vec3 at = killFrom.add(side.scale(p[0] * s)).add(killDir.scale(p[1] * s)).add(0, Math.max(0, p[2]) * s, 0);
			victimVel = at.subtract(victimLast);
			victimLast = at;
			victim.setPos(at);
			victim.setDeltaMovement(Vec3.ZERO);
			victim.fallDistance = 0;
		} else if (held) {
			// Let go: thrown on with the speed it had (K2's hurl), or just dropped.
			held = false;
			victim.setDeltaMovement(victimVel.lengthSqr() > 0.04 ? victimVel.scale(1.4).add(0, 0.3, 0) : Vec3.ZERO);
			RingPowers.syncVelocity(victim);
		}
		if (!struck && f >= clip.hit()) {
			struck = true;
			victim.hurtServer(level, level.damageSources().indirectMagic(this, owner), victim.getMaxHealth() * 4 + 40);
			level.playSound(null, victim.getX(), victim.getY() + 1, victim.getZ(),
					clip.name().contains("scream") ? SoundEvents.WARDEN_SONIC_BOOM : SoundEvents.WARDEN_ATTACK_IMPACT, SoundSource.PLAYERS, 1.6f, 0.9f);
		}
	}

	/** Fear on the ground every block it runs (see DreadTrails). */
	private void dropFear(ServerLevel level) {
		while (position().distanceTo(lastFear) >= 1.0) {
			Vec3 step = position().subtract(lastFear).normalize();
			lastFear = lastFear.add(step);
			DreadTrails.drop(level, lastFear, owner);
		}
	}

	// ---- a construct, not a creature -----------------------------------------------------

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		return false;
	}

	@Override
	public boolean isPushable() {
		return false;
	}

	@Override
	public void push(Entity entity) {
	}

	@Override
	protected void doPush(Entity entity) {
	}

	@Override
	public boolean isPickable() {
		return false;
	}

	@Override
	public boolean shouldBeSaved() {
		return false;
	}

	@Override
	public boolean removeWhenFarAway(double distance) {
		return false;
	}

	@Override
	public boolean fireImmune() {
		return true;
	}
}
