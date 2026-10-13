package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/** Client to server: the Ring Lab's pick of how big a hole the ram barrier leaves in a wall (RamBarrier.Hole ordinal). */
public record RamHolePayload(int hole) implements CustomPacketPayload {
	public static final CustomPacketPayload.Type<RamHolePayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("ram_hole"));
	public static final StreamCodec<RegistryFriendlyByteBuf, RamHolePayload> CODEC =
			ByteBufCodecs.VAR_INT.map(RamHolePayload::new, RamHolePayload::hole).cast();

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
