package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Client to server: the flight key was pressed. */
public record ToggleFlightPayload() implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<ToggleFlightPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("toggle_flight"));
	public static final StreamCodec<RegistryFriendlyByteBuf, ToggleFlightPayload> CODEC = StreamCodec.unit(new ToggleFlightPayload());

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
