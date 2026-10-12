package com.sparky.lanternring;

import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;

/** Ambient block effects are drawn by the client in the style picked in the Ring Lab; it fills these in. */
public final class ClientHooks {
	public interface BlockAmbient {
		void animate(Level level, BlockPos pos, RandomSource random);
	}

	public static BlockAmbient batteryAmbient = (level, pos, random) -> { };
	public static BlockAmbient constructAmbient = (level, pos, random) -> { };

	private ClientHooks() {
	}
}
