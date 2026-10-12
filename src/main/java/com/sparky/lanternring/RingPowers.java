package com.sparky.lanternring;

import com.sparky.lanternring.block.LightConstructBlock;
import com.sparky.lanternring.net.RingFxPayload.Kind;
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
import net.minecraft.world.level.Explosion;
import net.minecraft.world.level.ExplosionDamageCalculator;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;

/** What each ring mode does. Everything here runs on the server. */
public final class RingPowers {
	private static final double BEAM_RANGE = 48;
	private static final float BEAM_DAMAGE = 8.0f;
	/** The charged beam (hold right-click) costs twice a tap and hits for 225%. */
	public static final int BEAM_CHARGED_COST = 2 * RingMode.BEAM.cost;
	private static final float BEAM_CHARGED_DAMAGE = BEAM_DAMAGE * 2.25f;
	/** A tap's hit pops like a 1.5-block explosion and breaks a block or two. */
	private static final float BEAM_BLAST = 1.5f;

	private RingPowers() {
	}

	public static boolean activate(RingMode mode, ServerLevel level, Player player) {
		return switch (mode) {
			case BLAST -> BlastDrills.start(level, player, BlastDrills.LENGTH, 1);
			case BEAM -> beam(level, player, false);
			case WALL -> wall(level, player);
			case DOME -> false; // held construct, see HeldConstructs
			case BRIDGE -> bridge(level, player);
			case PUSH -> push(level, player);
			case TETHER -> false; // held, see Lasso
			case ANVIL -> false; // held to aim, dropped on release; see Anvils
			case ARMY -> false; // held to aim, summoned on release; see ConstructArmy
		};
	}

	/** Flashes invisible lights along a Beam so it lights up what it passes, then they fade. */
	private static void lightBeam(ServerLevel level, Player player, Vec3 to) {
		Vec3 from = player.getEyePosition();
		Vec3 d = to.subtract(from);
		double len = d.length();
		if (len < 1) return;
		Vec3 dir = d.scale(1 / len);
		BlockState glow = ModRegistry.BEAM_GLOW.defaultBlockState();
		for (double t = 2.0; t < len; t += 4.0) {
			BlockPos pos = BlockPos.containing(from.add(dir.scale(t)));
			if (level.getBlockState(pos).isAir() && level.mayInteract(player, pos)) level.setBlock(pos, glow, 3);
		}
	}

	/**
	 * Fires the Beam: a tap hits for BEAM_DAMAGE with a small explosion at the hit. Charged (held
	 * for RingTuning.BEAM_CHARGE), it hits for 225% and the impact blows out a hard-light dome the
	 * size of a Shockwave: explosive damage and knockback to everything inside, but only the
	 * handful of blocks right at the hit break.
	 */
	public static boolean beam(ServerLevel level, Player player, boolean charged) {
		Vec3 look = player.getLookAngle();
		Target target = trace(level, player, BEAM_RANGE);
		if (target.entity != null) {
			target.entity.hurtServer(level, level.damageSources().indirectMagic(player, player), charged ? BEAM_CHARGED_DAMAGE : BEAM_DAMAGE);
			target.entity.push(look.x * 0.6, 0.15, look.z * 0.6);
			syncVelocity(target.entity);
		}
		RingFx.send(level, charged ? Kind.BEAM_CHARGED : Kind.BEAM, handPos(player), target.pos);
		lightBeam(level, player, target.pos);
		Vec3 at = target.pos;
		ExplosionDamageCalculator sparesOwner = new ExplosionDamageCalculator() {
			@Override
			public boolean shouldDamageEntity(Explosion explosion, Entity entity) {
				return entity != player && super.shouldDamageEntity(explosion, entity);
			}

			@Override
			public float getKnockbackMultiplier(Entity entity) {
				return entity == player ? 0f : super.getKnockbackMultiplier(entity);
			}
		};
		// A miss into open air just fades out.
		if (target.entity != null || target.hitBlock) {
			if (charged) {
				// Explosive force fills the whole dome (an explosion hurts out to twice its power) ...
				level.explode(player, null, sparesOwner, at.x, at.y, at.z, (float) (Shockwaves.RADIUS / 2), false, Level.ExplosionInteraction.NONE);
			}
			// ... and only this small pop at the hit breaks blocks.
			level.explode(player, null, sparesOwner, at.x, at.y, at.z, BEAM_BLAST, false, Level.ExplosionInteraction.TNT);
			// A tap also sends a small Shockwave out from the hit (the charged dome already covers that).
			if (!charged) Shockwaves.startAtBeamHit(level, player, at);
		}
		level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.BEACON_ACTIVATE,
				SoundSource.PLAYERS, charged ? 1.2f : 0.7f, charged ? 1.0f : 2.0f);
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
	public static void syncVelocity(Entity entity) {
		entity.needsSync = true;
		if (entity instanceof ServerPlayer serverPlayer) {
			serverPlayer.connection.send(new ClientboundSetEntityMotionPacket(serverPlayer));
		}
	}
}
