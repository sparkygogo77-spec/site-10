package com.sparky.lanternring;

import com.sparky.lanternring.block.BlastGlowBlock;
import com.sparky.lanternring.block.LightConstructBlock;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Brightness;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;

/**
 * ANVIL: hold right-click and a glowing anvil-shaped marker slides along the ground under your
 * cursor. Let go and a big hard-light anvil (3x3 base, 5 tall) is built block by block about 10
 * blocks above the ground there, glowing bright, then cools to clear jade while it drops. It falls
 * with gravity, and where it lands it smashes a round crater, nearest blocks first, flinging some
 * of them out as real falling blocks. The anvil sinks into its crater, rests a while, then fades.
 *
 * <p>While it moves the anvil is a set of block displays the client glides smoothly between ticks,
 * so it falls at its real speed instead of hopping a block at a time. Once it has settled in its
 * finished crater it turns back into solid blocks.
 */
public final class Anvils {
	/** How far ahead the marker can be. */
	private static final double RANGE = 64;
	/** How high above the average ground around the marker the anvil is built. */
	private static final int HEIGHT = 10;
	/** Crater radius in blocks. */
	private static final double CRATER_RADIUS = 6.5;
	/** Share of crater blocks thrown out as falling blocks, and at most how many per crater. */
	private static final float EJECTA_CHANCE = 0.12f;
	private static final int EJECTA_MAX = 60;
	private static final float IMPACT_DAMAGE = 24f;
	/** Ticks the anvil hangs after it's built before it drops. */
	private static final int HANG_TICKS = 6;
	/** Vanilla falling-block gravity and drag. */
	private static final double GRAVITY = 0.08;
	private static final double DRAG = 0.98;
	/** How bright the marker's light is (blast glow levels go to 15). */
	private static final int MARKER_LIGHT = 8;

	/**
	 * The anvil, as offsets from the middle of its base: x across its long side, z front to back.
	 * Base 3x3, a 3-long waist two blocks high, then a 5x3 face with a horn on one end.
	 */
	private static final List<int[]> SHAPE = new ArrayList<>();

	static {
		for (int x = -1; x <= 1; x++) for (int z = -1; z <= 1; z++) SHAPE.add(new int[] {x, 0, z});
		for (int y = 1; y <= 2; y++) for (int x = -1; x <= 1; x++) SHAPE.add(new int[] {x, y, 0});
		for (int y = 3; y <= 4; y++) {
			for (int x = -1; x <= 2; x++) for (int z = -1; z <= 1; z++) SHAPE.add(new int[] {x, y, z});
			SHAPE.add(new int[] {-2, y, 0});
		}
		// The horn tapers to a point.
		SHAPE.add(new int[] {-3, 4, 0});
	}

	/** Where a bearer is aiming while they hold right-click. */
	private static final class Aim {
		ServerLevel level;
		BlockPos mark;
		Direction facing;
		BlockPos light;
		long lastTick;
	}

	private static final class Cell {
		final int dx, dy, dz;
		long buildAt;
		long dimAt;
		boolean built;
		/** Its spot was taken when it was built, so this anvil goes without it. */
		boolean missing;
		boolean bright = true;
		/** Stands in for the block while the anvil is moving. */
		Display.BlockDisplay body;

		Cell(int dx, int dy, int dz) {
			this.dx = dx;
			this.dy = dy;
			this.dz = dz;
		}
	}

	private static final class Drop {
		final ServerLevel level;
		final Player owner;
		final List<Cell> cells = new ArrayList<>();
		/** Blocks of this anvil currently in the world. */
		final Set<BlockPos> placed = new HashSet<>();
		/** True while the anvil is solid blocks; false while it is moving as block displays. */
		boolean solid = true;
		BlockPos origin;
		double y;
		double speed;
		long buildEnd;
		double fallen;
		/** Crater blocks still to break, nearest first. */
		List<BlockPos> crater;
		Vec3 craterCenter;
		int craterIndex;
		int craterPerTick;
		int ejecta;
		long restingSince = -1;
		long expires = Long.MAX_VALUE;

		Drop(ServerLevel level, Player owner, BlockPos origin) {
			this.level = level;
			this.owner = owner;
			this.origin = origin;
			this.y = origin.getY();
		}

		BlockPos at(Cell c, BlockPos base) {
			return base.offset(c.dx, c.dy, c.dz);
		}
	}

	private static final Map<UUID, Aim> AIMS = new HashMap<>();
	private static final List<Drop> DROPS = new ArrayList<>();

	private Anvils() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(Anvils::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			// The moving bodies are entities: don't let them be saved with the world.
			for (Drop drop : DROPS) discardBodies(drop);
			AIMS.clear();
			DROPS.clear();
		});
	}

	public static boolean isLive(ServerLevel level, BlockPos pos) {
		for (Drop drop : DROPS) {
			if (drop.level == level && drop.placed.contains(pos)) return true;
		}
		return false;
	}

	// ---- aiming ---------------------------------------------------------------------------

	/** Called every tick while the ring is held in ANVIL mode: moves the marker and its light. */
	public static void aim(ServerPlayer player) {
		ServerLevel level = player.level();
		Aim aim = AIMS.computeIfAbsent(player.getUUID(), id -> new Aim());
		if (aim.level != null && aim.level != level) clearLight(aim);
		aim.level = level;
		aim.lastTick = level.getGameTime();
		aim.mark = findMark(level, player);
		aim.facing = player.getDirection();
		BlockPos light = aim.mark;
		if (light != null && !light.equals(aim.light)) {
			clearLight(aim);
			BlockState there = level.getBlockState(light);
			if (there.isAir() && !there.is(ModRegistry.BLAST_GLOW)) {
				level.setBlock(light, glow(), 3);
				aim.light = light;
			}
		} else if (light != null) {
			// Keep it lit while it sits still; the block would otherwise start fading by itself.
			BlockState there = level.getBlockState(light);
			if (there.is(ModRegistry.BLAST_GLOW) && there.getValue(BlastGlowBlock.LEVEL) != MARKER_LIGHT) {
				level.setBlock(light, glow(), 2);
			} else if (there.isAir() && !there.is(ModRegistry.BLAST_GLOW)) {
				level.setBlock(light, glow(), 3);
				aim.light = light;
			}
		} else {
			clearLight(aim);
		}
		if (aim.mark != null && level.getGameTime() % 2 == 0) {
			Vec3 at = new Vec3(aim.mark.getX() + 0.5, aim.mark.getY(), aim.mark.getZ() + 0.5);
			RingFx.send(level, Kind.ANVIL_MARK, at, at.add(aim.facing.getStepX(), 0, aim.facing.getStepZ()));
		}
	}

	private static BlockState glow() {
		return ModRegistry.BLAST_GLOW.defaultBlockState().setValue(BlastGlowBlock.LEVEL, MARKER_LIGHT);
	}

	private static void clearLight(Aim aim) {
		if (aim.light != null && aim.level != null && aim.level.getBlockState(aim.light).is(ModRegistry.BLAST_GLOW)) {
			aim.level.setBlock(aim.light, Blocks.AIR.defaultBlockState(), 3);
		}
		aim.light = null;
	}

	/**
	 * The air block resting on the ground under the cursor: the first solid block along the
	 * player's line of sight, then straight down from there to the ground.
	 */
	static BlockPos findMark(ServerLevel level, Player player) {
		Vec3 eye = player.getEyePosition();
		BlockHitResult hit = level.clip(new ClipContext(eye, eye.add(player.getLookAngle().scale(RANGE)),
				ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
		if (hit.getType() == HitResult.Type.MISS) return null;
		BlockPos pos = hit.getBlockPos().relative(hit.getDirection());
		for (int i = 0; i < 24 && pos.getY() > level.getMinY(); i++) {
			if (isGround(level, pos.below())) return pos;
			pos = pos.below();
		}
		return null;
	}

	private static boolean isGround(ServerLevel level, BlockPos pos) {
		BlockState state = level.getBlockState(pos);
		return !state.canBeReplaced() && !isOurs(state);
	}

	private static boolean isOurs(BlockState state) {
		return state.is(ModRegistry.LIGHT_CONSTRUCT) || state.is(ModRegistry.BLAST_GLOW);
	}

	/** Called when right-click is let go, in any mode: drops an anvil if the player was aiming one. */
	public static void release(Player player) {
		Aim aim = AIMS.remove(player.getUUID());
		if (aim == null) return;
		clearLight(aim);
		if (aim.mark != null && aim.level == player.level()) drop(aim.level, player, aim.mark, aim.facing);
	}

	// ---- the drop ---------------------------------------------------------------------------

	private static void drop(ServerLevel level, Player owner, BlockPos mark, Direction facing) {
		BlockPos origin = new BlockPos(mark.getX(), averageGround(level, mark) + HEIGHT, mark.getZ());
		Drop drop = new Drop(level, owner, origin);
		long now = level.getGameTime();
		int buildTicks = Math.max(1, RingTuning.ANVIL_BUILD.ticks());
		// Build bottom to top, with a little shuffle within each layer so it looks assembled.
		List<Cell> order = new ArrayList<>();
		boolean alongX = facing.getAxis() == Direction.Axis.Z;
		for (int[] s : SHAPE) {
			// The long side faces the bearer: across their view.
			order.add(alongX ? new Cell(s[0], s[1], s[2]) : new Cell(s[2], s[1], s[0]));
		}
		order.sort(Comparator.comparingDouble(c -> c.dy + level.getRandom().nextFloat() * 0.9));
		for (int i = 0; i < order.size(); i++) {
			Cell c = order.get(i);
			c.buildAt = now + (long) i * buildTicks / order.size();
		}
		drop.cells.addAll(order);
		drop.buildEnd = now + buildTicks;
		int glowTicks = RingTuning.ANVIL_GLOW.ticks();
		for (Cell c : drop.cells) c.dimAt = drop.buildEnd + level.getRandom().nextInt(glowTicks + 1);
		DROPS.add(drop);
		RingFx.send(level, Kind.CONSTRUCT, RingPowers.handPos(owner), Vec3.atCenterOf(origin.above(2)));
		level.playSound(null, origin, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 2.0f, 0.8f);
	}

	/** Mean ground height (top of the ground) in a 7x7 patch around the marker. */
	private static int averageGround(ServerLevel level, BlockPos mark) {
		int total = 0;
		int n = 0;
		for (int x = -3; x <= 3; x++) {
			for (int z = -3; z <= 3; z++) {
				BlockPos pos = mark.offset(x, 6, z);
				for (int i = 0; i < 14; i++, pos = pos.below()) {
					if (!isGround(level, pos) && isGround(level, pos.below())) {
						total += pos.getY();
						n++;
						break;
					}
				}
			}
		}
		return n == 0 ? mark.getY() : Math.round(total / (float) n);
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Map.Entry<UUID, Aim>> it = AIMS.entrySet().iterator(); it.hasNext(); ) {
			Aim aim = it.next().getValue();
			// Stopped holding without a release (switched items, logged out...): no anvil.
			if (aim.level == null || aim.level.getGameTime() - aim.lastTick > 2) {
				clearLight(aim);
				it.remove();
			}
		}
		for (Iterator<Drop> it = DROPS.iterator(); it.hasNext(); ) {
			Drop drop = it.next();
			if (tick(drop)) continue;
			for (BlockPos pos : drop.placed) removeIfOurs(drop.level, pos);
			drop.placed.clear();
			discardBodies(drop);
			it.remove();
		}
	}

	/** @return false once the drop is over and its blocks should go */
	private static boolean tick(Drop drop) {
		ServerLevel level = drop.level;
		long now = level.getGameTime();
		build(drop, now);
		dim(drop, now);
		if (now < drop.buildEnd + HANG_TICKS) return true;
		if (drop.solid && drop.placed.isEmpty()) return false;

		if (drop.solid && canMoveDown(drop)) loosen(drop);
		if (!drop.solid) {
			boolean landed = fall(drop, now);
			if (landed && drop.crater != null && drop.craterIndex >= drop.crater.size()) solidify(drop);
		}
		dig(drop);
		rest(drop, now);
		if (now >= drop.expires) {
			level.playSound(null, drop.origin, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1.5f, 0.8f);
			return false;
		}
		return true;
	}

	private static BlockState state(Cell c) {
		return ModRegistry.LIGHT_CONSTRUCT.defaultBlockState()
				.setValue(LightConstructBlock.HELD, true).setValue(LightConstructBlock.RIM, c.bright);
	}

	/** Puts each block up at its moment; a block whose spot is taken is left out. */
	private static void build(Drop drop, long now) {
		for (Cell c : drop.cells) {
			if (c.built || now < c.buildAt) continue;
			c.built = true;
			BlockPos pos = drop.at(c, drop.origin);
			BlockState state = state(c);
			BlockState current = drop.level.getBlockState(pos);
			if (!current.canBeReplaced() || !drop.level.isUnobstructed(state, pos, CollisionContext.empty())) {
				c.missing = true;
				continue;
			}
			drop.level.setBlock(pos, state, 3);
			drop.placed.add(pos);
			if (drop.level.getRandom().nextInt(6) == 0) {
				drop.level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.0f, 1.6f);
			}
		}
		drop.cells.removeIf(c -> c.missing);
	}

	/** Fresh blocks glow bright, then cool one by one to clear jade. */
	private static void dim(Drop drop, long now) {
		for (Cell c : drop.cells) {
			if (!c.built || !c.bright || now < c.dimAt) continue;
			c.bright = false;
			if (c.body != null) c.body.setBlockState(state(c));
			BlockPos pos = drop.at(c, drop.origin);
			if (drop.placed.contains(pos) && drop.level.getBlockState(pos).is(ModRegistry.LIGHT_CONSTRUCT)) {
				drop.level.setBlock(pos, state(c), 2);
			}
		}
	}

	/**
	 * Gravity: speeds up each tick and glides the whole anvil down until it hits something. Its
	 * block position steps down a block at a time underneath, for collisions and crushing.
	 *
	 * @return true if it is sitting on something this tick
	 */
	private static boolean fall(Drop drop, long now) {
		drop.speed = (drop.speed + GRAVITY) * DRAG;
		double target = drop.y - drop.speed;
		boolean landed = false;
		while (Mth.floor(target) < drop.origin.getY()) {
			if (!canMoveDown(drop)) {
				// Landed. The first landing makes the crater; after that it just rests.
				if (drop.crater == null) impact(drop);
				drop.speed = 0;
				target = drop.origin.getY();
				landed = true;
				break;
			}
			drop.origin = drop.origin.below();
			drop.fallen++;
			drop.restingSince = -1;
			crush(drop);
		}
		drop.y = target;
		moveBodies(drop);
		if (landed && drop.restingSince < 0) drop.restingSince = now;
		return landed;
	}

	/** Settled at the bottom of a finished crater: rest, then fade. */
	private static void rest(Drop drop, long now) {
		if (drop.crater != null && drop.craterIndex >= drop.crater.size() && drop.restingSince >= 0
				&& now - drop.restingSince > 10 && drop.expires == Long.MAX_VALUE) {
			drop.expires = now + RingTuning.ANVIL_LIFETIME.ticks();
		}
	}

	/** Swaps the anvil's blocks for block displays so it can move smoothly. */
	private static void loosen(Drop drop) {
		for (BlockPos pos : drop.placed) removeIfOurs(drop.level, pos);
		drop.placed.clear();
		drop.y = drop.origin.getY();
		for (Cell c : drop.cells) {
			Display.BlockDisplay body = EntityTypes.BLOCK_DISPLAY.create(drop.level, EntitySpawnReason.TRIGGERED);
			if (body == null) continue;
			body.setBlockState(state(c));
			// Hard light: as bright in the dark as the glowing blocks it stands in for.
			body.setBrightnessOverride(Brightness.FULL_BRIGHT);
			// The client glides it from one tick's spot to the next instead of jumping.
			body.setPosRotInterpolationDuration(1);
			body.setPos(drop.origin.getX() + c.dx, drop.y + c.dy, drop.origin.getZ() + c.dz);
			drop.level.addFreshEntity(body);
			c.body = body;
		}
		drop.solid = false;
		drop.restingSince = -1;
	}

	private static void moveBodies(Drop drop) {
		for (Cell c : drop.cells) {
			if (c.body != null) c.body.setPos(drop.origin.getX() + c.dx, drop.y + c.dy, drop.origin.getZ() + c.dz);
		}
	}

	/** Back to solid blocks where it rests; a cell whose spot is taken is left out. */
	private static void solidify(Drop drop) {
		for (Cell c : drop.cells) {
			BlockPos pos = drop.at(c, drop.origin);
			BlockState state = state(c);
			if (drop.level.getBlockState(pos).canBeReplaced() && drop.level.isUnobstructed(state, pos, CollisionContext.empty())) {
				drop.level.setBlock(pos, state, 3);
				drop.placed.add(pos);
			}
		}
		discardBodies(drop);
		drop.solid = true;
	}

	private static void discardBodies(Drop drop) {
		for (Cell c : drop.cells) {
			if (c.body != null) c.body.discard();
			c.body = null;
		}
	}

	private static boolean canMoveDown(Drop drop) {
		BlockPos below = drop.origin.below();
		if (below.getY() <= drop.level.getMinY()) return false;
		for (Cell c : drop.cells) {
			BlockPos pos = drop.at(c, below);
			if (drop.placed.contains(pos)) continue;
			BlockState state = drop.level.getBlockState(pos);
			if (!state.canBeReplaced() && !state.is(ModRegistry.BLAST_GLOW)) return false;
		}
		return true;
	}

	/** Anything under the falling anvil gets hit, like a vanilla anvil: harder the further it fell. */
	private static void crush(Drop drop) {
		AABB box = new AABB(drop.origin).inflate(1.5, 0, 1.5).expandTowards(0, 4, 0);
		float damage = (float) Math.min(40, 2 * drop.fallen);
		if (damage <= 0) return;
		for (LivingEntity target : drop.level.getEntitiesOfClass(LivingEntity.class, box,
				e -> e != drop.owner && e.isAlive() && !e.isSpectator())) {
			target.hurtServer(drop.level, drop.level.damageSources().indirectMagic(drop.owner, drop.owner), damage);
		}
	}

	/** The anvil lands: a boom, a hit to everything nearby, and a crater to dig. */
	private static void impact(Drop drop) {
		ServerLevel level = drop.level;
		Vec3 center = new Vec3(drop.origin.getX() + 0.5, drop.origin.getY(), drop.origin.getZ() + 0.5);
		double r = CRATER_RADIUS;
		List<BlockPos> crater = new ArrayList<>();
		BlockPos c = BlockPos.containing(center);
		int ri = (int) Math.ceil(r);
		for (BlockPos pos : BlockPos.betweenClosed(c.offset(-ri, -ri, -ri), c.offset(ri, ri, ri))) {
			if (Vec3.atCenterOf(pos).distanceToSqr(center) <= r * r) crater.add(pos.immutable());
		}
		crater.sort(Comparator.comparingDouble(p -> Vec3.atCenterOf(p).distanceToSqr(center)));
		drop.crater = crater;
		drop.craterCenter = center;
		drop.craterPerTick = Math.max(1, (int) Math.ceil(crater.size() / (double) Math.max(1, RingTuning.ANVIL_CRATER_TIME.ticks())));

		for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, new AABB(center, center).inflate(r + 2),
				e -> e != drop.owner && e.isAlive() && !e.isSpectator())) {
			Vec3 away = target.position().subtract(center);
			double d = away.length();
			if (d > r + 2) continue;
			away = away.multiply(1, 0, 1);
			away = away.lengthSqr() < 1.0e-4 ? new Vec3(1, 0, 0) : away.normalize();
			float falloff = (float) (1 - d / (r + 2));
			target.hurtServer(level, level.damageSources().indirectMagic(drop.owner, drop.owner), IMPACT_DAMAGE * falloff + 2);
			target.setDeltaMovement(away.x * 1.4 * falloff, 0.5 + 0.6 * falloff, away.z * 1.4 * falloff);
			RingPowers.syncVelocity(target);
		}

		RingFx.send(level, Kind.ANVIL_IMPACT, center, center.add(r, 0, 0));
		level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, center.x, center.y, center.z, 1, 0, 0, 0, 0);
		level.playSound(null, center.x, center.y, center.z, SoundEvents.ANVIL_LAND, SoundSource.PLAYERS, 4.0f, 0.5f);
		level.playSound(null, center.x, center.y, center.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 3.0f, 0.7f);
	}

	/** Breaks the next batch of crater blocks, nearest the impact first, so the bowl opens outwards fast. */
	private static void dig(Drop drop) {
		if (drop.crater == null) return;
		ServerLevel level = drop.level;
		Vec3 center = drop.craterCenter;
		int end = Math.min(drop.crater.size(), drop.craterIndex + drop.craterPerTick);
		for (; drop.craterIndex < end; drop.craterIndex++) {
			BlockPos pos = drop.crater.get(drop.craterIndex);
			if (drop.placed.contains(pos)) continue;
			BlockState state = level.getBlockState(pos);
			if (state.isAir() || isOurs(state) || state.getDestroySpeed(level, pos) < 0 || state.hasBlockEntity()
					|| !state.getFluidState().isEmpty() || !level.mayInteract(drop.owner, pos)) {
				continue;
			}
			if (drop.ejecta < EJECTA_MAX && state.isCollisionShapeFullBlock(level, pos)
					&& level.getRandom().nextFloat() < EJECTA_CHANCE) {
				fling(level, pos, state, center);
				drop.ejecta++;
			} else {
				level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
				HeldConstructs.debris(level, pos, state);
			}
		}
	}

	/** Throws a crater block up and out as a real falling block; it lands wherever physics takes it. */
	private static void fling(ServerLevel level, BlockPos pos, BlockState state, Vec3 center) {
		FallingBlockEntity block = FallingBlockEntity.fall(level, pos, state);
		block.disableDrop();
		Vec3 out = Vec3.atCenterOf(pos).subtract(center).multiply(1, 0, 1);
		out = out.lengthSqr() < 1.0e-4 ? new Vec3(level.getRandom().nextGaussian(), 0, level.getRandom().nextGaussian()) : out;
		out = out.normalize().scale(0.35 + level.getRandom().nextDouble() * 0.45);
		block.setDeltaMovement(out.x, 0.55 + level.getRandom().nextDouble() * 0.45, out.z);
		block.needsSync = true;
	}

	private static void removeIfOurs(ServerLevel level, BlockPos pos) {
		if (level.getBlockState(pos).is(ModRegistry.LIGHT_CONSTRUCT)) {
			level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
		}
	}
}
