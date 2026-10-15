package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Client to server, for OmegaBeams: the omega key went down (with the Ring Lab's Omega start pick, see
 * OmegaBeams.Start, and its Omega chain pick, see OmegaBeams.Chain) or came back up.
 */
public record OmegaInputPayload(boolean down, int start, int chain) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<OmegaInputPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("omega_input"));
	public static final StreamCodec<ByteBuf, OmegaInputPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.BOOL, OmegaInputPayload::down, ByteBufCodecs.VAR_INT, OmegaInputPayload::start,
			ByteBufCodecs.VAR_INT, OmegaInputPayload::chain,
			OmegaInputPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
