package com.sparky.lanternring.hero;

import com.mojang.math.Transformation;
import com.sparky.lanternring.RingPowers;
import com.sparky.lanternring.ally.ConstructAlly;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Brightness;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * The thrown Shield and the shield slam. A thrown shield is an item display the server flies
 * itself: it heads for the mob you aimed at (or straight ahead), hits it, then ricochets to the
 * nearest hostile mob it hasn't hit yet, up to five hits, and flies back to your hand. A wall in
 * its way bounces it on to the next mob too. While it's out your hand is empty; if you log out or
 * die it drops where it is.
 */
public final class ShieldThrows {
	/** Blocks per tick out and back. */
	private static final double SPEED = 1.6;
	private static final double RETURN_SPEED = 1.9;
	private static final double AIM_RANGE = 32;
	/** How far a ricochet looks for its next mob. */
	private static final double BOUNCE_RANGE = 14;
	private static final int MAX_HITS = 5;
	private static final float HIT_DAMAGE = 9f;
	/** It turns for home after this long however many mobs are left. */
	private static final int MAX_OUT_TICKS = 80;
	private static final float SLAM_RADIUS = 5f;
	private static final float SLAM_DAMAGE = 8f;

	private static final List<Flight> FLIGHTS = new ArrayList<>();
	/** Players diving down in a slam; it lands on the first tick they touch the ground. */
	private static final Set<UUID> SLAMMING = new HashSet<>();

	private static final class Flight {
		final ServerLevel level;
		final UUID owner;
		final ItemStack stack;
		final Display.ItemDisplay body;
		final Set<UUID> hit = new HashSet<>();
		Vec3 pos;
		LivingEntity target;
		Vec3 aim;
		boolean returning;
		int age;
		float spin;

		Flight(ServerLevel level, ServerPlayer owner, ItemStack stack, Display.ItemDisplay body, Vec3 pos) {
			this.level = level;
			this.owner = owner.getUUID();
			this.stack = stack;
			this.body = body;
			this.pos = pos;
		}
	}

	private ShieldThrows() {
	}

	public static void register() {
		ServerTickEvents.END_SERVER_TICK.register(ShieldThrows::tick);
		// Nothing is saved: hand every shield still in the air back before the server stops.
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
			for (Flight f : FLIGHTS) giveBack(f, server.getPlayerList().getPlayer(f.owner));
			FLIGHTS.clear();
			SLAMMING.clear();
		});
	}

	// ---- throwing -------------------------------------------------------------------------

	static void toss(ServerLevel level, ServerPlayer player, InteractionHand hand) {
		ItemStack stack = player.getItemInHand(hand);
		if (stack.isEmpty()) return;
		Vec3 start = player.getEyePosition().add(player.getLookAngle().scale(0.8)).subtract(0, 0.3, 0);
		Display.ItemDisplay body = EntityTypes.ITEM_DISPLAY.create(level, EntitySpawnReason.TRIGGERED);
		if (body == null) return;
		ItemStack carried = stack.copy();
		player.setItemInHand(hand, ItemStack.EMPTY);
		body.setItemStack(carried.copy());
		body.setItemTransform(ItemDisplayContext.FIXED);
		body.setPosRotInterpolationDuration(1);
		body.setBrightnessOverride(new Brightness(15, 15));
		body.setPos(start.x, start.y, start.z);
		level.addFreshEntity(body);

		Flight f = new Flight(level, player, carried, body, start);
		f.target = aimedAt(level, player);
		f.aim = f.target != null ? null : player.getEyePosition().add(player.getLookAngle().scale(AIM_RANGE));
		FLIGHTS.add(f);
		turn(f);
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.TRIDENT_THROW.value(), SoundSource.PLAYERS, 1f, 0.8f);
	}

	/** The living thing nearest the player's crosshair within AIM_RANGE, with a generous cone. */
	private static LivingEntity aimedAt(ServerLevel level, ServerPlayer player) {
		Vec3 eye = player.getEyePosition();
		Vec3 look = player.getLookAngle();
		BlockHitResult wall = level.clip(new ClipContext(eye, eye.add(look.scale(AIM_RANGE)), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
		double reach = wall.getType() == HitResult.Type.MISS ? AIM_RANGE : wall.getLocation().distanceTo(eye) + 1;
		AABB box = player.getBoundingBox().expandTowards(look.scale(reach)).inflate(3);
		LivingEntity best = null;
		double bestScore = Double.MAX_VALUE;
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box, e -> e != player && e.isAlive() && !e.isSpectator())) {
			Vec3 to = e.getBoundingBox().getCenter().subtract(eye);
			double along = to.dot(look);
			if (along <= 0 || along > reach) continue;
			double off = to.subtract(look.scale(along)).length();
			// Within about 12 degrees of the crosshair, or a couple of blocks for close mobs.
			if (off > Math.max(2.0, along * 0.2)) continue;
			double score = off * 4 + along;
			if (score < bestScore) {
				bestScore = score;
				best = e;
			}
		}
		return best;
	}

	// ---- flying ---------------------------------------------------------------------------

	private static void tick(MinecraftServer server) {
		Iterator<Flight> it = FLIGHTS.iterator();
		while (it.hasNext()) {
			Flight f = it.next();
			ServerPlayer owner = server.getPlayerList().getPlayer(f.owner);
			if (owner == null || !owner.isAlive() || owner.level() != f.level || f.body.isRemoved()) {
				drop(f);
				it.remove();
				continue;
			}
			if (fly(f, owner)) {
				catchShield(f, owner);
				it.remove();
			}
		}
		Iterator<UUID> slams = SLAMMING.iterator();
		while (slams.hasNext()) {
			ServerPlayer p = server.getPlayerList().getPlayer(slams.next());
			if (p == null || !p.isAlive()) {
				slams.remove();
				continue;
			}
			p.fallDistance = 0;
			if (!airborne(p) || p.isInWater()) {
				slams.remove();
				slamDown((ServerLevel) p.level(), p);
			}
		}
	}

	/** Moves the shield one tick; true once it is back in the owner's reach. */
	private static boolean fly(Flight f, ServerPlayer owner) {
		f.age++;
		f.spin += 0.9f;
		if (!f.returning && f.age > MAX_OUT_TICKS) f.returning = true;
		if (f.returning) {
			Vec3 home = owner.getEyePosition().subtract(0, 0.4, 0);
			Vec3 d = home.subtract(f.pos);
			double dist = d.length();
			if (dist < RETURN_SPEED + 0.6) return true;
			// Home through anything: it must never get stuck behind a wall.
			move(f, f.pos.add(d.scale(RETURN_SPEED / dist)));
			return false;
		}

		if (f.target != null && (!f.target.isAlive() || f.target.isRemoved())) nextTarget(f, owner);
		if (f.returning) return false;
		Vec3 dest = f.target != null ? f.target.getBoundingBox().getCenter() : f.aim;
		Vec3 d = dest.subtract(f.pos);
		double dist = d.length();
		Vec3 next = dist <= SPEED ? dest : f.pos.add(d.scale(SPEED / dist));

		BlockHitResult wall = f.level.clip(new ClipContext(f.pos, next, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, owner));
		if (wall.getType() != HitResult.Type.MISS) {
			Vec3 at = wall.getLocation().add(Vec3.atLowerCornerOf(wall.getDirection().getUnitVec3i()).scale(0.3));
			move(f, at);
			clang(f, at, f.level.getBlockState(wall.getBlockPos()));
			nextTarget(f, owner);
			return false;
		}
		move(f, next);

		// Anything it passes through on the way gets hit too (once per throw).
		AABB sweep = new AABB(f.pos, f.pos).inflate(0.7);
		for (LivingEntity e : f.level.getEntitiesOfClass(LivingEntity.class, sweep, e -> e != owner && e.isAlive() && !e.isSpectator()
				&& !f.hit.contains(e.getUUID()) && !(e instanceof ConstructAlly))) {
			strike(f, owner, e);
		}
		if (f.target != null && f.hit.contains(f.target.getUUID())) {
			nextTarget(f, owner);
		} else if (f.target == null && dist <= SPEED) {
			// Reached the spot it was thrown at without meeting anything.
			nextTarget(f, owner);
		}
		return false;
	}

	private static void strike(Flight f, ServerPlayer owner, LivingEntity e) {
		f.hit.add(e.getUUID());
		e.hurtServer(f.level, f.level.damageSources().playerAttack(owner), HIT_DAMAGE);
		Vec3 push = e.position().subtract(f.pos).multiply(1, 0, 1);
		if (push.lengthSqr() > 1e-4) push = push.normalize();
		e.push(push.x * 0.8, 0.3, push.z * 0.8);
		RingPowers.syncVelocity(e);
		f.level.playSound(null, e.getX(), e.getY(), e.getZ(), SoundEvents.SHIELD_BLOCK.value(), SoundSource.PLAYERS, 1.2f, 1.5f);
		f.level.playSound(null, e.getX(), e.getY(), e.getZ(), SoundEvents.ANVIL_LAND, SoundSource.PLAYERS, 0.25f, 2f);
		f.level.sendParticles(ParticleTypes.CRIT, f.pos.x, f.pos.y, f.pos.z, 12, 0.2, 0.2, 0.2, 0.4);
	}

	private static void clang(Flight f, Vec3 at, BlockState block) {
		f.level.playSound(null, at.x, at.y, at.z, SoundEvents.ANVIL_LAND, SoundSource.PLAYERS, 0.35f, 1.9f);
		f.level.sendParticles(ParticleTypes.CRIT, at.x, at.y, at.z, 8, 0.1, 0.1, 0.1, 0.3);
		if (!block.isAir()) {
			f.level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, block), at.x, at.y, at.z, 10, 0.15, 0.15, 0.15, 0.1);
		}
	}

	/** Picks the next hostile mob to ricochet to, or turns for home. */
	private static void nextTarget(Flight f, ServerPlayer owner) {
		f.aim = null;
		f.target = null;
		if (f.hit.size() >= MAX_HITS) {
			f.returning = true;
			return;
		}
		LivingEntity best = null;
		double bestDist = BOUNCE_RANGE * BOUNCE_RANGE;
		for (LivingEntity e : f.level.getEntitiesOfClass(LivingEntity.class, new AABB(f.pos, f.pos).inflate(BOUNCE_RANGE),
				e -> e != owner && ConstructAlly.isBadMob(e) && !f.hit.contains(e.getUUID()))) {
			double d = e.getBoundingBox().getCenter().distanceToSqr(f.pos);
			if (d >= bestDist) continue;
			// Only mobs it can actually see from where it is.
			BlockHitResult wall = f.level.clip(new ClipContext(f.pos, e.getBoundingBox().getCenter(), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, owner));
			if (wall.getType() != HitResult.Type.MISS) continue;
			bestDist = d;
			best = e;
		}
		if (best == null) f.returning = true;
		else f.target = best;
	}

	private static void move(Flight f, Vec3 to) {
		f.pos = to;
		f.body.setPos(to.x, to.y, to.z);
		turn(f);
		f.level.sendParticles(ParticleTypes.ELECTRIC_SPARK, to.x, to.y, to.z, 1, 0.05, 0.05, 0.05, 0);
	}

	/** Spins it flat like a frisbee, star side up. */
	private static void turn(Flight f) {
		Quaternionf rot = new Quaternionf().rotationY(f.spin).rotateX((float) (Math.PI / 2));
		f.body.setTransformation(new Transformation(new Vector3f(), rot, new Vector3f(1.1f, 1.1f, 1.1f), null));
		f.body.setTransformationInterpolationDelay(0);
		f.body.setTransformationInterpolationDuration(1);
	}

	private static void catchShield(Flight f, ServerPlayer owner) {
		f.body.discard();
		giveBack(f, owner);
		f.level.playSound(null, owner.getX(), owner.getY(), owner.getZ(), SoundEvents.ARMOR_EQUIP_IRON.value(), SoundSource.PLAYERS, 1f, 1.2f);
	}

	/** Back into the main hand if it's free, else the off hand, else the inventory, else dropped. */
	private static void giveBack(Flight f, ServerPlayer owner) {
		f.body.discard();
		if (owner == null) {
			drop(f);
			return;
		}
		ItemStack stack = f.stack.copy();
		if (owner.getMainHandItem().isEmpty()) owner.setItemInHand(InteractionHand.MAIN_HAND, stack);
		else if (owner.getOffhandItem().isEmpty()) owner.setItemInHand(InteractionHand.OFF_HAND, stack);
		else if (!owner.getInventory().add(stack)) {
			ItemEntity item = new ItemEntity(owner.level(), owner.getX(), owner.getY() + 0.5, owner.getZ(), stack);
			item.setNoPickUpDelay();
			owner.level().addFreshEntity(item);
		}
	}

	private static void drop(Flight f) {
		f.body.discard();
		ItemEntity item = new ItemEntity(f.level, f.pos.x, f.pos.y, f.pos.z, f.stack.copy());
		item.setUnlimitedLifetime();
		f.level.addFreshEntity(item);
	}

	// ---- slam -----------------------------------------------------------------------------

	static void slam(ServerLevel level, ServerPlayer player, InteractionHand hand) {
		if (player.getCooldowns().isOnCooldown(player.getItemInHand(hand))) return;
		player.getCooldowns().addCooldown(player.getItemInHand(hand), 20);
		if (!airborne(player)) {
			slamDown(level, player);
			return;
		}
		// Dive: straight down hard, landing in the shockwave (and no fall damage).
		player.setDeltaMovement(player.getDeltaMovement().multiply(0.3, 0, 0.3).add(0, -2.2, 0));
		RingPowers.syncVelocity(player);
		SLAMMING.add(player.getUUID());
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.TRIDENT_RIPTIDE_1.value(), SoundSource.PLAYERS, 1f, 0.8f);
	}

	/**
	 * Nothing to stand on just under the player's feet. (onGround lags a tick behind on the
	 * server, for example right after a teleport.)
	 */
	static boolean airborne(ServerPlayer player) {
		return player.level().noCollision(player, player.getBoundingBox().move(0, -0.2, 0));
	}

	private static void slamDown(ServerLevel level, ServerPlayer player) {
		Vec3 c = player.position();
		AABB area = new AABB(c, c).inflate(SLAM_RADIUS, 2, SLAM_RADIUS);
		for (Entity e : level.getEntities(player, area, e -> e instanceof LivingEntity l && l.isAlive() && !(e instanceof ConstructAlly))) {
			Vec3 away = e.position().subtract(c).multiply(1, 0, 1);
			double dist = away.length();
			if (dist > SLAM_RADIUS) continue;
			float scale = (float) (1 - dist / (SLAM_RADIUS + 1));
			((LivingEntity) e).hurtServer(level, level.damageSources().playerAttack(player), SLAM_DAMAGE * scale + 2);
			Vec3 dir = dist > 1e-3 ? away.scale(1 / dist) : new Vec3(0, 0, 0);
			e.push(dir.x * 1.4 * scale, 0.5 + 0.4 * scale, dir.z * 1.4 * scale);
			RingPowers.syncVelocity(e);
		}
		BlockState ground = level.getBlockState(player.blockPosition().below());
		if (!ground.isAir()) {
			level.sendParticles(new BlockParticleOption(ParticleTypes.BLOCK, ground), c.x, c.y + 0.1, c.z, 80, SLAM_RADIUS / 2, 0.1, SLAM_RADIUS / 2, 0.2);
		}
		for (int i = 0; i < 32; i++) {
			double a = i * Math.PI * 2 / 32;
			level.sendParticles(ParticleTypes.SWEEP_ATTACK, c.x + Math.cos(a) * 3, c.y + 0.3, c.z + Math.sin(a) * 3, 1, 0, 0, 0, 0);
		}
		level.sendParticles(ParticleTypes.EXPLOSION, c.x, c.y + 0.3, c.z, 1, 0, 0, 0, 0);
		level.playSound(null, c.x, c.y, c.z, SoundEvents.ANVIL_LAND, SoundSource.PLAYERS, 0.8f, 0.6f);
		level.playSound(null, c.x, c.y, c.z, SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 0.6f, 1.3f);
	}
}
