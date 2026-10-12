package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.LassoInputPayload;
import com.sparky.lanternring.net.LassoPayload;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
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
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * LASSO (the TETHER mode): hold right-click to catch a mob in a bubble of hard light tied to the
 * ring by a green string. The bubble is a spring-pulled body the server moves itself: it chases a
 * point straight ahead of the bearer, so swinging your view swings the mob and builds momentum,
 * and letting go throws it with whatever speed it had. A far catch is reeled in; left-click sends
 * it further out; space holds it at its current distance (space again resumes reeling). Nothing
 * can hurt the mob in the bubble, and it can't hurt anyone, except that slamming the bubble into
 * the ground or a wall deals fall damage. The bubble collides as a box around the whole sphere,
 * so it never sinks into the ground or passes through blocks.
 */
public final class Lasso {
	/** How far the lasso reaches to catch something. */
	public static final double RANGE = 32;
	/** Gap between the bubble's surface and the bearer's eyes once reeled in. */
	private static final double CLOSE = 2.5;
	/** How far a catch can be sent out with left-click. */
	private static final double MAX_DISTANCE = 40;
	private static final double SEND_STEP = 8;
	/** The string snaps if the bubble ends up this far beyond its hold distance (stuck behind terrain). */
	private static final double SNAP_SLACK = 12;
	/** Spring towards the hold point, and how much speed survives each tick. */
	private static final double SPRING = 0.3;
	private static final double DAMPING = 0.7;
	private static final double MAX_SPEED = 3.0;
	/** Hitting a block faster than this (blocks per tick) hurts. */
	private static final double SMASH_SPEED = 0.7;
	private static final float SMASH_DAMAGE_PER_SPEED = 12f;
	private static final double MAX_RADIUS = 3;

	public static final int INPUT_SEND = 0;
	public static final int INPUT_HOLD = 1;

	private static final class Catch {
		final ServerLevel level;
		final LivingEntity target;
		final double radius;
		Vec3 center;
		Vec3 velocity = Vec3.ZERO;
		double distance;
		boolean holding;
		long lastTick;
		/** Which axes were pressed against a block last tick: a smash needs a fresh hit. */
		final boolean[] blocked = new boolean[3];

		Catch(ServerLevel level, LivingEntity target, double distance) {
			this.level = level;
			this.target = target;
			this.radius = radiusFor(target);
			this.center = target.getBoundingBox().getCenter();
			this.distance = distance;
		}
	}

	private static final Map<UUID, Catch> CATCHES = new HashMap<>();
	/** Set while the lasso itself deals a smash, so the bubble's protection lets it through. */
	private static boolean smashing;

	private Lasso() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(Lasso::cleanup);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> CATCHES.clear());
		ServerPlayNetworking.registerGlobalReceiver(LassoInputPayload.TYPE, (payload, context) -> input(context.player(), payload.action()));
		ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) -> {
			if (smashing) return true;
			if (isCaught(entity)) return false;
			// A caught mob can't hit anything from inside its bubble.
			Entity attacker = source.getEntity();
			return !(attacker instanceof LivingEntity living && isCaught(living));
		});
	}

	private static boolean isCaught(LivingEntity entity) {
		for (Catch c : CATCHES.values()) {
			if (c.target == entity) return true;
		}
		return false;
	}

	private static double radiusFor(LivingEntity target) {
		AABB box = target.getBoundingBox();
		double hx = box.getXsize() / 2, hy = box.getYsize() / 2, hz = box.getZsize() / 2;
		return Math.min(MAX_RADIUS, Math.sqrt(hx * hx + hy * hy + hz * hz) + 0.15);
	}

	/** Called every tick while the ring is held in this mode. */
	public static void tick(ServerPlayer player, ItemStack ring) {
		ServerLevel level = player.level();
		Catch c = CATCHES.get(player.getUUID());
		if (c != null && (c.level != level || !c.target.isAlive())) {
			release(player);
			c = null;
		}
		if (c == null) {
			c = tryCatch(level, player);
			if (c == null) return;
			CATCHES.put(player.getUUID(), c);
		}
		c.lastTick = level.getGameTime();

		Vec3 eye = player.getEyePosition();
		Vec3 look = player.getLookAngle();
		double close = CLOSE + c.radius;
		if (!c.holding && c.distance > close) {
			double reel = (RANGE - CLOSE) / Math.max(1, RingTuning.LASSO_REEL_TIME.ticks());
			c.distance = Math.max(close, c.distance - reel);
		}
		Vec3 hold = eye.add(look.scale(c.distance));

		c.velocity = c.velocity.scale(DAMPING).add(hold.subtract(c.center).scale(SPRING));
		if (c.velocity.length() > MAX_SPEED) c.velocity = c.velocity.normalize().scale(MAX_SPEED);
		move(c, player);

		if (c.center.distanceTo(eye) > c.distance + c.radius + SNAP_SLACK) {
			release(player);
			return;
		}

		LivingEntity target = c.target;
		AABB box = target.getBoundingBox();
		target.setPos(c.center.x, c.center.y - box.getYsize() / 2, c.center.z);
		target.setDeltaMovement(c.velocity);
		target.resetFallDistance();
		RingPowers.syncVelocity(target);

		player.resetFallDistance();
		if (!player.isCreative()) {
			PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - 1);
			if (PowerRingItem.getCharge(ring) == 0) player.stopUsingItem();
		}
		broadcast(level, player, c);
	}

	private static Catch tryCatch(ServerLevel level, ServerPlayer player) {
		RingPowers.Target hit = RingPowers.trace(level, player, RANGE);
		if (!(hit.entity() instanceof LivingEntity target) || target instanceof Player || !target.isAlive()
				|| isCaught(target)) {
			return null;
		}
		double distance = Math.min(MAX_DISTANCE, target.getBoundingBox().getCenter().distanceTo(player.getEyePosition()));
		Catch c = new Catch(level, target, distance);
		c.velocity = target.getDeltaMovement();
		// The bubble is bigger than the mob, so lift it clear of the ground it was standing on.
		liftClear(c);
		RingFx.send(level, Kind.TETHER, RingPowers.handPos(player), c.center);
		level.playSound(null, target.getX(), target.getY(), target.getZ(), SoundEvents.FISHING_BOBBER_THROW,
				SoundSource.PLAYERS, 1.0f, 0.7f);
		level.playSound(null, target.getX(), target.getY(), target.getZ(), SoundEvents.AMETHYST_BLOCK_RESONATE,
				SoundSource.PLAYERS, 0.8f, 1.6f);
		return c;
	}

	/**
	 * Moves the bubble by its velocity, one axis at a time in small steps so it can't skip through
	 * thin walls. An axis that runs into a block stops, and smashes the mob if it hit hard.
	 */
	private static void move(Catch c, ServerPlayer player) {
		Vec3 v = c.velocity;
		int steps = Math.max(1, (int) Math.ceil(v.length() / 0.4));
		// Wedged in (a block appeared around it): float up out of it if it can, otherwise move by
		// the mob's own box until the bubble is clear again.
		boolean wedged = !liftClear(c);
		double[] moved = new double[3];
		boolean[] hit = new boolean[3];
		for (int s = 0; s < steps; s++) {
			for (int axis : new int[] {1, 0, 2}) {
				if (hit[axis]) continue;
				double amount = component(v, axis) / steps;
				if (amount == 0) continue;
				Vec3 next = c.center.add(axisVec(axis, amount));
				if (free(c, wedged ? mobBox(c, next) : bubble(next, c.radius))) {
					c.center = next;
					moved[axis] += amount;
					continue;
				}
				// Close the last gap to the block, then stop on this axis.
				double lo = 0, hi = amount;
				for (int i = 0; i < 6; i++) {
					double mid = (lo + hi) / 2;
					Vec3 at = c.center.add(axisVec(axis, mid));
					if (free(c, wedged ? mobBox(c, at) : bubble(at, c.radius))) lo = mid;
					else hi = mid;
				}
				c.center = c.center.add(axisVec(axis, lo));
				hit[axis] = true;
			}
		}

		double impact = 0;
		for (int axis = 0; axis < 3; axis++) {
			if (hit[axis] && !c.blocked[axis]) impact = Math.max(impact, Math.abs(component(v, axis)));
			c.blocked[axis] = hit[axis];
		}
		if (hit[0] || hit[1] || hit[2]) {
			c.velocity = new Vec3(hit[0] ? 0 : v.x, hit[1] ? 0 : v.y, hit[2] ? 0 : v.z);
		}
		if (impact > SMASH_SPEED) smash(c, player, impact);
	}

	private static void smash(Catch c, ServerPlayer player, double speed) {
		float damage = (float) ((speed - SMASH_SPEED) * SMASH_DAMAGE_PER_SPEED) + 2f;
		smashing = true;
		try {
			c.target.hurtServer(c.level, c.level.damageSources().fall(), damage);
		} finally {
			smashing = false;
		}
		float volume = (float) Mth.clamp(speed / 2, 0.4, 1.2);
		c.level.playSound(null, c.center.x, c.center.y, c.center.z, SoundEvents.MACE_SMASH_GROUND,
				SoundSource.PLAYERS, volume, 1.1f);
		RingFx.send(c.level, Kind.MODE_CHANGE, c.center.subtract(0, 1 + c.radius * 0.5, 0));
	}

	/** Raises the bubble by up to its radius until it touches no blocks; false if it can't get clear. */
	private static boolean liftClear(Catch c) {
		for (double up = 0; up <= c.radius + 0.5; up += 0.1) {
			Vec3 lifted = c.center.add(0, up, 0);
			if (free(c, bubble(lifted, c.radius))) {
				c.center = lifted;
				return true;
			}
		}
		return false;
	}

	private static boolean free(Catch c, AABB box) {
		return c.level.noCollision(c.target, box);
	}

	private static AABB bubble(Vec3 center, double radius) {
		return new AABB(center, center).inflate(radius);
	}

	private static AABB mobBox(Catch c, Vec3 center) {
		AABB box = c.target.getBoundingBox();
		return box.move(center.subtract(box.getCenter()));
	}

	private static double component(Vec3 v, int axis) {
		return axis == 0 ? v.x : axis == 1 ? v.y : v.z;
	}

	private static Vec3 axisVec(int axis, double amount) {
		return new Vec3(axis == 0 ? amount : 0, axis == 1 ? amount : 0, axis == 2 ? amount : 0);
	}

	/** Left-click and space from the bearer's client. */
	private static void input(ServerPlayer player, int action) {
		Catch c = CATCHES.get(player.getUUID());
		if (c == null) return;
		if (action == INPUT_SEND) {
			c.distance = Math.min(MAX_DISTANCE, c.distance + SEND_STEP);
			c.velocity = c.velocity.add(player.getLookAngle().scale(1.2));
			c.level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.FISHING_BOBBER_THROW,
					SoundSource.PLAYERS, 0.8f, 1.2f);
		} else if (action == INPUT_HOLD) {
			c.holding = !c.holding;
			c.level.playSound(null, c.center.x, c.center.y, c.center.z, SoundEvents.AMETHYST_BLOCK_CHIME,
					SoundSource.PLAYERS, 1.0f, c.holding ? 0.8f : 1.4f);
		}
		broadcast(c.level, player, c);
	}

	/** Lets go: the mob flies off with the bubble's speed. */
	public static void release(Player player) {
		Catch c = CATCHES.remove(player.getUUID());
		if (c == null) return;
		if (c.target.isAlive()) {
			c.target.setDeltaMovement(c.velocity);
			RingPowers.syncVelocity(c.target);
		}
		c.level.playSound(null, c.center.x, c.center.y, c.center.z, SoundEvents.AMETHYST_CLUSTER_BREAK,
				SoundSource.PLAYERS, 0.8f, 1.5f);
		for (ServerPlayer viewer : PlayerLookup.around(c.level, c.center, 96)) {
			ServerPlayNetworking.send(viewer, new LassoPayload(player.getId(), -1, 0f, false));
		}
	}

	private static void broadcast(ServerLevel level, Player holder, Catch c) {
		LassoPayload payload = new LassoPayload(holder.getId(), c.target.getId(), (float) c.radius, c.holding);
		for (ServerPlayer viewer : PlayerLookup.around(level, c.center, 96)) {
			ServerPlayNetworking.send(viewer, payload);
		}
	}

	/** Lets go of catches whose bearer stopped holding the ring without a release (item switched, logged out...). */
	private static void cleanup(MinecraftServer server) {
		for (Iterator<Map.Entry<UUID, Catch>> it = CATCHES.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<UUID, Catch> e = it.next();
			Catch c = e.getValue();
			ServerPlayer player = server.getPlayerList().getPlayer(e.getKey());
			boolean stillHolding = player != null && player.isUsingItem()
					&& player.getUseItem().getItem() instanceof PowerRingItem
					&& c.level.getGameTime() - c.lastTick <= 2;
			if (!stillHolding) {
				if (player != null) {
					release(player);
				} else {
					it.remove();
				}
				// release() removed the entry through the map, so restart iteration safely.
				return;
			}
		}
	}
}
