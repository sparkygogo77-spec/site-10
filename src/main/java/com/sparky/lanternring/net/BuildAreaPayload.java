package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import java.util.List;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.world.phys.Vec3;

/**
 * Server to client: the outline of a Build mode area to trace on the ground. shape is
 * Builds.CIRCLE, SQUARE or PAINT; circles and squares are drawn from center and radius, painted
 * areas from rim, the columns along their edge packed as (dx << 16 | dz & 0xFFFF) from center.
 * locked is true once the area is chosen (it's drawn calmer then).
 */
public record BuildAreaPayload(int shape, Vec3 center, float radius, boolean locked, List<Integer> rim) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<BuildAreaPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("build_area"));
	public static final StreamCodec<ByteBuf, BuildAreaPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, BuildAreaPayload::shape,
			Vec3.STREAM_CODEC, BuildAreaPayload::center,
			ByteBufCodecs.FLOAT, BuildAreaPayload::radius,
			ByteBufCodecs.BOOL, BuildAreaPayload::locked,
			ByteBufCodecs.INT.apply(ByteBufCodecs.list(16384)), BuildAreaPayload::rim,
			BuildAreaPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
