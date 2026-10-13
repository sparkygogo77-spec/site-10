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
	/** Hope boost: extra charge a Blue city's crown lantern gave a Green ring, spent before its own (see PowerRingItem.setCharge). */
	public static final DataComponentType<Integer> HOPE_RESERVE = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("hope_reserve"),
			DataComponentType.<Integer>builder().persistent(ExtraCodecs.NON_NEGATIVE_INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());
	/** Overcharge: extra charge past full from holding the lantern charge on (see LanternCharge), spent before the ring's own. */
	public static final DataComponentType<Integer> OVERCHARGE = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("overcharge"),
			DataComponentType.<Integer>builder().persistent(ExtraCodecs.NON_NEGATIVE_INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());
	/** How many of a Power Battery's charges overcharging has burnt out (0..LanternCharge.BATTERY_CHARGES). */
	public static final DataComponentType<Integer> BATTERY_BURNT = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("battery_burnt"),
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

	/** The Deluge's level on this ring: 0, 1 or 2 (left-click while aiming cycles it; see Deluges). */
	public static final DataComponentType<Integer> DELUGE_LEVEL = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("deluge_level"),
			DataComponentType.<Integer>builder().persistent(ExtraCodecs.NON_NEGATIVE_INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());
	/** The Yellow ring's fear (0 to 100): what its bearer has frightened and killed on their fear ground (see corps/FearNuke). */
	public static final DataComponentType<Integer> FEAR = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("fear"),
			DataComponentType.<Integer>builder().persistent(ExtraCodecs.NON_NEGATIVE_INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());
	/** Where this ring's Portal exit stands (see PortalGun); the Loot Golem stores loot in a chest beside it. */
	public static final DataComponentType<PortalExit> PORTAL_EXIT = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("portal_exit"),
			DataComponentType.<PortalExit>builder().persistent(PortalExit.CODEC).networkSynchronized(PortalExit.STREAM_CODEC).build());
	/** The Black Hole's size on this ring: 1, 2 or 3 (left-click while aiming cycles it). */
	public static final DataComponentType<Integer> BLACK_HOLE_SIZE = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("black_hole_size"),
			DataComponentType.<Integer>builder().persistent(ExtraCodecs.POSITIVE_INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());
	/** The Build mode's area shape on this ring: Builds.CIRCLE, SQUARE or PAINT (left-click while holding cycles it). */
	public static final DataComponentType<Integer> BUILD_SHAPE = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("build_shape"),
			DataComponentType.<Integer>builder().persistent(ExtraCodecs.NON_NEGATIVE_INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());
	/** Which construct Army mode summons on this ring: an index into ConstructArmy.Type. */
	public static final DataComponentType<Integer> ARMY_TYPE = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("army_type"),
			DataComponentType.<Integer>builder().persistent(ExtraCodecs.NON_NEGATIVE_INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());

	/** Which Lantern Corps a ring belongs to (green when missing); see Corps. */
	public static final DataComponentType<Corps> CORPS = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("corps"),
			DataComponentType.<Corps>builder().persistent(Corps.CODEC).networkSynchronized(Corps.STREAM_CODEC).build());

	/** Rounds left in a 1911's magazine (see item/Pistol1911Item). */
	public static final DataComponentType<Integer> ROUNDS = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("rounds"),
			DataComponentType.<Integer>builder().persistent(ExtraCodecs.NON_NEGATIVE_INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());
	/** When a construct weapon from the Fear Nuke's gas fades (game time; see corps/FearFrenzy). */
	public static final DataComponentType<Long> FADES_AT = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("fades_at"),
			DataComponentType.<Long>builder().persistent(Codec.LONG).networkSynchronized(ByteBufCodecs.VAR_LONG).build());

	static void init() {
	}

	private ModComponents() {
	}
}
