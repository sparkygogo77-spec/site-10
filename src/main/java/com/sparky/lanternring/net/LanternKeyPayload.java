package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Client to server: the lantern key (R) was tapped, and whether you were crouching; or ({@code power})
 * held with the lantern summoned, which sets off its corps' power (see LanternSlot); or ({@code release})
 * let go after setting it off, which ends a power that lasts while held (the Green fortress).
 */
public record LanternKeyPayload(boolean crouch, boolean power, boolean release) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<LanternKeyPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("lantern_key"));
	public static final StreamCodec<ByteBuf, LanternKeyPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.BOOL, LanternKeyPayload::crouch,
			ByteBufCodecs.BOOL, LanternKeyPayload::power,
			ByteBufCodecs.BOOL, LanternKeyPayload::release,
			LanternKeyPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
