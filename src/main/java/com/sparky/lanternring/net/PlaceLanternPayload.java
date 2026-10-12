package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Client to server: the player double-clicked and held right-click to set the off-hand lantern down. */
public record PlaceLanternPayload() implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<PlaceLanternPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("place_lantern"));
	public static final StreamCodec<RegistryFriendlyByteBuf, PlaceLanternPayload> CODEC = StreamCodec.unit(new PlaceLanternPayload());

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
