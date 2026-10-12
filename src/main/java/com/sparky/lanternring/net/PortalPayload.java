package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.world.phys.Vec3;

/**
 * Server to client: a Portal is open at center, its front facing yaw, for ticksLeft more ticks
 * (0 closes it now). Sent when it opens and again every half second, so players who arrive later see it.
 */
public record PortalPayload(int id, Vec3 center, float yaw, int ticksLeft) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<PortalPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("portal"));
	public static final StreamCodec<ByteBuf, PortalPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, PortalPayload::id,
			Vec3.STREAM_CODEC, PortalPayload::center,
			ByteBufCodecs.FLOAT, PortalPayload::yaw,
			ByteBufCodecs.VAR_INT, PortalPayload::ticksLeft,
			PortalPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
