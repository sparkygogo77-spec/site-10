package com.sparky.lanternring.client;

import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.net.ToggleFlightPayload;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.blockrenderlayer.v1.BlockRenderLayerMap;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.option.KeyBinding;
import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.util.InputUtil;
import org.lwjgl.glfw.GLFW;

public class LanternRingClient implements ClientModInitializer {
	private static KeyBinding flightKey;

	@Override
	public void onInitializeClient() {
		BlockRenderLayerMap.INSTANCE.putBlock(ModRegistry.LIGHT_CONSTRUCT, RenderLayer.getTranslucent());
		BlockRenderLayerMap.INSTANCE.putBlock(ModRegistry.POWER_BATTERY, RenderLayer.getCutout());

		flightKey = KeyBindingHelper.registerKeyBinding(new KeyBinding("key.lanternring.flight",
				InputUtil.Type.KEYSYM, GLFW.GLFW_KEY_V, "category.lanternring"));
		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			while (flightKey.wasPressed()) {
				if (client.player != null && ClientPlayNetworking.canSend(ToggleFlightPayload.ID)) {
					ClientPlayNetworking.send(new ToggleFlightPayload());
				}
			}
		});
	}
}
