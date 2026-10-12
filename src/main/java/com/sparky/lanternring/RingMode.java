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
	DELUGE("deluge", 10, 40),
	// The Shield costs a quarter of the Dome to raise and half as much to hold (1 point every 2 ticks, see HeldConstructs).
	SHIELD("shield", 10, 10),
	// Opening a pair of portals to the exit costs 4% (8% to another dimension, see PortalGun); setting the exit is free.
	PORTAL("portal", 40, 0),
	// Summoning the Loot Golem costs 10%; it then works for RingTuning.GOLEM_LIFETIME (see LootGolems).
	GOLEM("golem", 100, 0),
	// The Black Hole costs 5%, 10% or 20% of a full ring by size (see BlackHoles.cost); this is the smallest.
	BLACK_HOLE("black_hole", 50, 0),
	// Builds cost 1% to 75% of a full ring by block count (see Builds.cost); this is the smallest.
	BUILD("build", 10, 0),
	// Army allies cost 15% to 25% of a full ring each (see ConstructArmy.Type); this is the biggest.
	ARMY("army", 250, 20),
	// The Red Lantern's Flame Ring costs 10% of a full ring (see FlameRings).
	INFERNO("inferno", 100, 0),
	// The Violet Lantern's Mind Link costs 1% plus 2% for each mob it links (see MindLinks).
	MIND_LINK("mind_link", 10, 0),
	// The Orange Lantern's powers of avarice (see Avarice): Hoard pulls in all loot nearby (each stack
	// pays 0.5% back), Steal takes what a mob holds or wears, Avarice calls up copies of slain mobs.
	HOARD("hoard", 30, 0),
	STEAL("steal", 40, 0),
	AVARICE("avarice", 150, 0),
	// The Blue Lantern's powers (see Hope): Renew heals and regrows everything around you (6%),
	RENEW("renew", 60, 0),
	// Restore brings the last villager or pet that died near you back to life (15%),
	RESTORE("restore", 150, 0),
	// Villager Spark calls blue builder villagers who build a house and grow a village (12%),
	SPARK("spark", 120, 0),
	// and the Hope Golem is a powerful blue iron golem (20%).
	HOPE_GOLEM("hope_golem", 200, 0);

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
