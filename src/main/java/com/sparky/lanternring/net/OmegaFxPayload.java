package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.world.phys.Vec3;

/**
 * Server to client, for the omega beams (OmegaBeams; drawn by the client's OmegaFx). What id, other,
 * pos, a and b mean depends on kind:
 * <ul>
 * <li>{@link #EYES}: id the bearer's entity id, other the start (OmegaBeams.Start ordinal), a the ticks until the beams leave.</li>
 * <li>{@link #HEAD}: a beam's head moved to pos; id the beam, other the bearer.</li>
 * <li>{@link #END}: the beam is over at pos; id the beam, other 0 fizzled, 1 burnt a block, 2 burnt a creature.</li>
 * <li>{@link #BURN_BLOCK}: the block at pos (its corner) turns to embers for a ticks; id its block state id.</li>
 * <li>{@link #BURN_MOB}: the creature with entity id id glows with embers for a ticks.</li>
 * <li>{@link #ASH}: something a wide and b high crumbles to ash at pos (its feet).</li>
 * </ul>
 */
public record OmegaFxPayload(int kind, int id, int other, Vec3 pos, float a, float b) implements CustomPacketPayload {
	public static final int EYES = 0, HEAD = 1, END = 2, BURN_BLOCK = 3, BURN_MOB = 4, ASH = 5;
	public static final CustomPacketPayload.Type<OmegaFxPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("omega_fx"));
	public static final StreamCodec<ByteBuf, OmegaFxPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, OmegaFxPayload::kind, ByteBufCodecs.VAR_INT, OmegaFxPayload::id, ByteBufCodecs.VAR_INT, OmegaFxPayload::other,
			Vec3.STREAM_CODEC, OmegaFxPayload::pos, ByteBufCodecs.FLOAT, OmegaFxPayload::a, ByteBufCodecs.FLOAT, OmegaFxPayload::b,
			OmegaFxPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
