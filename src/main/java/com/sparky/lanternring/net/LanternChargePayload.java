package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Client to server, just before a right-click with the ring and the lantern: whether left-click is
 * down, so that right-click charges from the lantern instead of using the ring (see LanternCharge).
 */
public record LanternChargePayload(boolean charge) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<LanternChargePayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("lantern_charge"));
	public static final StreamCodec<ByteBuf, LanternChargePayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.BOOL, LanternChargePayload::charge,
			LanternChargePayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
