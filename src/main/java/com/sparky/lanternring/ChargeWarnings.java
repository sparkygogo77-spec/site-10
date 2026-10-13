package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

/**
 * Warns once when the ring drops to 10% and again when it runs dry, whatever drained it (flight,
 * a held Dome, a power). Checked from RingFlight's tick, which already finds each player's ring.
 */
public final class ChargeWarnings {
	public static final int LOW_CHARGE = PowerRingItem.MAX_CHARGE / 10;
	private static final Map<UUID, Integer> LAST = new HashMap<>();

	private ChargeWarnings() {
	}

	static void register() {
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> LAST.remove(handler.getPlayer().getUUID()));
	}

	static void check(ServerPlayer player, ItemStack ring) {
		if (ring.isEmpty()) {
			LAST.remove(player.getUUID());
			return;
		}
		int now = PowerRingItem.getCharge(ring);
		Integer was = LAST.put(player.getUUID(), now);
		if (was == null || now >= was) return;
		if (now == 0) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.depleted").withStyle(ChatFormatting.RED));
			RingSounds.depleted(player.level(), player);
		} else if (was > LOW_CHARGE && now <= LOW_CHARGE) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.low").withStyle(ChatFormatting.YELLOW));
			RingSounds.low(player.level(), player);
		}
	}
}
