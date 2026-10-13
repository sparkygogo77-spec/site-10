package com.sparky.lanternring;

import com.sparky.lanternring.corps.CorpsVillager;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.LassoInputPayload;
import com.sparky.lanternring.net.LassoPayload;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
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
 *
 * <p>Double-click and hold to gather: every mob within GROUP_RADIUS of the spot you aim at is pulled
 * into one big bubble, packed around the mob nearest the middle, and they all swing, fly and slam
 * together.
 *
 * <p>Hold left-click (without right-click) and sweep the crosshair over mobs to pick them: each one
 * glows and costs SELECT_COST. The next right-click pulls every picked mob into one tightly packed
 * bubble, and holding that bubble costs nothing more.
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
	private static final float SMASH_DAMAGE_PER_SPEED = 18f;
	/** A slam dents the ground or wall it hits: this many blocks across at SMASH_SPEED, growing with speed up to DENT_MAX. */
	private static final double DENT_MIN = 0.9;
	private static final double DENT_PER_SPEED = 0.8;
	private static final double DENT_MAX = 2.5;
	/** A catch dents at most once per this many ticks, so a bubble held into its own hole can't burrow down. */
	private static final int DENT_COOLDOWN = 30;
	/** Share of dented blocks thrown up as falling blocks. */
	private static final float DENT_FLING = 0.3f;
	/** A bubble hitting a block faster than this bounces back off it, keeping BOUNCE of its speed. */
	private static final double BOUNCE_SPEED = 0.45;
	private static final double BOUNCE = 0.45;
	/** A thrown bubble bounces at most this many times before it pops. */
	private static final int MAX_BOUNCES = 3;
	/** A slam this fast (blocks per tick) or more is a heavy one: crater blast and knockback around it. */
	private static final double HEAVY_SMASH = 1.6;
	/** Mobs the bubble runs into while going at least this fast get bowled over. */
	private static final double BOWL_SPEED = 0.6;
	private static final double MAX_RADIUS = 3;
	/** Double-click: a second right-click this soon after the first gathers a group. */
	private static final int DOUBLE_CLICK_TICKS = 8;
	/** How far from the aimed spot a group catch reaches (blocks), its size cap, and its biggest bubble. */
	private static final double GROUP_RADIUS = 3;
	private static final int GROUP_MAX = 12;
	private static final double GROUP_MAX_RADIUS = 4.5;

	/** Picking a mob with left-click costs this much charge (0.5% of a full ring), and holding them is free. */
	public static final int SELECT_COST = 5;
	private static final int SELECT_MAX = 24;
	/** Picked mobs are let go (and stop glowing) this long after the last pick if nothing catches them. */
	private static final int SELECT_TICKS = 1200;

	/** Ticks per point of charge (a point is 0.1% of a full ring) while holding a catch. */
	public static final int HOLD_DRAIN_INTERVAL = 20;

	public static final int INPUT_SEND = 0;
	public static final int INPUT_HOLD = 1;
	/** Left-click held in Lasso mode without a catch: pick the mob under the crosshair. */
	public static final int INPUT_SELECT = 2;

	private static final class Catch {
		final ServerLevel level;
		final LivingEntity target;
		/** The bearer: a player, or a corps villager using its ring (see npcCatch). */
		final LivingEntity holder;
		/** The bearer's ring colour: the bubble and rope are drawn in it, and keep it in flight. */
		final Corps corps;
		/** The rest of a group catch, each held at a fixed offset from the bubble's centre. */
		final List<Member> others;
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
		/** Made from picked mobs: they were paid for when picked, so holding them is free. */
		boolean free;
		/** Mobs this bubble already bowled over, so each one is hit once. */
		final Set<Integer> bowled = new HashSet<>();
		/** Times a thrown bubble has bounced, and whether the last move bounced it. */
		int bounces;
		boolean bounced;
		/** Game time of this catch's last dent. */
		long lastDent = -100;

		Catch(ServerLevel level, LivingEntity holder, LivingEntity target, List<Member> others, double distance) {
			this.level = level;
			this.holder = holder;
			this.corps = holder instanceof CorpsVillager v ? v.corps() : Corps.held(holder);
			this.target = target;
			this.others = others;
			double r = radiusFor(target);
			for (Member m : others) r = Math.max(r, m.offset.length() + radiusFor(m.mob));
			this.radius = others.isEmpty() ? r : Math.min(GROUP_MAX_RADIUS, r);
			this.center = target.getBoundingBox().getCenter();
			this.distance = distance;
		}
	}

	private record Member(LivingEntity mob, Vec3 offset) {
	}

	private static final Map<UUID, Catch> CATCHES = new HashMap<>();
	/** Mobs each player has picked with left-click, and when they last picked one. */
	private static final Map<UUID, List<LivingEntity>> PICKED = new HashMap<>();
	private static final Map<UUID, Long> LAST_PICK = new HashMap<>();
	/** When each player last started holding the lasso, and who double-clicked to gather a group. */
	private static final Map<UUID, Long> LAST_PRESS = new HashMap<>();
	private static final Set<UUID> GATHERING = new HashSet<>();
	/** Thrown bubbles still in the air, by their mob. */
	private static final Map<UUID, Catch> FLYING = new HashMap<>();
	/** Bubbles corps villagers are holding, by villager. */
	private static final Map<UUID, Catch> NPC_CATCHES = new HashMap<>();
	/** Set while the lasso itself deals a smash, so the bubble's protection lets it through. */
	private static boolean smashing;

	private Lasso() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(Lasso::cleanup);
		ServerTickEvents.END_SERVER_TICK.register(Lasso::fly);
		ServerTickEvents.END_SERVER_TICK.register(Lasso::npcCleanup);
		ServerTickEvents.END_SERVER_TICK.register(Lasso::expirePicks);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			CATCHES.clear();
			NPC_CATCHES.clear();
			FLYING.clear();
			LAST_PRESS.clear();
			GATHERING.clear();
			PICKED.clear();
			LAST_PICK.clear();
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

	public static boolean isCaught(LivingEntity entity) {
		return holding(CATCHES, entity) != null || holding(FLYING, entity) != null || holding(NPC_CATCHES, entity) != null;
	}

	/** The catch in this map that holds this mob, as its main mob or one of a group. */
	private static Catch holding(Map<UUID, Catch> catches, LivingEntity entity) {
		for (Catch c : catches.values()) {
			if (c.target == entity) return c;
			for (Member m : c.others) {
				if (m.mob == entity) return c;
			}
		}
		return null;
	}

	/** Right-click pressed with the lasso: a second press soon after the first gathers a group. */
	public static void pressed(ServerPlayer player) {
		long now = player.level().getGameTime();
		Long last = LAST_PRESS.put(player.getUUID(), now);
		if (last != null && now - last <= DOUBLE_CLICK_TICKS) GATHERING.add(player.getUUID());
		else GATHERING.remove(player.getUUID());
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
		// Holding a catch costs 0.1% of a full ring a second.
		if (!c.free && !player.isCreative() && level.getGameTime() % HOLD_DRAIN_INTERVAL == 0) {
			PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - 1);
			if (PowerRingItem.getCharge(ring) == 0) player.stopUsingItem();
		}
		broadcast(player.getId(), c);
	}

	/** Puts the mob where its bubble is, moving the way the bubble moves. */
	private static void place(Catch c) {
		LivingEntity target = c.target;
		AABB box = target.getBoundingBox();
		if (target instanceof ServerPlayer) {
			// A player moves themselves: steer them to the bubble's middle instead of placing them there.
			Vec3 at = new Vec3(c.center.x, c.center.y - box.getYsize() / 2, c.center.z);
			target.setDeltaMovement(at.subtract(target.position()).scale(0.45).add(c.velocity).add(0, 0.08, 0));
		} else {
			target.setPos(c.center.x, c.center.y - box.getYsize() / 2, c.center.z);
			target.setDeltaMovement(c.velocity);
		}
		target.resetFallDistance();
		RingPowers.syncVelocity(target);
		c.others.removeIf(m -> !m.mob.isAlive() || m.mob.isRemoved() || m.mob.level() != c.level);
		for (Member m : c.others) {
			Vec3 at = c.center.add(m.offset);
			// Picked mobs from further away fly in to their place over a few ticks.
			Vec3 now = m.mob.getBoundingBox().getCenter();
			double gap = now.distanceTo(at);
			if (gap > 0.3) at = now.add(at.subtract(now).scale(Math.max(0.35, Math.min(1, 1.2 / gap))));
			m.mob.setPos(at.x, at.y - m.mob.getBbHeight() / 2, at.z);
			m.mob.setDeltaMovement(c.velocity);
			m.mob.resetFallDistance();
			RingPowers.syncVelocity(m.mob);
		}
	}

	private static Catch tryCatch(ServerLevel level, ServerPlayer player) {
		List<LivingEntity> picked = takePicked(player);
		if (!picked.isEmpty()) return catchPicked(level, player, picked);
		RingPowers.Target hit = RingPowers.trace(level, player, RANGE);
		boolean gather = GATHERING.contains(player.getUUID());
		// A mob in a thrown bubble can be caught again in mid-air; one someone is holding can't.
		LivingEntity target = hit.entity() instanceof LivingEntity living && !(living instanceof Player) && living.isAlive()
				&& holding(CATCHES, living) == null && holding(NPC_CATCHES, living) == null ? living : null;
		List<LivingEntity> group = new ArrayList<>();
		if (gather) {
			// Everything around the spot you aim at, nearest first; the nearest mob is the heart of the bubble.
			Vec3 spot = hit.pos();
			group.addAll(level.getEntitiesOfClass(LivingEntity.class, new AABB(spot, spot).inflate(GROUP_RADIUS),
					e -> catchable(e) && e.getBoundingBox().getCenter().distanceTo(spot) <= GROUP_RADIUS + e.getBbWidth() / 2));
			group.sort(Comparator.comparingDouble(e -> e.getBoundingBox().getCenter().distanceToSqr(spot)));
			if (target == null && !group.isEmpty()) target = group.get(0);
			group.remove(target);
			if (group.size() > GROUP_MAX - 1) group = new ArrayList<>(group.subList(0, GROUP_MAX - 1));
		}
		if (target == null) return null;

		Catch c;
		Catch flying = holding(FLYING, target);
		double distance;
		if (flying != null) {
			// Caught again in mid-air: the whole bubble, with everything in it.
			FLYING.remove(flying.target.getUUID());
			distance = Math.min(reach(level, flying.target), flying.center.distanceTo(player.getEyePosition()));
			c = new Catch(level, player, flying.target, flying.others, distance);
			c.center = flying.center;
			c.velocity = flying.velocity;
			c.free = flying.free;
		} else {
			distance = Math.min(reach(level, target), target.getBoundingBox().getCenter().distanceTo(player.getEyePosition()));
			c = new Catch(level, player, target, pack(target, group), distance);
			c.velocity = target.getDeltaMovement();
		}
		// The bubble is bigger than the mob, so lift it clear of the ground it was standing on.
		liftClear(c);
		RingFx.send(level, Kind.TETHER, RingPowers.handPos(player), c.center);
		level.playSound(null, c.center.x, c.center.y, c.center.z, SoundEvents.BEACON_POWER_SELECT,
				SoundSource.PLAYERS, 0.9f, c.others.isEmpty() ? 1.5f : 1.0f);
		level.playSound(null, c.center.x, c.center.y, c.center.z, SoundEvents.AMETHYST_BLOCK_RESONATE,
				SoundSource.PLAYERS, 0.8f, 1.6f);
		return c;
	}

	/** One bubble around everything picked, centred on the picked mob nearest the crosshair. */
	private static Catch catchPicked(ServerLevel level, ServerPlayer player, List<LivingEntity> picked) {
		Vec3 eye = player.getEyePosition();
		Vec3 look = player.getLookAngle();
		LivingEntity target = picked.get(0);
		double best = Double.MAX_VALUE;
		for (LivingEntity mob : picked) {
			Vec3 to = mob.getBoundingBox().getCenter().subtract(eye);
			double off = to.length() - to.dot(look);
			if (off < best) {
				best = off;
				target = mob;
			}
		}
		List<LivingEntity> group = new ArrayList<>(picked);
		group.remove(target);
		// Nearest first, so the closest mobs get the inner places.
		LivingEntity heart = target;
		group.sort(Comparator.comparingDouble(e -> e.distanceToSqr(heart)));
		double distance = Math.min(reach(level, target), target.getBoundingBox().getCenter().distanceTo(eye));
		Catch c = new Catch(level, player, target, pack(target, group), distance);
		c.velocity = target.getDeltaMovement();
		c.free = true;
		liftClear(c);
		RingFx.send(level, Kind.TETHER, RingPowers.handPos(player), c.center);
		level.playSound(null, c.center.x, c.center.y, c.center.z, SoundEvents.BEACON_POWER_SELECT,
				SoundSource.PLAYERS, 0.9f, 0.9f);
		level.playSound(null, c.center.x, c.center.y, c.center.z, SoundEvents.AMETHYST_BLOCK_RESONATE,
				SoundSource.PLAYERS, 0.8f, 1.6f);
		return c;
	}

	/** The player's picked mobs still around to catch (they stop glowing), and forgets the pick. */
	private static List<LivingEntity> takePicked(ServerPlayer player) {
		List<LivingEntity> picked = PICKED.remove(player.getUUID());
		LAST_PICK.remove(player.getUUID());
		List<LivingEntity> out = new ArrayList<>();
		if (picked == null) return out;
		for (LivingEntity mob : picked) {
			mob.removeEffect(MobEffects.GLOWING);
			if (mob.isAlive() && !mob.isRemoved() && mob.level() == player.level() && catchable(mob)) out.add(mob);
		}
		return out;
	}

	/** Left-click held in Lasso mode: the mob under the crosshair is picked, for SELECT_COST. */
	private static void pick(ServerPlayer player) {
		ItemStack ring = player.getMainHandItem();
		if (!(ring.getItem() instanceof PowerRingItem) || PowerRingItem.getMode(ring) != RingMode.TETHER || player.isUsingItem()) return;
		ServerLevel level = player.level();
		RingPowers.Target hit = RingPowers.trace(level, player, RANGE);
		if (!(hit.entity() instanceof LivingEntity mob) || !catchable(mob)) return;
		List<LivingEntity> picked = PICKED.computeIfAbsent(player.getUUID(), id -> new ArrayList<>());
		picked.removeIf(m -> !m.isAlive() || m.isRemoved());
		if (picked.contains(mob) || picked.size() >= SELECT_MAX) return;
		if (!player.isCreative()) {
			int charge = PowerRingItem.getCharge(ring);
			if (charge < SELECT_COST) {
				level.playSound(null, player.getX(), player.getEyeY(), player.getZ(), SoundEvents.AMETHYST_BLOCK_HIT,
						SoundSource.PLAYERS, 0.6f, 0.6f);
				return;
			}
			PowerRingItem.setCharge(ring, charge - SELECT_COST);
		}
		picked.add(mob);
		LAST_PICK.put(player.getUUID(), level.getGameTime());
		mob.addEffect(new MobEffectInstance(MobEffects.GLOWING, SELECT_TICKS, 0, false, false));
		Vec3 at = mob.getBoundingBox().getCenter();
		RingFx.send(level, Kind.TETHER, RingPowers.handPos(player), at);
		// Each pick rings a little higher, so you can hear the count go up.
		level.playSound(null, at.x, at.y, at.z, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.0f,
				(float) Math.min(2.0, 0.9 + 0.08 * picked.size()));
	}

	/** Picks nobody caught in time are let go. */
	private static void expirePicks(MinecraftServer server) {
		for (Iterator<Map.Entry<UUID, Long>> it = LAST_PICK.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<UUID, Long> e = it.next();
			ServerPlayer player = server.getPlayerList().getPlayer(e.getKey());
			if (player != null && player.level().getGameTime() - e.getValue() < SELECT_TICKS) continue;
			it.remove();
			List<LivingEntity> picked = PICKED.remove(e.getKey());
			if (picked != null) picked.forEach(m -> m.removeEffect(MobEffects.GLOWING));
		}
	}

	private static boolean catchable(LivingEntity e) {
		return !(e instanceof Player) && e.isAlive() && !isCaught(e);
	}

	/** Packs a group tightly around its main mob, spread evenly over a sphere. */
	private static List<Member> pack(LivingEntity center, List<LivingEntity> group) {
		List<Member> members = new ArrayList<>();
		double inner = radiusFor(center) - 0.15;
		double golden = Math.PI * (3 - Math.sqrt(5));
		for (int i = 0; i < group.size(); i++) {
			LivingEntity mob = group.get(i);
			// Mostly around the middle, so the group sits in a band rather than stacked up.
			double y = group.size() == 1 ? 0 : 0.7 * (1 - (i + 0.5) * 2 / group.size());
			double ring = Math.sqrt(1 - y * y);
			double a = i * golden;
			Vec3 dir = new Vec3(Math.cos(a) * ring, y, Math.sin(a) * ring);
			// Squeezed in close: the mobs overlap a little, so the bubble stays small.
			members.add(new Member(mob, dir.scale(0.5 * (inner + radiusFor(mob) - 0.15))));
		}
		return members;
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

		boolean[] wasBlocked = c.blocked.clone();
		double impact = 0;
		int impactAxis = -1;
		for (int axis = 0; axis < 3; axis++) {
			if (hit[axis] && !c.blocked[axis] && Math.abs(component(v, axis)) > impact) {
				impact = Math.abs(component(v, axis));
				impactAxis = axis;
			}
			c.blocked[axis] = hit[axis];
		}
		c.bounced = false;
		if (hit[0] || hit[1] || hit[2]) {
			// A hard hit bounces back off the block with some of its speed; a soft one just stops.
			double[] out = {v.x, v.y, v.z};
			for (int axis = 0; axis < 3; axis++) {
				if (!hit[axis]) continue;
				// Only a fresh hit bounces: pressed against a block (held into the ground) it just stays put.
				if (!wasBlocked[axis] && Math.abs(out[axis]) > BOUNCE_SPEED) {
					out[axis] = -out[axis] * BOUNCE;
					c.bounced = true;
				} else {
					out[axis] = 0;
				}
			}
			// Scraping along the block it hit slows the rest of the motion too.
			double rub = c.bounced ? 0.8 : 1.0;
			for (int axis = 0; axis < 3; axis++) if (!hit[axis]) out[axis] *= rub;
			c.velocity = new Vec3(out[0], out[1], out[2]);
		}
		if (impact > SMASH_SPEED) smash(c, impact, axisVec(impactAxis, Math.signum(component(v, impactAxis))));
		bowl(c, v);
		return hit[0] || hit[1] || hit[2];
	}

	/** A fast bubble knocks the mobs it runs into flying, each one once. */
	private static void bowl(Catch c, Vec3 v) {
		double speed = v.length();
		if (speed < BOWL_SPEED) return;
		AABB box = bubble(c.center, c.radius).expandTowards(v.scale(-1));
		for (Entity e : c.level.getEntities(c.target, box, e -> e instanceof LivingEntity l && e != c.holder && e.isAlive() && mayHit(c, l))) {
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

	private static void smash(Catch c, double speed, Vec3 into) {
		float damage = (float) ((speed - SMASH_SPEED) * SMASH_DAMAGE_PER_SPEED) + 2f;
		smashing = true;
		try {
			c.target.hurtServer(c.level, c.level.damageSources().fall(), damage);
			for (Member m : c.others) m.mob.hurtServer(c.level, c.level.damageSources().fall(), damage);
		} finally {
			smashing = false;
		}
		float volume = (float) Mth.clamp(speed / 2, 0.4, 2.0);
		boolean heavy = speed >= HEAVY_SMASH;
		c.level.playSound(null, c.center.x, c.center.y, c.center.z,
				heavy ? SoundEvents.MACE_SMASH_GROUND_HEAVY : SoundEvents.MACE_SMASH_GROUND, SoundSource.PLAYERS, volume, heavy ? 0.9f : 1.1f);
		RingFx.send(c.level, Kind.MODE_CHANGE, c.center.subtract(0, 1 + c.radius * 0.5, 0));
		// The camera of everyone nearby jolts, harder the faster it hit (RingShake.impact).
		Vec3 contact = c.center.add(into.scale(c.radius));
		RingFx.send(c.level, Kind.LASSO_SLAM, contact, contact, (float) speed, 0, null);
		dent(c, speed, into, contact);
		bodyHit(c, speed);
		if (!heavy) return;
		// A heavy slam: a burst of dust and a blast, and everything nearby is thrown back.
		c.level.playSound(null, c.center.x, c.center.y, c.center.z, SoundEvents.GENERIC_EXPLODE,
				SoundSource.PLAYERS, (float) Mth.clamp(speed / 4, 0.4, 1.0), 1.3f);
		c.level.sendParticles(ParticleTypes.EXPLOSION, c.center.x, c.center.y, c.center.z, 1 + (int) speed, c.radius,
				c.radius * 0.5, c.radius, 0);
		c.level.sendParticles(ParticleTypes.CLOUD, c.center.x, c.center.y - c.radius, c.center.z, 30, c.radius + 0.5,
				0.2, c.radius + 0.5, 0.15);
		double reach = c.radius + 2 + speed;
		for (Entity e : c.level.getEntities(c.target, bubble(c.center, reach), e -> e instanceof LivingEntity l && e != c.holder && mayHit(c, l))) {
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

	/**
	 * The slam dents what it hit: a bowl of blocks is knocked out of the ground or wall around the
	 * contact point, deeper the faster it hit, and some of it is thrown up as falling blocks. Only
	 * a player's lasso digs (a villager's doesn't wreck the village), and never in claims or
	 * spawn protection, nor unbreakable blocks or ones holding things (chests, spawners).
	 */
	private static void dent(Catch c, double speed, Vec3 into, Vec3 contact) {
		if (!(c.holder instanceof Player player)) return;
		long now = c.level.getGameTime();
		if (now - c.lastDent < DENT_COOLDOWN) return;
		c.lastDent = now;
		double r = Math.min(DENT_MAX, DENT_MIN + (speed - SMASH_SPEED) * DENT_PER_SPEED);
		// The bowl's middle sits a little into the surface, so it digs in rather than up.
		Vec3 middle = contact.add(into.scale(0.4));
		int ri = (int) Math.ceil(r);
		BlockPos at = BlockPos.containing(middle);
		BlockState loudest = null;
		for (BlockPos pos : BlockPos.betweenClosed(at.offset(-ri, -ri, -ri), at.offset(ri, ri, ri))) {
			Vec3 rel = Vec3.atCenterOf(pos).subtract(middle);
			// Only the side facing into the surface, and a shallower bowl than it is wide.
			double depth = rel.dot(into);
			if (depth < -0.3) continue;
			Vec3 flat = rel.subtract(into.scale(depth));
			// Never dig out the ground the holder is standing on.
			Vec3 feet = c.holder.position();
			if (pos.getY() < feet.y && Math.abs(pos.getX() + 0.5 - feet.x) < 1.6 && Math.abs(pos.getZ() + 0.5 - feet.z) < 1.6 && feet.y - pos.getY() < 4) continue;
			if (flat.lengthSqr() / (r * r) + depth * depth / (r * r * 0.35) > 1) continue;
			BlockState state = c.level.getBlockState(pos);
			if (state.isAir() || !state.getFluidState().isEmpty() || state.hasBlockEntity() || state.getDestroySpeed(c.level, pos) < 0
					|| state.is(ModRegistry.LIGHT_CONSTRUCT) || state.getBlock() instanceof com.sparky.lanternring.block.BlastGlowBlock
					|| !c.level.mayInteract(player, pos)) {
				continue;
			}
			BlockPos hit = pos.immutable();
			c.level.setBlock(hit, net.minecraft.world.level.block.Blocks.AIR.defaultBlockState(), 3);
			if (c.level.getRandom().nextFloat() < DENT_FLING) Anvils.fling(c.level, hit, state, contact.subtract(into.scale(2)));
			else c.level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, state), hit.getX() + 0.5, hit.getY() + 0.5, hit.getZ() + 0.5, 6, 0.3, 0.3, 0.3, 0.15);
			if (loudest == null) loudest = state;
		}
		if (loudest != null) {
			c.level.playSound(null, contact.x, contact.y, contact.z, loudest.getSoundType().getBreakSound(), SoundSource.PLAYERS, 1.5f, 0.6f);
			// A spray of the ground's own dust thrown back out of the dent.
			Vec3 back = into.scale(-1);
			c.level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, loudest), contact.x, contact.y, contact.z, (int) (20 + speed * 15),
					r * 0.5 + Math.abs(back.x) * 0.2, r * 0.5 * Math.abs(back.y) + 0.2, r * 0.5 + Math.abs(back.z) * 0.2, 0.3);
		}
	}

	/** The mobs inside take the hit: a flash of damage, sparks and a puff off their bodies. */
	private static void bodyHit(Catch c, double speed) {
		List<LivingEntity> bodies = new ArrayList<>();
		bodies.add(c.target);
		for (Member m : c.others) bodies.add(m.mob);
		int n = (int) Mth.clamp(speed * 6, 4, 30);
		for (LivingEntity mob : bodies) {
			Vec3 mid = mob.getBoundingBox().getCenter();
			double w = mob.getBbWidth() * 0.5, h = mob.getBbHeight() * 0.5;
			c.level.sendParticles(ParticleTypes.DAMAGE_INDICATOR, mid.x, mid.y, mid.z, Math.max(2, n / 4), w, h, w, 0.2);
			c.level.sendParticles(ParticleTypes.CRIT, mid.x, mid.y, mid.z, n, w, h, w, 0.6);
			if (speed >= HEAVY_SMASH) c.level.sendParticles(ParticleTypes.POOF, mid.x, mid.y, mid.z, n / 2, w, h, w, 0.1);
		}
	}

	/** A villager's flung mob only knocks into other monsters, never players, villagers or animals. */
	private static boolean mayHit(Catch c, LivingEntity hit) {
		return c.holder instanceof Player || com.sparky.lanternring.ally.ConstructAlly.isBadMob(hit);
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
		if (c == null) {
			if (action == INPUT_SELECT) pick(player);
			return;
		}
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

	// ---- corps villagers' lassos -----------------------------------------------------------------

	/**
	 * A corps villager throws its lasso at {@code target}: the same bubble and string a player's
	 * ring makes, tied to the villager's ring. False if the mob is already caught by someone.
	 */
	public static boolean npcCatch(ServerLevel level, LivingEntity holder, LivingEntity target) {
		return npcCatch(level, holder, target, false);
	}

	/** The same, and with {@code players} a player too (a Blue rescue lifting someone who asked for it). */
	public static boolean npcCatch(ServerLevel level, LivingEntity holder, LivingEntity target, boolean players) {
		if (NPC_CATCHES.containsKey(holder.getUUID()) || !target.isAlive() || target instanceof Player && !players
				|| holding(CATCHES, target) != null || holding(NPC_CATCHES, target) != null) return false;
		Catch flying = holding(FLYING, target);
		if (flying != null) return false;
		Catch c = new Catch(level, holder, target, new ArrayList<>(), target.getBoundingBox().getCenter().distanceTo(holder.getEyePosition()));
		c.velocity = target.getDeltaMovement();
		c.free = true;
		liftClear(c);
		c.lastTick = level.getGameTime();
		NPC_CATCHES.put(holder.getUUID(), c);
		level.playSound(null, c.center.x, c.center.y, c.center.z, SoundEvents.BEACON_POWER_SELECT, SoundSource.NEUTRAL, 0.9f, 1.5f);
		level.playSound(null, c.center.x, c.center.y, c.center.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.NEUTRAL, 0.8f, 1.6f);
		broadcast(holder.getId(), c);
		return true;
	}

	/** The mob this villager has in its lasso, or null. */
	public static LivingEntity npcCaught(LivingEntity holder) {
		Catch c = NPC_CATCHES.get(holder.getUUID());
		return c == null ? null : c.target;
	}

	/** Pulls the villager's bubble towards {@code hold} this tick (call every tick while holding). */
	public static void npcHold(LivingEntity holder, Vec3 hold) {
		Catch c = NPC_CATCHES.get(holder.getUUID());
		if (c == null) return;
		if (!c.target.isAlive() || c.level != holder.level()) {
			NPC_CATCHES.remove(holder.getUUID());
			pop(c);
			return;
		}
		c.lastTick = c.level.getGameTime();
		c.velocity = c.velocity.scale(DAMPING).add(hold.subtract(c.center).scale(SPRING));
		if (c.velocity.length() > MAX_SPEED) c.velocity = c.velocity.normalize().scale(MAX_SPEED);
		move(c);
		place(c);
		broadcast(holder.getId(), c);
	}

	/** Lets the villager's bubble go at {@code velocity}: it flies on in an arc and pops where it lands. */
	public static void npcFling(LivingEntity holder, Vec3 velocity) {
		Catch c = NPC_CATCHES.remove(holder.getUUID());
		if (c == null) return;
		c.velocity = velocity.length() > THROW_MAX_SPEED ? velocity.normalize().scale(THROW_MAX_SPEED) : velocity;
		if (!c.target.isAlive()) {
			pop(c);
			return;
		}
		FLYING.put(c.target.getUUID(), c);
		float power = (float) Mth.clamp(c.velocity.length() / 3, 0, 1);
		c.level.playSound(null, holder.getX(), holder.getEyeY(), holder.getZ(),
				power > 0.5f ? SoundEvents.TRIDENT_RIPTIDE_3 : SoundEvents.TRIDENT_RIPTIDE_2, SoundSource.NEUTRAL, 0.6f + 0.6f * power, 1.2f);
		c.level.playSound(null, holder.getX(), holder.getEyeY(), holder.getZ(), SoundEvents.WIND_CHARGE_THROW, SoundSource.NEUTRAL, 0.8f, 0.8f);
		broadcast(-1, c);
	}

	/**
	 * Sets the villager's bubble down gently where it is (a Blue rescue): no momentum, no fall
	 * damage, the mob stepping out on the spot.
	 */
	public static void npcSetDown(LivingEntity holder) {
		Catch c = NPC_CATCHES.remove(holder.getUUID());
		if (c == null) return;
		c.velocity = Vec3.ZERO;
		c.target.resetFallDistance();
		pop(c);
	}

	/** A villager that stopped holding its bubble (killed, unloaded) lets it drop. */
	private static void npcCleanup(MinecraftServer server) {
		for (Iterator<Catch> it = NPC_CATCHES.values().iterator(); it.hasNext(); ) {
			Catch c = it.next();
			if (!c.holder.isAlive() || c.holder.isRemoved() || c.level.getGameTime() - c.lastTick > 2) {
				it.remove();
				pop(c);
			}
		}
	}

	/**
	 * Lets go. A fast-moving bubble flies on with its momentum (see fly); a slow one pops and drops
	 * the mob where it is.
	 */
	public static void release(Player player) {
		GATHERING.remove(player.getUUID());
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
			// It bounces a few times off what it hits, then pops when it stops or has bounced enough.
			if (hit && c.bounced && ++c.bounces <= MAX_BOUNCES) hit = false;
			if (hit) {
				it.remove();
				pop(c);
			} else {
				broadcast(-1, c);
			}
		}
	}

	/**
	 * The bubble lets go: the mob keeps the bubble's speed, and the clients draw the bubble coming
	 * apart from its far side with its light going back into the holder's ring.
	 */
	private static void pop(Catch c) {
		if (c.target.isAlive()) {
			c.target.setDeltaMovement(c.velocity);
			RingPowers.syncVelocity(c.target);
		}
		for (Member m : c.others) {
			if (!m.mob.isAlive()) continue;
			// The group bursts outwards a little as the bubble pops.
			m.mob.setDeltaMovement(c.velocity.add(m.offset.normalize().scale(0.25)));
			RingPowers.syncVelocity(m.mob);
		}
		c.level.playSound(null, c.center.x, c.center.y, c.center.z, SoundEvents.AMETHYST_CLUSTER_BREAK,
				SoundSource.PLAYERS, 0.8f, 1.5f);
		for (ServerPlayer viewer : PlayerLookup.tracking(c.target)) {
			// The holder rides along so the bubble's light can go back into their ring (LassoFx.dismiss).
			ServerPlayNetworking.send(viewer, new LassoPayload(c.target.getId(), c.holder.getId(), 0f, false, c.corps));
		}
	}

	/** Tells nearby clients where to draw the bubble, and the string to its holder (-1: thrown, no string). */
	private static void broadcast(int holder, Catch c) {
		LassoPayload payload = new LassoPayload(c.target.getId(), holder, (float) c.radius, !c.reeling, c.corps);
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
