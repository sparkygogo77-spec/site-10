package com.sparky.lanternring;

import com.sparky.lanternring.net.RingFxPayload;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

/** Tells nearby clients to draw a ring effect. */
public final class RingFx {
	private static final double RANGE = 96;

	public static void send(ServerLevel level, RingFxPayload.Kind kind, Vec3 from, Vec3 to) {
		RingFxPayload payload = new RingFxPayload(kind, from, to);
		for (ServerPlayer player : PlayerLookup.around(level, from, RANGE)) {
			ServerPlayNetworking.send(player, payload);
		}
	}

	public static void send(ServerLevel level, RingFxPayload.Kind kind, Vec3 at) {
		send(level, kind, at, at);
	}

	private RingFx() {
	}
}
