package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.LassoInputPayload;
import com.sparky.lanternring.net.LassoPayload;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
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
 * point straight ahead of the bearer, so swinging your view swings the mob and builds momentum.
 * Letting go throws it: the bubble keeps flying with its momentum (barely slowed by the air) until
 * it hits something, then pops. A far catch is reeled in when caught; space stops the reel (and
 * starts it again). Holding left-click pushes it further out, faster the longer it is held, and it
 * stays wherever it is left. Nothing can hurt the mob in the bubble, and it can't hurt anyone,
 * except that slamming the bubble into the ground or a wall deals fall damage. The bubble collides
 * as a box around the whole sphere, so it never sinks into the ground or passes through blocks.
 *
 * <p>There is no fixed reach limit: a catch can be pushed out as far as the bearer's client can still
 * see the mob (the server's view distance, or the mob type's tracking range if that is shorter). A
 * bubble moving fast bowls over anything it hits, and a hard slam knocks back everything around it.
 * The rope's hum is drawn by the clients (LassoSound), which bend it with the rope's length.
 */
public final class Lasso {
	/** How far the lasso reaches to catch something. */
	public static final double RANGE = 64;
	/** Reeling in covers this many blocks in RingTuning.LASSO_REEL_TIME (the menu says "from 32 blocks"). */
	private static final double REEL_SPAN = 32;
	/** Gap between the bubble's surface and the bearer's eyes once reeled in. */
	private static final double CLOSE = 2.5;
	/** Hard cap on how far a catch can be pushed out; usually the view distance stops it first. */
	private static final double MAX_DISTANCE = 512;
	/** Push speed in blocks per tick: starts slow and builds up the longer left-click is held. */
	private static final double PUSH_START = 0.08;
	private static final double PUSH_GAIN = 0.035;
	private static final double PUSH_MAX = 3.0;
	/** A thrown bubble: how much speed survives each tick in the air, and its gravity. */
	private static final double FLIGHT_DRAG = 0.996;
	private static final double FLIGHT_GRAVITY = 0.04;
	/** Throws come out much harder than the swing, so a good swing sends a mob a very long way. */
	private static final double THROW_BOOST = 1.8;
	private static final double THROW_MAX_SPEED = 9.0;
	private static final double MIN_THROW_SPEED = 0.35;
	private static final int MAX_FLIGHT_TICKS = 1200;
	/** The string snaps if the bubble ends up this far beyond its hold distance (stuck behind terrain). */
	private static final double SNAP_SLACK = 12;
	/** Spring towards the hold point, and how much speed survives each tick. */
	private static final double SPRING = 0.3;
	private static final double DAMPING = 0.7;
	private static final double MAX_SPEED = 6.0;
	/** Hitting a block faster than this (blocks per tick) hurts. */
	private static final double SMASH_SPEED = 0.7;
	private static final float SMASH_DAMAGE_PER_SPEED = 12f;
	/** A slam this fast (blocks per tick) or more is a heavy one: crater blast and knockback around it. */
	private static final double HEAVY_SMASH = 1.6;
	/** Mobs the bubble runs into while going at least this fast get bowled over. */
	private static final double BOWL_SPEED = 0.6;
	private static final double MAX_RADIUS = 3;

	public static final int INPUT_SEND = 0;
	public static final int INPUT_HOLD = 1;

	private static final class Catch {
		final ServerLevel level;
		final LivingEntity target;
		final Player holder;
		final double radius;
		Vec3 center;
		Vec3 velocity = Vec3.ZERO;
		double distance;
		/** Pulling the catch in towards the bearer (on when caught; space toggles it). */
		boolean reeling = true;
		/** Ticks left-click has been held in a row, and the last tick it was. */
		int pushTicks;
		long lastPush = -10;
		long lastTick;
		int flightTicks;
		/** Which axes were pressed against a block last tick: a smash needs a fresh hit. */
		final boolean[] blocked = new boolean[3];
		/** Mobs this bubble already bowled over, so each one is hit once. */
		final Set<Integer> bowled = new HashSet<>();

		Catch(ServerLevel level, Player holder, LivingEntity target, double distance) {
			this.level = level;
			this.holder = holder;
			this.target = target;
			this.radius = radiusFor(target);
			this.center = target.getBoundingBox().getCenter();
			this.distance = distance;
		}
	}

	private static final Map<UUID, Catch> CATCHES = new HashMap<>();
	/** Thrown bubbles still in the air, by their mob. */
	private static final Map<UUID, Catch> FLYING = new HashMap<>();
	/** Set while the lasso itself deals a smash, so the bubble's protection lets it through. */
	private static boolean smashing;

	private Lasso() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(Lasso::cleanup);
		ServerTickEvents.END_SERVER_TICK.register(Lasso::fly);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			CATCHES.clear();
			FLYING.clear();
		});
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
		if (FLYING.containsKey(entity.getUUID())) return true;
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
		if (c.lastPush < level.getGameTime() - 1) c.pushTicks = 0;
		if (c.reeling && c.distance > close) {
			double reel = (REEL_SPAN - CLOSE) / Math.max(1, RingTuning.LASSO_REEL_TIME.ticks());
			c.distance = Math.max(close, c.distance - reel);
		}
		Vec3 hold = eye.add(look.scale(c.distance));

		c.velocity = c.velocity.scale(DAMPING).add(hold.subtract(c.center).scale(SPRING));
		if (c.velocity.length() > MAX_SPEED) c.velocity = c.velocity.normalize().scale(MAX_SPEED);
		move(c);

		if (c.center.distanceTo(eye) > c.distance + c.radius + SNAP_SLACK) {
			release(player);
			return;
		}

		place(c);

		player.resetFallDistance();
		if (!player.isCreative()) {
			PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - 1);
			if (PowerRingItem.getCharge(ring) == 0) player.stopUsingItem();
		}
		broadcast(player.getId(), c);
	}

	/** Puts the mob where its bubble is, moving the way the bubble moves. */
	private static void place(Catch c) {
		LivingEntity target = c.target;
		AABB box = target.getBoundingBox();
		target.setPos(c.center.x, c.center.y - box.getYsize() / 2, c.center.z);
		target.setDeltaMovement(c.velocity);
		target.resetFallDistance();
		RingPowers.syncVelocity(target);
	}

	private static Catch tryCatch(ServerLevel level, ServerPlayer player) {
		RingPowers.Target hit = RingPowers.trace(level, player, RANGE);
		if (!(hit.entity() instanceof LivingEntity target) || target instanceof Player || !target.isAlive()) {
			return null;
		}
		for (Catch other : CATCHES.values()) {
			if (other.target == target) return null;
		}
		// A thrown bubble can be caught again in mid-air.
		FLYING.remove(target.getUUID());
		double distance = Math.min(reach(level, target), target.getBoundingBox().getCenter().distanceTo(player.getEyePosition()));
		Catch c = new Catch(level, player, target, distance);
		c.velocity = target.getDeltaMovement();
		// The bubble is bigger than the mob, so lift it clear of the ground it was standing on.
		liftClear(c);
		RingFx.send(level, Kind.TETHER, RingPowers.handPos(player), c.center);
		level.playSound(null, target.getX(), target.getY(), target.getZ(), SoundEvents.BEACON_POWER_SELECT,
				SoundSource.PLAYERS, 0.9f, 1.5f);
		level.playSound(null, target.getX(), target.getY(), target.getZ(), SoundEvents.AMETHYST_BLOCK_RESONATE,
				SoundSource.PLAYERS, 0.8f, 1.6f);
		return c;
	}

	/**
	 * How far out a catch can go: as far as the bearer's client still sees the mob, which is the
	 * server's view distance or the mob type's tracking range, whichever is shorter.
	 */
	private static double reach(ServerLevel level, LivingEntity target) {
		int chunks = Math.min(level.getServer().getPlayerList().getViewDistance(), target.getType().clientTrackingRange());
		return Mth.clamp(chunks * 16 - 8, RANGE, MAX_DISTANCE);
	}

	/**
	 * Moves the bubble by its velocity, one axis at a time in small steps so it can't skip through
	 * thin walls. An axis that runs into a block stops, and smashes the mob if it hit hard.
	 */
	private static boolean move(Catch c) {
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
		if (impact > SMASH_SPEED) smash(c, impact);
		bowl(c, v);
		return hit[0] || hit[1] || hit[2];
	}

	/** A fast bubble knocks the mobs it runs into flying, each one once. */
	private static void bowl(Catch c, Vec3 v) {
		double speed = v.length();
		if (speed < BOWL_SPEED) return;
		AABB box = bubble(c.center, c.radius).expandTowards(v.scale(-1));
		for (Entity e : c.level.getEntities(c.target, box, e -> e instanceof LivingEntity && e != c.holder && e.isAlive())) {
			LivingEntity mob = (LivingEntity) e;
			if (isCaught(mob) || !c.bowled.add(mob.getId())) continue;
			Vec3 away = mob.getBoundingBox().getCenter().subtract(c.center).normalize();
			Vec3 push = v.scale(0.9).add(away.scale(0.6)).add(0, 0.35 + speed * 0.1, 0);
			mob.setDeltaMovement(push);
			RingPowers.syncVelocity(mob);
			mob.hurtServer(c.level, c.level.damageSources().thrown(c.target, c.holder), (float) (2 + speed * 3));
			c.level.playSound(null, mob.getX(), mob.getY(), mob.getZ(), SoundEvents.MACE_SMASH_AIR,
					SoundSource.PLAYERS, 1.0f, 1.2f);
			c.level.sendParticles(ParticleTypes.CRIT, mob.getX(), mob.getY() + mob.getBbHeight() / 2, mob.getZ(),
					12, 0.3, 0.3, 0.3, 0.4);
		}
	}

	private static void smash(Catch c, double speed) {
		float damage = (float) ((speed - SMASH_SPEED) * SMASH_DAMAGE_PER_SPEED) + 2f;
		smashing = true;
		try {
			c.target.hurtServer(c.level, c.level.damageSources().fall(), damage);
		} finally {
			smashing = false;
		}
		float volume = (float) Mth.clamp(speed / 2, 0.4, 2.0);
		boolean heavy = speed >= HEAVY_SMASH;
		c.level.playSound(null, c.center.x, c.center.y, c.center.z,
				heavy ? SoundEvents.MACE_SMASH_GROUND_HEAVY : SoundEvents.MACE_SMASH_GROUND, SoundSource.PLAYERS, volume, heavy ? 0.9f : 1.1f);
		RingFx.send(c.level, Kind.MODE_CHANGE, c.center.subtract(0, 1 + c.radius * 0.5, 0));
		if (!heavy) return;
		// A heavy slam: a burst of dust and a blast, and everything nearby is thrown back.
		c.level.playSound(null, c.center.x, c.center.y, c.center.z, SoundEvents.GENERIC_EXPLODE,
				SoundSource.PLAYERS, (float) Mth.clamp(speed / 4, 0.4, 1.0), 1.3f);
		c.level.sendParticles(ParticleTypes.EXPLOSION, c.center.x, c.center.y, c.center.z, 1 + (int) speed, c.radius,
				c.radius * 0.5, c.radius, 0);
		c.level.sendParticles(ParticleTypes.CLOUD, c.center.x, c.center.y - c.radius, c.center.z, 30, c.radius + 0.5,
				0.2, c.radius + 0.5, 0.15);
		double reach = c.radius + 2 + speed;
		for (Entity e : c.level.getEntities(c.target, bubble(c.center, reach), e -> e instanceof LivingEntity && e != c.holder)) {
			LivingEntity mob = (LivingEntity) e;
			if (isCaught(mob)) continue;
			Vec3 away = mob.position().subtract(c.center);
			double falloff = 1 - Math.min(1, away.length() / reach);
			Vec3 flat = new Vec3(away.x, 0, away.z);
			flat = flat.lengthSqr() < 1e-4 ? Vec3.ZERO : flat.normalize();
			mob.setDeltaMovement(mob.getDeltaMovement().add(flat.scale(speed * 0.6 * falloff)).add(0, 0.3 + speed * 0.25 * falloff, 0));
			RingPowers.syncVelocity(mob);
			mob.hurtServer(c.level, c.level.damageSources().thrown(c.target, c.holder), (float) (speed * 3 * falloff));
		}
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

	/** Left-click (sent every tick it is held) and space from the bearer's client. */
	private static void input(ServerPlayer player, int action) {
		Catch c = CATCHES.get(player.getUUID());
		if (c == null) return;
		long now = c.level.getGameTime();
		if (action == INPUT_SEND) {
			if (c.lastPush == now) return;
			c.pushTicks = c.lastPush >= now - 1 ? c.pushTicks + 1 : 1;
			c.lastPush = now;
			c.reeling = false;
			c.distance = Math.min(reach(c.level, c.target), c.distance + Math.min(PUSH_MAX, PUSH_START + PUSH_GAIN * c.pushTicks));
		} else if (action == INPUT_HOLD) {
			c.reeling = !c.reeling;
			c.level.playSound(null, c.center.x, c.center.y, c.center.z, SoundEvents.AMETHYST_BLOCK_CHIME,
					SoundSource.PLAYERS, 1.0f, c.reeling ? 1.4f : 0.8f);
		}
	}

	/**
	 * Lets go. A fast-moving bubble flies on with its momentum (see fly); a slow one pops and drops
	 * the mob where it is.
	 */
	public static void release(Player player) {
		Catch c = CATCHES.remove(player.getUUID());
		if (c == null) return;
		c.velocity = c.velocity.scale(THROW_BOOST);
		if (c.velocity.length() > THROW_MAX_SPEED) c.velocity = c.velocity.normalize().scale(THROW_MAX_SPEED);
		double speed = c.velocity.length();
		if (c.target.isAlive() && speed >= MIN_THROW_SPEED) {
			FLYING.put(c.target.getUUID(), c);
			// A whoosh at the bearer that gets bigger the harder the throw.
			float power = (float) Mth.clamp(speed / THROW_MAX_SPEED, 0, 1);
			c.level.playSound(null, player.getX(), player.getEyeY(), player.getZ(),
					power > 0.5f ? SoundEvents.TRIDENT_RIPTIDE_3 : power > 0.2f ? SoundEvents.TRIDENT_RIPTIDE_2 : SoundEvents.TRIDENT_RIPTIDE_1,
					SoundSource.PLAYERS, 0.6f + 0.6f * power, 1.3f - 0.3f * power);
			c.level.playSound(null, player.getX(), player.getEyeY(), player.getZ(), SoundEvents.WIND_CHARGE_THROW,
					SoundSource.PLAYERS, 0.5f + 0.5f * power, 0.8f);
			broadcast(-1, c);
		} else {
			pop(c);
		}
	}

	/** Moves every thrown bubble along its arc; it pops when it hits something. */
	private static void fly(MinecraftServer server) {
		for (Iterator<Catch> it = FLYING.values().iterator(); it.hasNext(); ) {
			Catch c = it.next();
			if (!c.target.isAlive() || c.target.isRemoved() || ++c.flightTicks > MAX_FLIGHT_TICKS) {
				it.remove();
				pop(c);
				continue;
			}
			c.velocity = c.velocity.scale(FLIGHT_DRAG).subtract(0, FLIGHT_GRAVITY, 0);
			// Flying out of the loaded world: let go and leave the mob to vanilla physics.
			if (!c.level.hasChunkAt(BlockPos.containing(c.center.add(c.velocity)))) {
				it.remove();
				pop(c);
				continue;
			}
			boolean hit = move(c);
			place(c);
			if (hit) {
				it.remove();
				pop(c);
			} else {
				broadcast(-1, c);
			}
		}
	}

	/** The bubble bursts: the mob keeps the bubble's speed and the clients draw the pop. */
	private static void pop(Catch c) {
		if (c.target.isAlive()) {
			c.target.setDeltaMovement(c.velocity);
			RingPowers.syncVelocity(c.target);
		}
		c.level.playSound(null, c.center.x, c.center.y, c.center.z, SoundEvents.AMETHYST_CLUSTER_BREAK,
				SoundSource.PLAYERS, 0.8f, 1.5f);
		for (ServerPlayer viewer : PlayerLookup.tracking(c.target)) {
			ServerPlayNetworking.send(viewer, new LassoPayload(c.target.getId(), -1, 0f, false));
		}
	}

	/** Tells nearby clients where to draw the bubble, and the string to its holder (-1: thrown, no string). */
	private static void broadcast(int holder, Catch c) {
		LassoPayload payload = new LassoPayload(c.target.getId(), holder, (float) c.radius, !c.reeling);
		for (ServerPlayer viewer : PlayerLookup.tracking(c.target)) {
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
