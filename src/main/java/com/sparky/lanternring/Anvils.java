package com.sparky.lanternring;

import com.mojang.math.Transformation;
import com.sparky.lanternring.block.BlastGlowBlock;
import com.sparky.lanternring.block.LightConstructBlock;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.AnvilInputPayload;
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
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
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
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * ANVIL: hold right-click and a glowing anvil-shaped marker slides along the ground under your
 * cursor. Let go and a big hard-light construct is built block by block about 10 blocks above the
 * ground there, glowing bright, then cools to clear jade while it drops: at level 1 an anvil, at
 * level 2 a mining drill bit point first, at level 3 a ship's anchor crown first (AnvilShape). It
 * falls with gravity, and where it lands it smashes a crater shaped for it, nearest blocks first,
 * flinging some of them out as real falling blocks. It sinks into its crater, rests a while, then fades.
 *
 * <p>While it moves the anvil is a set of block displays the client glides smoothly between ticks,
 * so it falls at its real speed instead of hopping a block at a time. Once it has settled in its
 * finished crater it turns back into solid blocks.
 */
public final class Anvils {
	/** How far ahead the marker can be. */
	private static final double RANGE = 64;
	/** How high above the average ground around the marker the anvil's base is built (at least 9 clear blocks below it). */
	private static final int HEIGHT = 10;
	/** Crater radius in blocks. */
	private static final double CRATER_RADIUS = 6.5;
	/** Share of crater blocks thrown out as falling blocks, and at most how many per crater. */
	private static final float EJECTA_CHANCE = 0.12f;
	/** At 1x; bigger craters throw out more. */
	private static final int EJECTA_MAX = 60;
	private static final float IMPACT_DAMAGE = 24f;
	/** Ticks the anvil hangs after it's built before it drops. */
	private static final int HANG_TICKS = 6;
	/** Vanilla falling-block gravity and drag. */
	private static final double GRAVITY = 0.08;
	private static final double DRAG = 0.98;
	/**
	 * However it goes, a drop is gone this long after it's built (plus its rest time): a backstop
	 * so nothing can leave an anvil hanging in the world for good.
	 */
	private static final int MAX_DROP_TICKS = 600;
	/** How bright the marker's light is (blast glow levels go to 15). */
	private static final int MARKER_LIGHT = 8;

	/** Where a bearer is aiming while they hold left-click. */
	private static final class Aim {
		ServerLevel level;
		int size = 1;
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
		/**
		 * Set when this block is the low corner of one of the shape's body boxes (AnvilShape.bodies):
		 * its size {x, y, z}. It gets the moving display that covers that box.
		 */
		int[] box;
		/** Part of the tank's drill, which turns about its axis while it falls. */
		boolean spin;

		Cell(int dx, int dy, int dz) {
			this.dx = dx;
			this.dy = dy;
			this.dz = dz;
		}
	}

	private static final class Drop {
		final ServerLevel level;
		final Player owner;
		final int size;
		final AnvilShape shape;
		/** The shape's long side runs along world x (the bearer faced north or south). */
		boolean alongX;
		final List<Cell> cells = new ArrayList<>();
		/** Blocks of this anvil currently in the world. */
		final Set<BlockPos> placed = new HashSet<>();
		/** True while the anvil is solid blocks; false while it is moving as block displays. */
		boolean solid = true;
		BlockPos origin;
		double y;
		double speed;
		/**
		 * Above 0 the big levels plough through their crater at this steady speed (blocks a tick,
		 * 15% under the speed they hit at) instead of settling into it as it's dug: the tank bores
		 * down, the ship tears straight to the bottom.
		 */
		double plough;
		/** The tank's drill turn, in radians. */
		float spin;
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

		Drop(ServerLevel level, Player owner, BlockPos origin, int size) {
			this.level = level;
			this.owner = owner;
			this.size = size;
			this.shape = AnvilShape.of(size);
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
		ServerPlayNetworking.registerGlobalReceiver(AnvilInputPayload.TYPE, (payload, context) -> input(context.player(), payload.action()));
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			// The moving bodies are entities: don't let them be saved with the world.
			for (Drop drop : DROPS) discardBodies(drop);
			AIMS.clear();
			DROPS.clear();
			NO_CHARGE_NOTE.clear();
		});
	}

	public static boolean isLive(ServerLevel level, BlockPos pos) {
		for (Drop drop : DROPS) {
			if (drop.level == level && drop.placed.contains(pos)) return true;
		}
		return false;
	}

	// ---- sizes ----------------------------------------------------------------------------

	/**
	 * The levels a left-click while holding right-click cycles through: 1 the anvil, 3 the drill
	 * bit, 5 the anchor (see AnvilShape; the numbers are kept from when they were anvil sizes).
	 */
	public static final int[] SIZES = {1, 3, 5, 7};

	public static int size(ItemStack ring) {
		int size = ring.getOrDefault(ModComponents.ANVIL_SIZE, 1);
		for (int s : SIZES) if (s == size) return size;
		return 1;
	}

	/** Charge per drop: 0.5% anvil, 1% drill tank, 1.5% anchor, 2.5% ship (of PowerRingItem.MAX_CHARGE = 1000). */
	public static int cost(int size) {
		return size >= 7 ? 25 : size >= 5 ? 15 : size >= 3 ? 10 : 5;
	}

	/** Left-click while holding right-click in Anvil mode: the next size, with a note of what it costs. */
	public static void cycleSize(ServerPlayer player, ItemStack ring) {
		int size = size(ring);
		int next = SIZES[0];
		for (int i = 0; i < SIZES.length; i++) if (SIZES[i] == size) next = SIZES[(i + 1) % SIZES.length];
		ring.set(ModComponents.ANVIL_SIZE, next);
		player.sendOverlayMessage(sizeText(next).copy().withStyle(ChatFormatting.GREEN));
		player.level().playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1f, 1.6f - 0.15f * next);
	}

	public static Component sizeText(int size) {
		int level = 1;
		for (int i = 0; i < SIZES.length; i++) if (SIZES[i] == size) level = i + 1;
		return Component.translatable("message.lanternring.anvil_size", level,
				Component.translatable(AnvilShape.of(size).key()), String.valueOf(cost(size) / 10.0));
	}

	// ---- aiming ---------------------------------------------------------------------------

	/** Left-click from the bearer's client while aiming: see AnvilInputPayload. */
	private static void input(ServerPlayer player, int action) {
		ItemStack ring = player.getMainHandItem();
		if (action == AnvilInputPayload.ARMY_CYCLE) {
			if (ring.getItem() instanceof PowerRingItem && PowerRingItem.getMode(ring) == RingMode.ARMY && player.isUsingItem()
					&& !LanternCharge.started(player)) ConstructArmy.cycle(player, ring);
			return;
		}
		if (action == AnvilInputPayload.BLAST_CYCLE) {
			BlastDrills.cycleLevel(player);
			return;
		}
		if (action == AnvilInputPayload.DELUGE_CYCLE) {
			if (ring.getItem() instanceof PowerRingItem && PowerRingItem.getMode(ring) == RingMode.DELUGE
					&& player.isUsingItem() && !LanternCharge.started(player)) {
				Deluges.cycleLevel(player, ring);
			}
			return;
		}
		if (action == AnvilInputPayload.BLACK_HOLE_CYCLE) {
			if (ring.getItem() instanceof PowerRingItem && PowerRingItem.getMode(ring) == RingMode.BLACK_HOLE
					&& player.isUsingItem() && !LanternCharge.started(player)) {
				BlackHoles.cycleSize(player, ring);
			}
			return;
		}
		boolean buildRing = ring.getItem() instanceof PowerRingItem && PowerRingItem.getMode(ring) == RingMode.BUILD;
		if (action == AnvilInputPayload.BUILD_SHAPE && buildRing && player.isUsingItem() && !LanternCharge.started(player)) {
			Builds.cycleShape(player, ring);
			return;
		}
		if ((action == AnvilInputPayload.BUILD_NEXT || action == AnvilInputPayload.BUILD_PREV) && buildRing) {
			Builds.step(player, action == AnvilInputPayload.BUILD_NEXT ? 1 : -1);
			return;
		}
		boolean anvilRing = ring.getItem() instanceof PowerRingItem && PowerRingItem.getMode(ring) == RingMode.ANVIL;
		if (action == AnvilInputPayload.CYCLE && anvilRing && player.isUsingItem() && !LanternCharge.started(player)) {
			cycleSize(player, ring);
		}
	}

	/** Every tick right-click is held in Anvil mode (from PowerRingItem.onUseTick): moves the marker. */
	public static void aimTick(ServerPlayer player, ItemStack ring) {
		if (!AIMS.containsKey(player.getUUID())) {
			// A new aim: only with the charge for this size, and not during the cooldown.
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
		aim(player, size(ring));
	}

	private static final Map<UUID, Long> NO_CHARGE_NOTE = new HashMap<>();

	/** Moves the marker and its light; called every tick left-click is held in ANVIL mode. */
	public static void aim(ServerPlayer player, int size) {
		ServerLevel level = player.level();
		Aim aim = AIMS.computeIfAbsent(player.getUUID(), id -> new Aim());
		aim.size = size;
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
			// How far "to" is from "from" tells the client the size to trace.
			RingFx.send(level, Kind.ANVIL_MARK, at, at.add(aim.facing.getStepX() * size, 0, aim.facing.getStepZ() * size));
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
	public static BlockPos findMark(ServerLevel level, Player player) {
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

	/** Right-click let go: drops an anvil where the marker is, and pays for it. */
	public static void release(ServerPlayer player, ItemStack ring) {
		Aim aim = AIMS.remove(player.getUUID());
		if (aim == null) return;
		clearLight(aim);
		if (aim.mark == null || aim.level != player.level()) return;
		int cost = cost(aim.size);
		if (!player.isCreative()) {
			if (PowerRingItem.getCharge(ring) < cost) return;
			PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - cost);
		}
		drop(aim.level, player, aim.mark, aim.facing, aim.size);
		player.getCooldowns().addCooldown(ring, RingTuning.cooldownTicks(RingMode.ANVIL));
		player.sendOverlayMessage(PowerRingItem.chargeText(ring));
	}

	/** Stopped aiming without letting go on purpose (switched items or modes...): no anvil. */
	public static void cancel(Player player) {
		Aim aim = AIMS.remove(player.getUUID());
		if (aim != null) clearLight(aim);
	}

	// ---- the drop ---------------------------------------------------------------------------

	private static void drop(ServerLevel level, Player owner, BlockPos mark, Direction facing, int size) {
		// Every size is built at the same height: the same clear drop under its base, however tall it is.
		BlockPos origin = new BlockPos(mark.getX(), averageGround(level, mark, size) + HEIGHT, mark.getZ());
		Drop drop = new Drop(level, owner, origin, size);
		long now = level.getGameTime();
		// Bigger shapes take longer to build: x1, x1.75, x2.5 and x3.5 the Durations value.
		int buildTicks = Math.max(1, Math.round(RingTuning.ANVIL_BUILD.ticks() * buildScale(size)));
		// Build bottom to top, with a little shuffle within each layer so it looks assembled.
		List<Cell> order = new ArrayList<>();
		AnvilShape shape = drop.shape;
		// The long side faces the bearer: across their view.
		boolean alongX = facing.getAxis() == Direction.Axis.Z;
		drop.alongX = alongX;
		Map<Long, Cell> byPos = new HashMap<>();
		for (int[] b : shape.blocks) {
			Cell c = alongX ? new Cell(b[0], b[1], b[2]) : new Cell(b[2], b[1], b[0]);
			order.add(c);
			byPos.put(BlockPos.asLong(c.dx, c.dy, c.dz), c);
		}
		for (int[] b : shape.bodies) {
			Cell c = byPos.get(alongX ? BlockPos.asLong(b[0], b[1], b[2]) : BlockPos.asLong(b[2], b[1], b[0]));
			if (c != null) c.box = alongX ? new int[] {b[3], b[4], b[5]} : new int[] {b[5], b[4], b[3]};
			if (c != null && shape == AnvilShape.TANK && b[1] <= AnvilShape.SPIN_TOP) c.spin = true;
		}
		// Each cell draws its shuffle once: a comparator that rolls new numbers breaks the sort.
		Map<Cell, Double> layer = new HashMap<>();
		for (Cell c : order) layer.put(c, c.dy + level.getRandom().nextFloat() * 0.9 * size);
		order.sort(Comparator.comparingDouble(layer::get));
		for (int i = 0; i < order.size(); i++) {
			Cell c = order.get(i);
			c.buildAt = now + (long) i * buildTicks / order.size();
		}
		drop.cells.addAll(order);
		// Under a ceiling or an overhang (the Nether...), build it lower down where it fits, but no
		// lower than the ground under the marker.
		while (drop.origin.getY() > mark.getY() && blocked(level, drop, drop.origin)) {
			drop.origin = drop.origin.below();
		}
		drop.y = drop.origin.getY();
		drop.buildEnd = now + buildTicks;
		int glowTicks = RingTuning.ANVIL_GLOW.ticks();
		for (Cell c : drop.cells) c.dimAt = drop.buildEnd + level.getRandom().nextInt(glowTicks + 1);
		DROPS.add(drop);
		RingFx.send(level, Kind.CONSTRUCT, RingPowers.handPos(owner), Vec3.atCenterOf(drop.origin.above(2)));
		level.playSound(null, drop.origin, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 2.0f, 0.8f);
	}

	/** How much longer than the anvil each level takes to build: 1, 1.75, 2.5, 3.5. */
	private static float buildScale(int size) {
		return size >= 7 ? 3.5f : 1 + (size - 1) * 0.375f;
	}

	/** Mean ground height (top of the ground) in a patch around the marker: 7x7 at 1x, wider for bigger anvils. */
	private static int averageGround(ServerLevel level, BlockPos mark, int size) {
		int total = 0;
		int n = 0;
		int reach = 3 * size;
		for (int x = -reach; x <= reach; x++) {
			for (int z = -reach; z <= reach; z++) {
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
			if (aim.level == null || aim.level.getGameTime() - aim.lastTick > 5) {
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

		if (drop.solid && drop.crater == null && !canMoveDown(drop)) {
			// Built resting on something (wedged against a cliff or still under an overhang): it
			// smashes its crater right there instead of hanging forever, and sinks into it.
			impact(drop);
			drop.restingSince = now;
		}
		if (drop.solid && canMoveDown(drop)) loosen(drop);
		if (!drop.solid) {
			boolean landed = fall(drop, now);
			if (landed && drop.crater != null && drop.craterIndex >= drop.crater.size()) solidify(drop);
		}
		dig(drop);
		rest(drop, now);
		if (now >= drop.expires || now >= drop.buildEnd + MAX_DROP_TICKS + RingTuning.ANVIL_LIFETIME.ticks()) {
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
		// Ploughing: a steady speed to the bottom, no gravity pulling it faster through the ground.
		if (drop.plough > 0 && drop.crater != null) drop.speed = drop.plough;
		double target = drop.y - drop.speed;
		boolean landed = false;
		while (Mth.floor(target) < drop.origin.getY()) {
			if (!canMoveDown(drop)) {
				// Landed. The first landing makes the crater; after that it just rests.
				if (drop.crater == null) {
					impact(drop);
					drop.plough = switch (drop.shape) {
						// Through the ground at the speed it hit, 15% slower, never faster.
						case TANK, SHIP -> Math.max(0.3, drop.speed * 0.85);
						default -> 0;
					};
				} else if (drop.craterIndex >= drop.crater.size()) {
					drop.plough = 0;
				}
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
		discardBodies(drop);
		drop.y = drop.origin.getY();
		for (Cell c : drop.cells) {
			if (c.box == null) continue;
			Display.BlockDisplay body = EntityTypes.BLOCK_DISPLAY.create(drop.level, EntitySpawnReason.TRIGGERED);
			if (body == null) continue;
			body.setBlockState(state(c));
			if (c.box[0] * c.box[1] * c.box[2] > 1) {
				// One stretched block per box keeps even the ship to a few hundred moving bodies.
				body.setTransformation(new Transformation(null, null, new Vector3f(c.box[0], c.box[1], c.box[2]), null));
			}
			// Hard light: as bright in the dark as the glowing blocks it stands in for.
			body.setBrightnessOverride(Brightness.FULL_BRIGHT);
			// The client glides it from one tick's spot to the next instead of jumping.
			body.setPosRotInterpolationDuration(1);
			c.body = body;
			place(drop, c);
			drop.level.addFreshEntity(body);
		}
		drop.solid = false;
		drop.restingSince = -1;
	}

	private static void moveBodies(Drop drop) {
		// The tank's drill turns about once a second while it moves.
		if (drop.shape == AnvilShape.TANK) drop.spin += (float) Math.toRadians(20);
		for (Cell c : drop.cells) {
			if (c.body != null) place(drop, c);
		}
	}

	/** Puts a cell's display where it is this tick; the tank's drill pieces turn about the drill's axis. */
	private static void place(Drop drop, Cell c) {
		Display.BlockDisplay body = c.body;
		if (!c.spin) {
			body.setPos(drop.origin.getX() + c.dx, drop.y + c.dy, drop.origin.getZ() + c.dz);
			return;
		}
		double ax = drop.alongX ? AnvilShape.SPIN_ALONG : AnvilShape.SPIN_ACROSS;
		double az = drop.alongX ? AnvilShape.SPIN_ACROSS : AnvilShape.SPIN_ALONG;
		// The display stands on the axis; its block is moved out to its spot and turned with the drill.
		body.setPos(drop.origin.getX() + ax, drop.y + c.dy, drop.origin.getZ() + az);
		Quaternionf turn = new Quaternionf().rotationY(drop.spin);
		Vector3f offset = turn.transform(new Vector3f((float) (c.dx - ax), 0, (float) (c.dz - az)));
		body.setTransformation(new Transformation(offset, turn, new Vector3f(c.box[0], c.box[1], c.box[2]), null));
		body.setTransformationInterpolationDelay(0);
		body.setTransformationInterpolationDuration(1);
	}

	/**
	 * Solid where it rests, but it keeps the bright look it fell with: the block displays stay
	 * and invisible barriers under them make it something you can stand on. (Swapping back to
	 * real construct blocks made it go dark once it settled.) A cell whose spot is taken is left out.
	 */
	private static void solidify(Drop drop) {
		BlockState barrier = Blocks.BARRIER.defaultBlockState();
		for (Cell c : drop.cells) {
			BlockPos pos = drop.at(c, drop.origin);
			if (drop.level.getBlockState(pos).canBeReplaced() && drop.level.isUnobstructed(barrier, pos, CollisionContext.empty())) {
				drop.level.setBlock(pos, barrier, 3);
				drop.placed.add(pos);
			}
		}
		drop.solid = true;
	}

	private static void discardBodies(Drop drop) {
		for (Cell c : drop.cells) {
			if (c.body != null) c.body.discard();
			c.body = null;
		}
	}

	/** Whether any of the drop's blocks would land in something solid with its base at {@code base}. */
	private static boolean blocked(ServerLevel level, Drop drop, BlockPos base) {
		for (Cell c : drop.cells) {
			if (!level.getBlockState(drop.at(c, base)).canBeReplaced()) return true;
		}
		return false;
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
		// What it falls onto first: the anvil's base, the drill's point, the anchor's crown and arms.
		double reach = switch (drop.shape) {
			case ANVIL -> 1.5;
			case TANK -> 2.5;
			case ANCHOR -> 6;
			case SHIP -> 4;
		};
		AABB box = new AABB(drop.origin).inflate(reach, 0, reach).expandTowards(0, drop.shape.height - 1, 0);
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
		List<BlockPos> crater = new ArrayList<>();
		BlockPos c = BlockPos.containing(center);
		// How far the blast reaches, for knocking things back and the ring of light.
		double r = switch (drop.shape) {
			case ANVIL -> CRATER_RADIUS;
			case TANK -> 10;
			case ANCHOR -> 17;
			case SHIP -> 18;
		};
		// The ship's shaft goes deeper than its blast reaches.
		int ri = (int) Math.ceil(drop.shape == AnvilShape.SHIP ? 34 : drop.shape == AnvilShape.TANK ? 14 : r);
		for (BlockPos pos : BlockPos.betweenClosed(c.offset(-ri, -ri, -ri), c.offset(ri, ri, ri))) {
			Vec3 d = Vec3.atCenterOf(pos).subtract(center);
			// Along and across the shape's long side.
			double along = drop.alongX ? d.x : d.z, across = drop.alongX ? d.z : d.x;
			if (inCrater(drop.shape, along, d.y, across)) crater.add(pos.immutable());
		}
		if (ploughs(drop.shape)) {
			// Ploughed out from the top down, just ahead of the falling shape (see dig).
			crater.sort(Comparator.<BlockPos>comparingInt(p -> -p.getY()).thenComparingDouble(p -> Vec3.atCenterOf(p).distanceToSqr(center)));
		} else {
			crater.sort(Comparator.comparingDouble(p -> Vec3.atCenterOf(p).distanceToSqr(center)));
		}
		drop.crater = crater;
		drop.craterCenter = center;
		// Bigger craters take a little longer to dig, like the build.
		int digTicks = Math.max(1, RingTuning.ANVIL_CRATER_TIME.ticks() * (drop.size + 1) / 2);
		drop.craterPerTick = Math.max(1, (int) Math.ceil(crater.size() / (double) digTicks));

		for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, new AABB(center, center).inflate(r + 2),
				e -> e != drop.owner && e.isAlive() && !e.isSpectator())) {
			Vec3 away = target.position().subtract(center);
			double d = away.length();
			if (d > r + 2) continue;
			away = away.multiply(1, 0, 1);
			away = away.lengthSqr() < 1.0e-4 ? new Vec3(1, 0, 0) : away.normalize();
			float falloff = (float) (1 - d / (r + 2));
			target.hurtServer(level, level.damageSources().indirectMagic(drop.owner, drop.owner), IMPACT_DAMAGE * (1 + (drop.size - 1) * 0.25f) * falloff + 2);
			target.setDeltaMovement(away.x * 1.4 * falloff, 0.5 + 0.6 * falloff, away.z * 1.4 * falloff);
			RingPowers.syncVelocity(target);
		}

		RingFx.send(level, Kind.ANVIL_IMPACT, center, center.add(r, 0, 0));
		level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, center.x, center.y, center.z, 1, 0, 0, 0, 0);
		level.playSound(null, center.x, center.y, center.z, SoundEvents.ANVIL_LAND, SoundSource.PLAYERS, 4.0f * drop.size, 0.5f);
		level.playSound(null, center.x, center.y, center.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 3.0f * drop.size, 0.7f - 0.05f * (drop.size - 1));
	}

	/**
	 * The crater each shape makes, around where it first touches down: the anvil smashes a round
	 * bowl, the drill tank bores a deep funnel it sinks drill first into (with a shallow bowl round
	 * the top), the anchor ploughs a long trench along its arms that its crown and arms bed into,
	 * and the ship plunges bow first down a 32-deep shaft, most of its length under the ground.
	 */
	private static boolean inCrater(AnvilShape shape, double along, double y, double across) {
		switch (shape) {
			case TANK -> {
				double flat = Math.hypot(along, across);
				// The funnel: 2 blocks wide at 13 deep, 9.4 at the surface.
				if (y >= -13 && y <= 4 && flat <= 2 + (y + 13) * 0.57) return true;
				return sq(flat / 9.5) + sq(y / 4) <= 1;
			}
			case ANCHOR -> {
				return sq(along / 17) + sq(y / 16) + sq(across / 7.5) <= 1;
			}
			case SHIP -> {
				// The ship's section: 12 wide, from its keel to its funnels and masts.
				double a = along / 8, c = (across - 3.5) / 11;
				if (y >= -32 && y <= 4 && a * a + c * c <= 1) return true;
				return sq(along / 15) + sq((across - 3) / 16) + sq(y / 6) <= 1;
			}
			default -> {
				return along * along + y * y + across * across <= CRATER_RADIUS * CRATER_RADIUS;
			}
		}
	}

	/** The tank and the ship plough through their craters rather than settling in. */
	private static boolean ploughs(AnvilShape shape) {
		return shape == AnvilShape.TANK || shape == AnvilShape.SHIP;
	}

	private static double sq(double v) {
		return v * v;
	}

	/** Breaks the next batch of crater blocks, nearest the impact first, so the bowl opens outwards fast. */
	private static void dig(Drop drop) {
		if (drop.crater == null) return;
		ServerLevel level = drop.level;
		Vec3 center = drop.craterCenter;
		int end = Math.min(drop.crater.size(), drop.craterIndex + drop.craterPerTick);
		if (ploughs(drop.shape)) {
			// Everything down to a few blocks under the shape goes now, so it never has to wait to sink.
			int ahead = drop.origin.getY() - 1 - (int) Math.ceil(drop.plough) * 2;
			while (end < drop.crater.size() && drop.crater.get(end).getY() >= ahead) end++;
		}
		for (; drop.craterIndex < end; drop.craterIndex++) {
			BlockPos pos = drop.crater.get(drop.craterIndex);
			if (drop.placed.contains(pos)) continue;
			BlockState state = level.getBlockState(pos);
			if (state.isAir() || isOurs(state) || state.getDestroySpeed(level, pos) < 0 || state.hasBlockEntity()
					|| !state.getFluidState().isEmpty() || !level.mayInteract(drop.owner, pos)) {
				continue;
			}
			if (drop.ejecta < EJECTA_MAX * drop.size && state.isCollisionShapeFullBlock(level, pos)
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
		BlockState state = level.getBlockState(pos);
		if (state.is(ModRegistry.LIGHT_CONSTRUCT) || state.is(Blocks.BARRIER)) {
			level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
		}
	}
}
