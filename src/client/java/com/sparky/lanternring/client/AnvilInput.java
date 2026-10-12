package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.AnvilInputPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.world.item.ItemStack;

/**
 * Left-click while holding right-click picks a size: the Anvil's (right-click aims the marker and
 * letting go drops it; see PowerRingItem), the Blast's level while it charges (see BlastDrills) or
 * the construct Army mode summons (see ConstructArmy).
 * With the lantern in the off hand, holding that left-click a moment charges from the
 * lantern instead (see LanternChargeInput), so then the size only changes when the click is let
 * go quickly. Left-click doesn't mine or hit with the ring while right-click is held (see MinecraftMixin).
 */
public final class AnvilInput {
	/** Ticks into the current right-click hold when the Blast's level last changed (its charge restarts). */
	static int blastRestart;
	/** A left-click with the lantern held, waiting to see if it's a click (size) or a hold (charge). */
	private static int pending = -1;
	private static int pendingTicks;
	/** A left-click held this long (longer than any click) is a lantern charge, not a size step. */
	private static final int SWITCH = 5;

	private AnvilInput() {
	}

	/** The size step a left-click sends right now (CYCLE or BLAST_CYCLE), or -1 if left-click isn't for sizes. */
	private static int action(Minecraft mc) {
		if (mc.player == null || !mc.player.isUsingItem() || LanternCharge.started(mc.player)) return -1;
		ItemStack used = mc.player.getUseItem();
		if (!(used.getItem() instanceof PowerRingItem)) return -1;
		RingMode mode = PowerRingItem.getMode(used);
		return switch (mode) {
			case ANVIL -> AnvilInputPayload.CYCLE;
			case BLAST -> AnvilInputPayload.BLAST_CYCLE;
			case ARMY -> AnvilInputPayload.ARMY_CYCLE;
			default -> -1;
		};
	}

	/** True while right-click is held in a mode that uses left-click for its size. */
	public static boolean picksSize(Minecraft mc) {
		return action(mc) >= 0;
	}

	/** Left-click belongs to the size (or the lantern charge) while aiming the Anvil or charging the Blast. */
	public static boolean ownsLeftClick(Minecraft mc) {
		return picksSize(mc);
	}

	/**
	 * Before vanilla handles the keys: each left-click while right-click is held is a size step.
	 * Counting clicks (rather than watching the key) catches a click shorter than a tick, and
	 * vanilla throws these clicks away while an item is in use anyway.
	 */
	public static void startTick(Minecraft mc) {
		int action = action(mc);
		if (action < 0) {
			pending = -1;
			return;
		}
		while (mc.options.keyAttack.consumeClick()) {
			if (LanternChargeInput.armed(mc)) {
				if (pending < 0) pendingTicks = 0;
				pending = action;
			} else {
				cycle(mc, action);
			}
		}
	}

	public static void tick(Minecraft mc) {
		if (pending < 0) return;
		if (action(mc) != pending) {
			pending = -1;
			return;
		}
		if (!mc.options.keyAttack.isDown()) {
			cycle(mc, pending);
			pending = -1;
		} else if (++pendingTicks >= SWITCH) {
			// Held long enough with right-click: it's a lantern charge, so the aim or Blast is called off.
			pending = -1;
			LanternChargeInput.switchToCharge(mc);
		}
	}

	private static void cycle(Minecraft mc, int action) {
		if (!ClientPlayNetworking.canSend(AnvilInputPayload.TYPE)) return;
		ClientPlayNetworking.send(new AnvilInputPayload(action));
		if (action == AnvilInputPayload.BLAST_CYCLE) blastRestart = mc.player.getTicksUsingItem();
	}
}
