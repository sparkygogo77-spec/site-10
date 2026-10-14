package com.sparky.lanternring.net;

import com.sparky.lanternring.LanternRing;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.world.phys.Vec3;

/**
 * Client to server, for MoveFlights: the ring flight moves only the flyer's own client sees start, passed
 * on so everyone else can draw them. {@link #TAKEOFF} the F2 rocket takeoff (dir: the way it launches),
 * {@link #GROUND} low ground flight starts (value 1, dir its heading) or ends (value 0),
 * {@link #GROUND_HIT} its barrier hit a wall at "at" (dir: the wall's face, value: the halt take 0..2),
 * {@link #BOOM} a sonic boom at "at" (dir: the way the flyer is going),
 * {@link #LAND} a super jump touched down at "at" (dir: its last move across the ground, blocks a tick; see PowerLandings),
 * {@link #SOFT_LAND} the L2 soft landing (dir: its heading; value 1 starts the descent, 2 touches down, 0 cancels it).
 */
public record MoveFxPayload(int action, Vec3 at, Vec3 dir, float value) implements CustomPacketPayload {
	public static final int TAKEOFF = 0, GROUND = 1, GROUND_HIT = 2, BOOM = 3, LAND = 4, SOFT_LAND = 5;
	public static final CustomPacketPayload.Type<MoveFxPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("move_fx"));
	public static final StreamCodec<RegistryFriendlyByteBuf, MoveFxPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, MoveFxPayload::action, Vec3.STREAM_CODEC, MoveFxPayload::at, Vec3.STREAM_CODEC, MoveFxPayload::dir,
			ByteBufCodecs.FLOAT, MoveFxPayload::value, MoveFxPayload::new);

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
