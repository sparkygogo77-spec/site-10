package com.sparky.lanternring;

import com.sparky.lanternring.block.BlastGlowBlock;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.OmegaFxPayload;
import com.sparky.lanternring.net.OmegaInputPayload;
import java.util.ArrayList;
import java.util.Collections;
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
 * Omega beams (J, from the lead Blender chat, passes 223-225): hold the omega key while aiming, with
 * a charged ring of any corps. The eyes flash red (the start is the Ring Lab's Omega start pick, see
 * {@link Start}); on the ground the body locks in place, in the air it brakes to a hover. Then two
 * thin red lasers leave, one from each eye, each on its own irregular path: a few random waypoints
 * thrown off the straight line and a random last approach, so they can strike from any angle, joined
 * by a smooth curve and routed round solid blocks. While the key is held they chase the target,
 * turning after it as it runs; let go and they fly straight on. Each beam incinerates the one block
 * it lands on, or the creature it hits: that glows with embers for RingTuning omega_embers and
 * crumbles to ash. The server moves the beams; clients draw them from the head positions it sends
 * (client OmegaFx).
 */
public final class OmegaBeams {
	/** The Ring Lab's Omega start (client LabSettings.OmegaStart has the same order). */
	public enum Start { SNAP, SMOULDER, AIR_BRAKE, CRACKLE }

	/** How far ahead a target is picked, and the furthest a beam flies from its bearer. */
	static final double RANGE = 64, MAX_FLIGHT = 96;
	/** Head speed along a planned path, and while turning after a moving target (blocks a tick). */
	static final double PATH_SPEED = 0.85, CHASE_SPEED = 0.55;
	/** The most a chasing beam turns in a tick (radians), and its wobble. */
	static final double TURN = 0.22, CHASE_NOISE = 0.05;
	/** How far a target may move off the planned path's end before the beam turns after it instead. */
	private static final double DRIFT = 1.5;
	/** Path spacing and how far the routing grid's cells are apart. */
	private static final double SAMPLE = 0.2, CELL = 0.5;
	/** How far a planned route keeps off blocks. */
	private static final double CLEARANCE = 0.15;
	/** The eyes are about 2 px either side of the middle of the face. */
	private static final double EYE_SIDE = 0.12;
	/** 1% of a full ring a use. */
	public static final int COST = 10;
	/** How long E1 snap's flash and E3 air brake's brake take before the beams leave, in ticks. */
	private static final int SNAP_TICKS = 2, BRAKE_TICKS = 10;
	/** How far the beams are seen from. */
	private static final double VIEW = 128;
	/** The attribute modifier that holds the body still while the key is down (the client keeps the FOV from zooming with it). */
	public static final Identifier LOCK = LanternRing.id("omega_lock");

	private static final Map<UUID, Session> SESSIONS = new HashMap<>();
	private static final List<Beam> BEAMS = new ArrayList<>();
	private static final List<Burning> BURNING = new ArrayList<>();
	private static int nextBeam = 1;

	private OmegaBeams() {
	}

	/** One use: the start, then the two beams, while the key is held. */
	private static final class Session {
		final ServerPlayer player;
		final Start start;
		final Corps corps;
		int age, windup;
		boolean held = true, fired;

		Session(ServerPlayer player, Start start, Corps corps, int windup) {
			this.player = player;
			this.start = start;
			this.corps = corps;
			this.windup = windup;
		}
	}

	private enum Mode { PATH, CHASE, STRAIGHT }

	private static final class Beam {
		final int id = nextBeam++;
		final ServerPlayer owner;
		final ServerLevel level;
		final Session session;
		final RandomSource random;
		Vec3 pos, dir;
		List<Vec3> path = List.of();
		int along;
		@Nullable LivingEntity target;
		Vec3 goal;
		Mode mode = Mode.PATH;
		int age, replan;
		boolean done;

		Beam(Session session, Vec3 pos, Vec3 dir, @Nullable LivingEntity target, Vec3 goal) {
			this.session = session;
			this.owner = session.player;
			this.level = (ServerLevel) owner.level();
			this.random = owner.getRandom();
			this.pos = pos;
			this.dir = dir;
			this.target = target;
			this.goal = goal;
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
			if (payload.down()) press(player, Start.values()[Mth.clamp(payload.start(), 0, Start.values().length - 1)]);
			else release(player);
		});
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> end(handler.player));
		ServerTickEvents.END_SERVER_TICK.register(OmegaBeams::tick);
	}

	/** Whether this player is using the omega beams right now (its start or its beams, key held). */
	public static boolean active(Player player) {
		Session s = SESSIONS.get(player.getUUID());
		return s != null && s.held;
	}

	/** The omega key went down. Public for the game tests. */
	public static void press(ServerPlayer player, Start start) {
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
		Session s = new Session(player, start, Corps.of(ring), windup);
		SESSIONS.put(player.getUUID(), s);
		lock(player, true);
		ServerLevel level = (ServerLevel) player.level();
		send(level, player.getEyePosition(), new OmegaFxPayload(OmegaFxPayload.EYES, player.getId(), start.ordinal(), player.getEyePosition(), windup, 0));
		level.playSound(null, player.getX(), player.getEyeY(), player.getZ(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 0.6f, 1.9f);
	}

	/** The omega key came up: the beams stop chasing and fly straight on. */
	public static void release(ServerPlayer player) {
		Session s = SESSIONS.get(player.getUUID());
		if (s == null) return;
		s.held = false;
		lock(player, false);
		for (Beam b : BEAMS) {
			if (b.session == s && b.mode != Mode.STRAIGHT) b.mode = Mode.STRAIGHT;
		}
		if (s.fired && beamsOf(s) == 0) SESSIONS.remove(player.getUUID());
	}

	private static void end(ServerPlayer player) {
		Session s = SESSIONS.remove(player.getUUID());
		if (s == null) return;
		lock(player, false);
		BEAMS.removeIf(b -> b.session == s);
	}

	private static int beamsOf(Session s) {
		int n = 0;
		for (Beam b : BEAMS) if (b.session == s) n++;
		return n;
	}

	/** On the ground the body locks in place; in the air gravity lets go, so the brake leaves you hovering. */
	private static void lock(ServerPlayer player, boolean on) {
		for (var attribute : List.of(Attributes.MOVEMENT_SPEED, Attributes.JUMP_STRENGTH, Attributes.GRAVITY, Attributes.FLYING_SPEED)) {
			AttributeInstance a = player.getAttribute(attribute);
			if (a == null) continue;
			a.removeModifier(LOCK);
			if (on) a.addTransientModifier(new AttributeModifier(LOCK, -1.0, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
		}
	}

	// ---- every tick ---------------------------------------------------------------------------

	private static void tick(MinecraftServer server) {
		for (Iterator<Session> it = SESSIONS.values().iterator(); it.hasNext(); ) {
			Session s = it.next();
			ServerPlayer p = s.player;
			if (p.isRemoved() || !p.isAlive()) {
				lock(p, false);
				it.remove();
				BEAMS.removeIf(b -> b.session == s);
				continue;
			}
			s.age++;
			if (!s.fired && s.age >= s.windup) fire(s);
			else if (s.fired && beamsOf(s) == 0) {
				// Both beams have landed: the body lets go, even if the key is still down.
				lock(p, false);
				if (!s.held) it.remove();
			}
		}
		for (Iterator<Beam> it = BEAMS.iterator(); it.hasNext(); ) {
			Beam b = it.next();
			if (!b.done) step(b);
			if (b.done) it.remove();
		}
		// Sessions whose beams just finished and whose key is up.
		SESSIONS.values().removeIf(s -> s.fired && !s.held && beamsOf(s) == 0);
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

	/** The start is over: the two beams leave the eyes. */
	private static void fire(Session s) {
		s.fired = true;
		ServerPlayer p = s.player;
		ServerLevel level = (ServerLevel) p.level();
		ItemStack ring = RingFlight.findRing(p);
		if (ring.isEmpty() || PowerRingItem.getCharge(ring) <= 0) return;
		if (!p.isCreative()) PowerRingItem.setCharge(ring, Math.max(0, PowerRingItem.getCharge(ring) - COST));
		LivingEntity target = aimed(level, p);
		Vec3 eye = p.getEyePosition();
		Vec3 look = p.getLookAngle();
		Vec3 goal = target != null ? middle(target) : aimPoint(level, p);
		Vec3 right = look.cross(new Vec3(0, 1, 0));
		right = right.lengthSqr() < 1e-6 ? new Vec3(1, 0, 0) : right.normalize();
		for (int side = -1; side <= 1; side += 2) {
			Vec3 from = eye.add(look.scale(0.3)).add(right.scale(side * EYE_SIDE));
			// At a block, each beam takes its own: the one aimed at and its neighbour, side by side.
			Vec3 own = goal;
			if (target == null) {
				Vec3 beside = goal.add(right.scale(side * 0.6));
				if (solidAt(level, BlockPos.containing(beside), beside)) own = beside;
			}
			Beam b = new Beam(s, from, look, target, own);
			if (s.held) b.path = plan(level, from, own, b.random, true);
			else b.mode = Mode.STRAIGHT;
			b.dir = b.path.size() > 1 ? b.path.get(1).subtract(b.path.get(0)).normalize() : look;
			if (!s.held) b.dir = own.subtract(from).normalize();
			BEAMS.add(b);
		}
		level.playSound(null, p.getX(), p.getEyeY(), p.getZ(), SoundEvents.FIRECHARGE_USE, SoundSource.PLAYERS, 0.9f, 1.7f);
		level.playSound(null, p.getX(), p.getEyeY(), p.getZ(), SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 0.5f, 2f);
	}

	/** One tick of a beam's flight. */
	private static void step(Beam b) {
		b.age++;
		if (b.owner.isRemoved() || b.age > RingTuning.OMEGA_CHASE.ticks() || b.pos.distanceToSqr(b.owner.position()) > MAX_FLIGHT * MAX_FLIGHT) {
			finish(b, 0);
			return;
		}
		LivingEntity target = b.target;
		boolean chasing = b.session.held && target != null && target.isAlive() && !target.isRemoved();
		if (b.mode != Mode.STRAIGHT && target != null && !chasing && b.mode == Mode.CHASE) b.mode = Mode.STRAIGHT;
		if (b.replan > 0) b.replan--;
		switch (b.mode) {
			case PATH -> {
				if (chasing && middle(target).distanceTo(b.goal) > DRIFT) {
					b.mode = Mode.CHASE;
					chase(b, target);
					return;
				}
				double left = PATH_SPEED;
				while (left > 0 && !b.done) {
					if (b.along + 1 >= b.path.size()) {
						// Off the end of the path: on after the target, or straight on into whatever is there.
						b.mode = chasing ? Mode.CHASE : Mode.STRAIGHT;
						move(b, b.pos.add(b.dir.scale(left)));
						break;
					}
					Vec3 next = b.path.get(b.along + 1);
					double d = next.distanceTo(b.pos);
					if (d <= left) {
						if (!move(b, next)) b.along++;
						left -= d;
					} else {
						move(b, b.pos.add(next.subtract(b.pos).scale(left / d)));
						left = 0;
					}
				}
			}
			case CHASE -> chase(b, target);
			case STRAIGHT -> move(b, b.pos.add(b.dir.scale(PATH_SPEED)));
		}
		if (!b.done) send(b.level, b.pos, new OmegaFxPayload(OmegaFxPayload.HEAD, b.id, b.owner.getId(), b.pos, 0, 0));
	}

	/** Turns after the target (at most TURN a tick, a little more up close so it can't circle it), or routes round blocks in the way. */
	private static void chase(Beam b, @Nullable LivingEntity target) {
		if (target == null || !target.isAlive()) {
			b.mode = Mode.STRAIGHT;
			move(b, b.pos.add(b.dir.scale(PATH_SPEED)));
			return;
		}
		Vec3 aim = middle(target);
		if (b.replan == 0 && blocked(b.level, b.pos, aim, b.owner)) {
			b.replan = 10;
			List<Vec3> route = plan(b.level, b.pos, aim, b.random, false);
			if (route.size() > 1) {
				b.path = route;
				b.along = 0;
				b.goal = aim;
				b.mode = Mode.PATH;
				return;
			}
		}
		Vec3 want = aim.subtract(b.pos);
		double dist = want.length();
		if (dist < 1e-4) {
			move(b, aim);
			return;
		}
		want = want.scale(1 / dist);
		double turn = TURN * Math.max(1, 2.5 / dist);
		b.dir = turn(b.dir, want, turn).add(jitter(b.random, CHASE_NOISE)).normalize();
		move(b, b.pos.add(b.dir.scale(Math.min(CHASE_SPEED, dist + 0.3))));
	}

	/** dir turned toward want by at most max radians. */
	static Vec3 turn(Vec3 dir, Vec3 want, double max) {
		double cos = Mth.clamp(dir.dot(want), -1, 1);
		double angle = Math.acos(cos);
		if (angle <= max) return want;
		Vec3 axis = dir.cross(want);
		if (axis.lengthSqr() < 1e-8) axis = Math.abs(dir.y) < 0.9 ? dir.cross(new Vec3(0, 1, 0)) : dir.cross(new Vec3(1, 0, 0));
		axis = axis.normalize();
		// Rodrigues: rotate dir about axis by max.
		double c = Math.cos(max), s = Math.sin(max);
		return dir.scale(c).add(axis.cross(dir).scale(s)).add(axis.scale(axis.dot(dir) * (1 - c))).normalize();
	}

	/** Moves the head to {@code to}, checking for hits on the way. True if it hit something (and is done). */
	private static boolean move(Beam b, Vec3 to) {
		Vec3 from = b.pos;
		Vec3 d = to.subtract(from);
		double len = d.length();
		if (len > 1e-6) b.dir = d.scale(1 / len);
		int steps = Math.max(1, (int) Math.ceil(len / 0.2));
		for (int i = 1; i <= steps; i++) {
			Vec3 p = from.add(d.scale(i / (double) steps));
			LivingEntity mob = mobAt(b, p);
			if (mob != null) {
				b.pos = p;
				burnMob(b, mob);
				finish(b, 2);
				return true;
			}
			BlockPos bp = BlockPos.containing(p);
			if (solidAt(b.level, bp, p)) {
				b.pos = p;
				burnBlock(b, bp);
				finish(b, 1);
				return true;
			}
		}
		b.pos = to;
		return false;
	}

	private static void finish(Beam b, int how) {
		b.done = true;
		send(b.level, b.pos, new OmegaFxPayload(OmegaFxPayload.END, b.id, how, b.pos, 0, 0));
	}

	private static @Nullable LivingEntity mobAt(Beam b, Vec3 p) {
		// A creature already burning still catches the second beam (it just adds to the embers).
		List<LivingEntity> hit = b.level.getEntitiesOfClass(LivingEntity.class, new AABB(p, p).inflate(0.15), e -> burnable(b.owner, e) || burning(e));
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

	/** For planning: whether p is in or within CLEARANCE of a solid block, so a route keeps a little off walls and corners. */
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
	private static void burnBlock(Beam b, BlockPos bp) {
		ServerLevel level = b.level;
		BlockState state = level.getBlockState(bp);
		if (state.getDestroySpeed(level, bp) < 0) {
			// Bedrock and the like only scorch.
			send(level, b.pos, new OmegaFxPayload(OmegaFxPayload.BURN_BLOCK, Block.getId(state), 1, Vec3.atLowerCornerOf(bp), 4, 0));
			return;
		}
		int ticks = Math.max(1, RingTuning.OMEGA_EMBERS.ticks());
		send(level, b.pos, new OmegaFxPayload(OmegaFxPayload.BURN_BLOCK, Block.getId(state), 0, Vec3.atLowerCornerOf(bp), ticks, 0));
		BlockState glow = ModRegistry.BEAM_GLOW.defaultBlockState().setValue(Corps.PROPERTY, Corps.ORANGE)
				.setValue(BlastGlowBlock.LEVEL, BlastGlowBlock.START_LEVEL);
		level.setBlock(bp, glow, 3);
		level.playSound(null, bp, SoundEvents.FIRECHARGE_USE, SoundSource.BLOCKS, 0.5f, 0.8f + b.random.nextFloat() * 0.3f);
		level.playSound(null, bp, SoundEvents.LAVA_POP, SoundSource.BLOCKS, 0.8f, 0.9f);
	}

	/**
	 * A creature hit: it freezes as glowing embers and crumbles to ash after RingTuning omega_embers.
	 * Players and bosses can't be unmade like that; they take a heavy burn instead.
	 */
	private static void burnMob(Beam b, LivingEntity mob) {
		ServerLevel level = b.level;
		if (burning(mob)) return;
		mob.igniteForSeconds(5);
		level.playSound(null, mob.getX(), mob.getEyeY(), mob.getZ(), SoundEvents.FIRECHARGE_USE, SoundSource.HOSTILE, 0.8f, 0.7f);
		if (!(mob instanceof Mob m) || mob instanceof EnderDragon || mob instanceof WitherBoss) {
			mob.hurtServer(level, level.damageSources().indirectMagic(b.owner, b.owner), mob instanceof Player ? 14 : 30);
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

	private static boolean blocked(ServerLevel level, Vec3 from, Vec3 to, Entity owner) {
		HitResult hit = level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, owner));
		return hit.getType() != HitResult.Type.MISS && hit.getLocation().distanceToSqr(to) > 0.36;
	}

	// ---- the route ----------------------------------------------------------------------------

	/**
	 * A beam's route from {@code from} to {@code goal}, as points about SAMPLE apart. With
	 * {@code wander}: 2 to 4 random waypoints thrown off the straight line (sigma 0.28 x the distance,
	 * biased upward) and a random last approach, so each beam takes its own path and can strike from
	 * any angle. Legs that run into blocks are routed round them on a half-block grid (A* with a
	 * little random cost); the control points are joined by a Catmull-Rom curve. If the curve still
	 * clips a block, the grid route itself is used.
	 */
	static List<Vec3> plan(ServerLevel level, Vec3 from, Vec3 goal, RandomSource random, boolean wander) {
		double dist = goal.distanceTo(from);
		List<Vec3> controls = new ArrayList<>();
		controls.add(from);
		if (wander && dist > 3) {
			Vec3 f = goal.subtract(from).scale(1 / dist);
			Vec3 u = f.cross(new Vec3(0, 1, 0));
			u = u.lengthSqr() < 1e-6 ? new Vec3(1, 0, 0) : u.normalize();
			Vec3 v = u.cross(f).normalize();
			double sigma = 0.28 * dist;
			int n = 2 + random.nextInt(3);
			List<Double> ts = new ArrayList<>();
			for (int i = 0; i < n; i++) ts.add(0.15 + random.nextDouble() * 0.6);
			Collections.sort(ts);
			for (double t : ts) {
				Vec3 w = from.add(f.scale(dist * t)).add(u.scale(random.nextGaussian() * sigma)).add(v.scale(random.nextGaussian() * sigma * 0.7))
						.add(0, Math.abs(random.nextGaussian()) * sigma * 0.4, 0);
				w = free(level, w);
				if (w != null) controls.add(w);
			}
			// The last approach: from any direction, as long as that point is in the open.
			double reach = Math.min(4, dist * 0.3);
			for (int tries = 0; tries < 8; tries++) {
				Vec3 a = new Vec3(random.nextGaussian(), random.nextGaussian(), random.nextGaussian());
				if (a.lengthSqr() < 1e-4) continue;
				Vec3 before = goal.subtract(a.normalize().scale(reach));
				if (!nearSolid(level, before)) {
					controls.add(before);
					break;
				}
			}
		}
		controls.add(goal);
		// Route each leg that runs into something round it.
		List<Vec3> routed = new ArrayList<>();
		routed.add(controls.get(0));
		for (int i = 1; i < controls.size(); i++) {
			Vec3 a = controls.get(i - 1), c = controls.get(i);
			boolean last = i == controls.size() - 1;
			if (legBlocked(level, a, c, last)) {
				List<Vec3> around = route(level, a, c, random);
				if (around != null) routed.addAll(simplify(around, random, level));
			}
			routed.add(c);
		}
		List<Vec3> curve = catmullRom(routed);
		if (clips(level, curve, goal)) {
			List<Vec3> grid = route(level, from, goal, random);
			if (grid != null) {
				grid.add(goal);
				return densify(grid);
			}
		}
		return curve;
	}

	/** The point, or the nearest free spot up to 6 blocks above it, or null. */
	private static @Nullable Vec3 free(ServerLevel level, Vec3 p) {
		for (int up = 0; up <= 6; up++) {
			Vec3 q = p.add(0, up, 0);
			if (!nearSolid(level, q)) return q;
		}
		return null;
	}

	private static boolean legBlocked(ServerLevel level, Vec3 a, Vec3 c, boolean toGoal) {
		double len = a.distanceTo(c);
		int steps = Math.max(1, (int) Math.ceil(len / 0.25));
		for (int i = 1; i < steps; i++) {
			Vec3 p = a.add(c.subtract(a).scale(i / (double) steps));
			if (toGoal && p.distanceToSqr(c) < 0.6 * 0.6) return false;
			if (nearSolid(level, p)) return true;
		}
		return false;
	}

	private static boolean clips(ServerLevel level, List<Vec3> path, Vec3 goal) {
		for (int i = 1; i < path.size(); i++) {
			Vec3 p = path.get(i);
			if (p.distanceToSqr(goal) < 0.6 * 0.6) return false;
			if (nearSolid(level, p)) return true;
		}
		return false;
	}

	/** A Catmull-Rom curve through the points, sampled about SAMPLE apart. */
	static List<Vec3> catmullRom(List<Vec3> pts) {
		List<Vec3> out = new ArrayList<>();
		out.add(pts.get(0));
		for (int i = 0; i + 1 < pts.size(); i++) {
			Vec3 p0 = pts.get(Math.max(0, i - 1)), p1 = pts.get(i), p2 = pts.get(i + 1), p3 = pts.get(Math.min(pts.size() - 1, i + 2));
			int n = Math.max(1, (int) Math.ceil(p1.distanceTo(p2) / SAMPLE));
			for (int k = 1; k <= n; k++) {
				double t = k / (double) n, t2 = t * t, t3 = t2 * t;
				out.add(p0.scale(-0.5 * t3 + t2 - 0.5 * t)
						.add(p1.scale(1.5 * t3 - 2.5 * t2 + 1))
						.add(p2.scale(-1.5 * t3 + 2 * t2 + 0.5 * t))
						.add(p3.scale(0.5 * t3 - 0.5 * t2)));
			}
		}
		return out;
	}

	private static List<Vec3> densify(List<Vec3> pts) {
		List<Vec3> out = new ArrayList<>();
		out.add(pts.get(0));
		for (int i = 0; i + 1 < pts.size(); i++) {
			Vec3 a = pts.get(i), c = pts.get(i + 1);
			int n = Math.max(1, (int) Math.ceil(a.distanceTo(c) / SAMPLE));
			for (int k = 1; k <= n; k++) out.add(a.add(c.subtract(a).scale(k / (double) n)));
		}
		return out;
	}

	/** A handful of the grid route's points (every third and the corners), jittered a little where that stays clear. */
	private static List<Vec3> simplify(List<Vec3> cells, RandomSource random, ServerLevel level) {
		List<Vec3> out = new ArrayList<>();
		for (int i = 1; i < cells.size() - 1; i++) {
			Vec3 prev = cells.get(i - 1), here = cells.get(i), next = cells.get(i + 1);
			boolean corner = here.subtract(prev).normalize().dot(next.subtract(here).normalize()) < 0.95;
			if (!corner && i % 3 != 0) continue;
			Vec3 j = here.add(jitter(random, 0.2));
			out.add(nearSolid(level, j) ? here : j);
		}
		return out;
	}

	private record Node(int x, int y, int z, double g, double f, @Nullable Node parent) {
	}

	/**
	 * A* on a half-block grid from a to c, avoiding solid blocks, with a little random cost so routes
	 * vary. Returns the grid points between (not a or c), or null if none was found in time.
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
				List<Vec3> out = new ArrayList<>();
				for (Node k = n; k != null && k.parent != null; k = k.parent) out.add(cell(a, k.x, k.y, k.z));
				Collections.reverse(out);
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
		return cache.computeIfAbsent(key(x, y, z), k -> {
			Vec3 p = cell(a, x, y, z);
			return nearSolid(level, p);
		});
	}

	private static Vec3 cell(Vec3 a, double x, double y, double z) {
		return a.add(x * CELL, y * CELL, z * CELL);
	}

	private static long key(int x, int y, int z) {
		return ((long) (x & 0x1FFFFF) << 42) | ((long) (y & 0x1FFFFF) << 21) | (z & 0x1FFFFF);
	}

	private static Vec3 jitter(RandomSource r, double amount) {
		return new Vec3((r.nextDouble() - 0.5) * 2 * amount, (r.nextDouble() - 0.5) * 2 * amount, (r.nextDouble() - 0.5) * 2 * amount);
	}

	private static void send(ServerLevel level, Vec3 at, OmegaFxPayload payload) {
		for (ServerPlayer viewer : PlayerLookup.around(level, at, VIEW)) ServerPlayNetworking.send(viewer, payload);
	}
}
