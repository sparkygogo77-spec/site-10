package com.sparky.lanternring;

import net.fabricmc.fabric.api.particle.v1.FabricParticleTypes;
import net.minecraft.core.Registry;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.core.registries.BuiltInRegistries;

/** Glowing hard-light particles. How each one looks and moves is decided on the client. */
public final class ModParticles {
	/** A soft glowing speck that floats and fades. */
	public static final SimpleParticleType MOTE = register("glow_mote");
	/** A drip that clings, then falls and splashes, like crying obsidian. */
	public static final SimpleParticleType DRIP = register("glow_drip");
	/** A spinning square fragment of a construct. */
	public static final SimpleParticleType SHARD = register("glow_shard");
	/** A quick bright flash. */
	public static final SimpleParticleType SPARK = register("glow_spark");
	/** A clear pane of hard light; many of them overlap into one sheet (the Shockwave dome). */
	public static final SimpleParticleType PANE = register("glow_pane");

	/** A big, faint, soft disc behind lingering light, so it reads as a glow. */
	public static final SimpleParticleType HALO = register("glow_halo");

	private static SimpleParticleType register(String name) {
		return Registry.register(BuiltInRegistries.PARTICLE_TYPE, LanternRing.id(name), FabricParticleTypes.simple(true));
	}

	static void init() {
	}

	private ModParticles() {
	}
}
