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
 * <li>{@link #START}: the pair's line leaves the eyes at pos; id the line, other the bearer, b flags: 1 a barrage
 * (several targets: it lets go of the eyes at OmegaBeams.LET_GO blocks long), 2 the pass 837 R4 chain (E3 pulse look).</li>
 * <li>{@link #CORNER}: the head turned a corner at pos; id the line, other the bearer, a the beam laid so far (blocks).</li>
 * <li>{@link #HEAD}: the line's head is at pos; id the line, other the bearer, a the head's speed (blocks a tick),
 * b flags: 1 let go of the eyes, 2 under water.</li>
 * <li>{@link #HIT}: a strike landed at pos (the flash ring); id the line.</li>
 * <li>{@link #END}: the line is over at pos and burns away; id the line, other 0 gave up, 1 burnt a block, 2 burnt
 * creatures; a the head's last speed.</li>
 * <li>{@link #BURN_BLOCK}: the block at pos (its corner) turns to embers for a ticks; id its block state id.</li>
 * <li>{@link #BURN_MOB}: the creature with entity id id glows with embers for a ticks.</li>
 * <li>{@link #ASH}: something a wide and b high crumbles to ash at pos (its feet).</li>
 * </ul>
 */
public record OmegaFxPayload(int kind, int id, int other, Vec3 pos, float a, float b) implements CustomPacketPayload {
	public static final int EYES = 0, HEAD = 1, END = 2, BURN_BLOCK = 3, BURN_MOB = 4, ASH = 5, START = 6, CORNER = 7, HIT = 8;
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
