package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Client to server: the lantern key (R) was pressed, and whether you were crouching (see LanternSlot). */
public record LanternKeyPayload(boolean crouch) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<LanternKeyPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("lantern_key"));
	public static final StreamCodec<ByteBuf, LanternKeyPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.BOOL, LanternKeyPayload::crouch,
			LanternKeyPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
