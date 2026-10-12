package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Client to server: a left-click while right-click is held to aim the Anvil (CYCLE, the next
 * size) or to charge the Blast (BLAST_CYCLE, the next level; see BlastDrills). Aiming and dropping
 * the Anvil go with right-click itself (see PowerRingItem).
 */
public record AnvilInputPayload(int action) implements CustomPacketPayload {
	public static final int CYCLE = 2, BLAST_CYCLE = 3;

	public static final CustomPacketPayload.Type<AnvilInputPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("anvil_input"));
	public static final StreamCodec<ByteBuf, AnvilInputPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, AnvilInputPayload::action,
			AnvilInputPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
