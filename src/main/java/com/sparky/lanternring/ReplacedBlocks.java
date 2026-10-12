package com.sparky.lanternring;

import java.util.HashMap;
import java.util.Map;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/**
 * What a construct stood in (lava, water, snow, grass), so it comes back when the construct goes.
 * Without this a Bridge across a lava lake left a trench: lava doesn't flow back by itself.
 */
public final class ReplacedBlocks {
	private record Key(ServerLevel level, BlockPos pos) {
	}

	private static final Map<Key, BlockState> REPLACED = new HashMap<>();

	private ReplacedBlocks() {
	}

	static void register() {
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> REPLACED.clear());
	}

	/** Call just before a construct is placed at {@code pos} over {@code was}. */
	public static void remember(ServerLevel level, BlockPos pos, BlockState was) {
		// A construct placed over another construct keeps what the first one replaced.
		if (was.is(ModRegistry.LIGHT_CONSTRUCT) || was.is(ModRegistry.CONSTRUCT_BRICK)) return;
		Key key = new Key(level, pos.immutable());
		if (was.isAir() || was.hasBlockEntity()) REPLACED.remove(key);
		else REPLACED.put(key, was);
	}

	/** Takes a construct away: what it replaced comes back, or air. */
	public static void restore(ServerLevel level, BlockPos pos) {
		BlockState was = REPLACED.remove(new Key(level, pos));
		level.setBlock(pos, was == null ? Blocks.AIR.defaultBlockState() : was, 3);
	}
}
