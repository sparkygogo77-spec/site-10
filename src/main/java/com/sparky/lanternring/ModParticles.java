package com.sparky.lanternring;

import java.util.EnumMap;
import java.util.HashMap;
import java.util.Map;
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

	/** The same particles for the other corps, drawn in their colour (red_glow_mote and so on). */
	private static final Map<Corps, Map<SimpleParticleType, SimpleParticleType>> CORPS = new EnumMap<>(Corps.class);

	static {
		for (Corps corps : Corps.values()) {
			if (corps == Corps.GREEN) continue;
			Map<SimpleParticleType, SimpleParticleType> map = new HashMap<>();
			map.put(MOTE, register(corps.getSerializedName() + "_glow_mote"));
			map.put(DRIP, register(corps.getSerializedName() + "_glow_drip"));
			map.put(SHARD, register(corps.getSerializedName() + "_glow_shard"));
			map.put(SPARK, register(corps.getSerializedName() + "_glow_spark"));
			map.put(PANE, register(corps.getSerializedName() + "_glow_pane"));
			CORPS.put(corps, map);
		}
	}

	/** {@code base} (MOTE, DRIP...) in the current corps' colour, for particles the server spawns. */
	public static SimpleParticleType of(SimpleParticleType base) {
		return of(base, Corps.current());
	}

	public static SimpleParticleType of(SimpleParticleType base, Corps corps) {
		Map<SimpleParticleType, SimpleParticleType> map = CORPS.get(corps);
		return map == null ? base : map.getOrDefault(base, base);
	}

	/** The corps whose colour a particle type is drawn in. */
	public static Corps corpsOf(SimpleParticleType type) {
		for (Map.Entry<Corps, Map<SimpleParticleType, SimpleParticleType>> e : CORPS.entrySet()) {
			if (e.getValue().containsValue(type)) return e.getKey();
		}
		return Corps.GREEN;
	}

	/** Every corps' version of {@code base}, green's own first. */
	public static Map<Corps, SimpleParticleType> all(SimpleParticleType base) {
		Map<Corps, SimpleParticleType> out = new EnumMap<>(Corps.class);
		for (Corps corps : Corps.values()) out.put(corps, of(base, corps));
		return out;
	}

	private static SimpleParticleType register(String name) {
		return Registry.register(BuiltInRegistries.PARTICLE_TYPE, LanternRing.id(name), FabricParticleTypes.simple(true));
	}

	static void init() {
	}

	private ModParticles() {
	}
}
