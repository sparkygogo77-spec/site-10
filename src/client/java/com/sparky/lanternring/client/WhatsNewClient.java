package com.sparky.lanternring.client;

import com.sparky.lanternring.net.WhatsNewPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;

/** Tells the server about things only the client sees, so the What's New book can tick them (see WhatsNew). */
public final class WhatsNewClient {
	private WhatsNewClient() {
	}

	public static void tell(String trigger) {
		if (Minecraft.getInstance().player == null || !ClientPlayNetworking.canSend(WhatsNewPayload.TYPE)) return;
		ClientPlayNetworking.send(new WhatsNewPayload(trigger));
	}

	/** The Ring Lab's "Get the What's New book" button. */
	public static void giveBook() {
		tell(WhatsNewPayload.GIVE_BOOK);
	}
}
