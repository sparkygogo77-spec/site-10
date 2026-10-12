package com.sparky.lanternring;

import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;

/**
 * Charging the ring from the Power Battery held in the off hand: hold right-click for
 * {@link #hold()} ticks, then the lantern rises, the ring hand goes into it, and {@link #charge()}
 * ticks later the ring is full. Both are editable in the Ring Lab's Durations page. A quick tap
 * still fires the ring's current power.
 *
 * <p>Shared by the server (which does the charging) and the client (which draws it), so both
 * agree on the timeline. Everything is measured from when right-click went down.
 */
public final class LanternCharge {
	/** Releasing before this counts as a tap: the ring fires its power instead. */
	public static final int TAP = 6;
	/** Ticks the lantern takes to rise and the hand to reach it, at the start of the charge. */
	public static final int REACH = 8;
	/** Ticks to lower everything again once the ring is full. */
	public static final int SETTLE = 10;

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

	/** True while this entity is holding right-click with the ring in its main hand and a battery in the other. */
	public static boolean isCharging(LivingEntity user) {
		if (!user.isUsingItem() || user.getUsedItemHand() != InteractionHand.MAIN_HAND) return false;
		ItemStack used = user.getUseItem();
		return used.is(ModRegistry.POWER_RING) && holdsBattery(user);
	}
}
