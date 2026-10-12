package com.sparky.lanternring;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * The Red Lantern's Flame Ring: a ring of burning red liquid and fire races out from the bearer
 * and everything it reaches dies. Nothing drops dead on the spot: each victim is held where the
 * ring caught it, burning in a small pool of the red liquid, and melts down into it (shrinking as
 * it sinks) before it is gone. The ring's liquid is a solid band of sources that moves with the
 * fire, so it never breaks up into single flowing blocks; the pools are whole 3x3 puddles.
 */
public final class FlameRings {
	/** How far the ring runs out, in blocks. */
	public static final int RADIUS = 14;
	/** How far above and below the bearer the ring looks for the ground in each column. */
	private static final int REACH_UP = 4, REACH_DOWN = 6;
	/** How deep a victim sinks into its pool as it melts. */
	private static final double SINK = 1.6;
	/** What's left of a victim's size when it's gone. */
	private static final double SHRINK = 0.75;
	/** How long a victim's pool lingers after it has melted away. */
	private static final int POOL_AFTER = 20;
	private static final Identifier MELT_ID = LanternRing.id("flame_ring_melt");

	private static final class Ring {
		final ServerLevel level;
		final Player owner;
		final Vec3 center;
		final long start;
		final int spreadTicks;
		/** The band of liquid this tick, and every column's ground (by BlockPos.asLong(x, 0, z)). */
		final Set<BlockPos> band = new HashSet<>();
		final Map<Long, BlockPos> ground = new HashMap<>();
		final Set<Integer> caught = new HashSet<>();
		double radius;

		Ring(ServerLevel level, Player owner) {
			this.level = level;
			this.owner = owner;
			this.center = owner.position();
			this.start = level.getGameTime();
			this.spreadTicks = Math.max(1, RingTuning.FLAME_RING_SPREAD.ticks());
		}
	}

	/** A victim melting down into its pool. */
	private static final class Melt {
		final ServerLevel level;
		final LivingEntity victim;
		final Player owner;
		final Vec3 at;
		final long start;
		final int ticks;
		final List<BlockPos> pool = new ArrayList<>();
		boolean gone;

		Melt(ServerLevel level, LivingEntity victim, Player owner) {
			this.level = level;
			this.victim = victim;
			this.owner = owner;
			this.at = victim.position();
			this.start = level.getGameTime();
			this.ticks = Math.max(2, RingTuning.FLAME_RING_MELT.ticks());
		}
	}

	private static final List<Ring> RINGS = new ArrayList<>();
	private static final List<Melt> MELTS = new ArrayList<>();

	private FlameRings() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(FlameRings::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			for (Ring ring : RINGS) clearBand(ring);
			for (Melt melt : MELTS) finish(melt, true);
			RINGS.clear();
			MELTS.clear();
		});
	}

	/** Whether a Flame Ring's liquid (its band or a victim's pool) is at pos. */
	public static boolean holds(ServerLevel level, BlockPos pos) {
		for (Ring ring : RINGS) {
			if (ring.level == level && ring.band.contains(pos)) return true;
		}
		for (Melt melt : MELTS) {
			if (melt.level == level && melt.pool.contains(pos)) return true;
		}
		return false;
	}

	public static boolean activate(ServerLevel level, Player player) {
		Ring ring = new Ring(level, player);
		BlockPos c = player.blockPosition();
		for (int dx = -RADIUS - 1; dx <= RADIUS + 1; dx++) {
			for (int dz = -RADIUS - 1; dz <= RADIUS + 1; dz++) {
				if (dx * dx + dz * dz > (RADIUS + 1) * (RADIUS + 1)) continue;
				BlockPos surface = surface(level, c.offset(dx, 0, dz));
				if (surface != null) ring.ground.put(BlockPos.asLong(surface.getX(), 0, surface.getZ()), surface);
			}
		}
		RINGS.add(ring);
		Vec3 p = ring.center;
		level.sendParticles(ParticleTypes.FLAME, p.x, p.y + 0.3, p.z, 120, 0.8, 0.1, 0.8, 0.25);
		level.sendParticles(ParticleTypes.LAVA, p.x, p.y + 0.5, p.z, 30, 0.6, 0.2, 0.6, 0.4);
		level.sendParticles(ModParticles.of(ModParticles.MOTE), p.x, p.y + 1, p.z, 40, 0.6, 0.6, 0.6, 0.15);
		level.playSound(null, p.x, p.y, p.z, SoundEvents.BLAZE_SHOOT, SoundSource.PLAYERS, 3.0f, 0.4f);
		level.playSound(null, p.x, p.y, p.z, SoundEvents.FIRECHARGE_USE, SoundSource.PLAYERS, 3.0f, 0.5f);
		level.playSound(null, p.x, p.y, p.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 2.0f, 0.6f);
		return true;
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Ring> it = RINGS.iterator(); it.hasNext(); ) {
			Ring ring = it.next();
			Corps before = Corps.enter(Corps.RED);
			try {
				if (!spread(ring)) {
					clearBand(ring);
					it.remove();
				}
			} finally {
				Corps.restore(before);
			}
		}
		for (Iterator<Melt> it = MELTS.iterator(); it.hasNext(); ) {
			Melt melt = it.next();
			if (!melt(melt)) {
				finish(melt, false);
				it.remove();
			}
		}
	}

	// ---- the ring ---------------------------------------------------------------------------

	/** Moves the band of fire out a step and catches whatever it passes. @return false once it's done */
	private static boolean spread(Ring ring) {
		ServerLevel level = ring.level;
		long age = level.getGameTime() - ring.start;
		if (age > ring.spreadTicks) return false;
		double before = ring.radius;
		// Fast out of the middle, slowing as it reaches the edge.
		double t = age / (double) ring.spreadTicks;
		ring.radius = 1.0 + (RADIUS - 1.0) * (1 - (1 - t) * (1 - t));
		double r = ring.radius;
		Vec3 c = ring.center;
		BlockState liquid = ModFluids.EMBER_BLOCK.defaultBlockState();

		Set<BlockPos> next = new HashSet<>();
		int ri = (int) Math.ceil(r + 1);
		for (int dx = -ri; dx <= ri; dx++) {
			for (int dz = -ri; dz <= ri; dz++) {
				double d = Math.sqrt(dx * dx + dz * dz);
				if (d < r - 1.4 || d > r + 0.2) continue;
				BlockPos ground = ring.ground.get(BlockPos.asLong(Mth.floor(c.x) + dx, 0, Mth.floor(c.z) + dz));
				if (ground == null) continue;
				next.add(ground);
				// What it leaves behind burns.
				if (level.getRandom().nextInt(7) == 0 && d < r - 0.5) {
					BlockPos behind = ground;
					if (level.getBlockState(behind).isAir() && level.mayInteract(ring.owner, behind)
							&& Blocks.FIRE.defaultBlockState().canSurvive(level, behind)) {
						ring.band.remove(behind);
						level.setBlock(behind, Blocks.FIRE.defaultBlockState(), 3);
					}
				}
			}
		}
		for (BlockPos pos : ring.band) {
			if (!next.contains(pos) && ModFluids.isDelugeLiquid(level.getBlockState(pos))) level.setBlock(pos, Blocks.AIR.defaultBlockState(), 2);
		}
		ring.band.clear();
		for (BlockPos pos : next) {
			BlockState there = level.getBlockState(pos);
			if (there.is(ModFluids.EMBER_BLOCK) || (there.isAir() || there.canBeReplaced() && there.getFluidState().isEmpty())
					&& !there.hasBlockEntity() && level.mayInteract(ring.owner, pos)) {
				// No neighbour updates: the band comes and goes every tick without spilling.
				if (!there.is(ModFluids.EMBER_BLOCK)) level.setBlock(pos, liquid, 2);
				ring.band.add(pos);
			}
		}

		// The wall of fire along the band.
		int puffs = 10 + (int) (r * 5);
		for (int i = 0; i < puffs; i++) {
			double a = level.getRandom().nextDouble() * Math.PI * 2;
			double px = c.x + Math.cos(a) * r, pz = c.z + Math.sin(a) * r;
			BlockPos ground = ring.ground.get(BlockPos.asLong(Mth.floor(px), 0, Mth.floor(pz)));
			double py = ground != null ? ground.getY() : c.y;
			level.sendParticles(ParticleTypes.FLAME, px, py + 0.4, pz, 3, 0.25, 0.6, 0.25, 0.03);
			if (i % 2 == 0) level.sendParticles(ParticleTypes.LAVA, px, py + 0.6, pz, 1, 0.2, 0.2, 0.2, 0);
			if (i % 12 == 0) level.sendParticles(ParticleTypes.SMOKE, px, py + 1.8, pz, 1, 0.3, 0.4, 0.3, 0.02);
			if (i % 3 == 0) level.sendParticles(ModParticles.of(ModParticles.MOTE), px, py + 1.2, pz, 1, 0.3, 0.8, 0.3, 0.05);
		}
		if (age % 5 == 0) {
			level.playSound(null, c.x, c.y, c.z, SoundEvents.FIRE_AMBIENT, SoundSource.PLAYERS, 3.0f, 0.5f + 0.3f * (float) t);
			level.playSound(null, c.x, c.y, c.z, SoundEvents.LAVA_AMBIENT, SoundSource.PLAYERS, 2.0f, 0.6f);
		}

		// Everything the front passed over this tick is caught.
		AABB box = new AABB(c, c).inflate(r + 1.5, 0, r + 1.5).expandTowards(0, 6, 0).move(0, -REACH_DOWN, 0).expandTowards(0, REACH_DOWN, 0);
		for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, box, e -> spared(ring.owner, e) == false)) {
			double d = Math.sqrt(Mth.square(target.getX() - c.x) + Mth.square(target.getZ() - c.z));
			if (d > r + 0.8 || d < Math.min(before, r) - 1.5 && before > 0) continue;
			if (!ring.caught.add(target.getId())) continue;
			catchVictim(level, target, ring.owner);
		}
		return true;
	}

	/** The bearer, their own pets, players who can't be hurt, armor stands and anything already melting are spared. */
	private static boolean spared(Player owner, LivingEntity e) {
		if (e == owner || !e.isAlive() || e.isSpectator() || e instanceof ArmorStand) return true;
		if (e instanceof Player p && (p.isCreative() || p.isSpectator())) return true;
		if (e instanceof TamableAnimal pet && pet.isOwnedBy(owner)) return true;
		for (Melt melt : MELTS) {
			if (melt.victim == e) return true;
		}
		return false;
	}

	private static void clearBand(Ring ring) {
		for (BlockPos pos : ring.band) {
			if (ModFluids.isDelugeLiquid(ring.level.getBlockState(pos)) && !holdsPool(ring.level, pos)) {
				ring.level.setBlock(pos, Blocks.AIR.defaultBlockState(), 2);
			}
		}
		ring.band.clear();
	}

	private static boolean holdsPool(ServerLevel level, BlockPos pos) {
		for (Melt melt : MELTS) {
			if (melt.level == level && melt.pool.contains(pos)) return true;
		}
		return false;
	}

	// ---- the victims ------------------------------------------------------------------------

	private static void catchVictim(ServerLevel level, LivingEntity victim, Player owner) {
		Melt melt = new Melt(level, victim, owner);
		victim.igniteForSeconds(10);
		if (victim instanceof Mob mob) mob.setNoAi(true);
		victim.setNoGravity(true);
		victim.noPhysics = true;
		victim.setDeltaMovement(Vec3.ZERO);
		// A whole 3x3 puddle under it, so it melts into one pool rather than a single trickle.
		BlockPos foot = victim.blockPosition();
		BlockPos base = surface(level, foot);
		if (base == null) base = foot;
		BlockState liquid = ModFluids.EMBER_BLOCK.defaultBlockState();
		for (int dx = -1; dx <= 1; dx++) {
			for (int dz = -1; dz <= 1; dz++) {
				BlockPos pos = base.offset(dx, 0, dz);
				BlockState there = level.getBlockState(pos);
				if (!(there.isAir() || there.is(ModFluids.EMBER_BLOCK) || there.canBeReplaced() && there.getFluidState().isEmpty())
						|| there.hasBlockEntity() || !level.mayInteract(owner, pos)) {
					continue;
				}
				level.setBlock(pos, liquid, 2);
				melt.pool.add(pos.immutable());
			}
		}
		MELTS.add(melt);
		level.sendParticles(ParticleTypes.LAVA, melt.at.x, melt.at.y + 0.5, melt.at.z, 8, 0.4, 0.3, 0.4, 0.2);
		level.playSound(null, melt.at.x, melt.at.y, melt.at.z, SoundEvents.LAVA_POP, SoundSource.HOSTILE, 1.5f, 0.7f);
		level.playSound(null, melt.at.x, melt.at.y, melt.at.z, SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 1.0f, 0.8f);
	}

	/** One tick of a victim melting down into its pool. @return false once the pool should go */
	private static boolean melt(Melt melt) {
		ServerLevel level = melt.level;
		long age = level.getGameTime() - melt.start;
		LivingEntity victim = melt.victim;
		if (!melt.gone) {
			if (!victim.isAlive() || victim.isRemoved() || victim.level() != level) {
				melt.gone = true;
			} else if (age >= melt.ticks) {
				dissolve(melt);
			} else {
				double t = age / (double) melt.ticks;
				// Slowly at first, then it slumps.
				double sink = SINK * t * t;
				Vec3 at = melt.at.subtract(0, sink, 0);
				victim.setDeltaMovement(Vec3.ZERO);
				if (victim instanceof ServerPlayer player) player.teleportTo(at.x, at.y, at.z);
				else victim.setPos(at.x, at.y, at.z);
				AttributeInstance scale = victim.getAttribute(Attributes.SCALE);
				if (scale != null) scale.addOrUpdateTransientModifier(new AttributeModifier(MELT_ID, -SHRINK * t, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
				if (victim.getRemainingFireTicks() < 20) victim.igniteForSeconds(5);
				float h = victim.getBbHeight();
				level.sendParticles(ParticleTypes.FLAME, at.x, at.y + h * 0.5, at.z, 2, victim.getBbWidth() * 0.4, h * 0.3, victim.getBbWidth() * 0.4, 0.01);
				if (age % 3 == 0) level.sendParticles(ParticleTypes.LAVA, at.x, at.y + 0.6, at.z, 1, 0.3, 0.1, 0.3, 0);
				if (age % 10 == 0) level.sendParticles(ParticleTypes.SMOKE, at.x, at.y + h, at.z, 1, 0.2, 0.2, 0.2, 0.02);
				if (age % 8 == 0) level.playSound(null, at.x, at.y, at.z, SoundEvents.LAVA_EXTINGUISH, SoundSource.HOSTILE, 0.6f, 0.6f + 0.4f * (float) t);
			}
			return true;
		}
		// The pool lingers a moment after its victim is gone, then goes all at once.
		long left = melt.ticks + POOL_AFTER - age;
		if (left <= 0 || melt.pool.isEmpty()) return false;
		return true;
	}

	/** The victim is all melted: it's gone without a body, in a gout of flame. */
	private static void dissolve(Melt melt) {
		ServerLevel level = melt.level;
		LivingEntity victim = melt.victim;
		melt.gone = true;
		Vec3 at = victim.position();
		level.sendParticles(ParticleTypes.LAVA, at.x, at.y + 0.8, at.z, 10, 0.3, 0.2, 0.3, 0.3);
		level.sendParticles(ParticleTypes.FLAME, at.x, at.y + 0.6, at.z, 25, 0.4, 0.3, 0.4, 0.06);
		level.sendParticles(ParticleTypes.SMOKE, at.x, at.y + 1.0, at.z, 6, 0.3, 0.4, 0.3, 0.03);
		level.playSound(null, at.x, at.y, at.z, SoundEvents.LAVA_POP, SoundSource.HOSTILE, 1.2f, 0.6f);
		// Back up to the surface so whatever it drops isn't buried.
		victim.setPos(melt.at.x, melt.at.y, melt.at.z);
		victim.setInvisible(true);
		victim.hurtServer(level, level.damageSources().indirectMagic(melt.owner, melt.owner), Float.MAX_VALUE);
		if (victim.isAlive()) {
			// Something that shrugged that off (a totem) is let go, still burning.
			release(victim);
		}
	}

	private static void release(LivingEntity victim) {
		AttributeInstance scale = victim.getAttribute(Attributes.SCALE);
		if (scale != null) scale.removeModifier(MELT_ID);
		victim.setInvisible(false);
		victim.setNoGravity(false);
		victim.noPhysics = false;
		if (victim instanceof Mob mob) mob.setNoAi(false);
	}

	private static void finish(Melt melt, boolean stopping) {
		if (!melt.gone || stopping) {
			if (melt.victim.isAlive()) release(melt.victim);
		}
		ServerLevel level = melt.level;
		melt.pool.clear();
		// The whole puddle goes at once, what ran off its edge too, so it never breaks up into stray drops.
		BlockPos c = BlockPos.containing(melt.at);
		for (BlockPos pos : BlockPos.betweenClosed(c.offset(-4, -2, -4), c.offset(4, 2, 4))) {
			if (ModFluids.isDelugeLiquid(level.getBlockState(pos)) && !Deluges.isLive(level, pos) && !holds(level, pos)) {
				level.setBlock(pos, Blocks.AIR.defaultBlockState(), 2);
			}
		}
	}

	/** In the column through pos: the lowest open block resting on the ground, near pos's height. */
	private static BlockPos surface(ServerLevel level, BlockPos pos) {
		BlockPos at = pos.above(REACH_UP);
		boolean openAbove = false;
		for (int i = 0; i < REACH_UP + REACH_DOWN; i++, at = at.below()) {
			BlockState state = level.getBlockState(at);
			if (state.isAir() || state.is(ModFluids.EMBER_BLOCK) || state.canBeReplaced() && state.getFluidState().isEmpty()) {
				openAbove = true;
				continue;
			}
			if (!openAbove || !state.getFluidState().isEmpty()) return null;
			return at.above();
		}
		return null;
	}
}
