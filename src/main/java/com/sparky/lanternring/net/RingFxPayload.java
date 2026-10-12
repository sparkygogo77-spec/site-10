package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.world.phys.Vec3;

/**
 * Server to client: a ring power just fired, draw its effect. Each player's client draws it in the
 * style picked in their Ring Lab menu. value is extra data some effects need (the Blast drill's
 * speed in blocks per tick), variant which version of it (the Blast's level, 1 to 3).
 */
public record RingFxPayload(Kind kind, Vec3 from, Vec3 to, float value, int variant) implements CustomPacketPayload {
	public enum Kind {
		BLAST, BEAM, CONSTRUCT, PUSH, TETHER, CHARGE, MODE_CHANGE, BEAM_CHARGED, ANVIL_MARK, ANVIL_IMPACT, SHOCKWAVE, BLACK_HOLE_MARK, BLACK_HOLE
	}

	public static final CustomPacketPayload.Type<RingFxPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("ring_fx"));
	public static final StreamCodec<ByteBuf, RingFxPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.idMapper(i -> Kind.values()[i], Kind::ordinal), RingFxPayload::kind,
			Vec3.STREAM_CODEC, RingFxPayload::from,
			Vec3.STREAM_CODEC, RingFxPayload::to,
			ByteBufCodecs.FLOAT, RingFxPayload::value,
			ByteBufCodecs.VAR_INT, RingFxPayload::variant,
			RingFxPayload::new);

	public RingFxPayload(Kind kind, Vec3 from, Vec3 to) {
		this(kind, from, to, 0f, 0);
	}

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
