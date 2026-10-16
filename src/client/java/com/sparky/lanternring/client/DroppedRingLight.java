package com.sparky.lanternring.client;

import java.util.HashSet;
import java.util.Set;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LightBlock;

/**
 * A dropped ring lights the ground round it (J, 2026-10-16), so it can be found in a dark cave: a
 * level-7 light block in the air where each nearby dropped ring lies, placed only in this client's
 * world as LanternLight does, and taken away when the ring is picked up or moves on.
 */
public final class DroppedRingLight {
	public static final int LEVEL = 7;
	private static final double RANGE = 48;
	private static final int MAX = 12;
	private static final Set<BlockPos> PLACED = new HashSet<>();
	private static ClientLevel placedIn;

	private DroppedRingLight() {
	}

	public static void tick(Minecraft mc) {
		ClientLevel level = mc.level;
		if (level != placedIn) {
			clear();
			placedIn = level;
		}
		if (level == null || mc.player == null) return;
		Set<BlockPos> want = new HashSet<>();
		for (ItemEntity item : level.getEntitiesOfClass(ItemEntity.class, mc.player.getBoundingBox().inflate(RANGE), DroppedRingRenderer::isRing)) {
			if (want.size() >= MAX) break;
			BlockPos at = BlockPos.containing(item.position().add(0, 0.25, 0));
			if (PLACED.contains(at) || level.getBlockState(at).isAir()) want.add(at);
		}
		for (BlockPos pos : PLACED) {
			if (!want.contains(pos) && level.getBlockState(pos).is(Blocks.LIGHT)) level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
		}
		for (BlockPos pos : want) {
			if (!PLACED.contains(pos)) level.setBlock(pos, Blocks.LIGHT.defaultBlockState().setValue(LightBlock.LEVEL, LEVEL), 3);
		}
		PLACED.clear();
		PLACED.addAll(want);
	}

	private static void clear() {
		if (placedIn != null && placedIn == Minecraft.getInstance().level) {
			for (BlockPos pos : PLACED) {
				if (placedIn.getBlockState(pos).is(Blocks.LIGHT)) placedIn.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
			}
		}
		PLACED.clear();
	}
}
