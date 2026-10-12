package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.LanternChargePayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.phys.HitResult;

/**
 * Charging from the off-hand lantern: hold left-click and right-click together (see LanternCharge).
 * <ul>
 * <li>Left-click first, then right-click: that right-click is a charge, never the ring's power.</li>
 * <li>Right-click first (a power is running), then left-click: the power is let go quietly and
 * the charge starts in its place. In Anvil mode a quick left-click there picks the size instead,
 * and only holding it for the charge time switches to charging (see AnvilInput).</li>
 * <li>Letting go of left-click before the charge starts calls it off, and right-click stays quiet
 * until it is let go too, so an aborted charge never fires a power.</li>
 * </ul>
 * With the ring and the lantern, left-click doesn't hit blocks (or mine them), so the gesture never
 * breaks the block you're looking at; it still hits mobs.
 */
public final class LanternChargeInput {
	private static boolean attackWasDown;
	/** A charge was called off: swallow right-click until it is let go. */
	private static boolean quiet;

	private LanternChargeInput() {
	}

	/** Ring in the main hand and the lantern in the off hand. */
	public static boolean armed(Minecraft mc) {
		LocalPlayer player = mc.player;
		return player != null && player.getMainHandItem().getItem() instanceof PowerRingItem && LanternCharge.holdsBattery(player);
	}

	/**
	 * Left-click belongs to the lantern gesture: while right-click is down, or when it would hit a
	 * block (not a mob).
	 */
	public static boolean ownsLeftClick(Minecraft mc) {
		if (!armed(mc)) return false;
		return mc.options.keyUse.isDown() || mc.player.isUsingItem()
				|| mc.hitResult == null || mc.hitResult.getType() != HitResult.Type.ENTITY;
	}

	/**
	 * Called from Minecraft.startUseItem before the ring is used (see MinecraftMixin). Tells both
	 * sides whether this right-click is a charge. Returns true to keep the use from the ring.
	 */
	public static boolean beforeUse(Minecraft mc) {
		if (quiet) return true;
		if (!armed(mc)) return false;
		send(mc, mc.options.keyAttack.isDown());
		return false;
	}

	/** Marks the next right-click on both sides as a charge (or not). The payload goes before the use packet. */
	static void send(Minecraft mc, boolean charge) {
		LanternCharge.want(mc.player, charge);
		if (ClientPlayNetworking.canSend(LanternChargePayload.TYPE)) ClientPlayNetworking.send(new LanternChargePayload(charge));
	}

	/** Lets go of the power that's running and starts charging in its place (vanilla re-presses right-click). */
	static void switchToCharge(Minecraft mc) {
		send(mc, true);
		if (mc.gameMode != null) mc.gameMode.releaseUsingItem(mc.player);
	}

	public static void tick(Minecraft mc) {
		boolean attack = mc.options.keyAttack.isDown();
		boolean pressed = attack && !attackWasDown;
		attackWasDown = attack;
		if (quiet && !mc.options.keyUse.isDown()) quiet = false;
		LocalPlayer player = mc.player;
		if (player == null || !armed(mc) || !player.isUsingItem() || mc.gameMode == null) return;
		if (LanternCharge.started(player)) {
			// Let go of left-click before the lantern started rising: no charge, and no power either.
			if (!attack && player.getTicksUsingItem() < LanternCharge.hold()) {
				quiet = true;
				mc.gameMode.releaseUsingItem(player);
			}
			return;
		}
		// Left-click while a power is held: charge instead. (The Anvil uses a quick left-click for its size.)
		if (pressed && PowerRingItem.getMode(player.getUseItem()) != RingMode.ANVIL) switchToCharge(mc);
	}
}
