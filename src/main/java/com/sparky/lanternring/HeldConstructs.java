package com.sparky.lanternring;

import com.sparky.lanternring.block.BlastGlowBlock;
import com.sparky.lanternring.block.LightConstructBlock;
import com.sparky.lanternring.item.PowerRingItem;
import java.util.HashMap;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;

/**
 * Hard-light constructs that are tracked by the server: the DOME, which exists only while the
 * bearer holds right-click and is rebuilt each tick where they look (the SHIELD is held the same
 * way but has no blocks: clients draw it, see ShieldReflect), and the 9x9 WALL, which
 * stands for RingTuning.WALL_LIFETIME (30 seconds by default) after a click.
 */
public final class HeldConstructs {
	/** How often a held block checks that it is still being held. */
	public static final int CHECK_TICKS = 10;

	private static final int WALL_HALF = 4;
	private static final int WALL_DISTANCE = 3;
	private static final double DOME_RADIUS = 4.5;
	/** Extra radius, and how far the cap's edge spreads (as cos), once fully crouched. */
	private static final double DOME_CROUCH_RADIUS = 2.0;
	private static final double DOME_CROUCH_SPREAD = 0.45;
	/** How fast the dome grows or shrinks per tick when crouching starts or stops (0..1). */
	private static final double DOME_GROW_RATE = 0.1;
	/** cos of the cap's half-angle; 0.4 makes the cap about 30% of a full sphere. */
	private static final double DOME_COS = 0.4;
	private static final float DEBRIS_CHANCE = 0.3f;
	/** Holding the Shield drains 1 point every this many ticks (the Dome drains 1 a tick). */
	public static final int SHIELD_DRAIN_INTERVAL = 2;

	private static final class Held {
		ServerLevel level;
		RingMode mode;
		final Set<BlockPos> blocks = new HashSet<>();
		long lastTick;
		/** 0 = normal dome, 1 = fully expanded by crouching. */
		double spread;
	}

	private record Wall(ServerLevel level, Set<BlockPos> blocks, long expires) {
	}

	private static final Map<UUID, Held> HELD = new HashMap<>();
	private static final List<Wall> WALLS = new ArrayList<>();

	private HeldConstructs() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(HeldConstructs::cleanup);
	}

	public static boolean isHeldMode(RingMode mode) {
		return mode == RingMode.DOME || mode == RingMode.SHIELD;
	}

	public static boolean isLive(ServerLevel level, BlockPos pos) {
		for (Held held : HELD.values()) {
			if (held.level == level && held.blocks.contains(pos)) return true;
		}
		for (Wall wall : WALLS) {
			if (wall.level == level && wall.blocks.contains(pos)) return true;
		}
		return Anvils.isLive(level, pos) || Builds.isLive(level, pos) || CrystalPrisons.isLive(level, pos);
	}

	/** Called every tick while the ring is held in DOME or SHIELD mode. */
	public static void tick(ServerPlayer player, RingMode mode, ItemStack ring) {
		ServerLevel level = player.level();
		Held held = HELD.computeIfAbsent(player.getUUID(), id -> new Held());
		if (held.level != null && (held.level != level || held.mode != mode)) clear(held);
		held.level = level;
		held.mode = mode;
		held.lastTick = level.getGameTime();

		double target = player.isShiftKeyDown() ? 1 : 0;
		held.spread += Math.clamp(target - held.spread, -DOME_GROW_RATE, DOME_GROW_RATE);
		boolean shield = mode == RingMode.SHIELD;
		// The Shield is drawn by each client (RiotShields), so it places no blocks.
		Map<BlockPos, BlockState> want = shield ? Map.of() : dome(player, level, held.spread);
		Set<BlockPos> next = new HashSet<>();
		for (Map.Entry<BlockPos, BlockState> e : want.entrySet()) {
			BlockPos pos = e.getKey();
			BlockState current = level.getBlockState(pos);
			if (held.blocks.contains(pos) && current.is(e.getValue().getBlock())) {
				if (current != e.getValue()) level.setBlock(pos, e.getValue(), 2);
				next.add(pos);
			} else if (canFill(level, player, pos, current, e.getValue())) {
				level.setBlock(pos, e.getValue(), 3);
				next.add(pos);
			}
		}
		for (BlockPos pos : held.blocks) {
			if (!next.contains(pos)) removeIfOurs(level, pos);
		}
		held.blocks.clear();
		held.blocks.addAll(next);

		if (shield) ShieldReflect.tick(level, player);
		else player.resetFallDistance();
		if (!player.isCreative() && (!shield || level.getGameTime() % SHIELD_DRAIN_INTERVAL == 0)) {
			PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - 1);
			if (PowerRingItem.getCharge(ring) == 0) player.stopUsingItem();
		}
	}

	public static void release(Player player) {
		Held held = HELD.remove(player.getUUID());
		if (held != null) clear(held);
	}

	private static void clear(Held held) {
		for (BlockPos pos : held.blocks) removeIfOurs(held.level, pos);
		held.blocks.clear();
	}

	private static void removeIfOurs(ServerLevel level, BlockPos pos) {
		BlockState state = level.getBlockState(pos);
		if (state.is(ModRegistry.LIGHT_CONSTRUCT) || state.is(ModRegistry.CONSTRUCT_BRICK)) {
			level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
		}
	}

	/**
	 * Drop constructs whose bearer stopped holding them without a release (item switched, logged
	 * out...), and walls whose time is up.
	 */
	private static void cleanup(MinecraftServer server) {
		for (Iterator<Wall> it = WALLS.iterator(); it.hasNext(); ) {
			Wall wall = it.next();
			if (wall.level.getGameTime() < wall.expires) continue;
			it.remove();
			for (BlockPos pos : wall.blocks) {
				if (!isLive(wall.level, pos)) removeIfOurs(wall.level, pos);
			}
		}
		for (Iterator<Map.Entry<UUID, Held>> it = HELD.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<UUID, Held> e = it.next();
			Held held = e.getValue();
			if (held.level == null) {
				it.remove();
				continue;
			}
			ServerPlayer player = server.getPlayerList().getPlayer(e.getKey());
			boolean stillHolding = player != null && player.isUsingItem()
					&& player.getUseItem().getItem() instanceof PowerRingItem
					&& held.level.getGameTime() - held.lastTick <= 2;
			if (!stillHolding) {
				clear(held);
				it.remove();
			}
		}
	}

	private static boolean canFill(ServerLevel level, Player player, BlockPos pos, BlockState current, BlockState placing) {
		return current.canBeReplaced() && level.mayInteract(player, pos)
				&& level.isUnobstructed(placing, pos, CollisionContext.empty());
	}

	/**
	 * Puts up a flat, upright 9x9 wall of glowing construct bricks WALL_DISTANCE blocks in front of
	 * the player, square to the way they face, standing on the ground at their feet. It stays for
	 * RingTuning.WALL_LIFETIME; blocks already in the way are left alone.
	 *
	 * @return how many blocks were placed
	 */
	public static int placeWall(ServerLevel level, Player player) {
		Direction forward = player.getDirection();
		Direction right = forward.getClockWise();
		BlockPos base = player.blockPosition().relative(forward, WALL_DISTANCE);
		BlockState brick = Corps.state(ModRegistry.CONSTRUCT_BRICK);
		int top = 2 * WALL_HALF;
		Set<BlockPos> placed = new HashSet<>();
		// Register first so the blocks' own checks find the wall straight away.
		WALLS.add(new Wall(level, placed, level.getGameTime() + RingTuning.WALL_LIFETIME.ticks()));
		for (int across = -WALL_HALF; across <= WALL_HALF; across++) {
			for (int up = 0; up <= top; up++) {
				BlockPos pos = base.relative(right, across).above(up);
				if (!canFill(level, player, pos, level.getBlockState(pos), brick)) continue;
				placed.add(pos);
				level.setBlock(pos, brick, 3);
			}
		}
		if (placed.isEmpty()) WALLS.removeLast();
		return placed.size();
	}

	/**
	 * A curved shell of see-through hard light, about 30% of a sphere, centred on the player and facing where they look. It
	 * breaks every block it touches except unbreakable ones (bedrock), but never digs below the
	 * player's feet, so looking down it becomes a bowl to stand in, even over lava. Crouching
	 * ({@code spread} rising to 1) pushes it further out and spreads its edge wider.
	 */
	private static Map<BlockPos, BlockState> dome(ServerPlayer player, ServerLevel level, double spread) {
		double radius = DOME_RADIUS + DOME_CROUCH_RADIUS * spread;
		double cos = DOME_COS - DOME_CROUCH_SPREAD * spread;
		Vec3 look = player.getLookAngle();
		Vec3 center = player.position().add(0, 1.0, 0);
		int feetY = player.blockPosition().getY();
		BlockState inner = Corps.state(ModRegistry.LIGHT_CONSTRUCT).setValue(LightConstructBlock.HELD, true);
		BlockState rim = inner.setValue(LightConstructBlock.RIM, true);
		Map<BlockPos, BlockState> shell = new HashMap<>();
		BlockPos c = BlockPos.containing(center);
		int r = (int) Math.ceil(radius + 2);
		for (int dx = -r; dx <= r; dx++) {
			for (int dy = -r; dy <= r; dy++) {
				for (int dz = -r; dz <= r; dz++) {
					BlockPos pos = c.offset(dx, dy, dz);
					Vec3 v = Vec3.atCenterOf(pos).subtract(center);
					double d = v.length();
					if (d < radius - 0.5 || d > radius + 1.5) continue;
					double facing = v.dot(look) / d;
					if (facing < cos - 0.05) continue;
					// Break what the shell touches, straight on or diagonally, at or above foot level.
					if (pos.getY() >= feetY) breakBlock(level, player, pos);
					if (d <= radius + 0.5 && facing >= cos) {
						// The outer band of the cap glows like a wall's outline.
						shell.put(pos, facing < cos + 0.12 ? rim : inner);
					}
				}
			}
		}
		return shell;
	}

	private static void breakBlock(ServerLevel level, Player player, BlockPos pos) {
		BlockState state = level.getBlockState(pos);
		if (state.isAir() || state.is(ModRegistry.CONSTRUCT_BRICK) || state.is(ModRegistry.LIGHT_CONSTRUCT) || state.getBlock() instanceof BlastGlowBlock
				|| !state.getFluidState().isEmpty() && state.canBeReplaced()) {
			return;
		}
		if (state.getDestroySpeed(level, pos) < 0 || !level.mayInteract(player, pos)) return;
		level.destroyBlock(pos, false);
		debris(level, pos, state);
	}

	/** Block-matching crumbs for about 30% of destroyed blocks, so big digs stay light. */
	public static void debris(ServerLevel level, BlockPos pos, BlockState state) {
		if (level.getRandom().nextFloat() >= DEBRIS_CHANCE) return;
		level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, state),
				pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, 5, 0.3, 0.3, 0.3, 0.05);
	}
}
