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
		NUKE_AURA,
		/** The Fear Nuke's bomb (FearNukeFx), launched from the bearer's raised hand at "from": it flies to "to" over value ticks, then hangs there drinking fear for variant ticks before it airbursts. */
		FEAR_NUKE,
		/** The Fear Nuke airbursts at "from" over the ground at "to": flash, fireball, mushroom cloud and a shock ring out to the crater's radius (value). */
		FEAR_BURST,
		/** The Fear Nuke's yellow gas lingers round "from" out to |to - from| for value ticks: a darkening yellow fog. */
		FEAR_GAS,
		/** The bearer is forming the Fear Nuke in the sky at "from", value 0..1 built (variant: ticks it takes): the bomb, and a line of light from their ring up to it. */
		FEAR_NUKE_FORM,
		/** The forming Fear Nuke at "from" breaks apart, value 0..1 how far built: its plates scatter and fade (variant 0: strayed too far, 1: let go early). */
		FEAR_NUKE_SCATTER,
		/** A lassoed mob's bubble slams into a block at "from", value blocks a tick: nearby cameras shake (RingShake.impact). */
		LASSO_SLAM,
		/** Bridge mode: the picked block at "from" and the deck's front at "to" are outlined (variant: blocks built so far). */
		BRIDGE_MARK,
		/** A Black Hole centred at "from" has swallowed something: value is how many things it has eaten so far. */
		BLACK_HOLE_FEED,
		/** Fast flight's ram barrier round the flyer whose id is variant: from is their middle, to - from the way it faces, value 1 up and 0 gone. Re-sent while it holds. */
		RAM_BARRIER,
		/** The ram barrier hit something at "from", blowing it toward "to" (value: the flyer's speed). */
		RAM_HIT,
		/** The ram barrier shattered against a wall at "from" (variant: the flyer's id, whose glide stops dead). */
		RAM_BREAK,
		/** The bearer leaps in Hammer mode from "from" to "to", landing in value ticks: the construct hammer forms in their hand and swings (HammerHold). */
		HAMMER_LEAP
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
