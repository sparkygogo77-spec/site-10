package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Client to server in Anvil mode: a left-click while right-click is held to aim (CYCLE, the next
 * size). Aiming and dropping go with right-click itself (see PowerRingItem).
 */
public record AnvilInputPayload(int action) implements CustomPacketPayload {
	public static final int CYCLE = 2;

	public static final CustomPacketPayload.Type<AnvilInputPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("anvil_input"));
	public static final StreamCodec<ByteBuf, AnvilInputPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, AnvilInputPayload::action,
			AnvilInputPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
