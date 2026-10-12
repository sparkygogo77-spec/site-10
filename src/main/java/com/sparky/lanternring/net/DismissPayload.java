package com.sparky.lanternring.net;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Server to client: a construct is being dismissed into its bearer's ring (see Dismissal). blocks
 * are its pieces, furthest from the ring first; each comes apart in turn over ticks and its light
 * streams back into the bearer's ring (DismissFx).
 */
public record DismissPayload(int bearer, Corps corps, int ticks, List<BlockPos> blocks) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<DismissPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("dismiss"));
	public static final StreamCodec<ByteBuf, DismissPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, DismissPayload::bearer,
			Corps.STREAM_CODEC, DismissPayload::corps,
			ByteBufCodecs.VAR_INT, DismissPayload::ticks,
			BlockPos.STREAM_CODEC.apply(ByteBufCodecs.list(1024)), DismissPayload::blocks,
			DismissPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
