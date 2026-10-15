package com.sparky.lanternring;

import com.sparky.lanternring.block.BlastGlowBlock;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.OmegaFxPayload;
import com.sparky.lanternring.net.OmegaInputPayload;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Deque;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.OwnableEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.boss.enderdragon.EnderDragon;
import net.minecraft.world.entity.boss.wither.WitherBoss;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.jspecify.annotations.Nullable;

/**
 * Omega beams (J, from the lead Blender chat): hold the omega key while aiming, with a charged ring
 * of any corps. The eyes flash red (the start is the Ring Lab's Omega start pick, see {@link Start});
 * in the air the body brakes to a hover, on the ground it can only walk slowly. Then a pair of thin
 * red lasers, one from each eye, is built out of the eyes: the server lays it here as straight sides
 * joined by sharp corners, and clients draw it from the corners and head it sends (client OmegaFx).
 * <p>
 * Final pass (J's picks, docs/handoff/2026-10-14-omega-beams-final): E2 wild routing, every side
 * 0.8-3.2 blocks (x1.4 with a fast target) bent 55-120 degrees off the way to where the target will
 * be, wild at first and more committed the more beam it has laid; once committed and close, K1 snap
 * strike: a kink 0.6 blocks off the line, then straight at where the target will be on arrival. Any
 * touch on the way is a hit. The head runs max(2.2, 0.95 x target speed / 0.45) blocks a tick, 1.6x
 * under water. Every creature in a 110 degree field of view in front is a target, in random order,
 * and the same pair threads them all; it gives up after RingTuning omega_chase. What it hits turns to
 * embers and crumbles to ash (RingTuning omega_embers); with no creature in view it burns the block
 * under the crosshair.
 * <p>
 * Pass 837 R4 (the Ring Lab's Omega chain, see {@link Chain}): the same physics run target to target,
 * but the head's speed is set per target, 0.45 x the straight distance to it (0.6-2.2 blocks a tick),
 * the line commits over 3x that distance, sides shorten for a close target (x0.45-1 of the distance /
 * 8), it runs straight on 0.8 blocks through each creature, stops in a player, and after the last hit
 * burns away from the eye end at 2.5x that speed. Clients draw it with E3's pulse glow and corner sparks.
 */
public final class OmegaBeams {
	/** The Ring Lab's Omega start (client LabSettings.OmegaStart has the same order). */
	public enum Start { SNAP, SMOULDER, AIR_BRAKE, CRACKLE }
	/** The Ring Lab's Omega chain (client LabSettings.OmegaChain has the same order): pass 837 R4, or today's chain. */
	public enum Chain { R4, TODAY }

	/** How far ahead targets are picked, and the furthest the head flies from its bearer. */
	static final double RANGE = 64, MAX_FLIGHT = 96;
	/** Half the barrage's field of view (110 degrees across). */
	private static final double FOV_HALF = Math.toRadians(55);
	/** The most creatures one use threads. */
	private static final int MAX_TARGETS = 12;
	/** The slowest the head runs (blocks a tick), and how much faster under water (U3). */
	public static final double HEAD_SPEED = 2.2, WATER = 1.6;
	/** P3: side lengths (blocks, x the speed scale) and how far a side bends off its way (degrees). */
	private static final double SIDE_MIN = 0.8, SIDE_MAX = 3.2, BEND_MIN = 55, BEND_MAX = 72, BEND_WILD = 120;
	/** E2: how wild it starts, and over how much beam (blocks) it becomes committed. */
	private static final double WILD = 0.15, COMMIT = HEAD_SPEED * 45;
	/** How close counts as touching the target (blocks), and the contact test's sample spacing. */
	private static final double HIT = 0.75, SAMPLE = 0.25;
	/** Corners stay this high over the floor, and no higher than CEILING over it. */
	private static final double FLOOR = 0.4, CEILING = 14, HIGH = 12;
	/** A barrage's line lets go of the eyes (and the body) once it is this long. */
	public static final double LET_GO = 10;
	/** One laser from each eye, side by side this far apart (blocks). */
	public static final double PAIR_SEPARATION = 0.26;
	/** 1% of a full ring a use. */
	public static final int COST = 10;
	/** How long E1 snap's flash and E3 air brake's brake take before the beams leave, in ticks. */
	private static final int SNAP_TICKS = 2, BRAKE_TICKS = 10;
	/** Ground use: walking slows to about 0.04 blocks a tick. */
	private static final double SLOW_WALK = -0.81;
	/** 837 R4: head speed = CHAIN_K x the distance to the next target, CHAIN_MIN to CHAIN_MAX blocks a tick; THROUGH blocks on past each hit. */
	private static final double CHAIN_K = 0.45, CHAIN_MIN = 0.6, CHAIN_MAX = 2.2, THROUGH = 0.8;
	/** How far the beams are seen from. */
	private static final double VIEW = 128;
	/** Routing round blocks when no side gets through: the grid's spacing and how far a route keeps off blocks. */
	private static final double CELL = 0.5, CLEARANCE = 0.15;
	/** The attribute modifier that holds the body back while the key is down (the client keeps the FOV from zooming with it). */
	public static final Identifier LOCK = LanternRing.id("omega_lock");

	private static final Map<UUID, Session> SESSIONS = new HashMap<>();
	private static final List<Line> LINES = new ArrayList<>();
	private static final List<Burning> BURNING = new ArrayList<>();
	private static int nextLine = 1;

	private OmegaBeams() {
	}

	/** One use: the start, then the line, while the key is held. */
	private static final class Session {
		final ServerPlayer player;
		final Start start;
		final Chain chain;
		final Corps corps;
		final boolean airborne;
		int age, windup;
		boolean held = true, fired, locked;

		Session(ServerPlayer player, Start start, Chain chain, Corps corps, int windup, boolean airborne) {
			this.player = player;
			this.start = start;
			this.chain = chain;
			this.corps = corps;
			this.windup = windup;
			this.airborne = airborne;
		}
	}

	/** The pair's line: its corners from the eyes out, the head, and who it is after. */
	private static final class Line {
		final int id = nextLine++;
		final ServerPlayer owner;
		final ServerLevel level;
		final Session session;
		final RandomSource random;
		final List<LivingEntity> targets;
		/** With no creature in view: the point in the block under the crosshair. */
		final @Nullable Vec3 blockGoal;
		final boolean barrage;
		Vec3 head;
		final Deque<Vec3> queue = new ArrayDeque<>();
		@Nullable LivingEntity target;
		Vec3 targetPrev = Vec3.ZERO, targetVel = Vec3.ZERO;
		/** Beam laid in all, and since the current target was picked (which sets how wild it is). */
		double laid, travelled;
		double roll;
		/** 837 R4: the head's speed for this target, the straight distance to it when picked, and the point 0.8 blocks past the last hit. */
		double legSpeed = HEAD_SPEED, legDist = 8;
		@Nullable Vec3 through;
		boolean striking, attached = true, done;
		int age, targetAge, hits;

		Line(Session session, Vec3 head, List<LivingEntity> targets, @Nullable Vec3 blockGoal) {
			this.session = session;
			this.owner = session.player;
			this.level = (ServerLevel) owner.level();
			this.random = RandomSource.create(owner.getRandom().nextLong());
			this.head = head;
			this.targets = targets;
			this.blockGoal = blockGoal;
			this.barrage = targets.size() > 1;
			this.roll = random.nextDouble() * Mth.TWO_PI;
		}

		boolean r4() {
			return session.chain == Chain.R4;
		}
	}

	/** A creature turned to embers, crumbling to ash when ticks runs out. */
	private record Burning(LivingEntity mob, int[] ticks) {
	}

	static void register() {
		PayloadTypeRegistry.serverboundPlay().register(OmegaInputPayload.TYPE, OmegaInputPayload.CODEC);
		PayloadTypeRegistry.clientboundPlay().register(OmegaFxPayload.TYPE, OmegaFxPayload.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(OmegaInputPayload.TYPE, (payload, context) -> {
			ServerPlayer player = context.player();
			if (payload.down()) press(player, Start.values()[Mth.clamp(payload.start(), 0, Start.values().length - 1)],
					Chain.values()[Mth.clamp(payload.chain(), 0, Chain.values().length - 1)]);
			else release(player);
		});
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> end(handler.player));
		ServerTickEvents.END_SERVER_TICK.register(OmegaBeams::tick);
	}

	/** Whether this player is using the omega beams right now (its start or its line, key held). */
	public static boolean active(Player player) {
		Session s = SESSIONS.get(player.getUUID());
		return s != null && s.held;
	}

	/** The omega key went down, with today's chain. Public for the game tests. */
	public static void press(ServerPlayer player, Start start) {
		press(player, start, Chain.TODAY);
	}

	/** The omega key went down. Public for the game tests. */
	public static void press(ServerPlayer player, Start start, Chain chain) {
		if (SESSIONS.containsKey(player.getUUID()) || player.isSpectator()) return;
		ItemStack ring = RingFlight.findRing(player);
		if (ring.isEmpty() || PowerRingItem.getCharge(ring) <= 0) return;
		boolean airborne = !player.onGround();
		int windup = switch (start) {
			case SNAP -> SNAP_TICKS;
			case SMOULDER -> Math.max(1, RingTuning.OMEGA_SMOULDER.ticks());
			case AIR_BRAKE -> airborne ? BRAKE_TICKS : SNAP_TICKS;
			case CRACKLE -> Math.max(1, RingTuning.OMEGA_CRACKLE.ticks());
		};
		Session s = new Session(player, start, chain, Corps.of(ring), windup, airborne);
		SESSIONS.put(player.getUUID(), s);
		lock(s, true);
		ServerLevel level = (ServerLevel) player.level();
		send(level, player.getEyePosition(), new OmegaFxPayload(OmegaFxPayload.EYES, player.getId(), start.ordinal(), player.getEyePosition(), windup, 0));
		level.playSound(null, player.getX(), player.getEyeY(), player.getZ(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 0.6f, 1.9f);
	}

	/** The omega key came up: the body lets go, and the line finishes the creature it is after but takes no more. */
	public static void release(ServerPlayer player) {
		Session s = SESSIONS.get(player.getUUID());
		if (s == null) return;
		s.held = false;
		lock(s, false);
		for (Line l : LINES) {
			if (l.session == s) l.targets.clear();
		}
		if (s.fired && linesOf(s) == 0) SESSIONS.remove(player.getUUID());
	}

	private static void end(ServerPlayer player) {
		Session s = SESSIONS.remove(player.getUUID());
		if (s == null) return;
		lock(s, false);
		LINES.removeIf(l -> l.session == s);
	}

	private static int linesOf(Session s) {
		int n = 0;
		for (Line l : LINES) if (l.session == s) n++;
		return n;
	}

	/**
	 * Holds the body while firing: in the air gravity lets go, so the brake leaves you hovering; on
	 * the ground walking slows to about 0.04 blocks a tick and jumping stops.
	 */
	private static void lock(Session s, boolean on) {
		ServerPlayer player = s.player;
		s.locked = on;
		for (var attribute : List.of(Attributes.MOVEMENT_SPEED, Attributes.JUMP_STRENGTH, Attributes.GRAVITY, Attributes.FLYING_SPEED)) {
			AttributeInstance a = player.getAttribute(attribute);
			if (a == null) continue;
			a.removeModifier(LOCK);
			if (!on || attribute == Attributes.GRAVITY && !s.airborne) continue;
			double amount = attribute == Attributes.MOVEMENT_SPEED ? SLOW_WALK : -1.0;
			a.addTransientModifier(new AttributeModifier(LOCK, amount, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
		}
	}

	// ---- every tick ---------------------------------------------------------------------------

	private static void tick(MinecraftServer server) {
		for (Iterator<Session> it = SESSIONS.values().iterator(); it.hasNext(); ) {
			Session s = it.next();
			ServerPlayer p = s.player;
			if (p.isRemoved() || !p.isAlive()) {
				lock(s, false);
				it.remove();
				LINES.removeIf(l -> l.session == s);
				continue;
			}
			s.age++;
			if (!s.fired && s.age >= s.windup) fire(s);
			else if (s.fired && linesOf(s) == 0) {
				// The line is done: the body lets go, even if the key is still down.
				if (s.locked) lock(s, false);
				if (!s.held) it.remove();
			}
		}
		for (Iterator<Line> it = LINES.iterator(); it.hasNext(); ) {
			Line l = it.next();
			if (!l.done) step(l);
			if (l.done) it.remove();
		}
		SESSIONS.values().removeIf(s -> s.fired && !s.held && linesOf(s) == 0);
		for (Iterator<Burning> it = BURNING.iterator(); it.hasNext(); ) {
			Burning burn = it.next();
			LivingEntity mob = burn.mob;
			if (mob.isRemoved()) {
				it.remove();
				continue;
			}
			mob.setDeltaMovement(Vec3.ZERO);
			if (--burn.ticks[0] > 0) continue;
			it.remove();
			ServerLevel level = (ServerLevel) mob.level();
			send(level, mob.position(), new OmegaFxPayload(OmegaFxPayload.ASH, mob.getId(), 0, mob.position(), mob.getBbWidth(), mob.getBbHeight()));
			level.playSound(null, mob.getX(), mob.getY(), mob.getZ(), SoundEvents.SOUL_ESCAPE, SoundSource.HOSTILE, 0.8f, 0.6f);
			mob.discard();
		}
	}

	/** The start is over: the line leaves the eyes, after every creature in view (or the block under the crosshair). */
	private static void fire(Session s) {
		s.fired = true;
		ServerPlayer p = s.player;
		ServerLevel level = (ServerLevel) p.level();
		ItemStack ring = RingFlight.findRing(p);
		if (ring.isEmpty() || PowerRingItem.getCharge(ring) <= 0) return;
		if (!p.isCreative()) PowerRingItem.setCharge(ring, Math.max(0, PowerRingItem.getCharge(ring) - COST));
		List<LivingEntity> targets = inView(level, p);
		Vec3 from = p.getEyePosition().add(p.getLookAngle().scale(0.3));
		Line l = new Line(s, from, targets, targets.isEmpty() ? aimPoint(level, p) : null);
		if (l.blockGoal != null) leg(l, l.blockGoal);
		LINES.add(l);
		send(level, from, new OmegaFxPayload(OmegaFxPayload.START, l.id, p.getId(), from, 0, (l.barrage ? 1 : 0) | (l.r4() ? 2 : 0)));
		level.playSound(null, p.getX(), p.getEyeY(), p.getZ(), SoundEvents.FIRECHARGE_USE, SoundSource.PLAYERS, 0.9f, 1.7f);
		level.playSound(null, p.getX(), p.getEyeY(), p.getZ(), SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 0.5f, 2f);
	}

	/** One tick of the head: picks its target, then lays sides toward it at the head's speed. */
	private static void step(Line l) {
		l.age++;
		if (l.owner.isRemoved() || l.head.distanceToSqr(l.owner.position()) > MAX_FLIGHT * MAX_FLIGHT) {
			finish(l, 0);
			return;
		}
		if (!valid(l, l.target)) {
			l.target = null;
			while (!l.targets.isEmpty() && l.target == null) {
				LivingEntity next = l.targets.remove(0);
				if (valid(l, next)) l.target = next;
			}
			if (l.target != null) {
				l.travelled = 0;
				l.targetAge = 0;
				l.striking = false;
				l.queue.clear();
				l.targetPrev = middle(l.target);
				l.targetVel = l.target.getDeltaMovement();
				if (l.r4()) {
					leg(l, l.targetPrev);
					// Straight on through the last creature before it turns for this one.
					if (l.through != null && clear(l, l.head, l.through)) l.queue.add(l.through);
				}
				l.through = null;
			} else if (l.hits > 0 || l.blockGoal == null) {
				finish(l, l.hits > 0 ? 2 : 0);
				return;
			}
		}
		Vec3 goal;
		if (l.target != null) {
			goal = middle(l.target);
			l.targetVel = goal.subtract(l.targetPrev);
			l.targetPrev = goal;
		} else {
			goal = l.blockGoal;
		}
		if (++l.targetAge > RingTuning.OMEGA_CHASE.ticks()) {
			finish(l, 0);
			return;
		}
		double v = l.targetVel.length();
		double scale = 1 + 0.4 * Math.min(1, v / 1.5);
		double speed = Math.max(HEAD_SPEED, 0.95 * v / 0.45) * (water(l.level, l.head) ? WATER : 1);
		if (l.r4()) {
			// 837 R4: speed by the distance to this target, and shorter sides for a close one.
			scale *= Mth.clamp(l.legDist / 8, 0.45, 1);
			speed = l.legSpeed * (water(l.level, l.head) ? WATER : 1);
		}
		double left = speed;
		while (left > 1e-6 && !l.done) {
			if (l.queue.isEmpty()) plan(l, goal, speed, scale);
			Vec3 next = l.queue.peekFirst();
			Vec3 d = next.subtract(l.head);
			double dist = d.length();
			double adv = Math.min(left, dist);
			Vec3 dir = dist < 1e-6 ? Vec3.ZERO : d.scale(1 / dist);
			// The contact test along this step.
			int n = Math.max(1, (int) Math.ceil(adv / SAMPLE));
			boolean hitTarget = false;
			for (int k = 1; k <= n && !l.done; k++) {
				Vec3 p = l.head.add(dir.scale(adv * k / n));
				if (l.target != null && touches(l.target, p)) {
					advance(l, p);
					LivingEntity struck = l.target;
					hit(l, struck);
					if (l.r4()) {
						if (struck instanceof Player) finish(l, 2);   // it stops in a player
						else l.through = p.add(dir.scale(THROUGH));
					}
					hitTarget = true;
					break;
				}
				LivingEntity other = mobAt(l, p);
				if (other != null) {
					// A creature in the way burns too; the line runs on.
					burnMob(l, other);
					flash(l, p);
					l.targets.remove(other);
					if (l.r4() && other instanceof Player) {
						advance(l, p);
						finish(l, 2);
						break;
					}
				}
				if (l.target == null && l.blockGoal != null && p.distanceToSqr(l.blockGoal) <= HIT * HIT) {
					advance(l, p);
					burnBlock(l, BlockPos.containing(l.blockGoal));
					flash(l, p);
					finish(l, 1);
					break;
				}
				BlockPos bp = BlockPos.containing(p);
				if (solidAt(l.level, bp, p)) {
					// Ran into something it couldn't route round: it burns that and stops.
					advance(l, p);
					burnBlock(l, bp);
					flash(l, p);
					finish(l, 1);
					break;
				}
			}
			if (l.done || hitTarget) break;
			advance(l, l.head.add(dir.scale(adv)));
			left -= adv;
			if (adv >= dist - 1e-9) {
				l.queue.pollFirst();
				corner(l);
				if (l.striking && l.queue.isEmpty()) l.striking = false;   // the strike missed: lay more sides and strike again
			}
		}
		if (l.done) return;
		if (l.attached && l.barrage && l.laid >= LET_GO) {
			l.attached = false;
			if (l.session.locked) lock(l.session, false);
		}
		send(l.level, l.head, new OmegaFxPayload(OmegaFxPayload.HEAD, l.id, l.owner.getId(), l.head, (float) speed,
				(l.attached ? 0 : 1) | (water(l.level, l.head) ? 2 : 0)));
	}

	/** 837 R4: a new target (or the block) at goal sets the head's speed and how long it takes to commit. */
	private static void leg(Line l, Vec3 goal) {
		double d = goal.distanceTo(l.head);
		l.legDist = d;
		l.legSpeed = Mth.clamp(CHAIN_K * d, CHAIN_MIN, CHAIN_MAX);
	}

	private static void advance(Line l, Vec3 to) {
		double d = to.distanceTo(l.head);
		l.laid += d;
		l.travelled += d;
		l.head = to;
	}

	private static void corner(Line l) {
		send(l.level, l.head, new OmegaFxPayload(OmegaFxPayload.CORNER, l.id, l.owner.getId(), l.head, (float) l.laid, 0));
	}

	/** The current target is touched: it burns, and the line goes on to the next. */
	private static void hit(Line l, LivingEntity mob) {
		corner(l);
		burnMob(l, mob);
		flash(l, l.head);
		l.hits++;
		l.target = null;
		l.queue.clear();
		l.striking = false;
	}

	private static void flash(Line l, Vec3 at) {
		send(l.level, at, new OmegaFxPayload(OmegaFxPayload.HIT, l.id, l.owner.getId(), at, 0, 0));
	}

	private static boolean valid(Line l, @Nullable LivingEntity e) {
		return e != null && !e.isRemoved() && e.isAlive() && e.level() == l.level && !burning(e);
	}

	private static boolean touches(LivingEntity e, Vec3 p) {
		return e.getBoundingBox().inflate(0.3).contains(p) || middle(e).distanceToSqr(p) <= HIT * HIT;
	}

	private static boolean water(ServerLevel level, Vec3 p) {
		return level.getFluidState(BlockPos.containing(p)).is(FluidTags.WATER);
	}

	// ---- laying sides (E2 wild, K1 snap) ------------------------------------------------------

	/** Queues the next side (or K1's two) from the head toward the goal. */
	private static void plan(Line l, Vec3 goal, double speed, double scale) {
		RandomSource r = l.random;
		Vec3 head = l.head;
		double dist = goal.distanceTo(head);
		// 837 R4 commits over 3x the leg's straight distance; today's chain over COMMIT blocks.
		double commit = l.r4() ? 3 * Math.max(l.legDist, 2) : COMMIT;
		double w = Math.min(1, WILD + (1 - WILD) * Math.pow(l.travelled / commit, 1.5));
		if (w > 0.6 && dist < 1.5 * SIDE_MAX * scale && !l.striking) {
			// K1 snap strike: a kink off the line at 35% of the way, then straight at where the target will be on arrival.
			l.striking = true;
			Vec3 aim = goal.add(l.targetVel.scale(dist / speed + 1));
			Vec3 u = unit(aim.subtract(head));
			Vec3[] b = basis(u);
			Vec3 kink = head.add(u.scale(0.35 * dist)).add(b[0].scale(Math.cos(l.roll) * 0.6)).add(b[1].scale(Math.sin(l.roll) * 0.6));
			if (clear(l, head, kink) && clear(l, kink, aim)) l.queue.add(kink);
			l.queue.add(aim);
			return;
		}
		int lead = (int) Math.min(40, dist / (speed * 0.45));
		Vec3 aim = goal.add(l.targetVel.scale(lead));
		Vec3 u = unit(aim.subtract(head));
		double floor = floorBelow(l.level, head);
		for (int tries = 0; tries < 8; tries++) {
			Vec3 rnd = new Vec3(r.nextGaussian(), r.nextGaussian(), r.nextGaussian());
			rnd = unit(rnd.add(0, 0.3 * rnd.length(), 0));
			if (head.y - floor > HIGH) rnd = new Vec3(rnd.x, -Math.abs(rnd.y), rnd.z);
			Vec3 dir = unit(u.scale(w).add(rnd.scale(1 - w)));
			l.roll += Math.PI + (r.nextDouble() * 2 - 1) * 1.2;
			Vec3[] b = basis(dir);
			Vec3 side = b[0].scale(Math.cos(l.roll)).add(b[1].scale(Math.sin(l.roll)));
			double hi = w < 0.95 ? BEND_MAX + (BEND_WILD - BEND_MAX) * (1 - w) : (BEND_MIN + BEND_MAX) / 2;
			double a = Math.toRadians(BEND_MIN + r.nextDouble() * (hi - BEND_MIN));
			Vec3 hd = dir.scale(Math.cos(a)).add(side.scale(Math.sin(a)));
			Vec3 e = head.add(hd.scale((SIDE_MIN + r.nextDouble() * (SIDE_MAX - SIDE_MIN)) * scale));
			double y = e.y;
			if (y < floor + FLOOR) y = floor + FLOOR + (floor + FLOOR - y);
			y = Math.min(y, floor + CEILING);
			e = new Vec3(e.x, y, e.z);
			if (clear(l, head, e)) {
				l.queue.add(e);
				return;
			}
		}
		// Boxed in: a short way round the blocks, on a grid.
		List<Vec3> around = route(l.level, head, goal, l.random);
		if (around != null && !around.isEmpty()) {
			Vec3 last = head;
			for (Vec3 p : around) {
				l.queue.add(p);
				if (p.distanceTo(head) > SIDE_MAX || p.distanceTo(last) > 2) break;
				last = p;
			}
			return;
		}
		l.queue.add(head.add(u.scale(Math.min(dist, SIDE_MIN))));
	}

	/** Whether a side from a to b gets through without touching a block (the goal block itself is fine to reach). */
	private static boolean clear(Line l, Vec3 a, Vec3 b) {
		HitResult hit = l.level.clip(new ClipContext(a, b, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, l.owner));
		if (hit.getType() == HitResult.Type.MISS) return true;
		return l.blockGoal != null && hit.getLocation().distanceToSqr(l.blockGoal) < 1.0;
	}

	/** The top of the ground below p (up to 24 blocks down; further than that counts as that far). */
	private static double floorBelow(ServerLevel level, Vec3 p) {
		HitResult hit = level.clip(new ClipContext(p, p.add(0, -24, 0), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, net.minecraft.world.phys.shapes.CollisionContext.empty()));
		return hit.getType() == HitResult.Type.MISS ? p.y - 24 : hit.getLocation().y;
	}

	private static Vec3 unit(Vec3 v) {
		double len = v.length();
		return len < 1e-9 ? new Vec3(0, 0, 1) : v.scale(1 / len);
	}

	/** Two unit vectors square to u and each other. */
	private static Vec3[] basis(Vec3 u) {
		Vec3 a = Math.abs(u.y) < 0.9 ? new Vec3(0, 1, 0) : new Vec3(1, 0, 0);
		Vec3 v = unit(u.cross(a));
		return new Vec3[] {v, u.cross(v)};
	}

	// ---- what it hits -------------------------------------------------------------------------

	private static void finish(Line l, int how) {
		l.done = true;
		double speed = l.r4() ? l.legSpeed : Math.max(HEAD_SPEED, l.targetVel.length() * 0.95 / 0.45);
		send(l.level, l.head, new OmegaFxPayload(OmegaFxPayload.END, l.id, how, l.head, (float) speed, 0));
	}

	private static @Nullable LivingEntity mobAt(Line l, Vec3 p) {
		List<LivingEntity> hit = l.level.getEntitiesOfClass(LivingEntity.class, new AABB(p, p).inflate(0.15), e -> e != l.target && burnable(l.owner, e));
		return hit.isEmpty() ? null : hit.get(0);
	}

	/** Everything alive but the bearer, their pets, spectators and what's already burning. */
	static boolean burnable(Player owner, LivingEntity e) {
		if (e == owner || !e.isAlive() || e.isSpectator()) return false;
		if (e instanceof OwnableEntity pet && owner.equals(pet.getOwner())) return false;
		return !burning(e);
	}

	private static boolean burning(LivingEntity e) {
		for (Burning burn : BURNING) if (burn.mob == e) return true;
		return false;
	}

	static boolean solidAt(ServerLevel level, BlockPos bp, Vec3 p) {
		BlockState state = level.getBlockState(bp);
		if (state.isAir()) return false;
		VoxelShape shape = state.getCollisionShape(level, bp);
		if (shape.isEmpty()) return false;
		for (AABB box : shape.toAabbs()) {
			if (box.move(bp).inflate(0.02).contains(p)) return true;
		}
		return false;
	}

	/** For routing: whether p is in or within CLEARANCE of a solid block. */
	private static boolean nearSolid(ServerLevel level, Vec3 p) {
		BlockPos.MutableBlockPos bp = new BlockPos.MutableBlockPos();
		for (int x = -1; x <= 1; x++) {
			for (int y = -1; y <= 1; y++) {
				for (int z = -1; z <= 1; z++) {
					Vec3 q = p.add(x * CLEARANCE, y * CLEARANCE, z * CLEARANCE);
					bp.set(Mth.floor(q.x), Mth.floor(q.y), Mth.floor(q.z));
					if (solidAt(level, bp, q)) return true;
				}
			}
		}
		return false;
	}

	/** Burns the block the beam landed on: embers on every client, a warm light while they glow, nothing left. */
	private static void burnBlock(Line l, BlockPos bp) {
		ServerLevel level = l.level;
		BlockState state = level.getBlockState(bp);
		if (state.isAir()) return;
		if (state.getDestroySpeed(level, bp) < 0) {
			// Bedrock and the like only scorch.
			send(level, l.head, new OmegaFxPayload(OmegaFxPayload.BURN_BLOCK, Block.getId(state), 1, Vec3.atLowerCornerOf(bp), 4, 0));
			return;
		}
		int ticks = Math.max(1, RingTuning.OMEGA_EMBERS.ticks());
		send(level, l.head, new OmegaFxPayload(OmegaFxPayload.BURN_BLOCK, Block.getId(state), 0, Vec3.atLowerCornerOf(bp), ticks, 0));
		BlockState glow = ModRegistry.BEAM_GLOW.defaultBlockState().setValue(Corps.PROPERTY, Corps.ORANGE)
				.setValue(BlastGlowBlock.LEVEL, BlastGlowBlock.START_LEVEL);
		level.setBlock(bp, glow, 3);
		level.playSound(null, bp, SoundEvents.FIRECHARGE_USE, SoundSource.BLOCKS, 0.5f, 0.8f + l.random.nextFloat() * 0.3f);
		level.playSound(null, bp, SoundEvents.LAVA_POP, SoundSource.BLOCKS, 0.8f, 0.9f);
	}

	/**
	 * A creature hit: it freezes as glowing embers and crumbles to ash after RingTuning omega_embers.
	 * Players and bosses can't be unmade like that; they take a heavy burn instead.
	 */
	private static void burnMob(Line l, LivingEntity mob) {
		ServerLevel level = l.level;
		if (burning(mob)) return;
		mob.igniteForSeconds(5);
		level.playSound(null, mob.getX(), mob.getEyeY(), mob.getZ(), SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 0.8f, 0.7f);
		if (!(mob instanceof Mob m) || mob instanceof EnderDragon || mob instanceof WitherBoss) {
			mob.hurtServer(level, level.damageSources().indirectMagic(l.owner, l.owner), mob instanceof Player ? 14 : 30);
			send(level, mob.position(), new OmegaFxPayload(OmegaFxPayload.BURN_MOB, mob.getId(), 0, mob.position(), 10, 0));
			return;
		}
		int ticks = Math.max(1, RingTuning.OMEGA_EMBERS.ticks());
		m.setNoAi(true);
		m.setNoGravity(true);
		m.setPermanentlyInvulnerable(true);
		m.setDeltaMovement(Vec3.ZERO);
		m.setRemainingFireTicks(ticks + 10);
		BURNING.add(new Burning(m, new int[] {ticks}));
		send(level, mob.position(), new OmegaFxPayload(OmegaFxPayload.BURN_MOB, mob.getId(), 0, mob.position(), ticks, 0));
		BlockPos light = BlockPos.containing(middle(mob));
		if (level.getBlockState(light).isAir()) {
			level.setBlock(light, ModRegistry.BEAM_GLOW.defaultBlockState().setValue(Corps.PROPERTY, Corps.ORANGE)
					.setValue(BlastGlowBlock.LEVEL, BlastGlowBlock.START_LEVEL), 3);
		}
	}

	// ---- aiming -------------------------------------------------------------------------------

	/**
	 * The barrage's targets: every creature within RANGE inside the 110 degree field of view in front
	 * that the eyes can see (and the one under the crosshair, seen or not), in random order.
	 */
	static List<LivingEntity> inView(ServerLevel level, ServerPlayer player) {
		Vec3 eye = player.getEyePosition();
		Vec3 look = player.getLookAngle();
		double cosMax = Math.cos(FOV_HALF);
		LivingEntity aimed = aimed(level, player);
		List<LivingEntity> out = new ArrayList<>();
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, player.getBoundingBox().inflate(RANGE), e -> burnable(player, e))) {
			if (e == aimed) continue;
			Vec3 to = middle(e).subtract(eye);
			double dist = to.length();
			if (dist > RANGE || dist < 1 || to.dot(look) / dist < cosMax) continue;
			if (seen(level, eye, e, player)) out.add(e);
		}
		if (aimed != null) out.add(aimed);
		Collections.shuffle(out, new java.util.Random(player.getRandom().nextLong()));
		while (out.size() > MAX_TARGETS) out.remove(out.size() - 1);
		return out;
	}

	private static boolean seen(ServerLevel level, Vec3 eye, LivingEntity e, Entity viewer) {
		for (Vec3 p : new Vec3[] {middle(e), e.getEyePosition()}) {
			HitResult hit = level.clip(new ClipContext(eye, p, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, viewer));
			if (hit.getType() == HitResult.Type.MISS) return true;
		}
		return false;
	}

	/** The creature under the crosshair, or failing that the one nearest the line of sight (within about 6 degrees). */
	static @Nullable LivingEntity aimed(ServerLevel level, ServerPlayer player) {
		RingPowers.Target hit = RingPowers.trace(level, player, RANGE);
		if (hit.entity() instanceof LivingEntity living && burnable(player, living)) return living;
		Vec3 eye = player.getEyePosition();
		Vec3 look = player.getLookAngle();
		LivingEntity best = null;
		double bestCos = Math.cos(Math.toRadians(6));
		AABB around = player.getBoundingBox().inflate(RANGE);
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, around, e -> burnable(player, e))) {
			Vec3 to = middle(e).subtract(eye);
			double dist = to.length();
			if (dist > RANGE || dist < 1) continue;
			double cos = to.dot(look) / dist;
			if (cos > bestCos) {
				bestCos = cos;
				best = e;
			}
		}
		return best;
	}

	/** Where the line of sight meets a block (or the end of the range). */
	private static Vec3 aimPoint(ServerLevel level, ServerPlayer player) {
		Vec3 eye = player.getEyePosition();
		Vec3 end = eye.add(player.getLookAngle().scale(RANGE));
		HitResult hit = level.clip(new ClipContext(eye, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
		if (hit.getType() == HitResult.Type.MISS) return end;
		// Just inside the block, so the beam lands in it.
		return hit.getLocation().add(player.getLookAngle().scale(0.1));
	}

	static Vec3 middle(Entity e) {
		return e.position().add(0, e.getBbHeight() * 0.55, 0);
	}

	// ---- the way round, when boxed in ---------------------------------------------------------

	private record Node(int x, int y, int z, double g, double f, @Nullable Node parent) {
	}

	/**
	 * A* on a half-block grid from a to c, avoiding solid blocks, with a little random cost so routes
	 * vary. Returns the grid's corners between (not a or c), or null if none was found in time.
	 */
	static @Nullable List<Vec3> route(ServerLevel level, Vec3 a, Vec3 c, RandomSource random) {
		int gx = (int) Math.round((c.x - a.x) / CELL), gy = (int) Math.round((c.y - a.y) / CELL), gz = (int) Math.round((c.z - a.z) / CELL);
		int margin = 16;
		int minX = Math.min(0, gx) - margin, maxX = Math.max(0, gx) + margin;
		int minY = Math.min(0, gy) - margin, maxY = Math.max(0, gy) + margin;
		int minZ = Math.min(0, gz) - margin, maxZ = Math.max(0, gz) + margin;
		PriorityQueue<Node> open = new PriorityQueue<>((p, q) -> Double.compare(p.f, q.f));
		Map<Long, Double> best = new HashMap<>();
		Map<Long, Boolean> solid = new HashMap<>();
		open.add(new Node(0, 0, 0, 0, Math.sqrt(gx * gx + gy * gy + gz * gz), null));
		best.put(key(0, 0, 0), 0.0);
		int expanded = 0;
		while (!open.isEmpty() && expanded++ < 6000) {
			Node n = open.poll();
			if (n.g > best.getOrDefault(key(n.x, n.y, n.z), Double.MAX_VALUE) + 1e-9) continue;
			int dx = gx - n.x, dy = gy - n.y, dz = gz - n.z;
			if (dx * dx + dy * dy + dz * dz <= 2) {
				List<Vec3> cells = new ArrayList<>();
				for (Node k = n; k != null && k.parent != null; k = k.parent) cells.add(cell(a, k.x, k.y, k.z));
				Collections.reverse(cells);
				// Only the corners: the route stays straight sides.
				List<Vec3> out = new ArrayList<>();
				for (int i = 0; i < cells.size(); i++) {
					boolean last = i == cells.size() - 1;
					Vec3 prev = i == 0 ? a : cells.get(i - 1);
					if (last || unit(cells.get(i).subtract(prev)).dot(unit(cells.get(i + 1).subtract(cells.get(i)))) < 0.95) out.add(cells.get(i));
				}
				return out;
			}
			for (int x = -1; x <= 1; x++) {
				for (int y = -1; y <= 1; y++) {
					for (int z = -1; z <= 1; z++) {
						if (x == 0 && y == 0 && z == 0) continue;
						int nx = n.x + x, ny = n.y + y, nz = n.z + z;
						if (nx < minX || nx > maxX || ny < minY || ny > maxY || nz < minZ || nz > maxZ) continue;
						if (blockedCell(level, a, nx, ny, nz, solid)) continue;
						// Diagonals must not cut a corner: the midpoint has to be clear too.
						if ((x != 0 ? 1 : 0) + (y != 0 ? 1 : 0) + (z != 0 ? 1 : 0) > 1) {
							Vec3 mid = cell(a, n.x + x * 0.5, n.y + y * 0.5, n.z + z * 0.5);
							if (nearSolid(level, mid)) continue;
						}
						double g = n.g + Math.sqrt(x * x + y * y + z * z) * (1 + random.nextDouble() * 0.15);
						long k = key(nx, ny, nz);
						if (g >= best.getOrDefault(k, Double.MAX_VALUE)) continue;
						best.put(k, g);
						int hx = gx - nx, hy = gy - ny, hz = gz - nz;
						open.add(new Node(nx, ny, nz, g, g + Math.sqrt(hx * hx + hy * hy + hz * hz), n));
					}
				}
			}
		}
		return null;
	}

	private static boolean blockedCell(ServerLevel level, Vec3 a, int x, int y, int z, Map<Long, Boolean> cache) {
		return cache.computeIfAbsent(key(x, y, z), k -> nearSolid(level, cell(a, x, y, z)));
	}

	private static Vec3 cell(Vec3 a, double x, double y, double z) {
		return a.add(x * CELL, y * CELL, z * CELL);
	}

	private static long key(int x, int y, int z) {
		return ((long) (x & 0x1FFFFF) << 42) | ((long) (y & 0x1FFFFF) << 21) | (z & 0x1FFFFF);
	}

	private static void send(ServerLevel level, Vec3 at, OmegaFxPayload payload) {
		for (ServerPlayer viewer : PlayerLookup.around(level, at, VIEW)) ServerPlayNetworking.send(viewer, payload);
	}
}
