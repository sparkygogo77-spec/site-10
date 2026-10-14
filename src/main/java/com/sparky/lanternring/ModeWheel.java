package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.SelectModePayload;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;

/** The server side of the mode wheel (ModeWheelScreen): sets the ring in hand to the mode picked. */
public final class ModeWheel {
	private ModeWheel() {
	}

	public static void register() {
		PayloadTypeRegistry.serverboundPlay().register(SelectModePayload.TYPE, SelectModePayload.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(SelectModePayload.TYPE, (payload, context) -> select(context.player(), payload.mode()));
	}

	private static void select(ServerPlayer player, int ordinal) {
		RingMode[] modes = RingMode.values();
		if (ordinal < 0 || ordinal >= modes.length) return;
		ItemStack stack = RingSlot.ring(player);
		if (stack.is(ModRegistry.POWER_RING)) PowerRingItem.selectMode(player.level(), player, stack, modes[ordinal]);
	}
}
