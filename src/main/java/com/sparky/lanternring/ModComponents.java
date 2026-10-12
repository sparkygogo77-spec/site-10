package com.sparky.lanternring;

import com.mojang.serialization.Codec;
import net.minecraft.component.ComponentType;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.util.dynamic.Codecs;

public final class ModComponents {
	/** Stored ring power, 0..PowerRingItem.MAX_CHARGE. */
	public static final ComponentType<Integer> CHARGE = Registry.register(Registries.DATA_COMPONENT_TYPE,
			LanternRing.id("charge"),
			ComponentType.<Integer>builder().codec(Codecs.NONNEGATIVE_INT).packetCodec(PacketCodecs.VAR_INT).build());
	/** Index into RingMode. */
	public static final ComponentType<Integer> MODE = Registry.register(Registries.DATA_COMPONENT_TYPE,
			LanternRing.id("mode"),
			ComponentType.<Integer>builder().codec(Codecs.NONNEGATIVE_INT).packetCodec(PacketCodecs.VAR_INT).build());
	/** Whether the bearer has switched ring flight on (flight key). */
	public static final ComponentType<Boolean> FLIGHT = Registry.register(Registries.DATA_COMPONENT_TYPE,
			LanternRing.id("flight"),
			ComponentType.<Boolean>builder().codec(Codec.BOOL).packetCodec(PacketCodecs.BOOL).build());

	static void init() {
	}

	private ModComponents() {
	}
}
