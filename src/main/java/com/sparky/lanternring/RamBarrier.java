package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import com.sparky.lanternring.net.RamHolePayload;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
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
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * The ram barrier: after a couple of seconds of fast ring flight a thin shell of hard light, a cap
 * of a sphere the Dome's size, forms ahead of the flyer. Mobs, players and projectiles it runs into
 * are blown away from where it hit them; a body knocked into the ground craters it and throws the
 * blocks out in a shockwave. Flying it into a wall stops you dead: the barrier shatters and takes
 * the part of the wall it hit with it, and it can't form again until its cooldown is over.
 *
 * <p>The server only decides what it hits. Clients draw it from RAM_BARRIER effects (see the
 * client's RamBarrierFx, which is where J's Blender model plugs in).
 */
public final class RamBarrier {
	/** The shell's radius round the flyer's middle: the held Dome's size. */
	public static final double RADIUS = 4.5;
	/** How far round from straight ahead the shell reaches (cos of the angle, about 55 degrees). */
	public static final double CAP_COS = 0.57;
	/** Blocks per tick that count as fast flight (the ring glide tops out near 1.6). */
	private static final double FAST = 0.75;
	/** Ticks of slower flight before the barrier fades, so a turn doesn't drop it. */
	private static final int FADE_TICKS = 10;
	/** How often a held barrier is re-announced, so clients that come near see it too. */
	private static final int ANNOUNCE = 8;
	/**
	 * How much of a wall the shattering barrier takes with it, picked per player in the Ring Lab
	 * (J wanted to try them side by side): depth and width of the hole, in blocks.
	 */
	public enum Hole {
		/** A bowl the shape of the shell pressed into the wall. */
		DENT(3, 3.2),
		/** A big crater. */
		CRATER(6, 5.5),
		/** Only the blocks the shell actually touched. */
		TOUCHING(1, 2.4);

		final double depth;
		final double width;

		Hole(double depth, double width) {
			this.depth = depth;
			this.width = width;
		}
	}

	/** Damage each flyer takes when two ram barriers meet: a little, and both shatter. */
	private static final float CLASH_DAMAGE = 3f;
	/** Share of broken wall blocks thrown out as falling blocks. */
	private static final float FLING = 0.25f;
	/** Ticks a launched body is watched for hitting the ground. */
	private static final int LAUNCH_WATCH = 60;
	/** Ticks a player's launch is forced on them before they get control back. */
	private static final int PLAYER_TUMBLE = 8;
	/** Charge a hit and a wall crash cost. */
	private static final int HIT_COST = 2;
	private static final int CRASH_COST = 6;

	private static final class State {
		Vec3 last;
		Vec3 dir = Vec3.ZERO;
		int fastTicks;
		int slowTicks;
		boolean up;
		long cooldownUntil;
		/** Entity id to the game time it was last hit, so one pass hits each thing once. */
		final Map<Integer, Long> hit = new HashMap<>();
	}

	/** A body the barrier knocked flying, watched until it lands. */
	private static final class Launch {
		final ServerLevel level;
		final Entity entity;
		final Player by;
		final Vec3 push;
		Vec3 last;
		double speed;
		int age;

		Launch(ServerLevel level, Entity entity, Player by, Vec3 push) {
			this.level = level;
			this.entity = entity;
			this.by = by;
			this.push = push;
			this.last = entity.position();
		}
	}

	private static final Map<UUID, State> STATES = new HashMap<>();
	private static final Map<Integer, Launch> LAUNCHED = new HashMap<>();
	/** Each player's Ring Lab pick of how big a hole a wall hit leaves. */
	private static final Map<UUID, Hole> HOLES = new HashMap<>();

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(RamBarrier::tick);
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
			STATES.remove(handler.player.getUUID());
			HOLES.remove(handler.player.getUUID());
		});
		PayloadTypeRegistry.serverboundPlay().register(RamHolePayload.TYPE, RamHolePayload.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(RamHolePayload.TYPE, (payload, context) -> {
			Hole[] holes = Hole.values();
			HOLES.put(context.player().getUUID(), holes[Math.floorMod(payload.hole(), holes.length)]);
		});
	}

	/** True while the player's barrier is up (for tests). */
	public static boolean isUp(Player player) {
		State s = STATES.get(player.getUUID());
		return s != null && s.up;
	}

	private static void tick(MinecraftServer server) {
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			State s = STATES.computeIfAbsent(player.getUUID(), id -> new State());
			ItemStack ring = RingFlight.findRing(player);
			Vec3 now = player.position();
			Vec3 move = s.last == null ? Vec3.ZERO : now.subtract(s.last);
			s.last = now;
			boolean flying = player.getAbilities().flying && !player.isSpectator() && !ring.isEmpty()
					&& PowerRingItem.getCharge(ring) > 0 && PowerRingItem.isFlightOn(ring)
					// Low ground flight has its own running barrier (MoveFlights).
					&& !MoveFlights.grounded(player);
			// A teleport isn't flight.
			if (!flying || move.length() > 8) {
				if (s.up) lower(player, s);
				s.fastTicks = 0;
				continue;
			}
			double speed = move.length();
			if (speed >= FAST) {
				s.fastTicks++;
				s.slowTicks = 0;
				Vec3 d = move.normalize();
				s.dir = s.dir == Vec3.ZERO ? d : s.dir.scale(0.6).add(d.scale(0.4)).normalize();
			} else if (++s.slowTicks > FADE_TICKS) {
				s.fastTicks = 0;
				if (s.up) lower(player, s);
			}
			ServerLevel level = (ServerLevel) player.level();
			if (!s.up && s.fastTicks >= RingTuning.RAM_BARRIER_FORM.ticks() && level.getGameTime() >= s.cooldownUntil) raise(player, s);
			if (!s.up) continue;
			Corps before = Corps.enter(Corps.of(ring));
			try {
				if (player.tickCount % ANNOUNCE == 0) announce(level, player, s, 1f);
				if (!crash(level, player, ring, s, Math.max(speed, FAST))) hits(level, player, ring, s, Math.max(speed, FAST));
			} finally {
				Corps.restore(before);
			}
		}
		watchLaunches();
	}

	private static Vec3 middle(Player player) {
		return player.getBoundingBox().getCenter();
	}

	private static void announce(ServerLevel level, Player player, State s, float up) {
		Vec3 mid = middle(player);
		// variant carries the flyer's id: "bearer" would point their ring arm as if they had fired.
		RingFx.send(level, Kind.RAM_BARRIER, mid, mid.add(s.dir), up, player.getId(), null);
	}

	private static void raise(ServerPlayer player, State s) {
		s.up = true;
		s.hit.clear();
		ServerLevel level = (ServerLevel) player.level();
		Corps before = Corps.enter(Corps.of(RingFlight.findRing(player)));
		try {
			announce(level, player, s, 1f);
		} finally {
			Corps.restore(before);
		}
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 0.8f, 1.7f);
	}

	private static void lower(ServerPlayer player, State s) {
		s.up = false;
		ServerLevel level = (ServerLevel) player.level();
		Corps before = Corps.enter(Corps.of(RingFlight.findRing(player)));
		try {
			announce(level, player, s, 0f);
		} finally {
			Corps.restore(before);
		}
	}

	/** Whether {@code at} lies on or inside the front of the shell. */
	private static boolean inCap(Vec3 mid, Vec3 dir, Vec3 at, double reach, double slack) {
		Vec3 rel = at.subtract(mid);
		double d = rel.length();
		if (d > RADIUS + reach || d < 1e-3) return false;
		return rel.scale(1 / d).dot(dir) >= CAP_COS - slack;
	}

	/** Runs the shell into whatever is in front of it. */
	private static void hits(ServerLevel level, ServerPlayer player, ItemStack ring, State s, double speed) {
		Vec3 mid = middle(player);
		long now = level.getGameTime();
		s.hit.values().removeIf(t -> now - t > 20);
		AABB box = new AABB(mid, mid).inflate(RADIUS + 2).expandTowards(s.dir.scale(speed));
		for (Entity e : level.getEntities(player, box, e -> e.isAlive() && (e instanceof LivingEntity || e instanceof Projectile))) {
			if (s.hit.containsKey(e.getId())) continue;
			if (e instanceof Projectile p && p.getOwner() == player) continue;
			Vec3 c = e.getBoundingBox().getCenter();
			if (!inCap(mid, s.dir, c, e.getBbWidth() * 0.5 + 0.5 + speed, 0.1)) continue;
			s.hit.put(e.getId(), now);
			if (e instanceof ServerPlayer other && isUp(other)) {
				clash(level, player, s, other, mid);
				return;
			}
			strike(level, player, ring, s.dir, speed, e, mid);
		}
	}

	/** Two ram barriers meet: both shatter, both flyers take a little damage and are thrown apart. */
	private static void clash(ServerLevel level, ServerPlayer player, State s, ServerPlayer other, Vec3 mid) {
		Vec3 otherMid = middle(other);
		Vec3 contact = mid.lerp(otherMid, 0.5);
		Vec3 apart = otherMid.subtract(mid);
		apart = apart.lengthSqr() < 1e-4 ? s.dir : apart.normalize();
		for (ServerPlayer p : new ServerPlayer[] {player, other}) {
			State ps = STATES.get(p.getUUID());
			ItemStack ring = RingFlight.findRing(p);
			Corps before = Corps.enter(ring.isEmpty() ? Corps.GREEN : Corps.of(ring));
			try {
				shatter(level, p, ps, contact, 1.5);
			} finally {
				Corps.restore(before);
			}
			p.hurtServer(level, level.damageSources().playerAttack(p == player ? other : player), CLASH_DAMAGE);
			Vec3 away = p == player ? apart.scale(-1) : apart;
			p.setDeltaMovement(away.scale(1.6).add(0, 0.3, 0));
			RingPowers.syncVelocity(p);
		}
		RingFx.send(level, Kind.LASSO_SLAM, contact, contact, 3f, 0, null);
		level.playSound(null, contact.x, contact.y, contact.z, SoundEvents.GENERIC_EXPLODE, SoundSource.PLAYERS, 2.5f, 0.9f);
		level.playSound(null, contact.x, contact.y, contact.z, SoundEvents.GLASS_BREAK, SoundSource.PLAYERS, 2f, 0.7f);
		level.sendParticles(ParticleTypes.EXPLOSION, contact.x, contact.y, contact.z, 4, 1, 1, 1, 0);
	}

	/** The barrier breaks at contact: it goes down, its cooldown starts, and every client draws it shattering. */
	private static void shatter(ServerLevel level, ServerPlayer player, State s, Vec3 contact, double speed) {
		s.up = false;
		s.fastTicks = 0;
		s.cooldownUntil = level.getGameTime() + RingTuning.RAM_BARRIER_COOLDOWN.ticks();
		announce(level, player, s, 0f);
		RingFx.send(level, Kind.RAM_BREAK, contact, contact.subtract(s.dir), (float) speed, player.getId(), null);
	}

	private static void strike(ServerLevel level, ServerPlayer player, ItemStack ring, Vec3 dir, double speed, Entity e, Vec3 mid) {
		Vec3 c = e.getBoundingBox().getCenter();
		Vec3 out = c.subtract(mid);
		out = out.lengthSqr() < 1e-4 ? dir : out.normalize();
		Vec3 contact = mid.add(out.scale(Math.min(RADIUS, c.distanceTo(mid))));
		// Away from where the shell met it, mostly along the flight.
		Vec3 away = dir.scale(0.75).add(out.scale(0.45)).normalize();
		double power = 1.4 + speed * 1.2;
		Vec3 push = away.scale(power);
		// A level or rising ram pops it up a little; diving onto it drives it down into the ground.
		if (dir.y > -0.35) push = push.add(0, 0.35, 0);
		level.playSound(null, contact.x, contact.y, contact.z, SoundEvents.GENERIC_EXPLODE, SoundSource.PLAYERS, 1.2f, 1.25f);
		level.sendParticles(ParticleTypes.EXPLOSION, contact.x, contact.y, contact.z, 2, 0.4, 0.4, 0.4, 0);
		RingFx.send(level, Kind.RAM_HIT, contact, contact.add(away), (float) speed, 0, null);
		if (e instanceof Projectile) {
			// Arrows and fireballs glance off back the way they came.
			e.setDeltaMovement(away.scale(Math.max(1.2, e.getDeltaMovement().length())));
			RingPowers.syncVelocity(e);
			return;
		}
		LivingEntity body = (LivingEntity) e;
		body.hurtServer(level, level.damageSources().playerAttack(player), (float) (4 + speed * 6));
		if (body instanceof ServerPlayer hitPlayer && hitPlayer.getAbilities().flying) {
			// Knocked out of the air: they tumble until they can fly again.
			hitPlayer.getAbilities().flying = false;
			hitPlayer.onUpdateAbilities();
		}
		body.setDeltaMovement(push);
		RingPowers.syncVelocity(body);
		LAUNCHED.put(body.getId(), new Launch(level, body, player, push));
		PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - HIT_COST);
	}

	/**
	 * Flying the shell into a wall: if what lies straight ahead would stop you before the next
	 * tick, the barrier shatters, takes the wall it hit with it, and you stop.
	 */
	private static boolean crash(ServerLevel level, ServerPlayer player, ItemStack ring, State s, double speed) {
		Vec3 mid = middle(player);
		double reach = RADIUS + speed;
		BlockHitResult hit = null;
		// The middle, head and feet: any of them about to run into something solid.
		for (double dy : new double[] {0, 0.7, -0.4}) {
			Vec3 from = mid.add(0, dy, 0);
			BlockHitResult r = level.clip(new ClipContext(from, from.add(s.dir.scale(reach)), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
			if (r.getType() == HitResult.Type.BLOCK && (hit == null || r.getLocation().distanceToSqr(from) < hit.getLocation().distanceToSqr(mid))) hit = r;
		}
		if (hit == null) return false;
		// The shell meets the wall first; skip a lone block it can't really have met (a flower, a torch).
		BlockState face = level.getBlockState(hit.getBlockPos());
		if (face.getCollisionShape(level, hit.getBlockPos()).isEmpty()) return false;
		Vec3 contact = hit.getLocation();
		breakWall(level, player, s.dir, contact, speed);
		PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - CRASH_COST);
		// The shattering: a burst of hard light, a blast, and every camera nearby jolts.
		shatter(level, player, s, contact, speed);
		RingFx.send(level, Kind.LASSO_SLAM, contact, contact, (float) (speed + 1), 0, null);
		level.playSound(null, contact.x, contact.y, contact.z, SoundEvents.GENERIC_EXPLODE, SoundSource.PLAYERS, 2f, 0.8f);
		level.playSound(null, contact.x, contact.y, contact.z, SoundEvents.GLASS_BREAK, SoundSource.PLAYERS, 2f, 0.6f);
		level.sendParticles(ParticleTypes.EXPLOSION, contact.x, contact.y, contact.z, 3, 1, 1, 1, 0);
		// You stop dead against it (the client drops its glide speed when it sees RAM_BREAK).
		player.setDeltaMovement(Vec3.ZERO);
		RingPowers.syncVelocity(player);
		return true;
	}

	/** Knocks a bowl out of the wall round where the shell hit it, deeper along the flight. */
	private static void breakWall(ServerLevel level, Player player, Vec3 dir, Vec3 contact, double speed) {
		Vec3 middle = contact.add(dir.scale(0.5));
		Hole hole = HOLES.getOrDefault(player.getUUID(), Hole.DENT);
		double depth = hole.depth + (hole == Hole.TOUCHING ? 0 : Math.min(1.5, speed * 0.5));
		int ri = (int) Math.ceil(Math.max(depth, hole.width)) + 1;
		BlockPos at = BlockPos.containing(middle);
		BlockState loudest = null;
		for (BlockPos pos : BlockPos.betweenClosed(at.offset(-ri, -ri, -ri), at.offset(ri, ri, ri))) {
			Vec3 rel = Vec3.atCenterOf(pos).subtract(contact);
			double along = rel.dot(dir);
			if (along < -0.6 || along > depth) continue;
			// The hole narrows toward its back, the shape of the shell pressed into the wall.
			double across = rel.subtract(dir.scale(along)).length();
			double width = hole.width * Math.sqrt(Math.max(0, 1 - Math.max(0, along) / (depth + 0.5)));
			if (across > width) continue;
			BlockState state = level.getBlockState(pos);
			if (!breakable(level, player, pos, state)) continue;
			BlockPos hit = pos.immutable();
			level.setBlock(hit, Blocks.AIR.defaultBlockState(), 3);
			if (level.getRandom().nextFloat() < FLING) Anvils.fling(level, hit, state, contact.add(dir.scale(3)));
			else HeldConstructs.debris(level, hit, state);
			if (loudest == null) loudest = state;
		}
		if (loudest != null) {
			level.playSound(null, contact.x, contact.y, contact.z, loudest.getSoundType().getBreakSound(), SoundSource.PLAYERS, 2f, 0.6f);
			level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, loudest), contact.x, contact.y, contact.z, 40, 1.5, 1.5, 1.5, 0.3);
		}
	}

	private static boolean breakable(ServerLevel level, Player player, BlockPos pos, BlockState state) {
		return !state.isAir() && state.getFluidState().isEmpty() && !state.hasBlockEntity() && state.getDestroySpeed(level, pos) >= 0
				&& !state.is(ModRegistry.LIGHT_CONSTRUCT) && !(state.getBlock() instanceof com.sparky.lanternring.block.BlastGlowBlock)
				&& level.mayInteract(player, pos);
	}

	/** Bodies the barrier knocked flying: a player can't steer for a moment, and hitting the ground craters it. */
	private static void watchLaunches() {
		Iterator<Launch> it = LAUNCHED.values().iterator();
		while (it.hasNext()) {
			Launch l = it.next();
			Entity e = l.entity;
			if (!e.isAlive() || e.level() != l.level || ++l.age > LAUNCH_WATCH) {
				it.remove();
				continue;
			}
			if (e instanceof ServerPlayer p && l.age <= PLAYER_TUMBLE) {
				// Sent flying uncontrollably: the push holds for a moment against their own steering.
				double fade = 1 - (double) l.age / (PLAYER_TUMBLE + 2);
				p.setDeltaMovement(l.push.scale(fade).add(0, -0.08 * l.age, 0));
				RingPowers.syncVelocity(p);
			}
			Vec3 now = e.position();
			double moved = now.distanceTo(l.last);
			Vec3 motion = now.subtract(l.last);
			l.last = now;
			if (l.age < 3) {
				l.speed = Math.max(l.speed, moved);
				continue;
			}
			boolean landed = e.onGround() || e.horizontalCollision || e.verticalCollision;
			if (landed && l.speed > 0.45) {
				it.remove();
				impact(l, motion.lengthSqr() > 1e-4 ? motion.normalize() : new Vec3(0, -1, 0));
				continue;
			}
			l.speed = moved;
		}
	}

	/** A body slammed into the ground: a crater, the blocks thrown out in a shockwave, and everyone round it shoved off. */
	private static void impact(Launch l, Vec3 travel) {
		ServerLevel level = l.level;
		Entity e = l.entity;
		double speed = l.speed;
		Vec3 at = e.position();
		ItemStack ring = l.by instanceof ServerPlayer sp ? RingFlight.findRing(sp) : ItemStack.EMPTY;
		Corps before = Corps.enter(ring.isEmpty() ? Corps.GREEN : Corps.of(ring));
		try {
			double r = Mth.clamp(1.5 + speed * 1.2, 2, 4.5);
			if (e instanceof LivingEntity body) body.hurtServer(level, level.damageSources().fall(), (float) (2 + speed * 4));
			RingFx.send(level, Kind.SHOCKWAVE, at.add(0, 0.2, 0), at.add(r * 1.8, 0.2, 0));
			RingFx.send(level, Kind.LASSO_SLAM, at, at, (float) speed, 0, null);
			level.playSound(null, at.x, at.y, at.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.PLAYERS, 1.6f, 0.8f);
			level.sendParticles(ParticleTypes.EXPLOSION, at.x, at.y, at.z, 2, r * 0.4, 0.2, r * 0.4, 0);
			// The crater: a shallow bowl under where it landed, its blocks flung out away from it.
			int ri = (int) Math.ceil(r);
			BlockPos centre = BlockPos.containing(at.x, at.y - 0.5, at.z);
			for (BlockPos pos : BlockPos.betweenClosed(centre.offset(-ri, -ri, -ri), centre.offset(ri, 1, ri))) {
				Vec3 rel = Vec3.atCenterOf(pos).subtract(at.x, at.y - 0.5, at.z);
				double flat = rel.x * rel.x + rel.z * rel.z;
				if (flat / (r * r) + rel.y * rel.y / (r * r * 0.3) > 1) continue;
				BlockState state = level.getBlockState(pos);
				if (l.by == null || !breakable(level, l.by, pos, state)) continue;
				BlockPos hit = pos.immutable();
				level.setBlock(hit, Blocks.AIR.defaultBlockState(), 3);
				if (level.getRandom().nextFloat() < 0.35f) Anvils.fling(level, hit, state, at.subtract(0, 1, 0));
				else HeldConstructs.debris(level, hit, state);
			}
			// The shockwave shoves what stands round the crater away from it.
			double reach = r + 3;
			for (Entity o : level.getEntities(e, new AABB(at, at).inflate(reach), o -> o instanceof LivingEntity && o != l.by && o.isAlive())) {
				Vec3 away = o.position().subtract(at);
				double falloff = 1 - Math.min(1, away.length() / reach);
				Vec3 flat = new Vec3(away.x, 0, away.z);
				flat = flat.lengthSqr() < 1e-4 ? Vec3.ZERO : flat.normalize();
				o.setDeltaMovement(o.getDeltaMovement().add(flat.scale(speed * 0.8 * falloff)).add(0, 0.25 + 0.3 * falloff, 0));
				RingPowers.syncVelocity(o);
			}
		} finally {
			Corps.restore(before);
		}
	}

	private RamBarrier() {
	}
}
