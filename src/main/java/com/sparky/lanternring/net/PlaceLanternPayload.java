package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Client to server: the player asked to set the off-hand lantern down. {@code style} is the lantern
 * picked in their Ring Lab (see LanternStyle), so the placed lantern is the one they were holding.
 */
public record PlaceLanternPayload(String style) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<PlaceLanternPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("place_lantern"));
	public static final StreamCodec<RegistryFriendlyByteBuf, PlaceLanternPayload> CODEC =
			StreamCodec.composite(ByteBufCodecs.stringUtf8(32), PlaceLanternPayload::style, PlaceLanternPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
