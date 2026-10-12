package com.sparky.lanternring;

import com.sparky.lanternring.block.LightConstructBlock;
import com.sparky.lanternring.item.PowerRingItem;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
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
 * Constructs that exist only while the bearer holds right-click: the 7x7 jade WALL and the DOME
 * shield. Each tick the construct is rebuilt where the player is looking; blocks it no longer
 * covers vanish.
 */
public final class HeldConstructs {
	/** How often a held block checks that it is still being held. */
	public static final int CHECK_TICKS = 10;

	private static final int WALL_HALF = 3;
	private static final double WALL_DISTANCE = 3.0;
	private static final double DOME_RADIUS = 4.5;
	/** cos of the cap's half-angle; 0.4 makes the cap about 30% of a full sphere. */
	private static final double DOME_COS = 0.4;
	private static final float DEBRIS_CHANCE = 0.3f;

	private static final class Held {
		ServerLevel level;
		RingMode mode;
		final Set<BlockPos> blocks = new HashSet<>();
		long lastTick;
	}

	private static final Map<UUID, Held> HELD = new HashMap<>();

	private HeldConstructs() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(HeldConstructs::cleanup);
	}

	public static boolean isHeldMode(RingMode mode) {
		return mode == RingMode.WALL || mode == RingMode.DOME;
	}

	public static boolean isLive(ServerLevel level, BlockPos pos) {
		for (Held held : HELD.values()) {
			if (held.level == level && held.blocks.contains(pos)) return true;
		}
		return false;
	}

	/** Called every tick while the ring is held in a WALL or DOME mode. */
	public static void tick(ServerPlayer player, RingMode mode, ItemStack ring) {
		ServerLevel level = player.level();
		Held held = HELD.computeIfAbsent(player.getUUID(), id -> new Held());
		if (held.level != null && (held.level != level || held.mode != mode)) clear(held);
		held.level = level;
		held.mode = mode;
		held.lastTick = level.getGameTime();

		Map<BlockPos, BlockState> want = mode == RingMode.WALL ? wall(player) : dome(player, level);
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

		player.resetFallDistance();
		if (!player.isCreative()) {
			int drain = mode == RingMode.DOME ? 1 : (player.tickCount % 2 == 0 ? 1 : 0);
			PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - drain);
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

	/** Drop constructs whose bearer stopped holding them without a release (item switched, logged out...). */
	private static void cleanup(MinecraftServer server) {
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

	/** A 7x7 flat shield facing wherever the player looks, 3 blocks out. Its outline glows. */
	private static Map<BlockPos, BlockState> wall(Player player) {
		Vec3 look = player.getLookAngle();
		Vec3 right = look.cross(new Vec3(0, 1, 0));
		if (right.lengthSqr() < 1.0e-4) {
			Direction side = player.getDirection().getClockWise();
			right = new Vec3(side.getStepX(), 0, side.getStepZ());
		}
		right = right.normalize();
		Vec3 up = right.cross(look).normalize();
		Vec3 center = player.getEyePosition().add(look.scale(WALL_DISTANCE));
		BlockState inner = ModRegistry.LIGHT_CONSTRUCT.defaultBlockState().setValue(LightConstructBlock.HELD, true);
		BlockState rim = inner.setValue(LightConstructBlock.RIM, true);
		Map<BlockPos, BlockState> out = new HashMap<>();
		// Half-block steps so a tilted wall has no gaps.
		for (double a = -WALL_HALF; a <= WALL_HALF; a += 0.5) {
			for (double b = -WALL_HALF; b <= WALL_HALF; b += 0.5) {
				BlockPos pos = BlockPos.containing(center.add(right.scale(a)).add(up.scale(b)));
				boolean edge = Math.abs(a) > WALL_HALF - 0.75 || Math.abs(b) > WALL_HALF - 0.75;
				if (edge) out.put(pos, rim);
				else out.putIfAbsent(pos, inner);
			}
		}
		return out;
	}

	/**
	 * A curved shell, about 30% of a sphere, centred on the player and facing where they look. It
	 * breaks every block it touches except unbreakable ones (bedrock), but never digs below the
	 * player's feet, so looking down it becomes a bowl to stand in, even over lava.
	 */
	private static Map<BlockPos, BlockState> dome(ServerPlayer player, ServerLevel level) {
		Vec3 look = player.getLookAngle();
		Vec3 center = player.position().add(0, 1.0, 0);
		int feetY = player.blockPosition().getY();
		BlockState brick = ModRegistry.CONSTRUCT_BRICK.defaultBlockState();
		Map<BlockPos, BlockState> shell = new HashMap<>();
		BlockPos c = BlockPos.containing(center);
		int r = (int) Math.ceil(DOME_RADIUS + 2);
		for (int dx = -r; dx <= r; dx++) {
			for (int dy = -r; dy <= r; dy++) {
				for (int dz = -r; dz <= r; dz++) {
					BlockPos pos = c.offset(dx, dy, dz);
					Vec3 v = Vec3.atCenterOf(pos).subtract(center);
					double d = v.length();
					if (d < DOME_RADIUS - 0.5 || d > DOME_RADIUS + 1.5) continue;
					double facing = v.dot(look) / d;
					if (facing < DOME_COS - 0.05) continue;
					// Break what the shell touches, straight on or diagonally, at or above foot level.
					if (pos.getY() >= feetY) breakBlock(level, player, pos);
					if (d <= DOME_RADIUS + 0.5 && facing >= DOME_COS) shell.put(pos, brick);
				}
			}
		}
		return shell;
	}

	private static void breakBlock(ServerLevel level, Player player, BlockPos pos) {
		BlockState state = level.getBlockState(pos);
		if (state.isAir() || state.is(ModRegistry.CONSTRUCT_BRICK) || state.is(ModRegistry.LIGHT_CONSTRUCT)
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
