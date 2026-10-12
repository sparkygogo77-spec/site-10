package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.network.protocol.game.ClientboundSetEntityMotionPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;

/** What each ring mode does. Everything here runs on the server. */
public final class RingPowers {
	private static final DustParticleOptions GREEN_DUST = PowerRingItem.GREEN_LIGHT;
	private static final DustParticleOptions GREEN_DUST_BIG = new DustParticleOptions(0x4DFF66, 2.0f);

	private static final double BLAST_LENGTH = 50;
	private static final float BLAST_DAMAGE = 10.0f;
	private static final double BEAM_RANGE = 48;
	private static final float BEAM_DAMAGE = 8.0f;
	private static final double TETHER_RANGE = 32;
	private static final double PUSH_RADIUS = 7;

	private RingPowers() {
	}

	public static boolean activate(RingMode mode, ServerLevel level, Player player) {
		return switch (mode) {
			case BLAST -> blast(level, player);
			case BEAM -> beam(level, player);
			case WALL -> wall(level, player);
			case BRIDGE -> bridge(level, player);
			case PUSH -> push(level, player);
			case TETHER -> tether(level, player);
		};
	}

	/**
	 * Bores a 3x3 tunnel BLAST_LENGTH blocks long, starting just in front of the player and following
	 * their aim in every direction. Blocks are destroyed without drops; unbreakable blocks and blocks
	 * with contents (chests, furnaces, spawners...) are left alone.
	 */
	private static boolean blast(ServerLevel level, Player player) {
		Vec3 look = player.getLookAngle();
		Vec3 right = look.cross(new Vec3(0, 1, 0));
		if (right.lengthSqr() < 1.0e-4) {
			// Looking straight up or down: use the way the player's body faces.
			Direction side = player.getDirection().getClockWise();
			right = new Vec3(side.getStepX(), 0, side.getStepZ());
		}
		right = right.normalize();
		Vec3 up = right.cross(look).normalize();

		// Centre the tunnel slightly below the eyes so the player's whole body fits through it.
		Vec3 origin = player.getEyePosition().subtract(0, 0.6, 0);
		Set<BlockPos> tunnel = new LinkedHashSet<>();
		for (double t = 1.0; t <= BLAST_LENGTH; t += 0.4) {
			Vec3 center = origin.add(look.scale(t));
			for (int a = -1; a <= 1; a++) {
				for (int b = -1; b <= 1; b++) {
					tunnel.add(BlockPos.containing(center.add(right.scale(a)).add(up.scale(b))));
				}
			}
		}

		int cleared = 0;
		for (BlockPos pos : tunnel) {
			BlockState state = level.getBlockState(pos);
			if (state.isAir() || state.getDestroySpeed(level, pos) < 0 || state.hasBlockEntity()
					|| !level.mayInteract(player, pos)) {
				continue;
			}
			level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
			if (cleared++ % 6 == 0) {
				level.sendParticles(GREEN_DUST_BIG, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5,
						2, 0.3, 0.3, 0.3, 0.0);
			}
		}

		AABB path = new AABB(origin, origin.add(look.scale(BLAST_LENGTH))).inflate(1.5);
		for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, path,
				e -> e != player && e.isAlive() && !e.isSpectator()
						&& distanceToRay(e.getBoundingBox().getCenter(), origin, look) < 2.0)) {
			target.hurtServer(level, level.damageSources().indirectMagic(player, player), BLAST_DAMAGE);
		}

		drawLine(level, handPos(player), origin.add(look.scale(BLAST_LENGTH)));
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.WARDEN_SONIC_BOOM,
				SoundSource.PLAYERS, 1.2f, 1.3f);
		return true;
	}

	private static boolean beam(ServerLevel level, Player player) {
		Vec3 look = player.getLookAngle();
		Target target = trace(level, player, BEAM_RANGE);
		if (target.entity != null) {
			target.entity.hurtServer(level, level.damageSources().indirectMagic(player, player), BEAM_DAMAGE);
			target.entity.push(look.x * 0.6, 0.15, look.z * 0.6);
			syncVelocity(target.entity);
		}
		drawLine(level, handPos(player), target.pos);
		level.sendParticles(GREEN_DUST_BIG, target.pos.x, target.pos.y, target.pos.z, 12, 0.25, 0.25, 0.25, 0.0);
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.BEACON_ACTIVATE,
				SoundSource.PLAYERS, 0.7f, 2.0f);
		return true;
	}

	/** A 5x3 wall of hard light two blocks in front of the player, standing on the ground. */
	private static boolean wall(ServerLevel level, Player player) {
		Direction facing = player.getDirection();
		Direction across = facing.getClockWise();
		BlockPos center = player.blockPosition().relative(facing, 2);
		int placed = 0;
		for (int w = -2; w <= 2; w++) {
			for (int h = 0; h < 3; h++) {
				if (placeConstruct(level, player, center.relative(across, w).above(h))) {
					placed++;
				}
			}
		}
		return finishConstruct(level, player, center.above(), placed);
	}

	/** A 3-wide, 12-long bridge at foot level, heading where the player faces. */
	private static boolean bridge(ServerLevel level, Player player) {
		Direction forward = player.getDirection();
		Direction right = forward.getClockWise();
		BlockPos start = player.blockPosition().below();
		int placed = 0;
		for (int along = 0; along <= 12; along++) {
			for (int across = -1; across <= 1; across++) {
				if (placeConstruct(level, player, start.relative(forward, along).relative(right, across))) {
					placed++;
				}
			}
		}
		return finishConstruct(level, player, start.relative(forward, 6), placed);
	}

	/** Shoves every living thing nearby away from the player. */
	private static boolean push(ServerLevel level, Player player) {
		AABB area = player.getBoundingBox().inflate(PUSH_RADIUS);
		List<LivingEntity> targets = level.getEntitiesOfClass(LivingEntity.class, area,
				e -> e != player && e.isAlive() && !e.isSpectator()
						&& e.distanceToSqr(player) <= PUSH_RADIUS * PUSH_RADIUS);
		for (LivingEntity target : targets) {
			Vec3 away = target.position().subtract(player.position()).multiply(1, 0, 1);
			away = away.lengthSqr() < 1.0e-4 ? player.getLookAngle() : away.normalize();
			target.hurtServer(level, level.damageSources().indirectMagic(player, player), 3.0f);
			target.setDeltaMovement(away.x * 1.8, 0.6, away.z * 1.8);
			syncVelocity(target);
		}
		for (int i = 0; i < 48; i++) {
			double angle = i * Math.PI * 2 / 48;
			level.sendParticles(GREEN_DUST_BIG, player.getX() + Math.cos(angle) * 2.5, player.getY() + 0.8,
					player.getZ() + Math.sin(angle) * 2.5, 1, 0, 0, 0, 0);
		}
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.BEACON_DEACTIVATE,
				SoundSource.PLAYERS, 1.0f, 1.5f);
		return true;
	}

	/** Pulls a mob to the player, or, aimed at a block, pulls the player to the block. */
	private static boolean tether(ServerLevel level, Player player) {
		Target target = trace(level, player, TETHER_RANGE);
		if (target.entity != null) {
			Vec3 pull = player.position().subtract(target.entity.position()).normalize();
			target.entity.setDeltaMovement(pull.x * 1.6, pull.y * 1.6 + 0.35, pull.z * 1.6);
			syncVelocity(target.entity);
		} else if (target.hitBlock) {
			Vec3 pull = target.pos.subtract(player.position()).normalize();
			player.setDeltaMovement(pull.x * 2.2, pull.y * 2.2 + 0.4, pull.z * 2.2);
			player.resetFallDistance();
			syncVelocity(player);
		} else {
			return false;
		}
		drawLine(level, handPos(player), target.pos);
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.FISHING_BOBBER_RETRIEVE,
				SoundSource.PLAYERS, 1.0f, 0.6f);
		return true;
	}

	/** Places one hard-light block; LightConstructBlock removes it again after its lifetime. */
	private static boolean placeConstruct(ServerLevel level, Player player, BlockPos pos) {
		BlockState state = ModRegistry.LIGHT_CONSTRUCT.defaultBlockState();
		if (!level.getBlockState(pos).canBeReplaced() || !level.mayInteract(player, pos)
				|| !level.isUnobstructed(state, pos, CollisionContext.empty())) {
			return false;
		}
		level.setBlockAndUpdate(pos, state);
		level.sendParticles(GREEN_DUST, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, 3, 0.3, 0.3, 0.3, 0.0);
		return true;
	}

	private static boolean finishConstruct(ServerLevel level, Player player, BlockPos at, int placed) {
		if (placed == 0) {
			return false;
		}
		drawLine(level, handPos(player), Vec3.atCenterOf(at));
		level.playSound(null, at, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.0f, 1.4f);
		return true;
	}

	private record Target(Vec3 pos, Entity entity, boolean hitBlock) {
	}

	/** First entity or block along the player's line of sight. */
	private static Target trace(ServerLevel level, Player player, double range) {
		Vec3 eye = player.getEyePosition();
		Vec3 look = player.getLookAngle();
		Vec3 end = eye.add(look.scale(range));
		BlockHitResult blockHit = level.clip(new ClipContext(eye, end, ClipContext.Block.COLLIDER,
				ClipContext.Fluid.NONE, player));
		boolean hitBlock = blockHit.getType() != HitResult.Type.MISS;
		Vec3 stop = hitBlock ? blockHit.getLocation() : end;
		AABB sweep = player.getBoundingBox().expandTowards(look.scale(range)).inflate(1.0);
		EntityHitResult entityHit = ProjectileUtil.getEntityHitResult(player, eye, stop, sweep,
				e -> !e.isSpectator() && e.isPickable() && e != player, eye.distanceToSqr(stop));
		if (entityHit != null) {
			return new Target(entityHit.getLocation(), entityHit.getEntity(), false);
		}
		return new Target(stop, null, hitBlock);
	}

	private static double distanceToRay(Vec3 point, Vec3 origin, Vec3 dir) {
		Vec3 rel = point.subtract(origin);
		double along = rel.dot(dir);
		if (along < 0) {
			return rel.length();
		}
		return rel.subtract(dir.scale(along)).length();
	}

	private static Vec3 handPos(Player player) {
		return player.getEyePosition().add(player.getLookAngle().scale(0.7)).subtract(0, 0.25, 0);
	}

	private static void drawLine(ServerLevel level, Vec3 from, Vec3 to) {
		Vec3 step = to.subtract(from);
		int points = Math.max(2, (int) (step.length() * 3));
		for (int i = 0; i <= points; i++) {
			Vec3 p = from.add(step.scale((double) i / points));
			level.sendParticles(GREEN_DUST, p.x, p.y, p.z, 1, 0.02, 0.02, 0.02, 0.0);
		}
	}

	/** Mobs need their new motion broadcast; players only see it if it's sent to them directly. */
	private static void syncVelocity(Entity entity) {
		entity.needsSync = true;
		if (entity instanceof ServerPlayer serverPlayer) {
			serverPlayer.connection.send(new ClientboundSetEntityMotionPacket(serverPlayer));
		}
	}
}
