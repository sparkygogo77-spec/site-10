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

	/** The Blast's level on this ring: 1 (3x3 tunnel), 2 (5x5) or 3 (7x7); left-click while charging cycles it. */
	public static final DataComponentType<Integer> BLAST_LEVEL = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("blast_level"),
			DataComponentType.<Integer>builder().persistent(ExtraCodecs.POSITIVE_INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());

	/** The Anvil's size on this ring: 1, 3 or 5 times the base anvil (right-click in Anvil mode cycles it). */
	public static final DataComponentType<Integer> ANVIL_SIZE = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("anvil_size"),
			DataComponentType.<Integer>builder().persistent(ExtraCodecs.POSITIVE_INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());

	/** The Build mode's area shape on this ring: Builds.CIRCLE, SQUARE or PAINT (left-click while holding cycles it). */
	public static final DataComponentType<Integer> BUILD_SHAPE = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("build_shape"),
			DataComponentType.<Integer>builder().persistent(ExtraCodecs.NON_NEGATIVE_INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());

	static void init() {
	}

	private ModComponents() {
	}
}
