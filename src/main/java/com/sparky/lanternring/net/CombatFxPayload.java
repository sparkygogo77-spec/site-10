package com.sparky.lanternring.net;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.world.phys.Vec3;

/**
 * Server to client: a combat move to draw (FlightSlams, FlyingFlurries, AbsorbBlasts). Every client draws it, in the
 * corps colour of the ring that made it; bearer is the player whose ring it was, target another entity it's about.
 */
public record CombatFxPayload(Kind kind, Vec3 from, Vec3 to, float value, int variant, int bearer, int target, Corps corps)
		implements CustomPacketPayload {
	public enum Kind {
		/** The bearer's big flight slam fired at "from" (value: ticks to the ground): the dive into the slam. */
		SLAM_DIVE,
		/** The slam touched down with the feet at "from": the 7x7 crater (value: the lock ticks, variant: ticks the crater stays lit longer). */
		SLAM_LAND,
		/** The bearer's flying flurry lands punch variant (0 jab, 1 cross, 2 backfist) on target at "from", going toward "to". */
		FLURRY_HIT,
		/** The backfist launches target from "from" toward "to" (value: blocks a tick): it tumbles. */
		FLURRY_LAUNCH,
		/** The launched target hit something at "from"; "to" - "from" is the face it hit (variant: its Direction, -1 an entity, no crater). */
		FLURRY_IMPACT,
		/** The launched target flew 50 blocks without hitting anything and rights itself at "from". */
		FLURRY_REGAIN,
		/** The bearer's ring caught a shot at "from" (value: its speed, variant: the attacker's colour as RGB). */
		ABSORB_CATCH,
		/** Let go: the green blast leaves the ring at "from" toward "to" (value: blocks a tick, variant: charge 0..100). */
		ABSORB_RELEASE,
		/** The blast hit something at "from" (variant: charge 0..100). */
		ABSORB_HIT,
		/** The held shot is gone without a blast (the ring ran dry or was put away). */
		ABSORB_END,
		/** The bearer's construct hammer starts forming, to land at "from" ("to" - "from": the bearer's flat forward; value: ticks since
		 * the press; variant: the face hit as a Direction, + 8 when it is a wall, -1 nothing hit). */
		HAMMER_FORM,
		/** The hammer hit at "from" ("to" - "from": the face's normal; variant: the face as a Direction, -1 nothing): the crater and shockwave. */
		HAMMER_HIT
	}

	public static final CustomPacketPayload.Type<CombatFxPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("combat_fx"));
	public static final StreamCodec<ByteBuf, CombatFxPayload> CODEC = StreamCodec.of((buf, fx) -> {
		ByteBufCodecs.VAR_INT.encode(buf, fx.kind.ordinal());
		Vec3.STREAM_CODEC.encode(buf, fx.from);
		Vec3.STREAM_CODEC.encode(buf, fx.to);
		ByteBufCodecs.FLOAT.encode(buf, fx.value);
		ByteBufCodecs.VAR_INT.encode(buf, fx.variant + 1);
		ByteBufCodecs.VAR_INT.encode(buf, fx.bearer + 1);
		ByteBufCodecs.VAR_INT.encode(buf, fx.target + 1);
		Corps.STREAM_CODEC.encode(buf, fx.corps);
	}, buf -> new CombatFxPayload(Kind.values()[ByteBufCodecs.VAR_INT.decode(buf)], Vec3.STREAM_CODEC.decode(buf), Vec3.STREAM_CODEC.decode(buf),
			ByteBufCodecs.FLOAT.decode(buf), ByteBufCodecs.VAR_INT.decode(buf) - 1, ByteBufCodecs.VAR_INT.decode(buf) - 1,
			ByteBufCodecs.VAR_INT.decode(buf) - 1, Corps.STREAM_CODEC.decode(buf)));

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
