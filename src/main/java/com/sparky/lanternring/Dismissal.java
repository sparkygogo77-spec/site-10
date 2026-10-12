package com.sparky.lanternring;

import com.sparky.lanternring.net.DismissPayload;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * Letting go of a construct: instead of vanishing at once, its hard light comes apart from the
 * piece furthest from the bearer's ring to the nearest, over RingTuning.DISMISS_TIME, and each
 * client draws that light streaming back into the ring (DismissFx). Every construct the bearer lets
 * go of or that runs out (Dome, Wall, Bridge, Anvil...) ends through here; the Lasso's bubble does
 * the same on the client (LassoFx).
 */
public final class Dismissal {
	/** Beyond this the bearer can't see it come home: the construct just goes. */
	private static final double RANGE = 96;
	/** Pieces sent to clients at most; a bigger construct sends an even sample. */
	private static final int MAX_SENT = 1024;

	private record Key(ServerLevel level, BlockPos pos) {
	}

	/** A piece waiting its turn: it goes at {@code due} if it is still the block it was. */
	private record Piece(Block block, long due) {
	}

	private static final Map<Key, Piece> PENDING = new HashMap<>();

	private Dismissal() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(Dismissal::tick);
	}

	/** True while this block is waiting to come apart (it must not vanish by itself first). */
	public static boolean isPending(ServerLevel level, BlockPos pos) {
		return !PENDING.isEmpty() && PENDING.containsKey(new Key(level, pos));
	}

	/** A construct being built again where a dismissed one is still coming apart keeps that block. */
	public static boolean reclaim(ServerLevel level, BlockPos pos) {
		return !PENDING.isEmpty() && PENDING.remove(new Key(level, pos)) != null;
	}

	/**
	 * Dismisses a construct's blocks into the bearer's ring. Only blocks that are still ours
	 * ({@code ours}) are taken; with no bearer nearby they go at once.
	 */
	public static void blocks(ServerLevel level, Entity bearer, Collection<BlockPos> blocks, java.util.function.Predicate<BlockState> ours) {
		List<BlockPos> list = new ArrayList<>();
		for (BlockPos pos : blocks) {
			if (ours.test(level.getBlockState(pos))) list.add(pos.immutable());
		}
		if (list.isEmpty()) return;
		int span = RingTuning.DISMISS_TIME.ticks();
		Vec3 ring = bearer == null || bearer.level() != level || bearer.isRemoved() ? null : bearer.getEyePosition();
		if (ring == null || span <= 0 || ring.distanceToSqr(Vec3.atCenterOf(list.getFirst())) > RANGE * RANGE) {
			for (BlockPos pos : list) level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
			return;
		}
		Map<BlockPos, Double> dist = new HashMap<>();
		for (BlockPos pos : list) dist.put(pos, Vec3.atCenterOf(pos).distanceTo(ring));
		list.sort(Comparator.comparingDouble((BlockPos p) -> dist.get(p)).reversed());
		double far = dist.get(list.getFirst()), near = dist.get(list.getLast());
		long now = level.getGameTime();
		Corps corps = Corps.GREEN;
		for (BlockPos pos : list) {
			BlockState state = level.getBlockState(pos);
			if (state.hasProperty(Corps.PROPERTY)) corps = state.getValue(Corps.PROPERTY);
			// The furthest piece goes first; the front sweeps back to the ring at an even speed.
			double f = far - near < 1e-3 ? 1 : (far - dist.get(pos)) / (far - near);
			PENDING.put(new Key(level, pos), new Piece(state.getBlock(), now + Math.round(f * span)));
		}
		// Only the glowing pieces send light home (not a hidden barrier).
		List<BlockPos> sent = new ArrayList<>();
		for (BlockPos pos : list) {
			if (level.getBlockState(pos).hasProperty(Corps.PROPERTY)) sent.add(pos);
		}
		if (sent.size() > MAX_SENT) {
			List<BlockPos> sample = new ArrayList<>(MAX_SENT);
			for (int i = 0; i < MAX_SENT; i++) sample.add(sent.get(i * sent.size() / MAX_SENT));
			sent = sample;
		}
		DismissPayload payload = new DismissPayload(bearer.getId(), corps, span, sent);
		for (ServerPlayer viewer : PlayerLookup.around(level, ring, RANGE)) {
			ServerPlayNetworking.send(viewer, payload);
		}
		level.playSound(null, ring.x, ring.y, ring.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 0.6f, 1.8f);
	}

	/** Takes away the pieces whose turn has come. */
	private static void tick(MinecraftServer server) {
		if (PENDING.isEmpty()) return;
		for (Iterator<Map.Entry<Key, Piece>> it = PENDING.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<Key, Piece> e = it.next();
			ServerLevel level = e.getKey().level;
			if (level.getGameTime() < e.getValue().due) continue;
			it.remove();
			BlockPos pos = e.getKey().pos;
			if (level.isLoaded(pos) && level.getBlockState(pos).is(e.getValue().block)) {
				level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
			}
		}
	}
}
