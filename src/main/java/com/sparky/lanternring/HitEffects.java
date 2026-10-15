package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.CombatFxPayload.Kind;
import it.unimi.dsi.fastutil.ints.Int2LongMap;
import it.unimi.dsi.fastutil.ints.Int2LongOpenHashMap;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import java.util.function.Predicate;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.AttackBlockCallback;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * The hit effects J kept from Blender pass 815 (server side; CombatFx/HitFx draw them):
 * <ul>
 * <li>F1 construct shatter: a ring bearer punching hard light breaks the construct from the punch outward, each
 * block RingTuning.SHATTER_STEP later per block of distance, into construct pixels that fly out and fall;
 * <li>F3 outline flash: a creature a ring bearer hurts (punch or power) flashes a shell in the ring's corps colour,
 * gone by RingTuning.HIT_FLASH, with sparks off the hit and a 12 degree rock.
 * </ul>
 */
public final class HitEffects {
	/** How far from the punch, and how many blocks, one shatter takes at most. */
	public static final double SHATTER_REACH = 10;
	public static final int SHATTER_MAX = 400;
	/** A creature flashes at most this often (powers that hurt every tick would flash it non-stop). */
	private static final int FLASH_GAP = 4;

	private record Break(ServerLevel level, BlockPos pos, long at) {
	}

	private static final List<Break> BREAKS = new ArrayList<>();
	private static final Int2LongMap LAST_FLASH = new Int2LongOpenHashMap();
	private static long now;

	private HitEffects() {
	}

	static void register() {
		AttackBlockCallback.EVENT.register((player, level, hand, pos, direction) -> {
			BlockState state = level.getBlockState(pos);
			if (!isConstruct(state) || !hasRing(player) || player.isSpectator()) return InteractionResult.PASS;
			// The client only stops its own mining here; the server decides what breaks.
			if (level instanceof ServerLevel server && player instanceof ServerPlayer p) shatter(server, p, pos, direction);
			return InteractionResult.SUCCESS;
		});
		ServerLivingEntityEvents.AFTER_DAMAGE.register((entity, source, base, taken, blocked) -> {
			if (taken <= 0 || !(source.getEntity() instanceof ServerPlayer p) || p == entity || !hasRing(p)) return;
			if (!(entity.level() instanceof ServerLevel level)) return;
			if (LAST_FLASH.containsKey(entity.getId()) && now - LAST_FLASH.get(entity.getId()) < FLASH_GAP) return;
			LAST_FLASH.put(entity.getId(), now);
			Vec3 from = source.getSourcePosition() != null ? source.getSourcePosition() : p.getEyePosition();
			flash(level, p, entity, from);
		});
		ServerTickEvents.END_SERVER_TICK.register(HitEffects::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			BREAKS.clear();
			LAST_FLASH.clear();
		});
	}

	public static boolean isConstruct(BlockState state) {
		return state.is(ModRegistry.LIGHT_CONSTRUCT) || state.is(ModRegistry.CONSTRUCT_BRICK);
	}

	private static boolean hasRing(Player player) {
		return RingSlot.ring(player).getItem() instanceof PowerRingItem;
	}

	/** Where a hit on {@code target} from {@code from} lands: the point of its box nearest the attacker. */
	public static Vec3 hitPoint(Entity target, Vec3 from) {
		AABB box = target.getBoundingBox();
		return new Vec3(Math.clamp(from.x, box.minX, box.maxX), Math.clamp(from.y, box.minY, box.maxY), Math.clamp(from.z, box.minZ, box.maxZ));
	}

	/** F3: every client near target draws the outline flash, sparks and rock (from: where the hit came from). */
	public static void flash(ServerLevel level, Player bearer, LivingEntity target, Vec3 from) {
		ItemStack ring = RingSlot.ring(bearer);
		Corps before = Corps.enter(Corps.of(ring));
		try {
			CombatMoves.send(level, Kind.HIT_FLASH, hitPoint(target, from), from, 0f, 0, bearer, target.getId());
		} finally {
			Corps.restore(before);
		}
	}

	/** The point on the punched face: its middle. */
	public static Vec3 facePoint(BlockPos pos, Direction face) {
		return Vec3.atCenterOf(pos).add(face.getStepX() * 0.5, face.getStepY() * 0.5, face.getStepZ() * 0.5);
	}

	/**
	 * The construct blocks one punch at pos breaks, nearest the punch first: every construct block joined to it
	 * (faces, edges or corners) within SHATTER_REACH of the hit, up to SHATTER_MAX. Clients run it too, so both sides
	 * agree on what goes and when (the server also skips what {@code canBreak} rules out).
	 */
	public static List<BlockPos> shatterCells(BlockGetter level, BlockPos start, Vec3 hit, Predicate<BlockPos> canBreak) {
		List<BlockPos> out = new ArrayList<>();
		Set<BlockPos> seen = new HashSet<>();
		ArrayDeque<BlockPos> queue = new ArrayDeque<>();
		queue.add(start.immutable());
		seen.add(start.immutable());
		double reach = SHATTER_REACH * SHATTER_REACH;
		while (!queue.isEmpty() && out.size() < SHATTER_MAX) {
			BlockPos pos = queue.poll();
			if (!isConstruct(level.getBlockState(pos)) || !canBreak.test(pos)) continue;
			out.add(pos);
			for (int dx = -1; dx <= 1; dx++) {
				for (int dy = -1; dy <= 1; dy++) {
					for (int dz = -1; dz <= 1; dz++) {
						BlockPos next = pos.offset(dx, dy, dz);
						if (Vec3.atCenterOf(next).distanceToSqr(hit) > reach || !seen.add(next)) continue;
						queue.add(next);
					}
				}
			}
		}
		out.sort(Comparator.comparingDouble(p -> Vec3.atCenterOf(p).distanceTo(hit)));
		return out;
	}

	/** When the block at pos goes, in ticks after the punch: SHATTER_STEP per block from the hit (0.5 counts as touching). */
	public static int delay(BlockPos pos, Vec3 hit) {
		double d = Math.max(0, Vec3.atCenterOf(pos).distanceTo(hit) - 0.5);
		return (int) Math.round(d * RingTuning.SHATTER_STEP.seconds() * 20);
	}

	/** F1: the punched construct shatters from the hit outward. */
	public static int shatter(ServerLevel level, ServerPlayer player, BlockPos pos, Direction face) {
		if (!level.mayInteract(player, pos) || !HeldConstructs.shatterable(level, pos)) return 0;
		Vec3 hit = facePoint(pos, face);
		List<BlockPos> cells = shatterCells(level, pos, hit, p -> HeldConstructs.shatterable(level, p));
		if (cells.isEmpty()) return 0;
		Corps before = Corps.enter(Corps.of(level.getBlockState(pos)));
		try {
			CombatMoves.send(level, Kind.CONSTRUCT_SHATTER, hit, Vec3.atCenterOf(pos), 0f, face.ordinal(), player, -1);
		} finally {
			Corps.restore(before);
		}
		// Each goes the tick after its turn comes, so the effect is on every client before the blocks go.
		for (BlockPos p : cells) BREAKS.add(new Break(level, p, now + 1 + delay(p, hit)));
		level.playSound(null, hit.x, hit.y, hit.z, SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.PLAYERS, 1f, 0.8f);
		level.playSound(null, hit.x, hit.y, hit.z, SoundEvents.GLASS_BREAK, SoundSource.PLAYERS, 0.7f, 1.3f);
		return cells.size();
	}

	private static void tick(MinecraftServer server) {
		now++;
		for (Iterator<Break> it = BREAKS.iterator(); it.hasNext(); ) {
			Break b = it.next();
			if (now < b.at()) continue;
			it.remove();
			if (b.level().isLoaded(b.pos()) && isConstruct(b.level().getBlockState(b.pos()))) ReplacedBlocks.restore(b.level(), b.pos());
		}
		if (now % 200 == 0) LAST_FLASH.int2LongEntrySet().removeIf(e -> now - e.getLongValue() > 100);
	}

	/** Whether a shatter is still breaking blocks (for tests). */
	public static boolean shattering() {
		return !BREAKS.isEmpty();
	}
}
