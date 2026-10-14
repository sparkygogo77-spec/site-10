package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.world.phys.Vec3;

/**
 * Client to server, for the combat moves (Blender passes 503, 510): the local client sees its own
 * flight, so it decides when the big flight slam fires and when it touches down.
 * {@link #SLAM} the slam fired at "at" (dir: the move per tick, value: ticks left to the ground),
 * {@link #SLAM_LAND} it touched down at "at" (dir: its last move),
 * {@link #ABSORB} left click held (value 1) or let go (0) with the ring, for the absorb and return blast.
 */
public record CombatPayload(int action, Vec3 at, Vec3 dir, float value) implements CustomPacketPayload {
	public static final int SLAM = 0, SLAM_LAND = 1, ABSORB = 2;
	public static final CustomPacketPayload.Type<CombatPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("combat"));
	public static final StreamCodec<RegistryFriendlyByteBuf, CombatPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, CombatPayload::action, Vec3.STREAM_CODEC, CombatPayload::at, Vec3.STREAM_CODEC, CombatPayload::dir,
			ByteBufCodecs.FLOAT, CombatPayload::value, CombatPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
