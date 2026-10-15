package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Client to server: left-click held (push it further, or pick mobs before a catch; sent every tick) or the mouse wheel (a notch out or in) while holding a catch. */
public record LassoInputPayload(int action) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<LassoInputPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("lasso_input"));
	public static final StreamCodec<ByteBuf, LassoInputPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, LassoInputPayload::action,
			LassoInputPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
