package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.packet.CustomPayload;

/** Client to server: the flight key was pressed. */
public record ToggleFlightPayload() implements CustomPayload {
	public static final CustomPayload.Id<ToggleFlightPayload> ID = new CustomPayload.Id<>(LanternRing.id("toggle_flight"));
	public static final PacketCodec<RegistryByteBuf, ToggleFlightPayload> CODEC = PacketCodec.unit(new ToggleFlightPayload());

	@Override
	public Id<? extends CustomPayload> getId() {
		return ID;
	}
}
