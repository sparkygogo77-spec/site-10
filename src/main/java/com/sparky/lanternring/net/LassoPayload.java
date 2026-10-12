package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Server to client, every tick a lasso bubble exists: draw the bubble around the target, and a
 * string to the holder's ring. A holder of -1 means it was thrown and flies free; a radius of 0
 * means the bubble popped.
 */
public record LassoPayload(int target, int holder, float radius, boolean holding) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<LassoPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("lasso"));
	public static final StreamCodec<ByteBuf, LassoPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, LassoPayload::target,
			ByteBufCodecs.VAR_INT, LassoPayload::holder,
			ByteBufCodecs.FLOAT, LassoPayload::radius,
			ByteBufCodecs.BOOL, LassoPayload::holding,
			LassoPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
