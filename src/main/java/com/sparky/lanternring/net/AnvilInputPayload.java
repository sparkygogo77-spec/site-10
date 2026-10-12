package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Client to server in Anvil mode: left-click held (AIM, sent every tick it is held), then one
 * RELEASE when it's let go; or a left-click while right-click is held (CYCLE, the next size).
 * BLAST_CYCLE is a left-click while charging the Blast: the next level (see BlastDrills).
 */
public record AnvilInputPayload(int action) implements CustomPacketPayload {
	public static final int RELEASE = 0, AIM = 1, CYCLE = 2, BLAST_CYCLE = 3;

	public static final CustomPacketPayload.Type<AnvilInputPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("anvil_input"));
	public static final StreamCodec<ByteBuf, AnvilInputPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, AnvilInputPayload::action,
			AnvilInputPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
