package com.sparky.lanternring;

import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

import org.joml.Vector3f;

import com.sparky.lanternring.item.PowerRingItem;
import net.minecraft.block.BlockState;
import net.minecraft.block.Blocks;
import net.minecraft.block.ShapeContext;
import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.projectile.ProjectileUtil;
import net.minecraft.network.packet.s2c.play.EntityVelocityUpdateS2CPacket;
import net.minecraft.particle.DustParticleEffect;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.hit.EntityHitResult;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.MathHelper;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.RaycastContext;

/** What each ring mode does. Everything here runs on the server. */
public final class RingPowers {
	private static final DustParticleEffect GREEN_DUST = PowerRingItem.GREEN_LIGHT;
	private static final DustParticleEffect GREEN_DUST_BIG = new DustParticleEffect(new Vector3f(0.3f, 1.0f, 0.4f), 2.0f);

	private static final double BLAST_LENGTH = 50;
	private static final float BLAST_DAMAGE = 10.0f;
	private static final double BEAM_RANGE = 48;
	private static final float BEAM_DAMAGE = 8.0f;
	private static final double TETHER_RANGE = 32;
	private static final double PUSH_RADIUS = 7;

	private RingPowers() {
	}

	public static boolean activate(RingMode mode, ServerWorld world, PlayerEntity player) {
		return switch (mode) {
			case BLAST -> blast(world, player);
			case BEAM -> beam(world, player);
			case WALL -> wall(world, player);
			case BRIDGE -> bridge(world, player);
			case PUSH -> push(world, player);
			case TETHER -> tether(world, player);
		};
	}

	/**
	 * Bores a 3x3 tunnel BLAST_LENGTH blocks long, starting just in front of the player and following
	 * their aim in every direction. Blocks are destroyed without drops; unbreakable blocks and blocks
	 * with contents (chests, furnaces, spawners...) are left alone.
	 */
	private static boolean blast(ServerWorld world, PlayerEntity player) {
		Vec3d eye = player.getEyePos();
		Vec3d look = player.getRotationVector();
		Vec3d right = look.crossProduct(new Vec3d(0, 1, 0));
		if (right.lengthSquared() < 1.0e-4) {
			// Looking straight up or down: use the way the player's body faces.
			right = Vec3d.of(player.getHorizontalFacing().rotateYClockwise().getVector());
		}
		right = right.normalize();
		Vec3d up = right.crossProduct(look).normalize();

		// Centre the tunnel slightly below the eyes so the player's whole body fits through it.
		Vec3d origin = eye.subtract(0, 0.6, 0);
		Set<BlockPos> tunnel = new LinkedHashSet<>();
		for (double t = 1.0; t <= BLAST_LENGTH; t += 0.4) {
			Vec3d center = origin.add(look.multiply(t));
			for (int a = -1; a <= 1; a++) {
				for (int b = -1; b <= 1; b++) {
					tunnel.add(BlockPos.ofFloored(center.add(right.multiply(a)).add(up.multiply(b))));
				}
			}
		}

		int cleared = 0;
		for (BlockPos pos : tunnel) {
			BlockState state = world.getBlockState(pos);
			if (state.isAir() || state.getHardness(world, pos) < 0 || state.hasBlockEntity()
					|| !world.canPlayerModifyAt(player, pos)) {
				continue;
			}
			world.setBlockState(pos, Blocks.AIR.getDefaultState(), 3);
			if (cleared++ % 6 == 0) {
				world.spawnParticles(GREEN_DUST_BIG, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5,
						2, 0.3, 0.3, 0.3, 0.0);
			}
		}

		Box path = new Box(origin, origin.add(look.multiply(BLAST_LENGTH))).expand(1.5);
		for (LivingEntity target : world.getEntitiesByClass(LivingEntity.class, path,
				e -> e != player && e.isAlive() && !e.isSpectator()
						&& distanceToRay(e.getBoundingBox().getCenter(), origin, look) < 2.0)) {
			target.damage(world.getDamageSources().indirectMagic(player, player), BLAST_DAMAGE);
		}

		drawLine(world, handPos(player), origin.add(look.multiply(BLAST_LENGTH)));
		world.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.ENTITY_WARDEN_SONIC_BOOM,
				SoundCategory.PLAYERS, 1.2f, 1.3f);
		return true;
	}

	private static boolean beam(ServerWorld world, PlayerEntity player) {
		Vec3d look = player.getRotationVector();
		Target target = trace(world, player, BEAM_RANGE);
		if (target.entity != null) {
			target.entity.damage(world.getDamageSources().indirectMagic(player, player), BEAM_DAMAGE);
			if (target.entity instanceof LivingEntity living) {
				living.takeKnockback(0.6, -look.x, -look.z);
			}
		}
		drawLine(world, handPos(player), target.pos);
		world.spawnParticles(GREEN_DUST_BIG, target.pos.x, target.pos.y, target.pos.z, 12, 0.25, 0.25, 0.25, 0.0);
		world.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.BLOCK_BEACON_ACTIVATE,
				SoundCategory.PLAYERS, 0.7f, 2.0f);
		return true;
	}

	/** A 5x3 wall of hard light two blocks in front of the player, standing on the ground. */
	private static boolean wall(ServerWorld world, PlayerEntity player) {
		Direction facing = player.getHorizontalFacing();
		Direction across = facing.rotateYClockwise();
		BlockPos center = player.getBlockPos().offset(facing, 2);
		int placed = 0;
		for (int w = -2; w <= 2; w++) {
			for (int h = 0; h < 3; h++) {
				if (placeConstruct(world, player, center.offset(across, w).up(h))) {
					placed++;
				}
			}
		}
		return finishConstruct(world, player, center.up(), placed);
	}

	/** A 3-wide, 12-long bridge at foot level, heading where the player faces. */
	private static boolean bridge(ServerWorld world, PlayerEntity player) {
		Direction forward = player.getHorizontalFacing();
		Direction right = forward.rotateYClockwise();
		BlockPos start = player.getBlockPos().down();
		int placed = 0;
		for (int along = 0; along <= 12; along++) {
			for (int across = -1; across <= 1; across++) {
				if (placeConstruct(world, player, start.offset(forward, along).offset(right, across))) {
					placed++;
				}
			}
		}
		return finishConstruct(world, player, start.offset(forward, 6), placed);
	}

	/** Shoves every living thing nearby away from the player. */
	private static boolean push(ServerWorld world, PlayerEntity player) {
		Box area = player.getBoundingBox().expand(PUSH_RADIUS);
		List<LivingEntity> targets = world.getEntitiesByClass(LivingEntity.class, area,
				e -> e != player && e.isAlive() && !e.isSpectator()
						&& e.squaredDistanceTo(player) <= PUSH_RADIUS * PUSH_RADIUS);
		for (LivingEntity target : targets) {
			Vec3d away = target.getPos().subtract(player.getPos()).multiply(1, 0, 1);
			away = away.lengthSquared() < 1.0e-4 ? player.getRotationVector() : away.normalize();
			target.damage(world.getDamageSources().indirectMagic(player, player), 3.0f);
			target.setVelocity(away.x * 1.8, 0.6, away.z * 1.8);
			target.velocityModified = true;
			syncVelocity(target);
		}
		for (int i = 0; i < 48; i++) {
			double angle = i * MathHelper.TAU / 48;
			world.spawnParticles(GREEN_DUST_BIG, player.getX() + Math.cos(angle) * 2.5, player.getY() + 0.8,
					player.getZ() + Math.sin(angle) * 2.5, 1, 0, 0, 0, 0);
		}
		world.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.BLOCK_BEACON_DEACTIVATE,
				SoundCategory.PLAYERS, 1.0f, 1.5f);
		return true;
	}

	/** Pulls a mob to the player, or, aimed at a block, pulls the player to the block. */
	private static boolean tether(ServerWorld world, PlayerEntity player) {
		Target target = trace(world, player, TETHER_RANGE);
		if (target.entity != null) {
			Vec3d pull = player.getPos().subtract(target.entity.getPos()).normalize();
			target.entity.setVelocity(pull.x * 1.6, pull.y * 1.6 + 0.35, pull.z * 1.6);
			target.entity.velocityModified = true;
			syncVelocity(target.entity);
		} else if (target.hitBlock) {
			Vec3d pull = target.pos.subtract(player.getPos()).normalize();
			player.setVelocity(pull.x * 2.2, pull.y * 2.2 + 0.4, pull.z * 2.2);
			player.velocityModified = true;
			player.fallDistance = 0;
			syncVelocity(player);
		} else {
			return false;
		}
		drawLine(world, handPos(player), target.pos);
		world.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.ENTITY_FISHING_BOBBER_RETRIEVE,
				SoundCategory.PLAYERS, 1.0f, 0.6f);
		return true;
	}

	/** Places one hard-light block; LightConstructBlock removes it again after its lifetime. */
	private static boolean placeConstruct(ServerWorld world, PlayerEntity player, BlockPos pos) {
		BlockState state = ModRegistry.LIGHT_CONSTRUCT.getDefaultState();
		if (!world.getBlockState(pos).isReplaceable() || !world.canPlayerModifyAt(player, pos)
				|| !world.canPlace(state, pos, ShapeContext.absent())) {
			return false;
		}
		world.setBlockState(pos, state);
		world.spawnParticles(GREEN_DUST, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, 3, 0.3, 0.3, 0.3, 0.0);
		return true;
	}

	private static boolean finishConstruct(ServerWorld world, PlayerEntity player, BlockPos at, int placed) {
		if (placed == 0) {
			return false;
		}
		drawLine(world, handPos(player), Vec3d.ofCenter(at));
		world.playSound(null, at, SoundEvents.BLOCK_AMETHYST_BLOCK_RESONATE, SoundCategory.PLAYERS, 1.0f, 1.4f);
		return true;
	}

	private record Target(Vec3d pos, Entity entity, boolean hitBlock) {
	}

	/** First entity or block along the player's line of sight. */
	private static Target trace(ServerWorld world, PlayerEntity player, double range) {
		Vec3d eye = player.getEyePos();
		Vec3d look = player.getRotationVector();
		Vec3d end = eye.add(look.multiply(range));
		BlockHitResult blockHit = world.raycast(new RaycastContext(eye, end, RaycastContext.ShapeType.COLLIDER,
				RaycastContext.FluidHandling.NONE, player));
		boolean hitBlock = blockHit.getType() != HitResult.Type.MISS;
		Vec3d stop = hitBlock ? blockHit.getPos() : end;
		Box sweep = player.getBoundingBox().stretch(look.multiply(range)).expand(1.0);
		EntityHitResult entityHit = ProjectileUtil.raycast(player, eye, stop, sweep,
				e -> !e.isSpectator() && e.canHit() && e != player, eye.squaredDistanceTo(stop));
		if (entityHit != null) {
			return new Target(entityHit.getPos(), entityHit.getEntity(), false);
		}
		return new Target(stop, null, hitBlock);
	}

	private static double distanceToRay(Vec3d point, Vec3d origin, Vec3d dir) {
		Vec3d rel = point.subtract(origin);
		double along = rel.dotProduct(dir);
		if (along < 0) {
			return rel.length();
		}
		return rel.subtract(dir.multiply(along)).length();
	}

	private static Vec3d handPos(PlayerEntity player) {
		return player.getEyePos().add(player.getRotationVector().multiply(0.7)).subtract(0, 0.25, 0);
	}

	private static void drawLine(ServerWorld world, Vec3d from, Vec3d to) {
		Vec3d step = to.subtract(from);
		int points = Math.max(2, (int) (step.length() * 3));
		for (int i = 0; i <= points; i++) {
			Vec3d p = from.add(step.multiply((double) i / points));
			world.spawnParticles(GREEN_DUST, p.x, p.y, p.z, 1, 0.02, 0.02, 0.02, 0.0);
		}
	}

	/** Players only see a server-side velocity change if it's sent to them directly. */
	private static void syncVelocity(Entity entity) {
		if (entity instanceof ServerPlayerEntity serverPlayer) {
			serverPlayer.networkHandler.sendPacket(new EntityVelocityUpdateS2CPacket(serverPlayer));
		}
	}
}
