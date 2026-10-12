package com.sparky.lanternring;

import net.minecraft.network.chat.Component;

public enum RingMode {
	BLAST("blast", 100, 40),
	BEAM("beam", 10, 8),
	WALL("wall", 50, 20),
	DOME("dome", 40, 20),
	BRIDGE("bridge", 60, 30),
	PUSH("push", 35, 30),
	TETHER("tether", 20, 15);

	private final String key;
	/** Charge spent per use. */
	public final int cost;
	/** Default ticks before the ring can be used again; RingTuning holds the edited value. */
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
