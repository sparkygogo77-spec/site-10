package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.CombatFxPayload.Kind;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.FishingHook;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.entity.projectile.ShulkerBullet;
import net.minecraft.world.entity.projectile.arrow.AbstractArrow;
import net.minecraft.world.entity.projectile.arrow.ThrownTrident;
import net.minecraft.world.entity.projectile.hurtingprojectile.AbstractHurtingProjectile;
import net.minecraft.world.entity.projectile.hurtingprojectile.DragonFireball;
import net.minecraft.world.entity.projectile.hurtingprojectile.WitherSkull;
import net.minecraft.world.entity.projectile.hurtingprojectile.windcharge.AbstractWindCharge;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * J's absorb and return blast (Blender pass 503, R4; R4b picked). Hold left click with a charged ring: a shot coming
 * at you (arrows, tridents, fireballs, wither skulls, wind charges, shulker bullets, anything thrown) is sucked into
 * the ring and held there while you hold (each client draws it in its Ring Lab Absorb pick: R4b at the ring, turning
 * from the attacker's colour to green and growing to 1.8x as it charges over RingTuning absorb_charge; R4a in a
 * construct cage; R4c swallowed, the ring burning brighter). Let go: a green blast twice the size leaves the ring at
 * 1.5x the shot's speed (1.5 blocks a tick for a 1 block a tick shot), with 3 trailing bolts and a ring flare.
 * With nothing coming, left click does what it always did; only a held shot takes it over (CombatInput).
 */
public final class AbsorbBlasts {
	/** How far out (blocks) a shot is looked for, and how close to your middle it must be heading. */
	private static final double SCAN = 10, CATCH_RADIUS = 2.2;
	/** Ticks ahead a shot's path is checked, so fast arrows can't slip through between checks. */
	private static final int LOOKAHEAD = 8;
	/** The blast: speed as a multiple of the shot's, its limits, how far it goes, its reach round its middle and its damage. */
	private static final double SPEED_UP = 1.5, MIN_SPEED = 1.5, MAX_SPEED = 4.5, RANGE = 64, RADIUS = 0.7;
	private static final float DAMAGE = 8f, CHARGED_DAMAGE = 10f, SPLASH = 2.5f;

	private record Held(Corps corps, double speed, int colour, int caught) {
	}

	private static final class Blast {
		final ServerLevel level;
		final ServerPlayer owner;
		final Corps corps;
		final float charge;
		Vec3 pos;
		final Vec3 vel;
		double travelled;

		Blast(ServerLevel level, ServerPlayer owner, Corps corps, Vec3 pos, Vec3 vel, float charge) {
			this.level = level;
			this.owner = owner;
			this.corps = corps;
			this.pos = pos;
			this.vel = vel;
			this.charge = charge;
		}
	}

	private static final Set<UUID> HOLDING = new HashSet<>();
	private static final Map<UUID, Held> HELD = new HashMap<>();
	private static final List<Blast> BLASTS = new ArrayList<>();

	private AbsorbBlasts() {
	}

	static void register() {
		ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
			HOLDING.remove(handler.player.getUUID());
			HELD.remove(handler.player.getUUID());
		});
	}

	/** Left click pressed or let go with the ring (CombatPayload.ABSORB). */
	static void hold(ServerPlayer p, boolean down) {
		if (down) HOLDING.add(p.getUUID());
		else HOLDING.remove(p.getUUID());
	}

	/** Whether this player holds an absorbed shot at their ring. */
	public static boolean holds(Player p) {
		return HELD.containsKey(p.getUUID());
	}

	/** 0..1: how far a shot caught {@code ticks} ago has charged. */
	public static float charge(int ticks) {
		return Mth.clamp(ticks / (float) Math.max(1, RingTuning.ABSORB_CHARGE.ticks()), 0f, 1f);
	}

	/** The ring in a hand, charged, or null: you have to hold it to catch with it. */
	private static net.minecraft.world.item.@Nullable ItemStack ringInHand(ServerPlayer p) {
		for (var stack : new net.minecraft.world.item.ItemStack[] {p.getMainHandItem(), p.getOffhandItem()}) {
			if (stack.getItem() instanceof PowerRingItem && PowerRingItem.getCharge(stack) > 0) return stack;
		}
		return null;
	}

	static void tick(MinecraftServer server) {
		int now = CombatMoves.now();
		for (ServerPlayer p : server.getPlayerList().getPlayers()) {
			UUID id = p.getUUID();
			Held held = HELD.get(id);
			var ring = ringInHand(p);
			if (held != null && (ring == null || !p.isAlive())) {
				HELD.remove(id);
				end(p, held);
				continue;
			}
			if (held != null && !HOLDING.contains(id)) {
				HELD.remove(id);
				release(p, held, now);
				continue;
			}
			if (held == null && ring != null && HOLDING.contains(id) && !p.isSpectator()) scan(p, ring);
		}
		for (Iterator<Blast> it = BLASTS.iterator(); it.hasNext(); ) {
			if (!move(it.next())) it.remove();
		}
	}

	/** A shot heading for this player's middle within LOOKAHEAD ticks is caught. */
	private static void scan(ServerPlayer p, net.minecraft.world.item.ItemStack ring) {
		ServerLevel level = p.level();
		Vec3 mid = p.getBoundingBox().getCenter();
		Projectile best = null;
		double bestTime = LOOKAHEAD + 1;
		for (Projectile shot : level.getEntitiesOfClass(Projectile.class, new AABB(mid, mid).inflate(SCAN), s -> incoming(s, p))) {
			Vec3 pos = shot.getBoundingBox().getCenter();
			Vec3 v = shot.getDeltaMovement();
			double speed2 = v.lengthSqr();
			// When it's closest to your middle, and how close it gets.
			double t = Mth.clamp(mid.subtract(pos).dot(v) / speed2, 0, LOOKAHEAD);
			if (mid.subtract(pos).dot(v) <= 0) continue;
			double miss = pos.add(v.scale(t)).distanceTo(mid);
			if (miss <= CATCH_RADIUS && t < bestTime) {
				bestTime = t;
				best = shot;
			}
		}
		if (best == null) return;
		Corps corps = Corps.of(ring);
		Vec3 at = best.getBoundingBox().getCenter();
		double speed = best.getDeltaMovement().length();
		int colour = colour(best);
		best.discard();
		HELD.put(p.getUUID(), new Held(corps, speed, colour, CombatMoves.now()));
		Corps before = Corps.enter(corps);
		try {
			CombatMoves.send(level, Kind.ABSORB_CATCH, at, RingPowers.handPos(p), (float) speed, colour, p, -1);
		} finally {
			Corps.restore(before);
		}
		level.playSound(null, p.getX(), p.getY(), p.getZ(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 1f, 1.6f);
		level.playSound(null, p.getX(), p.getY(), p.getZ(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1f, 0.7f);
	}

	private static boolean incoming(Projectile shot, ServerPlayer p) {
		if (!shot.isAlive() || shot instanceof FishingHook || shot.getOwner() == p) return false;
		// Arrows stuck in the ground have stopped.
		return shot.getDeltaMovement().lengthSqr() > 0.01;
	}

	/** The shot's colour as it arrives: a ring-bearer's corps, or what the shot is. */
	private static int colour(Projectile shot) {
		Entity owner = shot.getOwner();
		if (owner instanceof LivingEntity living) {
			Corps corps = Corps.held(living);
			if ((living.getMainHandItem().getItem() instanceof PowerRingItem || living.getOffhandItem().getItem() instanceof PowerRingItem)) {
				return Math.round(corps.red() * 255) << 16 | Math.round(corps.green() * 255) << 8 | Math.round(corps.blue() * 255);
			}
		}
		if (shot instanceof DragonFireball) return 0xB43CFF;
		if (shot instanceof WitherSkull) return 0x3C3C46;
		if (shot instanceof AbstractWindCharge) return 0xD8E8FF;
		if (shot instanceof AbstractHurtingProjectile) return 0xFF7A1A;
		if (shot instanceof ThrownTrident) return 0x4FD0C8;
		if (shot instanceof ShulkerBullet) return 0xF0E6C0;
		if (shot instanceof AbstractArrow) return 0xD0CCC4;
		return 0xE8E8E8;
	}

	/** Let go: the green blast leaves the ring, 1.5x the shot's speed, twice its size. */
	private static void release(ServerPlayer p, Held held, int now) {
		ServerLevel level = p.level();
		float charge = charge(now - held.caught());
		double speed = Mth.clamp(held.speed() * SPEED_UP, MIN_SPEED, MAX_SPEED);
		Vec3 from = RingPowers.handPos(p);
		Vec3 vel = p.getLookAngle().scale(speed);
		BLASTS.add(new Blast(level, p, held.corps(), from, vel, charge));
		Corps before = Corps.enter(held.corps());
		try {
			CombatMoves.send(level, Kind.ABSORB_RELEASE, from, from.add(vel), (float) speed, Math.round(charge * 100), p, -1);
		} finally {
			Corps.restore(before);
		}
		level.playSound(null, p.getX(), p.getY(), p.getZ(), SoundEvents.WARDEN_SONIC_BOOM, SoundSource.PLAYERS, 0.6f, 1.5f);
		level.playSound(null, p.getX(), p.getY(), p.getZ(), SoundEvents.FIRECHARGE_USE, SoundSource.PLAYERS, 1f, 0.8f);
	}

	private static void end(ServerPlayer p, Held held) {
		Corps before = Corps.enter(held.corps());
		try {
			CombatMoves.send(p.level(), Kind.ABSORB_END, p.position(), p.position(), 0f, 0, p, -1);
		} finally {
			Corps.restore(before);
		}
	}

	/** One tick of a blast; false once it has hit something or gone its range. */
	private static boolean move(Blast b) {
		if (b.owner.isRemoved() && b.travelled > 0) return false;
		Vec3 to = b.pos.add(b.vel);
		BlockHitResult block = b.level.clip(new ClipContext(b.pos, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, b.owner));
		double reach = block.getType() == HitResult.Type.MISS ? b.vel.length() : block.getLocation().distanceTo(b.pos);
		Vec3 hitAt = null;
		for (LivingEntity e : b.level.getEntitiesOfClass(LivingEntity.class, new AABB(b.pos, to).inflate(RADIUS + 0.5),
				e -> e != b.owner && e.isAlive() && !e.isSpectator() && !CombatMoves.spared(e, b.owner))) {
			Optional<Vec3> at = e.getBoundingBox().inflate(RADIUS).clip(b.pos, to);
			if (at.isPresent() && at.get().distanceTo(b.pos) < reach) {
				reach = at.get().distanceTo(b.pos);
				hitAt = at.get();
			}
		}
		if (hitAt == null && block.getType() != HitResult.Type.MISS) hitAt = block.getLocation();
		if (hitAt != null) {
			hit(b, hitAt);
			return false;
		}
		b.pos = to;
		b.travelled += b.vel.length();
		return b.travelled < RANGE;
	}

	/** The blast goes off at "at": everything round it is hurt and thrown back; no blocks break. */
	private static void hit(Blast b, Vec3 at) {
		float damage = Mth.lerp(b.charge, DAMAGE, DAMAGE + CHARGED_DAMAGE);
		Vec3 dir = b.vel.normalize();
		for (LivingEntity e : b.level.getEntitiesOfClass(LivingEntity.class, new AABB(at, at).inflate(SPLASH),
				e -> e != b.owner && e.isAlive() && !e.isSpectator() && !CombatMoves.spared(e, b.owner))) {
			double d = e.getBoundingBox().getCenter().distanceTo(at);
			if (d > SPLASH + e.getBbWidth()) continue;
			e.hurtServer(b.level, b.level.damageSources().indirectMagic(b.owner, b.owner), (float) (damage * Mth.clamp(1.2 - d / SPLASH, 0.3, 1)));
			Vec3 push = dir.scale(0.9 + 0.6 * b.charge);
			e.setDeltaMovement(e.getDeltaMovement().add(push.x, 0.35, push.z));
			RingPowers.syncVelocity(e);
		}
		Corps before = Corps.enter(b.corps);
		try {
			CombatMoves.send(b.level, Kind.ABSORB_HIT, at, at.subtract(dir), 0f, Math.round(b.charge * 100), b.owner, -1);
			b.level.sendParticles(ModParticles.of(ModParticles.SHARD, b.corps), at.x, at.y, at.z, 16, 0.4, 0.4, 0.4, 0.3);
		} finally {
			Corps.restore(before);
		}
		b.level.playSound(null, at.x, at.y, at.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 0.8f, 1.3f);
	}
}
