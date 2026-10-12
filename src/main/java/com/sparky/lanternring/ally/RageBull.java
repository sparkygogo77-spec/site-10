package com.sparky.lanternring.ally;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.HeldConstructs;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.block.BlastGlowBlock;
import com.sparky.lanternring.RingPowers;
import java.util.ArrayList;
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
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The Red Lantern's biggest Blast (level 4, see BlastDrills): a giant hard-light bull that trots
 * straight ahead in the way its owner faced, never rising or dropping, and bulldozes everything in
 * its path. The space it carves is a round tunnel {@link #DIAMETER} blocks across, like the hole a
 * huge bullet would leave, whichever way it runs (diagonals included): a block goes when its
 * centre is inside that circle and the bull's nose has reached it. The floor under its hooves stays
 * flat so it never sinks. Mobs it runs into are battered and thrown aside. When its run is over it
 * stops and fades.
 *
 * <p>The model is drawn by the client (RageBullRenderer); it is {@link #SCALE} times its Blockbench size.
 */
public class RageBull extends Mob {
	/** How much bigger than its Blockbench model (rage_bull.bbmodel, 31 px to the hump) it is drawn. */
	public static final float SCALE = 8.5f;
	/** The tunnel's width and height. */
	public static final double DIAMETER = 20;
	private static final double RADIUS = DIAMETER / 2;
	/** How far in front of its middle its muzzle is (28 px forward in the model). */
	public static final double NOSE = 28 / 16.0 * SCALE;
	/** How far behind its middle its rump is (16 px back). */
	private static final double RUMP = 16 / 16.0 * SCALE;
	/** The tunnel's axis, this far above the floor; the circle's lowest row is the floor the bull walks on. */
	private static final double AXIS = RADIUS - 1;
	/** A run reaches from MIN_RUN (a tap) to MAX_RUN (fully charged) blocks. */
	public static final double MIN_RUN = 24;
	public static final double MAX_RUN = 80;
	private static final float DAMAGE = 14f;
	/** Ticks the bull takes to fade once it has stopped. */
	public static final int FADE = 20;
	/** Only some broken blocks throw debris; there are hundreds a second. */
	private static final float DEBRIS_SHARE = 0.25f;

	/** Ticks since it stopped, or -1 while it is still running (the client fades it by this). */
	private static final EntityDataAccessor<Integer> STOPPED = SynchedEntityData.defineId(RageBull.class, EntityDataSerializers.INT);

	private record Cut(double along, BlockPos pos) {
	}

	@Nullable
	private Player owner;
	private Vec3 start = Vec3.ZERO;
	/** Its heading, flat. */
	private Vec3 dir = new Vec3(0, 0, 1);
	private double run;
	private double speed;
	private final List<Cut> cuts = new ArrayList<>();
	private int next;
	private double nextLight = 3;
	/** When each mob it hit can be hit again (game time). */
	private final Map<UUID, Long> hit = new HashMap<>();
	private Corps corps = Corps.RED;

	public RageBull(EntityType<? extends RageBull> type, Level level) {
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
		return MAX_RUN / Math.max(1, RingTuning.RAGE_BULL_RUN.ticks());
	}

	/** Lets the bull loose from in front of the player, heading the way they face. */
	public static boolean start(ServerLevel level, Player player, float fraction) {
		RageBull bull = ModEntities.RAGE_BULL.create(level, net.minecraft.world.entity.EntitySpawnReason.MOB_SUMMONED);
		if (bull == null) return false;
		float yaw = player.getYRot();
		Vec3 dir = Vec3.directionFromRotation(0, yaw);
		bull.owner = player;
		bull.corps = Corps.current();
		bull.dir = dir;
		bull.run = run(fraction);
		bull.speed = speed();
		// Its rump appears just ahead of the player, its hooves on the floor they stand on.
		bull.start = new Vec3(player.getX(), Math.floor(player.getY() + 0.01), player.getZ()).add(dir.scale(RUMP + 1));
		bull.planTunnel(player.position());
		bull.snapTo(bull.start.x, bull.start.y, bull.start.z, yaw, 0);
		bull.setYHeadRot(yaw);
		bull.yBodyRot = yaw;
		level.addFreshEntity(bull);
		level.playSound(null, bull.getX(), bull.getY(), bull.getZ(), SoundEvents.RAVAGER_ROAR, SoundSource.PLAYERS, 3f, 0.5f);
		level.playSound(null, bull.getX(), bull.getY(), bull.getZ(), SoundEvents.RAVAGER_AMBIENT, SoundSource.PLAYERS, 3f, 0.5f);
		// The ground where it appears goes at once, so it never stands inside rock.
		bull.carve(bull.reach());
		return true;
	}

	/**
	 * Every block of the round tunnel, from the player's feet to the end of the run, in the order
	 * the nose reaches them. A block is in when its centre is inside the circle round the axis.
	 */
	private void planTunnel(Vec3 from) {
		Vec3 side = new Vec3(-dir.z, 0, dir.x);
		double floor = start.y;
		double axisY = floor + AXIS;
		double end = (RUMP + 1) + run + NOSE;
		int r = (int) Math.ceil(RADIUS) + 1;
		Map<BlockPos, Double> first = new HashMap<>();
		Vec3 to = from.add(dir.scale(end));
		int x0 = Mth.floor(Math.min(from.x, to.x)) - r, x1 = Mth.floor(Math.max(from.x, to.x)) + r;
		int z0 = Mth.floor(Math.min(from.z, to.z)) - r, z1 = Mth.floor(Math.max(from.z, to.z)) + r;
		int y0 = Mth.floor(floor);
		for (int x = x0; x <= x1; x++) {
			for (int z = z0; z <= z1; z++) {
				double rx = x + 0.5 - from.x, rz = z + 0.5 - from.z;
				double along = rx * dir.x + rz * dir.z;
				if (along < 1 || along > end) continue;
				double across = rx * side.x + rz * side.z;
				if (Math.abs(across) > RADIUS) continue;
				for (int y = y0; y <= y0 + DIAMETER; y++) {
					double up = y + 0.5 - axisY;
					if (across * across + up * up <= RADIUS * RADIUS) first.put(new BlockPos(x, y, z), along);
				}
			}
		}
		first.forEach((pos, along) -> cuts.add(new Cut(along, pos)));
		cuts.sort((a, b) -> Double.compare(a.along, b.along));
		this.tunnelFrom = from;
	}

	private Vec3 tunnelFrom = Vec3.ZERO;

	/** How far along the tunnel the nose is. */
	private double reach() {
		Vec3 rel = position().subtract(tunnelFrom);
		return rel.x * dir.x + rel.z * dir.z + NOSE + 0.5;
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
		super.defineSynchedData(builder);
		builder.define(STOPPED, -1);
	}

	/** Ticks since it stopped, or -1 while running. */
	public int stopped() {
		return entityData.get(STOPPED);
	}

	@Override
	public void tick() {
		noPhysics = true;
		super.tick();
		if (!(level() instanceof ServerLevel level)) return;
		if (owner == null) {
			// Loaded from a save or lost its owner: nothing to run for.
			discard();
			return;
		}
		int stopped = stopped();
		if (stopped >= 0) {
			entityData.set(STOPPED, stopped + 1);
			if (stopped + 1 >= FADE) {
				level.sendParticles(ParticleTypes.CLOUD, getX(), getY() + AXIS, getZ(), 40, 4, 6, 4, 0.05);
				discard();
			}
			return;
		}
		Corps before = Corps.enter(corps);
		try {
			carve(reach());
			trample(level);
			lightTunnel(level);
		} finally {
			Corps.restore(before);
		}
		if (tickCount % 9 == 0) {
			level.playSound(null, getX(), getY(), getZ(), SoundEvents.RAVAGER_STEP, SoundSource.PLAYERS, 3f, 0.45f);
		}
		if (tickCount % 70 == 35) {
			level.playSound(null, getX(), getY(), getZ(), SoundEvents.RAVAGER_ROAR, SoundSource.PLAYERS, 2f, 0.55f);
		}
		if (position().subtract(start).horizontalDistance() >= run) {
			entityData.set(STOPPED, 0);
			level.playSound(null, getX(), getY(), getZ(), SoundEvents.RAVAGER_CELEBRATE, SoundSource.PLAYERS, 3f, 0.5f);
		}
	}

	/** Moves straight on at a steady trot (the server moves it; clients follow). */
	@Override
	public void travel(Vec3 input) {
		if (stopped() >= 0 || owner == null) return;
		setPos(position().add(dir.scale(speed)));
		setYRot((float) Math.toDegrees(Math.atan2(-dir.x, dir.z)));
		yBodyRot = getYRot();
		setYHeadRot(getYRot());
	}

	/** Breaks every block of the tunnel the nose has reached. */
	private void carve(double reach) {
		if (!(level() instanceof ServerLevel level)) return;
		BlockState loudest = null;
		while (next < cuts.size() && cuts.get(next).along <= reach) {
			BlockPos pos = cuts.get(next++).pos;
			if (!level.isLoaded(pos)) continue;
			BlockState state = level.getBlockState(pos);
			if (state.isAir() || state.getBlock() instanceof BlastGlowBlock || state.getDestroySpeed(level, pos) < 0 || state.hasBlockEntity()
					|| owner == null || !level.mayInteract(owner, pos)) {
				continue;
			}
			level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
			if (state.getFluidState().isEmpty()) {
				if (level.getRandom().nextFloat() < DEBRIS_SHARE) HeldConstructs.debris(level, pos, state);
				if (loudest == null || state.getDestroySpeed(level, pos) > loudest.getDestroySpeed(level, pos)) loudest = state;
			}
		}
		if (loudest != null && tickCount % 2 == 0) {
			Vec3 at = position().add(dir.scale(NOSE)).add(0, AXIS, 0);
			level.playSound(null, at.x, at.y, at.z, loudest.getSoundType().getBreakSound(), SoundSource.PLAYERS, 2f, 0.6f);
		}
	}

	/** Batters and throws aside anything alive in its path or under its hooves. */
	private void trample(ServerLevel level) {
		Vec3 side = new Vec3(-dir.z, 0, dir.x);
		Vec3 axis = position().add(0, AXIS, 0);
		AABB box = new AABB(position().subtract(dir.scale(RUMP)), position().add(dir.scale(NOSE + 1))).inflate(RADIUS, 0, RADIUS).expandTowards(0, DIAMETER, 0);
		long now = level.getGameTime();
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box, e -> e != owner && e != this && e.isAlive() && !e.isSpectator())) {
			Vec3 rel = e.getBoundingBox().getCenter().subtract(axis);
			double along = rel.x * dir.x + rel.z * dir.z;
			double across = rel.x * side.x + rel.z * side.z;
			if (along < -RUMP || along > NOSE + 1 || across * across + rel.y * rel.y > (RADIUS + 0.5) * (RADIUS + 0.5)) continue;
			Long until = hit.get(e.getUUID());
			if (until != null && now < until) continue;
			hit.put(e.getUUID(), now + 10);
			e.hurtServer(level, owner == null ? level.damageSources().magic() : level.damageSources().indirectMagic(this, owner), DAMAGE);
			// Tossed forward and out to whichever side it was on, like off a bull's horns.
			double out = across >= 0 ? 1 : -1;
			Vec3 fling = dir.scale(1.1).add(side.scale(out * 0.9)).add(0, 0.7, 0);
			e.setDeltaMovement(fling);
			RingPowers.syncVelocity(e);
		}
	}

	/** A few invisible lights down the tunnel behind it, so the scar glows red for a while. */
	private void lightTunnel(ServerLevel level) {
		if (RingTuning.BLAST_AFTERGLOW.ticks() <= 0 || owner == null) return;
		BlockState glow = Corps.state(ModRegistry.BLAST_GLOW);
		double behind = reach() - NOSE - RUMP;
		for (; nextLight <= behind; nextLight += 6) {
			Vec3 at = tunnelFrom.add(dir.scale(nextLight));
			for (double h : new double[] {2, AXIS + 4}) {
				BlockPos pos = BlockPos.containing(at.x, start.y + h, at.z);
				if (level.getBlockState(pos).isAir() && level.mayInteract(owner, pos)) level.setBlock(pos, glow, 3);
			}
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
