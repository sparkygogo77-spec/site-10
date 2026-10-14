package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Client to server, for OmegaBeams: the omega key went down (with the Ring Lab's Omega start and zigzag
 * picks, see OmegaBeams.Start and OmegaBeams.Zig) or came back up.
 */
public record OmegaInputPayload(boolean down, int start, int zig) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<OmegaInputPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("omega_input"));
	public static final StreamCodec<ByteBuf, OmegaInputPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.BOOL, OmegaInputPayload::down, ByteBufCodecs.VAR_INT, OmegaInputPayload::start,
			ByteBufCodecs.VAR_INT, OmegaInputPayload::zig, OmegaInputPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
