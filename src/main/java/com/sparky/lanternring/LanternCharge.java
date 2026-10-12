package com.sparky.lanternring;

import java.util.Collections;
import java.util.Set;
import java.util.WeakHashMap;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;

/**
 * Charging the ring from the Power Battery held in the off hand: crouch and hold right-click for
 * {@link #hold()} ticks, then the lantern rises, the ring hand goes into it, and {@link #charge()}
 * ticks later the ring is full. Both are editable in the Ring Lab's Durations page. A quick
 * crouch-tap still changes mode, and right-click without crouching uses the ring as normal, so the
 * lantern never gets in the way of a power (see {@link #begin}).
 *
 * <p>Shared by the server (which does the charging) and the client (which draws it), so both
 * agree on the timeline. Everything is measured from when right-click went down.
 */
public final class LanternCharge {
	/** Releasing before this counts as a tap: the ring changes mode instead. */
	public static final int TAP = 6;
	/** Ticks the lantern takes to rise and the hand to reach it, at the start of the charge. */
	public static final int REACH = 8;
	/** Ticks to lower everything again once the ring is full. */
	public static final int SETTLE = 10;

	/** Entities whose current right-click started crouched with the lantern: a charge, not a power. */
	private static final Set<LivingEntity> CHARGERS = Collections.synchronizedSet(Collections.newSetFromMap(new WeakHashMap<>()));

	private LanternCharge() {
	}

	/** How long right-click has to be held before charging starts (2 s by default). */
	public static int hold() {
		return Math.max(TAP, RingTuning.CHARGE_HOLD.ticks());
	}

	/** How long the ring stays in the lantern (1.5 s by default). */
	public static int charge() {
		return Math.max(REACH + 2, RingTuning.CHARGE_TIME.ticks());
	}

	public static int done() {
		return hold() + charge();
	}

	public static boolean holdsBattery(LivingEntity user) {
		return user.getOffhandItem().is(ModRegistry.POWER_BATTERY_ITEM);
	}

	/**
	 * Called whenever the ring is right-clicked: remembers whether this press is a lantern charge, so
	 * it stays one if the player stops crouching and every other press goes to the ring's mode.
	 * Runs on both sides (entities are separate objects there, so they never mix).
	 */
	public static void begin(LivingEntity user, boolean charge) {
		if (charge) CHARGERS.add(user);
		else CHARGERS.remove(user);
	}

	/** True if this entity's current right-click with the ring started as a lantern charge. */
	public static boolean started(LivingEntity user) {
		return CHARGERS.contains(user);
	}

	/** True while this entity is crouch-holding right-click with the ring in its main hand and a battery in the other. */
	public static boolean isCharging(LivingEntity user) {
		if (!user.isUsingItem() || user.getUsedItemHand() != InteractionHand.MAIN_HAND) return false;
		ItemStack used = user.getUseItem();
		return used.is(ModRegistry.POWER_RING) && holdsBattery(user) && started(user);
	}
}
