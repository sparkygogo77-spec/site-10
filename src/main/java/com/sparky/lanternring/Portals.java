package com.sparky.lanternring;

import com.sparky.lanternring.net.PortalPayload;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.portal.TeleportTransition;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * Open Rick and Morty style portals. Portals come in linked pairs: anything that passes through
 * one (players, mobs, dropped items, arrows) steps out of the front of the other, keeping its
 * speed, even in another dimension. A portal on its own (link null) is just shown, e.g. to
 * confirm where a new exit was set. Portals aren't blocks: the server keeps them here and each
 * client draws them (PortalFx), so they leave nothing behind.
 */
public final class Portals {
	/** The oval is 1.5 blocks wide and 2.4 tall. */
	public static final double HALF_WIDTH = 0.75;
	public static final double HALF_HEIGHT = 1.2;
	/** How close to the portal's plane an entity counts as touching it. */
	private static final double DEPTH = 0.35;
	/** Ticks an entity can't use a portal after coming out of one. */
	private static final int COOLDOWN = 15;
	private static final double SYNC_RANGE = 160;

	public static final class Portal {
		public final int id;
		public final ServerLevel level;
		public final Vec3 center;
		public final float yaw;
		/** Who opened it; a golem's portals are tagged so the player's own pair doesn't close them. */
		final UUID owner;
		final boolean golem;
		Portal link;
		long closeAt;

		Portal(int id, ServerLevel level, Vec3 center, float yaw, UUID owner, boolean golem, long closeAt) {
			this.id = id;
			this.level = level;
			this.center = center;
			this.yaw = yaw;
			this.owner = owner;
			this.golem = golem;
			this.closeAt = closeAt;
		}

		/** The way its front faces. */
		public Vec3 normal() {
			return Portals.normal(yaw);
		}
	}

	private static final List<Portal> OPEN = new ArrayList<>();
	private static final Map<UUID, Long> COOLDOWNS = new HashMap<>();
	private static int nextId = 1;

	private Portals() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(Portals::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			OPEN.clear();
			COOLDOWNS.clear();
		});
	}

	public static Vec3 normal(float yaw) {
		float r = yaw * Mth.DEG_TO_RAD;
		return new Vec3(-Mth.sin(r), 0, Mth.cos(r));
	}

	/** Opens two linked portals for {@code ticks}. Opening a new pair closes the owner's last one. */
	public static Portal[] openPair(ServerLevel aLevel, Vec3 a, float aYaw, ServerLevel bLevel, Vec3 b, float bYaw,
			UUID owner, boolean golem, int ticks) {
		if (!golem) {
			for (Portal p : OPEN) {
				if (!p.golem && owner.equals(p.owner)) p.closeAt = 0;
			}
		}
		long now = aLevel.getServer().getTickCount();
		Portal pa = new Portal(nextId++, aLevel, a, aYaw, owner, golem, now + ticks);
		Portal pb = new Portal(nextId++, bLevel, b, bYaw, owner, golem, now + ticks);
		pa.link = pb;
		pb.link = pa;
		OPEN.add(pa);
		OPEN.add(pb);
		opened(pa);
		opened(pb);
		return new Portal[] {pa, pb};
	}

	/** Shows a lone portal (no way through) for {@code ticks}, e.g. a freshly set exit. */
	public static void show(ServerLevel level, Vec3 center, float yaw, UUID owner, int ticks) {
		Portal p = new Portal(nextId++, level, center, yaw, owner, false, level.getServer().getTickCount() + ticks);
		OPEN.add(p);
		opened(p);
	}

	/** Closes a golem's pair early. */
	public static void close(Portal portal) {
		portal.closeAt = 0;
		if (portal.link != null) portal.link.closeAt = 0;
	}

	private static void opened(Portal p) {
		sync(p, p.level.getServer().getTickCount());
		p.level.playSound(null, p.center.x, p.center.y, p.center.z, SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 0.8f, 1.9f);
		p.level.playSound(null, p.center.x, p.center.y, p.center.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1f, 0.6f);
	}

	private static void sync(Portal p, long now) {
		PortalPayload payload = new PortalPayload(p.id, p.center, p.yaw, (int) Math.max(0, p.closeAt - now));
		for (ServerPlayer player : PlayerLookup.around(p.level, p.center, SYNC_RANGE)) {
			ServerPlayNetworking.send(player, payload);
		}
	}

	private static void tick(MinecraftServer server) {
		if (OPEN.isEmpty()) {
			COOLDOWNS.clear();
			return;
		}
		long now = server.getTickCount();
		COOLDOWNS.values().removeIf(until -> until < now);
		for (Portal p : new ArrayList<>(OPEN)) {
			if (now >= p.closeAt) {
				OPEN.remove(p);
				sync(p, now);
				p.level.playSound(null, p.center.x, p.center.y, p.center.z, SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.5f, 1.8f);
				continue;
			}
			if (now % 10 == 0) sync(p, now);
			if (p.link != null && OPEN.contains(p.link)) passThrough(p, now);
		}
	}

	/** Sends everything crossing this portal's oval out of its partner. */
	private static void passThrough(Portal p, long now) {
		Vec3 n = p.normal();
		Vec3 t = new Vec3(n.z, 0, -n.x);
		AABB box = new AABB(p.center, p.center).inflate(3, HALF_HEIGHT + 2, 3);
		for (Entity e : p.level.getEntities((Entity) null, box, e -> !e.isSpectator() && e.isAlive()
				&& !e.isPassenger() && !e.isVehicle() && !COOLDOWNS.containsKey(e.getUUID()))) {
			double mid = e.getBbHeight() / 2;
			Vec3 now3 = e.position().add(0, mid, 0).subtract(p.center);
			Vec3 old3 = new Vec3(e.xo, e.yo + mid, e.zo).subtract(p.center);
			double d1 = now3.dot(n);
			double d0 = old3.dot(n);
			boolean crossed = (d0 > 0) != (d1 > 0) || Math.abs(d1) < DEPTH;
			if (!crossed) continue;
			// Where it meets the plane must be inside the oval.
			double k = Math.abs(d0 - d1) < 1e-6 ? 1 : Mth.clamp(d0 / (d0 - d1), 0, 1);
			Vec3 at = old3.add(now3.subtract(old3).scale(k));
			double u = at.dot(t) / HALF_WIDTH;
			double v = at.y / HALF_HEIGHT;
			if (u * u + v * v > 1.0) continue;
			// Which side it came in from decides which side of the partner it leaves by.
			double side = Math.abs(d0) > 1e-4 ? Math.signum(d0) : -Math.signum(e.getDeltaMovement().dot(n));
			if (side == 0) side = 1;
			travel(e, p, p.link, side, at, now);
		}
	}

	private static void travel(Entity e, Portal from, Portal to, double side, Vec3 at, long now) {
		Vec3 n1 = from.normal();
		Vec3 n2 = to.normal();
		Vec3 out = n2.scale(side);
		// Turn by the difference between the two portals, plus half a turn: in one side, out the other.
		float turn = to.yaw - from.yaw + 180f;
		Vec3 vel = e.getDeltaMovement();
		double through = Math.max(0.15, Math.abs(vel.dot(n1)));
		Vec3 sideways = rotate(vel.subtract(n1.scale(vel.dot(n1))), turn);
		Vec3 newVel = out.scale(through).add(sideways.x, 0, sideways.z).add(0, vel.y, 0);
		double feet = Mth.clamp(at.y - e.getBbHeight() / 2, -HALF_HEIGHT, HALF_HEIGHT - 0.2);
		Vec3 pos = to.center.add(out.scale(0.6 + e.getBbWidth() / 2)).add(0, feet, 0);
		COOLDOWNS.put(e.getUUID(), now + COOLDOWN);
		e.resetFallDistance();
		Entity moved = e.teleport(new TeleportTransition(to.level, pos, newVel, e.getYRot() + turn, e.getXRot(),
				TeleportTransition.PLACE_PORTAL_TICKET));
		if (moved != null) {
			COOLDOWNS.put(moved.getUUID(), now + COOLDOWN);
			moved.resetFallDistance();
			RingPowers.syncVelocity(moved);
		}
		from.level.playSound(null, from.center.x, from.center.y, from.center.z, SoundEvents.PLAYER_TELEPORT, SoundSource.PLAYERS, 0.7f, 1.5f);
		to.level.playSound(null, to.center.x, to.center.y, to.center.z, SoundEvents.PLAYER_TELEPORT, SoundSource.PLAYERS, 0.7f, 1.5f);
	}

	private static Vec3 rotate(Vec3 v, float degrees) {
		float r = degrees * Mth.DEG_TO_RAD;
		double c = Mth.cos(r), s = Mth.sin(r);
		return new Vec3(v.x * c - v.z * s, v.y, v.x * s + v.z * c);
	}
}
