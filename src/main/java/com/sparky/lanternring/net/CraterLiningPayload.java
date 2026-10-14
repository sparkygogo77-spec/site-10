package com.sparky.lanternring.net;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import io.netty.buffer.ByteBuf;
import java.util.List;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.core.BlockPos;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.network.protocol.common.custom.CustomPacketPayload;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

/**
 * Server to client: the blocks a landing blasted out of the ground (J, 2026-10-13: "all of the
 * landings should get this, hammer too"). Each client lines that crater, and only it, with the
 * construct pad: a plate on every face of a block left standing against it (SuperLandConstruct).
 * {@code hold} is how many ticks the lining stays before it dissolves; 0 means a super jump's,
 * which waits for its SUPER_LAND and dissolves after the stand-up.
 */
public record CraterLiningPayload(int bearer, Corps corps, Vec3 centre, int hold, List<BlockPos> blocks) implements CustomPacketPayload {
	/** The most blocks one crater sends. */
	public static final int MAX = 2048;
	public static final CustomPacketPayload.Type<CraterLiningPayload> TYPE = new CustomPacketPayload.Type<>(LanternRing.id("crater_lining"));
	public static final StreamCodec<ByteBuf, CraterLiningPayload> CODEC = StreamCodec.composite(
			ByteBufCodecs.VAR_INT, CraterLiningPayload::bearer,
			Corps.STREAM_CODEC, CraterLiningPayload::corps,
			Vec3.STREAM_CODEC, CraterLiningPayload::centre,
			ByteBufCodecs.VAR_INT, CraterLiningPayload::hold,
			BlockPos.STREAM_CODEC.apply(ByteBufCodecs.list(MAX)), CraterLiningPayload::blocks,
			CraterLiningPayload::new);

	/** Sends a crater to everyone near it (nothing when no block was blasted). */
	public static void send(ServerLevel level, int bearer, Corps corps, Vec3 centre, int hold, List<BlockPos> blocks) {
		if (blocks.isEmpty()) return;
		CraterLiningPayload payload = new CraterLiningPayload(bearer, corps, centre, hold, List.copyOf(blocks.subList(0, Math.min(MAX, blocks.size()))));
		for (ServerPlayer viewer : PlayerLookup.around(level, centre, 128)) ServerPlayNetworking.send(viewer, payload);
	}

	@Override
	public Type<? extends CustomPacketPayload> type() {
		return TYPE;
	}
}
