package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;

/**
 * Client to server, for SuperJumps: {@link #JUMP} the player just super jumped (value 0..1: how
 * charged), or {@link #SPRINT} their Ring Lab's Super sprint pick (value: the extra speed, 0 for off).
 */
public record SuperJumpPayload(int action, float value) implements CustomPacketPayload {
	public static final int JUMP = 0, SPRINT = 1;
	public static final CustomPacketPayload.Type<SuperJumpPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("super_jump"));
	public static final StreamCodec<RegistryFriendlyByteBuf, SuperJumpPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, SuperJumpPayload::action, ByteBufCodecs.FLOAT, SuperJumpPayload::value, SuperJumpPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
