package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Server to client, every other tick while someone charges their ring at a lantern: how bright
 * the light pouring out of it is ({@code power}, about 0.2 building up, 1 just before full, more
 * at the burst) and the corps colour (an ordinal of Corps). Each client draws the sun on the
 * bearer's ring and, if it is looking at them, the flashbang over its own screen (see LanternFlash).
 */
public record LanternFlashPayload(int bearer, float power, int corps) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<LanternFlashPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("lantern_flash"));
	public static final StreamCodec<ByteBuf, LanternFlashPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, LanternFlashPayload::bearer,
			ByteBufCodecs.FLOAT, LanternFlashPayload::power,
			ByteBufCodecs.VAR_INT, LanternFlashPayload::corps,
			LanternFlashPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
