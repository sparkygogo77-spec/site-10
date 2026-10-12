package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Client to server: the mode wheel picked this RingMode (by ordinal) for the ring in hand. */
public record SelectModePayload(int mode) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<SelectModePayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("select_mode"));
	public static final StreamCodec<RegistryFriendlyByteBuf, SelectModePayload> CODEC =
			ByteBufCodecs.VAR_INT.map(SelectModePayload::new, SelectModePayload::mode).cast();

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
