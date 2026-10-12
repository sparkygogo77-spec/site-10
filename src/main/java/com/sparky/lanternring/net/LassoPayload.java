package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Server to client, every tick a lasso holds something: draw the string from the holder's ring to
 * the bubble around the target. A target of -1 means the holder let go.
 */
public record LassoPayload(int holder, int target, float radius, boolean holding) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<LassoPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("lasso"));
	public static final StreamCodec<ByteBuf, LassoPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, LassoPayload::holder,
			ByteBufCodecs.VAR_INT, LassoPayload::target,
			ByteBufCodecs.FLOAT, LassoPayload::radius,
			ByteBufCodecs.BOOL, LassoPayload::holding,
			LassoPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
