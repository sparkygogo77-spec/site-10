package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.RingFxPayload;
import java.util.EnumSet;
import java.util.Set;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

/** Tells nearby clients to draw a ring effect. */
public final class RingFx {
	private static final double RANGE = 96;
	/** How far from a player's eyes an effect's start may be to count as coming out of their ring. */
	private static final double BEARER_RANGE = 1.6;
	/** Effects that leave the bearer's ring (their from is the hand, see RingPowers.handPos). */
	private static final Set<RingFxPayload.Kind> EMITS = EnumSet.of(RingFxPayload.Kind.BLAST, RingFxPayload.Kind.BEAM,
			RingFxPayload.Kind.BEAM_CHARGED, RingFxPayload.Kind.CONSTRUCT, RingFxPayload.Kind.TETHER, RingFxPayload.Kind.PUSH,
			RingFxPayload.Kind.EMIT);

	public static void send(ServerLevel level, RingFxPayload.Kind kind, Vec3 from, Vec3 to) {
		send(level, kind, from, to, 0f);
	}

	/** value is extra data for the effect, e.g. the Blast drill's speed. */
	public static void send(ServerLevel level, RingFxPayload.Kind kind, Vec3 from, Vec3 to, float value) {
		send(level, kind, from, to, value, 0);
	}

	/** variant picks a version of the effect, e.g. the Blast's level. */
	public static void send(ServerLevel level, RingFxPayload.Kind kind, Vec3 from, Vec3 to, float value, int variant) {
		Player bearer = EMITS.contains(kind) ? bearerAt(level, from) : null;
		send(level, kind, from, to, value, variant, bearer);
	}

	/**
	 * Like send, naming the player whose ring the effect comes out of (null for none). Effects
	 * whose from is the player's hand (RingPowers.handPos) find their bearer by themselves; aim
	 * markers and the like, whose from is out in the world, name them here.
	 */
	public static void send(ServerLevel level, RingFxPayload.Kind kind, Vec3 from, Vec3 to, float value, int variant, Player bearer) {
		RingFxPayload payload = new RingFxPayload(kind, from, to, value, variant, Corps.current(), bearer == null ? -1 : bearer.getId());
		for (ServerPlayer player : PlayerLookup.around(level, from, RANGE)) {
			ServerPlayNetworking.send(player, payload);
		}
	}

	/** The ring-wearing player whose hand from is at (within BEARER_RANGE of their eyes), or null. */
	private static Player bearerAt(ServerLevel level, Vec3 from) {
		Player best = null;
		double bestDist = BEARER_RANGE * BEARER_RANGE;
		for (ServerPlayer player : level.players()) {
			if (!(RingSlot.ring(player).getItem() instanceof PowerRingItem)) continue;
			double d = player.getEyePosition().distanceToSqr(from);
			if (d < bestDist) {
				bestDist = d;
				best = player;
			}
		}
		return best;
	}

	public static void send(ServerLevel level, RingFxPayload.Kind kind, Vec3 at) {
		send(level, kind, at, at);
	}

	private RingFx() {
	}
}
