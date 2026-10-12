package com.sparky.lanternring.infinity;

import com.sparky.lanternring.RingTuning;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

/** One thing a stone can do. A loose stone uses its first power (crouch for the second); the Gauntlet cycles through them all. */
public enum InfinityPower {
	SOUL_REVIVE(InfinityStone.SOUL, "soul_revive"),
	SOUL_GRAVES(InfinityStone.SOUL, "soul_graves"),
	TIME_REWIND(InfinityStone.TIME, "time_rewind"),
	TIME_FREEZE(InfinityStone.TIME, "time_freeze");

	public final InfinityStone stone;
	public final String key;

	InfinityPower(InfinityStone stone, String key) {
		this.stone = stone;
		this.key = key;
	}

	public Component displayName() {
		return Component.translatable("power.lanternring." + key).withStyle(stone.chat);
	}

	public Component description() {
		return Component.translatable("power.lanternring." + key + ".desc");
	}

	/** Ticks before the stone (or Gauntlet) can be used again after this power worked. */
	public int cooldown() {
		return switch (this) {
			case SOUL_REVIVE, SOUL_GRAVES -> RingTuning.SOUL_COOLDOWN.ticks();
			case TIME_REWIND, TIME_FREEZE -> RingTuning.TIME_COOLDOWN.ticks();
		};
	}

	/** Runs the power on the server; false when it had nothing to act on. */
	public boolean use(ServerLevel level, ServerPlayer player) {
		return switch (this) {
			case SOUL_REVIVE -> SoulStone.revive(level, player);
			case SOUL_GRAVES -> SoulStone.raiseGraves(level, player);
			case TIME_REWIND -> TimeStone.rewind(level, player);
			case TIME_FREEZE -> TimeStone.freeze(level, player);
		};
	}
}
