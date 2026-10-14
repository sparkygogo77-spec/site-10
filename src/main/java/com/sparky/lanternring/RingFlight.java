package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.ToggleFlightPayload;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.world.entity.player.Abilities;
import net.minecraft.world.item.ItemStack;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.network.chat.Component;
import net.minecraft.ChatFormatting;

/**
 * Server-side ring flight: grants flight while a charged ring with flight switched on is
 * carried, drains charge while airborne, and takes flight away again when that stops.
 */
public final class RingFlight {
	private static final float RING_FLY_SPEED = 0.08f;
	private static final float DEFAULT_FLY_SPEED = 0.05f;

	/** Players whose flight we granted, so we only ever take back what we gave. */
	private static final Set<UUID> GRANTED = new HashSet<>();

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(RingFlight::tick);
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> revoke(handler.player));
		ServerPlayNetworking.registerGlobalReceiver(ToggleFlightPayload.TYPE, (payload, context) -> toggle(context.player()));
	}

	/** The first power ring the player carries: main hand, off hand, then the rest of the inventory. */
	public static ItemStack findRing(ServerPlayer player) {
		if (player.getMainHandItem().getItem() instanceof PowerRingItem) return player.getMainHandItem();
		if (player.getOffhandItem().getItem() instanceof PowerRingItem) return player.getOffhandItem();
		var inventory = player.getInventory();
		for (int i = 0; i < inventory.getContainerSize(); i++) {
			ItemStack stack = inventory.getItem(i);
			if (stack.getItem() instanceof PowerRingItem) return stack;
		}
		return RingSlot.worn(player);
	}

	private static void toggle(ServerPlayer player) {
		ItemStack ring = findRing(player);
		if (ring.isEmpty()) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.no_ring").withStyle(ChatFormatting.GRAY));
			return;
		}
		boolean on = !PowerRingItem.isFlightOn(ring);
		ring.set(ModComponents.FLIGHT, on);
		player.sendOverlayMessage(Component.translatable(on ? "message.lanternring.flight_on" : "message.lanternring.flight_off")
				.withStyle(ChatFormatting.GREEN));
		player.level().playSound(null, player.blockPosition(),
				on ? SoundEvents.BEACON_ACTIVATE : SoundEvents.BEACON_DEACTIVATE,
				SoundSource.PLAYERS, 0.5f, 1.6f);
	}

	private static void tick(MinecraftServer server) {
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			if (player.isCreative() || player.isSpectator()) {
				GRANTED.remove(player.getUUID());
				continue;
			}

			ItemStack ring = findRing(player);
			ChargeWarnings.check(player, ring);
			boolean charged = !ring.isEmpty() && PowerRingItem.getCharge(ring) > 0;
			// A charged ring shields its bearer from falls.
			if (charged) player.resetFallDistance();

			if (charged && PowerRingItem.isFlightOn(ring)) {
				Abilities abilities = player.getAbilities();
				boolean newlyGranted = GRANTED.add(player.getUUID());
				if (newlyGranted || !abilities.mayfly) {
					abilities.mayfly = true;
					abilities.setFlyingSpeed(RING_FLY_SPEED);
					player.onUpdateAbilities();
				}
				if (abilities.flying) fly(player, ring);
			} else if (GRANTED.contains(player.getUUID())) {
				revoke(player);
			}
		}
	}

	private static void fly(ServerPlayer player, ItemStack ring) {
		if (player.tickCount % RingTuning.flightDrainInterval() != 0) return;

		// The low and out-of-power warnings come from ChargeWarnings, for every drain alike.
		PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - 1);
	}

	private static void revoke(ServerPlayer player) {
		if (!GRANTED.remove(player.getUUID())) return;
		if (player.isCreative() || player.isSpectator()) return;
		Abilities abilities = player.getAbilities();
		abilities.mayfly = false;
		abilities.flying = false;
		abilities.setFlyingSpeed(DEFAULT_FLY_SPEED);
		player.onUpdateAbilities();
	}

	private RingFlight() {
	}
}
