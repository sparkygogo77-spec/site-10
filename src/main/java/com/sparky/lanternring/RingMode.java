package com.sparky.lanternring;

import net.minecraft.text.Text;

public enum RingMode {
	BLAST("blast", 100, 40),
	BEAM("beam", 15, 8),
	WALL("wall", 40, 20),
	BRIDGE("bridge", 60, 30),
	PUSH("push", 35, 30),
	TETHER("tether", 20, 15);

	private final String key;
	/** Charge spent per use. */
	public final int cost;
	/** Ticks before the ring can be used again. */
	public final int cooldown;

	RingMode(String key, int cost, int cooldown) {
		this.key = key;
		this.cost = cost;
		this.cooldown = cooldown;
	}

	public Text displayName() {
		return Text.translatable("mode.lanternring." + key);
	}

	public Text description() {
		return Text.translatable("mode.lanternring." + key + ".desc");
	}

	public RingMode next() {
		return values()[(ordinal() + 1) % values().length];
	}

	public static RingMode byIndex(int index) {
		RingMode[] modes = values();
		return modes[Math.floorMod(index, modes.length)];
	}
}
