package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.ToggleFlightPayload;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.entity.player.PlayerAbilities;
import net.minecraft.item.ItemStack;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;

/**
 * Server-side ring flight: grants flight while a charged ring with flight switched on is
 * carried, drains charge while airborne, and takes flight away again when that stops.
 */
public final class RingFlight {
	private static final float RING_FLY_SPEED = 0.08f;
	private static final float DEFAULT_FLY_SPEED = 0.05f;
	/** Ticks of flight per point of charge. */
	private static final int DRAIN_INTERVAL = 10;
	private static final int LOW_CHARGE = PowerRingItem.MAX_CHARGE / 10;

	/** Players whose flight we granted, so we only ever take back what we gave. */
	private static final Set<UUID> GRANTED = new HashSet<>();

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(RingFlight::tick);
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> revoke(handler.player));
		ServerPlayNetworking.registerGlobalReceiver(ToggleFlightPayload.ID, (payload, context) -> toggle(context.player()));
	}

	/** The first power ring the player carries: main hand, off hand, then the rest of the inventory. */
	public static ItemStack findRing(ServerPlayerEntity player) {
		if (player.getMainHandStack().getItem() instanceof PowerRingItem) return player.getMainHandStack();
		if (player.getOffHandStack().getItem() instanceof PowerRingItem) return player.getOffHandStack();
		var inventory = player.getInventory();
		for (int i = 0; i < inventory.size(); i++) {
			ItemStack stack = inventory.getStack(i);
			if (stack.getItem() instanceof PowerRingItem) return stack;
		}
		return ItemStack.EMPTY;
	}

	private static void toggle(ServerPlayerEntity player) {
		ItemStack ring = findRing(player);
		if (ring.isEmpty()) {
			player.sendMessage(Text.translatable("message.lanternring.no_ring").formatted(Formatting.GRAY), true);
			return;
		}
		boolean on = !PowerRingItem.isFlightOn(ring);
		ring.set(ModComponents.FLIGHT, on);
		player.sendMessage(Text.translatable(on ? "message.lanternring.flight_on" : "message.lanternring.flight_off")
				.formatted(Formatting.GREEN), true);
		player.getWorld().playSound(null, player.getBlockPos(),
				on ? SoundEvents.BLOCK_BEACON_ACTIVATE : SoundEvents.BLOCK_BEACON_DEACTIVATE,
				SoundCategory.PLAYERS, 0.5f, 1.6f);
	}

	private static void tick(MinecraftServer server) {
		for (ServerPlayerEntity player : server.getPlayerManager().getPlayerList()) {
			if (player.isCreative() || player.isSpectator()) {
				GRANTED.remove(player.getUuid());
				continue;
			}

			ItemStack ring = findRing(player);
			boolean charged = !ring.isEmpty() && PowerRingItem.getCharge(ring) > 0;
			// A charged ring shields its bearer from falls.
			if (charged) player.fallDistance = 0;

			if (charged && PowerRingItem.isFlightOn(ring)) {
				PlayerAbilities abilities = player.getAbilities();
				boolean newlyGranted = GRANTED.add(player.getUuid());
				if (newlyGranted || !abilities.allowFlying) {
					abilities.allowFlying = true;
					abilities.setFlySpeed(RING_FLY_SPEED);
					player.sendAbilitiesUpdate();
				}
				if (abilities.flying) fly(player, ring);
			} else if (GRANTED.contains(player.getUuid())) {
				revoke(player);
			}
		}
	}

	private static void fly(ServerPlayerEntity player, ItemStack ring) {
		if (player.age % 2 == 0) {
			player.getServerWorld().spawnParticles(PowerRingItem.GREEN_LIGHT,
					player.getX(), player.getY() + 0.1, player.getZ(), 2, 0.15, 0.05, 0.15, 0);
		}
		if (player.age % DRAIN_INTERVAL != 0) return;

		int charge = PowerRingItem.getCharge(ring) - 1;
		PowerRingItem.setCharge(ring, charge);
		if (charge == 0) {
			player.sendMessage(Text.translatable("message.lanternring.depleted").formatted(Formatting.RED), true);
		} else if (charge == LOW_CHARGE) {
			player.sendMessage(Text.translatable("message.lanternring.low").formatted(Formatting.YELLOW), true);
		}
	}

	private static void revoke(ServerPlayerEntity player) {
		if (!GRANTED.remove(player.getUuid())) return;
		if (player.isCreative() || player.isSpectator()) return;
		PlayerAbilities abilities = player.getAbilities();
		abilities.allowFlying = false;
		abilities.flying = false;
		abilities.setFlySpeed(DEFAULT_FLY_SPEED);
		player.sendAbilitiesUpdate();
	}

	private RingFlight() {
	}
}
