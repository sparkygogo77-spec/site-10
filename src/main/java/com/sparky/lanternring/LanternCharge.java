package com.sparky.lanternring;

import java.util.Collections;
import java.util.Set;
import java.util.WeakHashMap;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;

/**
 * Charging the ring from the Power Battery held in the off hand: hold left-click and right-click
 * together for {@link #hold()} ticks, then the lantern rises, the ring hand goes into it, and
 * {@link #charge()} ticks later the ring is full. Both are editable in the Ring Lab's Durations
 * page. While left-click is down, right-click never fires the ring's power (it starts a charge
 * instead); letting go of left-click before {@link #hold()} calls the charge off. Right-click on
 * its own uses the ring as normal, so the lantern never gets in the way of a power.
 *
 * <p>The server can't see left-click, so the client tells it with {@code LanternChargePayload}
 * before each right-click (see {@link #want}).
 *
 * <p>Shared by the server (which does the charging) and the client (which draws it), so both
 * agree on the timeline. Everything is measured from when the charging right-click started.
 */
public final class LanternCharge {
	/** Ticks to lower everything again once the ring is full. */
	public static final int SETTLE = 16;
	/**
	 * Ticks after the ring is full for the lantern's light to burn out completely and the darkened
	 * screen to clear, then for the lantern to flicker back to its idle glow.
	 */
	public static final int DEPLETE = 50;

	/** Entities whose current right-click started with left-click held and the lantern: a charge, not a power. */
	private static final Set<LivingEntity> CHARGERS = Collections.synchronizedSet(Collections.newSetFromMap(new WeakHashMap<>()));
	/** Entities whose left-click was down at their latest right-click (or went down during it). */
	private static final Set<LivingEntity> WANTS = Collections.synchronizedSet(Collections.newSetFromMap(new WeakHashMap<>()));

	private LanternCharge() {
	}

	/** How long both clicks have to be held before charging starts (0.5 s by default). */
	public static int hold() {
		return Math.max(1, RingTuning.CHARGE_HOLD.ticks());
	}

	/**
	 * Ticks the lantern takes to rise and the ring hand to bend, show the ring and press it into the
	 * port, at the start of the charge (0.9 s by default, part of {@link #charge()}).
	 */
	public static int reach() {
		return Math.max(4, RingTuning.CHARGE_REACH.ticks());
	}

	/** From the lantern rising until the ring is full, the hand's reach included (3.5 s by default). */
	public static int charge() {
		return Math.max(reach() + 10, RingTuning.CHARGE_TIME.ticks());
	}

	public static int done() {
		return hold() + charge();
	}

	/** A Power Battery holds this many charges' worth of overcharge before it burns out. */
	public static final int BATTERY_CHARGES = 25;
	/** Each overcharge burns this many of them. */
	public static final int OVERCHARGE_BURN = 2;
	/** The most an overcharge adds past full (+25%). */
	public static final int OVERCHARGE_MAX = 250;
	/** Ticks of grace after full before holding on commits to an overcharge (letting go then costs nothing). */
	public static final int OVER_GRACE = 10;

	/** From committing to the overcharge until it is full (1.5 s by default). */
	public static int over() {
		return Math.max(4, RingTuning.CHARGE_OVER.ticks());
	}

	/** The tick, from the right-click, at which holding on burns the battery and the overcharge starts filling. */
	public static int overStart() {
		return done() + OVER_GRACE;
	}

	public static int overDone() {
		return overStart() + over();
	}

	/** How far the charge has got {@code held} ticks after the right-click: 0 until the lantern rises, 1 when full. */
	public static float progress(float held) {
		return Math.clamp((held - hold()) / (float) charge(), 0f, 1f);
	}

	/** How far the overcharge has filled: 0 before it starts, 1 when full. */
	public static float overProgress(float held) {
		return Math.clamp((held - overStart()) / (float) over(), 0f, 1f);
	}

	public static int burnt(ItemStack battery) {
		return battery.getOrDefault(ModComponents.BATTERY_BURNT, 0);
	}

	public static int chargesLeft(ItemStack battery) {
		return Math.max(0, BATTERY_CHARGES - burnt(battery));
	}

	public static boolean canOvercharge(ItemStack battery) {
		return chargesLeft(battery) >= OVERCHARGE_BURN;
	}

	/** Entities whose current charge has paid for an overcharge (server side). */
	private static final Set<LivingEntity> OVERCHARGING = Collections.synchronizedSet(Collections.newSetFromMap(new WeakHashMap<>()));

	public static void overcharging(LivingEntity user, boolean on) {
		if (on) OVERCHARGING.add(user);
		else OVERCHARGING.remove(user);
	}

	public static boolean overcharging(LivingEntity user) {
		return OVERCHARGING.contains(user);
	}

	public static void burn(ItemStack battery) {
		battery.set(ModComponents.BATTERY_BURNT, Math.min(BATTERY_CHARGES, burnt(battery) + OVERCHARGE_BURN));
	}

	public static boolean holdsBattery(LivingEntity user) {
		// A lantern charges only its own corps' ring.
		return user.getOffhandItem().is(ModRegistry.POWER_BATTERY_ITEM)
				&& Corps.ofLantern(user.getOffhandItem()) == Corps.of(user.getMainHandItem());
	}

	/**
	 * Whether left-click is down for the ring's next (or current) right-click. The client sets it on
	 * its own player and sends it to the server just before the right-click itself, so both sides
	 * see it when {@code PowerRingItem.use} runs.
	 */
	public static void want(LivingEntity user, boolean charge) {
		if (charge) WANTS.add(user);
		else WANTS.remove(user);
	}

	/** True if this right-click with the ring should charge from the lantern instead of using the ring. */
	public static boolean wants(LivingEntity user) {
		return WANTS.contains(user) && holdsBattery(user);
	}

	/**
	 * Called whenever the ring is right-clicked: remembers whether this press is a lantern charge, so
	 * every other press goes to the ring's mode. Runs on both sides (entities are separate objects
	 * there, so they never mix).
	 */
	public static void begin(LivingEntity user, boolean charge) {
		if (charge) CHARGERS.add(user);
		else CHARGERS.remove(user);
	}

	/** True if this entity's current right-click with the ring started as a lantern charge. */
	public static boolean started(LivingEntity user) {
		return CHARGERS.contains(user);
	}

	/** True while this entity is holding a charge with the ring in its main hand and a battery in the other. */
	public static boolean isCharging(LivingEntity user) {
		if (!user.isUsingItem() || user.getUsedItemHand() != InteractionHand.MAIN_HAND) return false;
		ItemStack used = user.getUseItem();
		return used.is(ModRegistry.POWER_RING) && holdsBattery(user) && started(user);
	}
}
