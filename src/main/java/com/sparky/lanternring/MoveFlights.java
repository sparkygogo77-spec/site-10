package com.sparky.lanternring;

import com.sparky.lanternring.net.MoveFxPayload;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/**
 * J's movement and flight hand-off (2026-10-14): the take-off (F2 rocket, then pass 403's double-jump
 * puff and dart), the L2 soft landing, low ground flight with its running barrier, and the sonic boom. Movement is the flyer's own client's; this only checks they carry
 * a ring and passes each move on to everyone nearby as a RingFx (FLIGHT_TAKEOFF, GROUND_FLIGHT,
 * GROUND_HIT, SONIC_BOOM, SOFT_LANDING), in the ring's corps colour, so every client draws the poses and effects.
 */
public final class MoveFlights {
	/** Players in low ground flight: the ram barrier stays down for them (the running barrier is theirs). */
	private static final Set<UUID> GROUND = new HashSet<>();

	private MoveFlights() {
	}

	static void register() {
		PayloadTypeRegistry.serverboundPlay().register(MoveFxPayload.TYPE, MoveFxPayload.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(MoveFxPayload.TYPE, (payload, context) -> handle(context.player(), payload));
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> GROUND.remove(handler.player.getUUID()));
	}

	/** Whether this player is skimming the ground in low flight. */
	public static boolean grounded(ServerPlayer player) {
		return GROUND.contains(player.getUUID());
	}

	private static void handle(ServerPlayer player, MoveFxPayload payload) {
		ItemStack ring = RingFlight.findRing(player);
		if (ring.isEmpty() || !(player.level() instanceof ServerLevel level)) return;
		// A client may only report moves near where it is.
		Vec3 at = payload.at().distanceTo(player.position()) > 8 ? player.position() : payload.at();
		Vec3 dir = payload.dir().lengthSqr() > 1e-6 ? payload.dir().normalize() : player.getLookAngle();
		if (payload.action() == MoveFxPayload.LAND) {
			Vec3 step = payload.dir();
			PowerLandings.reported(player, at, step.length() > 2.5 ? step.normalize().scale(2.5) : step);
			return;
		}
		Kind kind;
		float value = payload.value();
		switch (payload.action()) {
			case MoveFxPayload.TAKEOFF -> {
				kind = Kind.FLIGHT_TAKEOFF;
				value = Mth.clamp(Math.round(value), 0, 4);
			}
			case MoveFxPayload.SOFT_LAND -> {
				kind = Kind.SOFT_LANDING;
				value = Mth.clamp(Math.round(value), 0, 2);
			}
			case MoveFxPayload.GROUND -> {
				kind = Kind.GROUND_FLIGHT;
				if (value > 0) GROUND.add(player.getUUID());
				else GROUND.remove(player.getUUID());
			}
			case MoveFxPayload.GROUND_HIT -> {
				kind = Kind.GROUND_HIT;
				value = Mth.clamp(Math.round(value), 0, 2);
			}
			case MoveFxPayload.BOOM -> kind = Kind.SONIC_BOOM;
			default -> {
				return;
			}
		}
		Corps before = Corps.enter(Corps.of(ring));
		try {
			RingFx.send(level, kind, at, at.add(dir), value, player.getId(), player);
		} finally {
			Corps.restore(before);
		}
	}
}
