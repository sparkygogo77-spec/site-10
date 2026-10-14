package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Server to client: the blocks a super landing blasted out (see SuperJumps). Sent just before the
 * landing's SUPER_LAND, so the client lines that crater, and only it, with the construct pad
 * (SuperLandConstruct).
 */
public record SuperCraterPayload(int bearer, List<BlockPos> blocks) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<SuperCraterPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("super_crater"));
	public static final StreamCodec<ByteBuf, SuperCraterPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, SuperCraterPayload::bearer,
			BlockPos.STREAM_CODEC.apply(ByteBufCodecs.list(2048)), SuperCraterPayload::blocks,
			SuperCraterPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
