package com.sparky.lanternring.net;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.world.phys.Vec3;

/**
 * Server to client: a ring power just fired, draw its effect. Each player's client draws it in the
 * style picked in their Ring Lab menu. value is extra data some effects need (the Blast drill's
 * speed in blocks per tick), variant which version of it (the Blast's level, 1 to 3), corps the
 * colour of the ring that made it. bearer is the entity id of the player whose ring it came out of
 * (-1 when no ring made it, like a construct ally's shot): each client then starts the effect at
 * that player's ring, where it is drawn on their screen, instead of at from.
 */
public record RingFxPayload(Kind kind, Vec3 from, Vec3 to, float value, int variant, Corps corps, int bearer) implements CustomPacketPayload {
	public enum Kind {
		BLAST, BEAM, CONSTRUCT, PUSH, TETHER, CHARGE, MODE_CHANGE, BEAM_CHARGED, ANVIL_MARK, ANVIL_IMPACT, SHOCKWAVE, DELUGE_MARK, DELUGE_SPLASH, REFLECT, BLACK_HOLE_MARK, BLACK_HOLE,
		/** Army mode: a construct ally shoots (from its eye to the mob), aims (where it will form) or forms. */
		ALLY_SHOT, ALLY_MARK, ALLY_SUMMON,
		/** A power with no other line of light (the Flame Ring): a flash at the ring and a stream from it to "to". */
		EMIT,
		/** The Deluge's ball is held in the air (from = to = its middle): the bearer's ring flares and pours light into it. value 0..1 is how hard. */
		DELUGE_FORM,
		/** A bit of a Deluge being sucked back into the bearer's ring, from "from" (variant 1: the red one). */
		DELUGE_RECALL,
		/** The Fear Nuke goes off: a yellow aura sweeps out from "from" to the radius |to - from| over value ticks, encasing and burning (variant: ticks each block glows first). */
		NUKE_AURA
	}

	public static final CustomPacketPayload.Type<RingFxPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("ring_fx"));
	public static final StreamCodec<ByteBuf, RingFxPayload> CODEC = StreamCodec.of((buf, fx) -> {
		ByteBufCodecs.VAR_INT.encode(buf, fx.kind.ordinal());
		Vec3.STREAM_CODEC.encode(buf, fx.from);
		Vec3.STREAM_CODEC.encode(buf, fx.to);
		ByteBufCodecs.FLOAT.encode(buf, fx.value);
		ByteBufCodecs.VAR_INT.encode(buf, fx.variant);
		Corps.STREAM_CODEC.encode(buf, fx.corps);
		ByteBufCodecs.VAR_INT.encode(buf, fx.bearer + 1);
	}, buf -> new RingFxPayload(Kind.values()[ByteBufCodecs.VAR_INT.decode(buf)], Vec3.STREAM_CODEC.decode(buf), Vec3.STREAM_CODEC.decode(buf),
			ByteBufCodecs.FLOAT.decode(buf), ByteBufCodecs.VAR_INT.decode(buf), Corps.STREAM_CODEC.decode(buf), ByteBufCodecs.VAR_INT.decode(buf) - 1));

	public RingFxPayload(Kind kind, Vec3 from, Vec3 to) {
		this(kind, from, to, 0f, 0, Corps.GREEN, -1);
	}

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
