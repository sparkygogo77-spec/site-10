package com.sparky.lanternring;

import com.sparky.lanternring.net.ToggleFlightPayload;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.CreativeModeTabs;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LanternRing implements ModInitializer {
	public static final String MOD_ID = "lanternring";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	public static Identifier id(String path) {
		return Identifier.fromNamespaceAndPath(MOD_ID, path);
	}

	@Override
	public void onInitialize() {
		ModComponents.init();
		ModRegistry.init();
		PayloadTypeRegistry.serverboundPlay().register(ToggleFlightPayload.TYPE, ToggleFlightPayload.CODEC);
		RingFlight.register();

		CreativeModeTabEvents.modifyOutputEvent(CreativeModeTabs.TOOLS_AND_UTILITIES).register(output -> {
			output.accept(ModRegistry.POWER_RING);
			output.accept(ModRegistry.POWER_BATTERY_ITEM);
		});
		LOGGER.info("The ring has chosen you.");
	}
}
