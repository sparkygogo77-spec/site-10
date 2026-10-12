package com.sparky.lanternring;

import com.sparky.lanternring.net.RingFxPayload;
import com.sparky.lanternring.net.ToggleFlightPayload;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.resource.v1.ResourceLoader;
import net.fabricmc.fabric.api.resource.v1.pack.PackActivationType;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.network.chat.Component;
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
		ModParticles.init();
		ModRegistry.init();
		PayloadTypeRegistry.serverboundPlay().register(ToggleFlightPayload.TYPE, ToggleFlightPayload.CODEC);
		PayloadTypeRegistry.clientboundPlay().register(RingFxPayload.TYPE, RingFxPayload.CODEC);
		RingFlight.register();
		HeldConstructs.register();
		Shockwaves.register();

		CreativeModeTabEvents.modifyOutputEvent(CreativeModeTabs.TOOLS_AND_UTILITIES).register(output -> {
			output.accept(ModRegistry.POWER_RING);
			output.accept(ModRegistry.POWER_BATTERY_ITEM);
		});
		// Texture drafts players can switch on under Options > Resource Packs.
		FabricLoader.getInstance().getModContainer(MOD_ID).ifPresent(mod -> {
			for (String size : new String[] {"16px", "64px"}) {
				ResourceLoader.registerBuiltinPack(id("constructs_" + size), mod,
						Component.literal("Lantern Ring: " + size + " constructs"), PackActivationType.NORMAL);
			}
		});
		LOGGER.info("The ring has chosen you.");
	}
}
