package com.sparky.lanternring.designs;

import java.util.LinkedHashMap;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;

/**
 * One build's blocks in its own coordinates: x across, z front to back, y up. Layer y = 0 is the
 * ground layer (it replaces the flattened ground's top block); the front, with the door, is the
 * +z side, and Builds turns it to face the bearer.
 */
public final class Blueprint {
	public final Map<Long, BlockState> blocks = new LinkedHashMap<>();
	/** Footprint and height. */
	public int w, d, h;

	public Blueprint(int w, int d) {
		this.w = w;
		this.d = d;
	}

	public void set(int x, int y, int z, BlockState state) {
		if (x < 0 || z < 0 || x >= w || z >= d || y < 0) return;
		blocks.put(BlockPos.asLong(x, y, z), state);
		if (y + 1 > h) h = y + 1;
	}

	/** Air that clears whatever is there when it's built (an empty room inside a house). */
	public void clear(int x, int y, int z) {
		set(x, y, z, Blocks.AIR.defaultBlockState());
	}

	public BlockState get(int x, int y, int z) {
		return blocks.get(BlockPos.asLong(x, y, z));
	}

	public boolean has(int x, int y, int z) {
		BlockState s = get(x, y, z);
		return s != null && !s.isAir();
	}

	public void fill(int x0, int y0, int z0, int x1, int y1, int z1, BlockState state) {
		for (int x = Math.min(x0, x1); x <= Math.max(x0, x1); x++) {
			for (int y = Math.min(y0, y1); y <= Math.max(y0, y1); y++) {
				for (int z = Math.min(z0, z1); z <= Math.max(z0, z1); z++) set(x, y, z, state);
			}
		}
	}

	/** A one-thick box outline of walls (no floor or ceiling) from y0 to y1. */
	public void walls(int x0, int z0, int x1, int z1, int y0, int y1, BlockState state) {
		for (int y = y0; y <= y1; y++) {
			for (int x = x0; x <= x1; x++) {
				set(x, y, z0, state);
				set(x, y, z1, state);
			}
			for (int z = z0; z <= z1; z++) {
				set(x0, y, z, state);
				set(x1, y, z, state);
			}
		}
	}

	/** A door two blocks tall at (x, y, z), opening along facing (the way you walk in). */
	public void door(int x, int y, int z, BlockState door, Direction facing) {
		if (!door.hasProperty(BlockStateProperties.DOUBLE_BLOCK_HALF)) {
			clear(x, y, z);
			clear(x, y + 1, z);
			return;
		}
		BlockState lower = door.setValue(BlockStateProperties.HORIZONTAL_FACING, facing);
		set(x, y, z, lower);
		set(x, y + 1, z, lower.setValue(BlockStateProperties.DOUBLE_BLOCK_HALF,
				net.minecraft.world.level.block.state.properties.DoubleBlockHalf.UPPER));
	}

	public int count() {
		int n = 0;
		for (BlockState s : blocks.values()) if (!s.isAir()) n++;
		return n;
	}
}
