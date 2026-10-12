package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Client to server: left-click held in Anvil mode (sent every tick it is held), then one release when it's let go. */
public record AnvilInputPayload(boolean held) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<AnvilInputPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("anvil_input"));
	public static final StreamCodec<ByteBuf, AnvilInputPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.BOOL, AnvilInputPayload::held,
			AnvilInputPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
