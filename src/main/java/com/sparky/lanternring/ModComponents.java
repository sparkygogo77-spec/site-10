package com.sparky.lanternring;

import com.mojang.serialization.Codec;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.util.ExtraCodecs;

public final class ModComponents {
	/** Stored ring power, 0..PowerRingItem.MAX_CHARGE. */
	public static final DataComponentType<Integer> CHARGE = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("charge"),
			DataComponentType.<Integer>builder().persistent(ExtraCodecs.NON_NEGATIVE_INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());
	/** Index into RingMode. */
	public static final DataComponentType<Integer> MODE = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("mode"),
			DataComponentType.<Integer>builder().persistent(ExtraCodecs.NON_NEGATIVE_INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());
	/** Whether the bearer has switched ring flight on (flight key). */
	public static final DataComponentType<Boolean> FLIGHT = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("flight"),
			DataComponentType.<Boolean>builder().persistent(Codec.BOOL).networkSynchronized(ByteBufCodecs.BOOL).build());

	static void init() {
	}

	private ModComponents() {
	}
}
