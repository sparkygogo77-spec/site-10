package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.world.phys.Vec3;

/**
 * Server to client, every tick a Loot Golem is out: draw it at pos facing yaw, its sack this full
 * (0 to 1). visible false means it is inside a portal (or gone for good when fill is negative).
 */
public record GolemPayload(int id, Vec3 pos, float yaw, float fill, boolean visible) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<GolemPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("golem"));
	public static final StreamCodec<ByteBuf, GolemPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, GolemPayload::id,
			Vec3.STREAM_CODEC, GolemPayload::pos,
			ByteBufCodecs.FLOAT, GolemPayload::yaw,
			ByteBufCodecs.FLOAT, GolemPayload::fill,
			ByteBufCodecs.BOOL, GolemPayload::visible,
			GolemPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
