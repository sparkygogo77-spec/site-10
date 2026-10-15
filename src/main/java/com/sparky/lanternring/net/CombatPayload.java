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
 * {@link #ABSORB} left click held (value 1) or let go (0) with the ring, for the absorb and return blast,
 * {@link #PRIMED_SLAM} as SLAM, primed by shift in hyper speed (pass 518),
 * {@link #REBUILD} left click on your primed crater at "at" while it is lined,
 * {@link #PUNCH} left click with the ring hand (pass 502: everyone else draws the punch),
 * {@link #DASH} the dash strike (pass 505) leaves "at" (dir: its move per tick, value: the target's id),
 * {@link #DASH_HIT} the dash ended at "at" and the ring fist lands on the target (value: its id).
 */
public record CombatPayload(int action, Vec3 at, Vec3 dir, float value) implements CustomPacketPayload {
	public static final int SLAM = 0, SLAM_LAND = 1, ABSORB = 2, PRIMED_SLAM = 3, REBUILD = 4, PUNCH = 5, DASH = 6, DASH_HIT = 7;
	public static final CustomPacketPayload.Type<CombatPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("combat"));
	public static final StreamCodec<RegistryFriendlyByteBuf, CombatPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, CombatPayload::action, Vec3.STREAM_CODEC, CombatPayload::at, Vec3.STREAM_CODEC, CombatPayload::dir,
			ByteBufCodecs.FLOAT, CombatPayload::value, CombatPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
