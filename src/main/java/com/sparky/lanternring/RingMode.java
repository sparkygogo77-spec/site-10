package com.sparky.lanternring;

import net.minecraft.network.chat.Component;

public enum RingMode {
	// The Blast is charged by holding: 0.5% to 1% of a full ring at level 1 (more at levels 2 and 3, see BlastDrills.cost).
	BLAST("blast", 10, 40),
	BEAM("beam", 10, 8),
	WALL("wall", 50, 20),
	DOME("dome", 40, 20),
	BRIDGE("bridge", 60, 30),
	PUSH("push", 35, 30),
	// The Lasso costs 0.1% of a full ring to catch with (and 0.1% a second to hold, see Lasso).
	TETHER("tether", 1, 15),
	// The Anvil's cost depends on its size (0.5%, 1% or 1.5% per anvil, see Anvils.cost); this is the smallest.
	ANVIL("anvil", 5, 40),
	// The Deluge costs 1%, 2% or 3% by level (see Deluges.cost); this is the smallest.
	DELUGE("deluge", 10, 40);

	private final String key;
	/** Charge spent per use. */
	public final int cost;
	/**
	 * The cooldown this mode used to have, in ticks. Cooldowns now default to none (J sets them per
	 * mode in the Durations menu); RingTuning only uses this to drop an old saved default.
	 */
	public final int cooldown;

	RingMode(String key, int cost, int cooldown) {
		this.key = key;
		this.cost = cost;
		this.cooldown = cooldown;
	}

	public Component displayName() {
		return Component.translatable("mode.lanternring." + key);
	}

	public Component description() {
		return Component.translatable("mode.lanternring." + key + ".desc");
	}

	public RingMode next() {
		return values()[(ordinal() + 1) % values().length];
	}

	public static RingMode byIndex(int index) {
		RingMode[] modes = values();
		return modes[Math.floorMod(index, modes.length)];
	}
}
