package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Client to server: a left-click while right-click is held to aim the Anvil (CYCLE, the next
 * size), to charge the Blast (BLAST_CYCLE, the next level; see BlastDrills) or to aim the Deluge
 * (DELUGE_CYCLE, the next level; see Deluges) or the Black Hole (BLACK_HOLE_CYCLE, the next size;
 * see BlackHoles), or to summon in Army mode (ARMY_CYCLE, the next construct; see ConstructArmy).
 * Aiming and dropping
 * the Anvil go with right-click itself (see PowerRingItem).
 */
public record AnvilInputPayload(int action) implements CustomPacketPayload {
	public static final int CYCLE = 2, BLAST_CYCLE = 3, DELUGE_CYCLE = 4, BLACK_HOLE_CYCLE = 5;
	/** Build mode: the next area shape while holding; the next or previous design while choosing (see Builds). */
	public static final int BUILD_SHAPE = 6, BUILD_NEXT = 7, BUILD_PREV = 8;
	/** Army mode: the next construct while holding (see ConstructArmy). */
	public static final int ARMY_CYCLE = 9;
	/** Build mode: the next or previous materials of the design showing (crouch + scroll; see Builds). */
	public static final int BUILD_MATERIAL_NEXT = 10, BUILD_MATERIAL_PREV = 11;
	/** Deluge mode, not aiming: left-click held sucks the bearer's Deluges back into the ring (see Deluges.recall). */
	public static final int DELUGE_RECALL = 12;
	/** Bridge mode while right-click is held: left-click held builds (sent every tick), space and crouch move the deck a level (see Bridges). */
	public static final int BRIDGE_BUILD = 13, BRIDGE_UP = 14, BRIDGE_DOWN = 15;

	public static final CustomPacketPayload.Type<AnvilInputPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("anvil_input"));
	public static final StreamCodec<ByteBuf, AnvilInputPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, AnvilInputPayload::action,
			AnvilInputPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
