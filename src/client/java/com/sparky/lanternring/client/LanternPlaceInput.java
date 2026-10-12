package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.PlaceLanternPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.HitResult;

/**
 * Setting the off-hand lantern down: double-click right-click on a block and hold the second click
 * for {@link RingTuning#LANTERN_PLACE_HOLD}. The second click (and the hold after it) is kept from
 * the ring, so the gesture doesn't fire a power too; every other click goes to the ring as normal.
 * <p>Or, in any mode: crouch and hold right-click on a block for the same time. A quick crouched
 * click on a block still changes the ring's mode (when it's let go).
 *
 * <p>In Lasso mode the double-click belongs to the Lasso (it gathers a group), and in Anvil mode a
 * held right-click aims the anvil, so it never places in either. With left-click down, right-click
 * charges from the lantern (see LanternChargeInput), so that never places either.
 */
public final class LanternPlaceInput {
	private static int ticks;
	private static int lastPress = -1000;
	private static boolean wasDown;
	/** The current press is the second click of a double-click. */
	private static boolean armed;
	private static boolean placed;
	private static int held;
	/** The armed press was a crouched click on a block (a tap changes mode, a hold places). */
	private static boolean crouched;

	private LanternPlaceInput() {
	}

	/**
	 * Called from Minecraft.startUseItem (see MinecraftMixin), which runs on a fresh right-click
	 * and every few ticks while it is held. Returns true to keep that use from the ring.
	 */
	public static boolean consumesUse(Minecraft mc) {
		// Once armed the press stays ours until it's let go, even after the lantern has left the hand.
		if (armed) return true;
		if (mc.player == null || !LanternCharge.holdsBattery(mc.player)) return false;
		boolean fresh = !wasDown;
		boolean onBlock = mc.hitResult != null && mc.hitResult.getType() == HitResult.Type.BLOCK;
		if (fresh && onBlock && mc.player.isShiftKeyDown() && !mc.options.keyAttack.isDown()) {
			lastPress = -1000;
			armed = true;
			crouched = true;
			placed = false;
			held = 0;
			return true;
		}
		ItemStack main = mc.player.getMainHandItem();
		if (main.getItem() instanceof PowerRingItem) {
			RingMode mode = PowerRingItem.getMode(main);
			if (mode == RingMode.TETHER || mode == RingMode.ANVIL) return false;
		}
		if (mc.options.keyAttack.isDown()) {
			lastPress = -1000;
			return false;
		}
		if (!fresh) return false;
		if (onBlock && !mc.player.isShiftKeyDown() && ticks - lastPress <= RingTuning.LANTERN_DOUBLE_CLICK.ticks()) {
			// A third quick click starts over instead of counting as another double-click.
			lastPress = -1000;
			armed = true;
			crouched = false;
			placed = false;
			held = 0;
			return true;
		}
		lastPress = ticks;
		return false;
	}

	public static void tick(Minecraft mc) {
		ticks++;
		boolean down = mc.options.keyUse.isDown();
		if (mc.player == null || (!armed && !LanternCharge.holdsBattery(mc.player))) {
			armed = false;
			wasDown = down;
			return;
		}
		if (armed) {
			if (!down) {
				armed = false;
				// A quick crouched click: the mode change it held back.
				if (crouched && !placed && mc.player.isShiftKeyDown() && mc.gameMode != null
						&& mc.player.getMainHandItem().getItem() instanceof PowerRingItem) {
					LanternChargeInput.send(mc, false);
					mc.gameMode.useItem(mc.player, InteractionHand.MAIN_HAND);
				}
			} else if (!placed && ++held >= Math.max(1, RingTuning.LANTERN_PLACE_HOLD.ticks())) {
				placed = true;
				if (ClientPlayNetworking.canSend(PlaceLanternPayload.TYPE)) ClientPlayNetworking.send(new PlaceLanternPayload());
			}
		}
		wasDown = down;
	}
}
