package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.network.codec.StreamCodec;

/**
 * Server to the bearer's client: where their Build mode plan is (Builds.NONE, SELECT, CLEAR or
 * CHOOSE), so left-click picks designs while choosing instead of mining, and while choosing what
 * the design showing costs (0.1% = 1), for the charge meter.
 */
public record BuildStatePayload(int phase, int cost) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<BuildStatePayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("build_state"));
	public static final StreamCodec<ByteBuf, BuildStatePayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, BuildStatePayload::phase,
			ByteBufCodecs.VAR_INT, BuildStatePayload::cost,
			BuildStatePayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
