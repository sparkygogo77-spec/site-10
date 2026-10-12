package com.sparky.lanternring.client;

import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.AnvilInputPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.world.item.ItemStack;

/**
 * Deluge mode with right-click not held: holding left-click a moment sucks your Deluges back
 * into the ring (Deluges.recall). While one of yours may still be out (one formed in the last
 * minute), left-click is kept for that instead of hitting or mining (see MinecraftMixin).
 */
public final class DelugeRecallInput {
	/** Ticks left-click has to be held before it counts as a recall. */
	private static final int HOLD = 3;
	private static int held;
	/** How long after your last Deluge formed left-click still belongs to the recall. */
	private static final long OUT_FOR = 20 * 60;
	/** Game time your last Deluge formed (from its DELUGE_FORM), or Long.MIN_VALUE. */
	private static long lastOut = Long.MIN_VALUE;

	private DelugeRecallInput() {
	}

	/** One of your Deluges is out (its ball just formed). */
	public static void formed(Minecraft mc) {
		if (mc.level != null) lastOut = mc.level.getGameTime();
	}

	/** Deluge mode, not aiming, with a Deluge of yours maybe still out: left-click is the recall. */
	public static boolean ownsLeftClick(Minecraft mc) {
		return mc.player != null && mc.level != null && !mc.player.isUsingItem() && delugeRing(mc.player.getMainHandItem())
				&& mc.level.getGameTime() - lastOut < OUT_FOR && mc.level.getGameTime() >= lastOut;
	}

	public static void tick(Minecraft mc) {
		if (mc.player == null || mc.gui.screen() != null || mc.player.isUsingItem() || !mc.options.keyAttack.isDown() || !delugeRing(mc.player.getMainHandItem())) {
			held = 0;
			return;
		}
		if (++held == HOLD && ClientPlayNetworking.canSend(AnvilInputPayload.TYPE)) {
			ClientPlayNetworking.send(new AnvilInputPayload(AnvilInputPayload.DELUGE_RECALL));
			lastOut = Long.MIN_VALUE;
		}
	}

	private static boolean delugeRing(ItemStack stack) {
		return stack.getItem() instanceof PowerRingItem && PowerRingItem.getMode(stack) == RingMode.DELUGE;
	}
}
