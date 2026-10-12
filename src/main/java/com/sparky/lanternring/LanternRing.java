package com.sparky.lanternring;

import com.sparky.lanternring.net.ToggleFlightPayload;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.minecraft.item.ItemGroups;
import net.minecraft.util.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LanternRing implements ModInitializer {
	public static final String MOD_ID = "lanternring";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	public static Identifier id(String path) {
		return Identifier.of(MOD_ID, path);
	}

	@Override
	public void onInitialize() {
		ModComponents.init();
		ModRegistry.init();
		PayloadTypeRegistry.playC2S().register(ToggleFlightPayload.ID, ToggleFlightPayload.CODEC);
		RingFlight.register();

		ItemGroupEvents.modifyEntriesEvent(ItemGroups.TOOLS).register(entries -> {
			entries.add(ModRegistry.POWER_RING);
			entries.add(ModRegistry.POWER_BATTERY_ITEM);
		});
		LOGGER.info("The ring has chosen you.");
	}
}
