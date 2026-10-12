package com.sparky.lanternring.client;

import com.mojang.blaze3d.platform.InputConstants;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.net.ToggleFlightPayload;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.KeyMapping;

public class LanternRingClient implements ClientModInitializer {
	private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(LanternRing.id("lanternring"));
	private static KeyMapping flightKey;

	@Override
	public void onInitializeClient() {
		flightKey = KeyMappingHelper.registerKeyMapping(new KeyMapping("key.lanternring.flight",
				InputConstants.Type.KEYBOARD, InputConstants.KEY_V, CATEGORY));
		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			while (flightKey.consumeClick()) {
				if (client.player != null && ClientPlayNetworking.canSend(ToggleFlightPayload.TYPE)) {
					ClientPlayNetworking.send(new ToggleFlightPayload());
				}
			}
		});
	}
}
