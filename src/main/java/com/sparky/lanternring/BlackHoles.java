package com.sparky.lanternring;

import com.sparky.lanternring.block.BlastGlowBlock;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.ExperienceOrb;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.DoublePlantBlock;
import net.minecraft.world.level.block.FallingBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * BLACK HOLE: hold right-click and a swirl of light marks where the hole will open, hovering just
 * off whatever you point at; left-click while holding picks its size. Let go and a gravity well
 * opens there: it pulls in mobs, dropped items, arrows and loose blocks, spinning them round as they
 * fall in, and crushes what reaches its core. After RingTuning.BLACK_HOLE_TIME it collapses with a
 * bang that throws what's left outward, and drops every item it caught in a pile underneath.
 *
 * <p>It only eats loose or soft natural blocks (sand, gravel, dirt and grass, snow, leaves, plants)
 * that are open to the air, and only so many per hole, so it scoops a dent rather than levelling
 * the area. Everything here runs on the server; the hole itself is drawn by each client
 * (BlackHoleFx) from one RingFxPayload sent when it opens.
 */
public final class BlackHoles {
	/** How far ahead the hole can open. */
	private static final double RANGE = 40;
	/** Ticks the hole takes to open to full size, and to collapse at the end. */
	public static final int GROW = 20;
	public static final int COLLAPSE = 14;
	/** The sizes left-click cycles through. */
	public static final int[] SIZES = {1, 2, 3};
	/** Ticks between crushing hits on a mob in the core. */
	private static final int CRUSH_INTERVAL = 10;
	/** Fastest anything is pulled, in blocks per tick. */
	private static final double MAX_SPEED = 1.1;

	private static final class Aim {
		ServerLevel level;
		Vec3 center;
		long lastTick;
	}

	private static final class Hole {
		final ServerLevel level;
		final Player owner;
		final Vec3 center;
		final int size;
		final long start;
		final int pullTicks;
		/** Blocks this hole turned into falling blocks: crushed at the core, or cleared when it ends. */
		final Set<FallingBlockEntity> debris = new HashSet<>();
		/** Items it caught: dropped in a pile under it when it collapses. */
		final Set<Entity> caught = new HashSet<>();
		final Map<UUID, Long> lastCrush = new HashMap<>();
		/** The invisible lights it put round itself (see lightUp), cleared when it collapses. */
		final Set<BlockPos> lights = new HashSet<>();
		int blocksTaken;

		Hole(ServerLevel level, Player owner, Vec3 center, int size, int pullTicks) {
			this.level = level;
			this.owner = owner;
			this.center = center;
			this.size = size;
			this.start = level.getGameTime();
			this.pullTicks = pullTicks;
		}

		long end() {
			return start + GROW + pullTicks + COLLAPSE;
		}
	}

	private static final Map<UUID, Aim> AIMS = new HashMap<>();
	private static final List<Hole> HOLES = new ArrayList<>();
	private static final Map<UUID, Long> NO_CHARGE_NOTE = new HashMap<>();

	private BlackHoles() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(BlackHoles::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			for (Hole hole : HOLES) clearDebris(hole);
			HOLES.clear();
			AIMS.clear();
			NO_CHARGE_NOTE.clear();
		});
	}

	// ---- sizes ----------------------------------------------------------------------------

	public static int size(ItemStack ring) {
		int size = ring.getOrDefault(ModComponents.BLACK_HOLE_SIZE, 1);
		return Mth.clamp(size, 1, SIZES.length);
	}

	/** Charge per hole: 5%, 10% or 20% of a full ring (PowerRingItem.MAX_CHARGE = 1000). */
	public static int cost(int size) {
		return size >= 3 ? 200 : size == 2 ? 100 : 50;
	}

	/** How far out it pulls, in blocks. */
	public static double pullRadius(int size) {
		return size >= 3 ? 16 : size == 2 ? 12 : 8;
	}

	/** The black core's radius, in blocks. Anything that reaches it is crushed. */
	public static double coreRadius(int size) {
		return size >= 3 ? 2.1 : size == 2 ? 1.5 : 1.0;
	}

	/** How far from the core it tears loose blocks away, and at most how many. */
	private static double blockReach(int size) {
		return size >= 3 ? 7 : size == 2 ? 5.5 : 4;
	}

	private static int blockBudget(int size) {
		return size >= 3 ? 140 : size == 2 ? 70 : 30;
	}

	private static float crushDamage(int size) {
		return size >= 3 ? 10f : size == 2 ? 7f : 5f;
	}

	/** Left-click while holding right-click in Black Hole mode: the next size. */
	public static void cycleSize(ServerPlayer player, ItemStack ring) {
		int next = size(ring) % SIZES.length + 1;
		ring.set(ModComponents.BLACK_HOLE_SIZE, next);
		player.sendOverlayMessage(sizeText(next).copy().withStyle(ChatFormatting.GREEN));
		player.level().playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1f, 1.5f - 0.3f * next);
	}

	public static Component sizeText(int size) {
		return Component.translatable("message.lanternring.black_hole_size", size,
				Component.translatable("black_hole_size.lanternring." + size), String.valueOf(cost(size) / 10));
	}

	// ---- aiming ---------------------------------------------------------------------------

	/** Every tick right-click is held in Black Hole mode (from PowerRingItem.onUseTick). */
	public static void aimTick(ServerPlayer player, ItemStack ring) {
		if (!AIMS.containsKey(player.getUUID())) {
			if (player.getCooldowns().isOnCooldown(ring)) return;
			if (!player.isCreative() && PowerRingItem.getCharge(ring) < cost(size(ring))) {
				long now = player.level().getGameTime();
				if (now - NO_CHARGE_NOTE.getOrDefault(player.getUUID(), Long.MIN_VALUE / 2) > 20) {
					NO_CHARGE_NOTE.put(player.getUUID(), now);
					player.sendOverlayMessage(Component.translatable("message.lanternring.no_charge").withStyle(ChatFormatting.RED));
					player.level().playSound(null, player.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.6f, 1.4f);
				}
				return;
			}
		}
		ServerLevel level = player.level();
		Aim aim = AIMS.computeIfAbsent(player.getUUID(), id -> new Aim());
		int size = size(ring);
		aim.level = level;
		aim.lastTick = level.getGameTime();
		aim.center = findCenter(level, player, size);
		if (level.getGameTime() % 2 == 0) {
			RingFx.send(level, Kind.BLACK_HOLE_MARK, aim.center, aim.center, (float) pullRadius(size), size);
		}
		if (level.getGameTime() % 16 == 0) {
			level.playSound(null, aim.center.x, aim.center.y, aim.center.z, SoundEvents.BEACON_AMBIENT, SoundSource.PLAYERS, 0.5f, 0.5f);
		}
	}

	/**
	 * Where the hole would open: a little way back from the first block along the line of sight,
	 * lifted so its core floats clear of the ground. Pointing at the sky, it opens out in the air.
	 */
	static Vec3 findCenter(ServerLevel level, Player player, int size) {
		Vec3 eye = player.getEyePosition();
		Vec3 look = player.getLookAngle();
		BlockHitResult hit = level.clip(new ClipContext(eye, eye.add(look.scale(RANGE)),
				ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
		double core = coreRadius(size);
		Vec3 at;
		if (hit.getType() == HitResult.Type.MISS) {
			at = eye.add(look.scale(RANGE * 0.6));
		} else {
			double back = Math.min(core + 1.5, hit.getLocation().distanceTo(eye) * 0.5);
			at = hit.getLocation().subtract(look.scale(back));
		}
		// Float above the ground: up to a few blocks, until there's air under the core.
		double clear = core + 1.5;
		for (int i = 0; i < 6 && !level.getBlockState(BlockPos.containing(at.x, at.y - clear, at.z)).getCollisionShape(level,
				BlockPos.containing(at.x, at.y - clear, at.z)).isEmpty(); i++) {
			at = at.add(0, 1, 0);
		}
		return at;
	}

	/** Right-click let go: opens the hole where the marker is, and pays for it. */
	public static void release(ServerPlayer player, ItemStack ring) {
		Aim aim = AIMS.remove(player.getUUID());
		if (aim == null || aim.center == null || aim.level != player.level()) return;
		int size = size(ring);
		int cost = cost(size);
		if (!player.isCreative()) {
			if (PowerRingItem.getCharge(ring) < cost) return;
			PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - cost);
		}
		open(aim.level, player, aim.center, size);
		player.getCooldowns().addCooldown(ring, RingTuning.cooldownTicks(RingMode.BLACK_HOLE));
		player.sendOverlayMessage(PowerRingItem.chargeText(ring));
	}

	/** Stopped holding without letting go on purpose (switched items or modes...): nothing opens. */
	public static void cancel(Player player) {
		AIMS.remove(player.getUUID());
	}

	static void open(ServerLevel level, Player owner, Vec3 center, int size) {
		Hole hole = new Hole(level, owner, center, size, Math.max(20, RingTuning.BLACK_HOLE_TIME.ticks()));
		HOLES.add(hole);
		// The disk tips a little toward the bearer, so they see across its top with the core in front.
		Vec3 toOwner = owner.position().subtract(center).multiply(1, 0, 1);
		toOwner = toOwner.lengthSqr() < 1.0e-4 ? new Vec3(1, 0, 0) : toOwner.normalize();
		double tilt = Math.toRadians(20);
		Vec3 axis = new Vec3(0, Math.cos(tilt), 0).add(toOwner.scale(Math.sin(tilt)));
		RingFx.send(level, Kind.BLACK_HOLE, center, center.add(axis), hole.pullTicks, size);
		RingFx.send(level, Kind.CONSTRUCT, RingPowers.handPos(owner), center);
		lightUp(hole);
		level.playSound(null, center.x, center.y, center.z, SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 2.0f, 0.5f);
		level.playSound(null, center.x, center.y, center.z, SoundEvents.PORTAL_TRIGGER, SoundSource.PLAYERS, 0.7f, 1.6f);
	}

	// ---- the hole -------------------------------------------------------------------------

	private static void tick(MinecraftServer server) {
		for (Iterator<Map.Entry<UUID, Aim>> it = AIMS.entrySet().iterator(); it.hasNext(); ) {
			Aim aim = it.next().getValue();
			if (aim.level == null || aim.level.getGameTime() - aim.lastTick > 5) it.remove();
		}
		for (Iterator<Hole> it = HOLES.iterator(); it.hasNext(); ) {
			Hole hole = it.next();
			long now = hole.level.getGameTime();
			if (now >= hole.end() || now < hole.start) {
				collapse(hole);
				it.remove();
				continue;
			}
			tick(hole, now - hole.start);
		}
	}

	/** How hard it pulls at this age: growing, full, then a last hard squeeze as it collapses. */
	private static double strength(Hole hole, long age) {
		if (age < GROW) return age / (double) GROW;
		if (age < GROW + hole.pullTicks) return 1;
		return 1.6;
	}

	private static void tick(Hole hole, long age) {
		ServerLevel level = hole.level;
		double strength = strength(hole, age);
		double reach = hole.size >= 3 ? pullRadius(hole.size) : pullRadius(hole.size) * Math.min(1, 0.4 + strength);
		double core = coreRadius(hole.size) * Math.min(1, strength);
		AABB area = new AABB(hole.center, hole.center).inflate(reach);
		for (Entity e : level.getEntities((Entity) null, area, e -> pulls(hole, e))) {
			pull(hole, e, reach, core, strength, age);
		}
		// Keep the light field bright (the light blocks would otherwise start to fade by themselves).
		if (age % 20 == 10 && age < GROW + hole.pullTicks) lightUp(hole);
		// Tears loose blocks away while it's open (not while it grows or collapses).
		if (age >= GROW && age < GROW + hole.pullTicks && age % 2 == 0) tearBlocks(hole);
		if (age % 30 == 0 && age < GROW + hole.pullTicks) {
			level.playSound(null, hole.center.x, hole.center.y, hole.center.z, SoundEvents.BEACON_AMBIENT, SoundSource.PLAYERS, 1.6f, 0.5f);
		}
		if (age == GROW + hole.pullTicks) {
			level.playSound(null, hole.center.x, hole.center.y, hole.center.z, SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 2.0f, 0.5f);
		}
	}

	private static boolean pulls(Hole hole, Entity e) {
		if (e == hole.owner || !e.isAlive() || e.isSpectator()) return false;
		if (e instanceof Player p && (p.isCreative() || p.getAbilities().flying && p.isCreative())) return false;
		if (e instanceof OwnableEntity pet && pet.getOwner() == hole.owner) return false;
		if (e instanceof ItemEntity || e instanceof ExperienceOrb || e instanceof FallingBlockEntity) return true;
		if (e instanceof Projectile projectile) return projectile.getOwner() != hole.owner || hole.owner == null;
		return e instanceof LivingEntity;
	}

	/** Pulls one thing in, swirling it round the hole; inside the core it is crushed or held. */
	private static void pull(Hole hole, Entity e, double reach, double core, double strength, long age) {
		Vec3 at = e.getBoundingBox().getCenter();
		Vec3 in = hole.center.subtract(at);
		double dist = in.length();
		if (dist > reach || dist < 1.0e-4) return;
		Vec3 dir = in.scale(1 / dist);
		// Round the hole's vertical axis, so things spiral in rather than fall straight.
		Vec3 swirl = new Vec3(-dir.z, 0, dir.x);
		swirl = swirl.lengthSqr() < 1.0e-4 ? Vec3.ZERO : swirl.normalize();
		boolean loose = !(e instanceof LivingEntity);
		double close = 1 - dist / reach;
		double accel = strength * (loose ? 0.16 : 0.11) * (0.3 + 0.7 * close) * (0.8 + 0.2 * hole.size);
		Vec3 v = e.getDeltaMovement();
		if (e.getBoundingBox().inflate(0.4).distanceToSqr(hole.center) < (core + 0.3) * (core + 0.3) || dist < core + 0.7) {
			// In the core: hold it there, turning, and crush it.
			v = in.scale(0.35).add(swirl.scale(0.25));
			crush(hole, e, age);
		} else {
			v = v.scale(0.92).add(dir.scale(accel)).add(swirl.scale(accel * 0.75));
			// Cancel most of gravity so mobs lift off the ground toward a hovering hole.
			if (!e.isNoGravity()) v = v.add(0, (loose ? 0.04 : 0.06) * strength, 0);
		}
		double speed = v.length();
		if (speed > MAX_SPEED) v = v.scale(MAX_SPEED / speed);
		e.setDeltaMovement(v);
		e.resetFallDistance();
		if (e instanceof ItemEntity || e instanceof ExperienceOrb) hole.caught.add(e);
		RingPowers.syncVelocity(e);
	}

	private static void crush(Hole hole, Entity e, long age) {
		ServerLevel level = hole.level;
		if (e instanceof FallingBlockEntity block) {
			level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, block.getBlockState()),
					e.getX(), e.getY() + 0.5, e.getZ(), 8, 0.3, 0.3, 0.3, 0.05);
			hole.debris.remove(block);
			block.discard();
			if (level.getRandom().nextInt(3) == 0) {
				level.playSound(null, e.getX(), e.getY(), e.getZ(), SoundEvents.GRAVEL_BREAK, SoundSource.BLOCKS, 0.8f, 0.6f);
			}
			return;
		}
		if (e instanceof Projectile) {
			e.discard();
			return;
		}
		if (!(e instanceof LivingEntity living)) return;
		long now = level.getGameTime();
		Long last = hole.lastCrush.get(e.getUUID());
		if (last != null && now - last < CRUSH_INTERVAL) return;
		hole.lastCrush.put(e.getUUID(), now);
		living.hurtServer(level, level.damageSources().indirectMagic(hole.owner, hole.owner), crushDamage(hole.size));
		level.playSound(null, e.getX(), e.getY(), e.getZ(), SoundEvents.AMETHYST_BLOCK_BREAK, SoundSource.PLAYERS, 1.0f, 0.5f);
	}

	/** Tears a few loose blocks near the core out of the ground as falling blocks it then swallows. */
	private static void tearBlocks(Hole hole) {
		int budget = blockBudget(hole.size);
		if (hole.blocksTaken >= budget) return;
		ServerLevel level = hole.level;
		RandomSource r = level.getRandom();
		double reach = blockReach(hole.size);
		int want = hole.size;
		for (int tries = 0; tries < 24 && want > 0 && hole.blocksTaken < budget; tries++) {
			// A random spot in the ball round the core, weighted toward the middle.
			Vec3 off = new Vec3(r.nextGaussian(), r.nextGaussian(), r.nextGaussian());
			if (off.lengthSqr() < 1.0e-4) continue;
			off = off.normalize().scale(reach * Math.sqrt(r.nextDouble()));
			BlockPos pos = BlockPos.containing(hole.center.add(off));
			BlockState state = level.getBlockState(pos);
			if (!eats(level, pos, state) || !exposed(level, pos) || !level.mayInteract(hole.owner, pos)) continue;
			want--;
			hole.blocksTaken++;
			if (!state.isCollisionShapeFullBlock(level, pos)) {
				// Plants and snow layers just shred.
				level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
				level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, state),
						pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, 6, 0.3, 0.3, 0.3, 0.05);
				continue;
			}
			FallingBlockEntity block = FallingBlockEntity.fall(level, pos, state);
			block.disableDrop();
			block.setNoGravity(true);
			block.setDeltaMovement(0, 0.15, 0);
			block.needsSync = true;
			hole.debris.add(block);
		}
	}

	/** Loose or soft natural blocks: sand and gravel, dirt and grass, snow, leaves, plants. */
	private static boolean eats(ServerLevel level, BlockPos pos, BlockState state) {
		if (state.isAir() || !state.getFluidState().isEmpty() || state.hasBlockEntity()) return false;
		if (state.is(ModRegistry.LIGHT_CONSTRUCT) || state.is(ModRegistry.BLAST_GLOW) || state.getBlock() instanceof DoublePlantBlock) return false;
		float hardness = state.getDestroySpeed(level, pos);
		if (hardness < 0 || hardness > 1) return false;
		return state.getBlock() instanceof FallingBlock || state.is(BlockTags.LEAVES) || state.is(BlockTags.DIRT)
				|| state.is(BlockTags.SAND) || state.is(Blocks.SNOW) || state.is(Blocks.SNOW_BLOCK)
				|| state.is(BlockTags.FLOWERS) || state.canBeReplaced();
	}

	private static boolean exposed(ServerLevel level, BlockPos pos) {
		for (Direction d : Direction.values()) {
			if (level.getBlockState(pos.relative(d)).canBeReplaced()) return true;
		}
		return false;
	}

	/** How far round the hole its light reaches, in blocks: further than it pulls. */
	private static int lightRadius(int size) {
		return size >= 3 ? 30 : size == 2 ? 24 : 18;
	}

	/**
	 * Lights a wide area round the hole like a green sun: full-strength invisible lights (the Blast's
	 * light block, green under shader packs with colored lighting, see ShaderPackIds) at its core,
	 * on a grid round it at its height and on the ground under each grid point, so the ground,
	 * walls and caves round it are all lit. Called again while it is open to keep them at full strength.
	 */
	private static void lightUp(Hole hole) {
		ServerLevel level = hole.level;
		BlockState glow = ModRegistry.BLAST_GLOW.defaultBlockState().setValue(BlastGlowBlock.LEVEL, BlastGlowBlock.START_LEVEL);
		BlockPos c = BlockPos.containing(hole.center);
		int reach = lightRadius(hole.size);
		int step = 7;
		for (int dx = -reach; dx <= reach; dx += step) {
			for (int dz = -reach; dz <= reach; dz += step) {
				if (dx * dx + dz * dz > reach * reach) continue;
				BlockPos at = c.offset(dx, 0, dz);
				light(hole, glow, at);
				// And down on the ground (or a cave floor) below it.
				BlockPos pos = at.below();
				for (int i = 0; i < 24 && pos.getY() > level.getMinY(); i++, pos = pos.below()) {
					if (!level.getBlockState(pos.below()).getCollisionShape(level, pos.below()).isEmpty()) {
						if (pos.distManhattan(at) > 3) light(hole, glow, pos.above());
						break;
					}
				}
			}
		}
	}

	private static void light(Hole hole, BlockState glow, BlockPos pos) {
		BlockState there = hole.level.getBlockState(pos);
		if (there.is(ModRegistry.BLAST_GLOW)) {
			if (there.getValue(BlastGlowBlock.LEVEL) != BlastGlowBlock.START_LEVEL) hole.level.setBlock(pos, glow, 2);
			hole.lights.add(pos.immutable());
		} else if (there.isAir() && hole.level.mayInteract(hole.owner, pos)) {
			hole.level.setBlock(pos, glow, 3);
			hole.lights.add(pos.immutable());
		}
	}

	/** The end: a bang that throws what's still near outward, and the caught items dropped underneath. */
	private static void collapse(Hole hole) {
		ServerLevel level = hole.level;
		Vec3 c = hole.center;
		clearDebris(hole);
		for (BlockPos light : hole.lights) {
			if (level.getBlockState(light).is(ModRegistry.BLAST_GLOW)) level.setBlock(light, Blocks.AIR.defaultBlockState(), 3);
		}
		hole.lights.clear();
		double reach = pullRadius(hole.size) * 0.6;
		AABB area = new AABB(c, c).inflate(reach);
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, area, e -> pulls(hole, e))) {
			Vec3 out = e.getBoundingBox().getCenter().subtract(c);
			double dist = out.length();
			if (dist > reach) continue;
			out = dist < 1.0e-4 ? new Vec3(0, 1, 0) : out.scale(1 / dist);
			double push = 1.4 * (1 - dist / reach) + 0.4;
			e.setDeltaMovement(out.x * push, 0.35 + Math.max(0, out.y) * push * 0.5, out.z * push);
			e.hurtServer(level, level.damageSources().indirectMagic(hole.owner, hole.owner), crushDamage(hole.size) * 0.6f);
			RingPowers.syncVelocity(e);
		}
		for (Entity e : hole.caught) {
			if (!e.isAlive() || e.level() != level) continue;
			RandomSource r = level.getRandom();
			e.setPos(c.x + (r.nextDouble() - 0.5) * 0.6, c.y - 0.3, c.z + (r.nextDouble() - 0.5) * 0.6);
			e.setDeltaMovement((r.nextDouble() - 0.5) * 0.1, -0.1, (r.nextDouble() - 0.5) * 0.1);
			RingPowers.syncVelocity(e);
		}
		level.playSound(null, c.x, c.y, c.z, SoundEvents.WARDEN_SONIC_BOOM, SoundSource.PLAYERS, 1.2f, 1.4f);
		level.playSound(null, c.x, c.y, c.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 2.0f, 0.5f);
	}

	private static void clearDebris(Hole hole) {
		for (FallingBlockEntity block : hole.debris) {
			if (block.isAlive()) {
				hole.level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, block.getBlockState()),
						block.getX(), block.getY() + 0.5, block.getZ(), 6, 0.3, 0.3, 0.3, 0.05);
				block.discard();
			}
		}
		hole.debris.clear();
	}
}
