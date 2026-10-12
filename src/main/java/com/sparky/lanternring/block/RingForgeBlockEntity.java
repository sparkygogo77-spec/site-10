package com.sparky.lanternring.block;

import com.sparky.lanternring.ModRegistry;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** Holds no data; it is there so RingForgeRenderer can draw the forge's floating core, ports and emblem. */
public class RingForgeBlockEntity extends BlockEntity {
	public RingForgeBlockEntity(BlockPos pos, BlockState state) {
		super(ModRegistry.RING_FORGE_ENTITY, pos, state);
	}
}
