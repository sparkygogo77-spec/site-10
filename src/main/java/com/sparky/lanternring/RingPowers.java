package com.sparky.lanternring;

import com.sparky.lanternring.block.LightConstructBlock;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.LinkedHashSet;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
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
	private static final double BLAST_LENGTH = 50;
	private static final float BLAST_DAMAGE = 10.0f;
	private static final double BEAM_RANGE = 48;
	private static final float BEAM_DAMAGE = 8.0f;

	private RingPowers() {
	}

	public static boolean activate(RingMode mode, ServerLevel level, Player player) {
		return switch (mode) {
			case BLAST -> blast(level, player);
			case BEAM -> beam(level, player);
			case WALL -> wall(level, player);
			case DOME -> false; // held construct, see HeldConstructs
			case BRIDGE -> bridge(level, player);
			case PUSH -> push(level, player);
			case TETHER -> false; // held, see Lasso
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

		for (BlockPos pos : tunnel) {
			BlockState state = level.getBlockState(pos);
			if (state.isAir() || state.is(ModRegistry.BLAST_GLOW) || state.getDestroySpeed(level, pos) < 0 || state.hasBlockEntity()
					|| !level.mayInteract(player, pos)) {
				continue;
			}
			level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
			HeldConstructs.debris(level, pos, state);
		}

		lightTunnel(level, player, origin, look);

		AABB path = new AABB(origin, origin.add(look.scale(BLAST_LENGTH))).inflate(1.5);
		for (LivingEntity target : level.getEntitiesOfClass(LivingEntity.class, path,
				e -> e != player && e.isAlive() && !e.isSpectator()
						&& distanceToRay(e.getBoundingBox().getCenter(), origin, look) < 2.0)) {
			target.hurtServer(level, level.damageSources().indirectMagic(player, player), BLAST_DAMAGE);
		}

		RingFx.send(level, Kind.BLAST, origin, origin.add(look.scale(BLAST_LENGTH)));
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.WARDEN_SONIC_BOOM,
				SoundSource.PLAYERS, 1.2f, 1.3f);
		return true;
	}

	/**
	 * Leaves a few invisible lights down the middle of a fresh Blast tunnel, so the glowing scar
	 * lights its walls. Plain block light, so it works with any shader pack.
	 */
	private static void lightTunnel(ServerLevel level, Player player, Vec3 origin, Vec3 look) {
		if (RingTuning.BLAST_AFTERGLOW.ticks() <= 0) return;
		BlockState glow = ModRegistry.BLAST_GLOW.defaultBlockState();
		for (double t = 2.0; t <= BLAST_LENGTH; t += 4.0) {
			BlockPos pos = BlockPos.containing(origin.add(look.scale(t)));
			if (level.getBlockState(pos).isAir() && level.mayInteract(player, pos)) level.setBlock(pos, glow, 3);
		}
	}

	private static boolean beam(ServerLevel level, Player player) {
		Vec3 look = player.getLookAngle();
		Target target = trace(level, player, BEAM_RANGE);
		if (target.entity != null) {
			target.entity.hurtServer(level, level.damageSources().indirectMagic(player, player), BEAM_DAMAGE);
			target.entity.push(look.x * 0.6, 0.15, look.z * 0.6);
			syncVelocity(target.entity);
		}
		RingFx.send(level, Kind.BEAM, handPos(player), target.pos);
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.BEACON_ACTIVATE,
				SoundSource.PLAYERS, 0.7f, 2.0f);
		return true;
	}

	/** A flat 9x9 wall in front of the player that stands for RingTuning.WALL_LIFETIME. */
	private static boolean wall(ServerLevel level, Player player) {
		int placed = HeldConstructs.placeWall(level, player);
		return finishConstruct(level, player, player.blockPosition().relative(player.getDirection(), 3).above(4), placed);
	}

	/** A 3-wide, 12-long bridge at foot level, heading where the player faces. */
	private static boolean bridge(ServerLevel level, Player player) {
		Direction forward = player.getDirection();
		Direction right = forward.getClockWise();
		BlockPos start = player.blockPosition().below();
		int placed = 0;
		for (int along = 0; along <= 12; along++) {
			for (int across = -1; across <= 1; across++) {
				if (placeConstruct(level, player, start.relative(forward, along).relative(right, across), across != 0)) {
					placed++;
				}
			}
		}
		return finishConstruct(level, player, start.relative(forward, 6), placed);
	}

	/** Sends out an expanding dome that shoves every living thing it reaches away; see Shockwaves. */
	private static boolean push(ServerLevel level, Player player) {
		Shockwaves.start(level, player);
		return true;
	}

	/** Places one hard-light block; LightConstructBlock removes it again after its lifetime. */
	private static boolean placeConstruct(ServerLevel level, Player player, BlockPos pos, boolean rim) {
		BlockState state = ModRegistry.LIGHT_CONSTRUCT.defaultBlockState().setValue(LightConstructBlock.RIM, rim);
		if (!level.getBlockState(pos).canBeReplaced() || !level.mayInteract(player, pos)
				|| !level.isUnobstructed(state, pos, CollisionContext.empty())) {
			return false;
		}
		level.setBlockAndUpdate(pos, state);
		return true;
	}

	private static boolean finishConstruct(ServerLevel level, Player player, BlockPos at, int placed) {
		if (placed == 0) {
			return false;
		}
		RingFx.send(level, Kind.CONSTRUCT, handPos(player), Vec3.atCenterOf(at));
		level.playSound(null, at, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1.0f, 1.4f);
		return true;
	}

	record Target(Vec3 pos, Entity entity, boolean hitBlock) {
	}

	/** First entity or block along the player's line of sight. */
	static Target trace(ServerLevel level, Player player, double range) {
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

	static Vec3 handPos(Player player) {
		return player.getEyePosition().add(player.getLookAngle().scale(0.7)).subtract(0, 0.25, 0);
	}

	/** Mobs need their new motion broadcast; players only see it if it's sent to them directly. */
	static void syncVelocity(Entity entity) {
		entity.needsSync = true;
		if (entity instanceof ServerPlayer serverPlayer) {
			serverPlayer.connection.send(new ClientboundSetEntityMotionPacket(serverPlayer));
		}
	}
}
