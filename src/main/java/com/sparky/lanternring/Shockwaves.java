package com.sparky.lanternring;

import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.DoublePlantBlock;
import net.minecraft.world.level.block.FlowerBlock;
import net.minecraft.world.level.block.SnowLayerBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * SHOCKWAVE: a dome of hard light grows out from where the player stood. The dome's surface is the
 * barrier: nothing is pushed until the surface reaches it. Clients draw the same dome growing at
 * the same speed (LabFx.shockwave), so what you see hitting a mob is what pushed it.
 */
public final class Shockwaves {
	/** How far the dome grows, in blocks. */
	public static final double RADIUS = 7;
	/** How fast the dome grows, in blocks per tick (about 0.6 seconds to full size). */
	public static final double SPEED = 0.6;
	private static final float DAMAGE = 3.0f;

	private static final class Wave {
		final ServerLevel level;
		final Player owner;
		final Vec3 center;
		final Set<UUID> hit = new HashSet<>();
		double radius;

		Wave(ServerLevel level, Player owner, Vec3 center) {
			this.level = level;
			this.owner = owner;
			this.center = center;
		}
	}

	private static final List<Wave> WAVES = new ArrayList<>();

	private Shockwaves() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(Shockwaves::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> WAVES.clear());
	}

	static void start(ServerLevel level, Player player) {
		Vec3 center = player.position();
		WAVES.add(new Wave(level, player, center));
		RingFx.send(level, Kind.PUSH, center);
		level.playSound(null, center.x, center.y, center.z, SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 1.0f, 1.5f);
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Wave> it = WAVES.iterator(); it.hasNext(); ) {
			Wave wave = it.next();
			double from = wave.radius;
			wave.radius = Math.min(RADIUS, wave.radius + SPEED);
			sweep(wave);
			mow(wave, from);
			if (wave.radius >= RADIUS) it.remove();
		}
	}

	/** Pushes everything the dome's surface has reached since last tick, once per wave. */
	private static void sweep(Wave wave) {
		double r = wave.radius;
		AABB area = new AABB(wave.center, wave.center).inflate(r);
		for (LivingEntity target : wave.level.getEntitiesOfClass(LivingEntity.class, area,
				e -> e != wave.owner && e.isAlive() && !e.isSpectator() && !wave.hit.contains(e.getUUID()))) {
			if (distanceSqr(target.getBoundingBox(), wave.center) > r * r) continue;
			wave.hit.add(target.getUUID());
			Vec3 away = target.position().subtract(wave.center).multiply(1, 0, 1);
			if (away.lengthSqr() < 1.0e-4) away = wave.owner.getLookAngle().multiply(1, 0, 1);
			away = away.lengthSqr() < 1.0e-4 ? new Vec3(1, 0, 0) : away.normalize();
			target.hurtServer(wave.level, wave.level.damageSources().indirectMagic(wave.owner, wave.owner), DAMAGE);
			target.setDeltaMovement(away.x * 1.8, 0.6, away.z * 1.8);
			RingPowers.syncVelocity(target);
		}
	}

	/** Flattens grass, ferns, flowers and other plants in the shell the dome just passed through. */
	private static void mow(Wave wave, double from) {
		double r = wave.radius;
		BlockPos lo = BlockPos.containing(wave.center.subtract(r, r, r));
		BlockPos hi = BlockPos.containing(wave.center.add(r, r, r));
		for (BlockPos pos : BlockPos.betweenClosed(lo, hi)) {
			double d = pos.getCenter().distanceToSqr(wave.center);
			if (d <= from * from || d > r * r) continue;
			if (isFoliage(wave.level.getBlockState(pos))) wave.level.destroyBlock(pos, false);
		}
	}

	private static boolean isFoliage(BlockState state) {
		if (state.isAir() || !state.getFluidState().isEmpty() || state.getBlock() instanceof SnowLayerBlock) return false;
		return state.canBeReplaced() || state.getBlock() instanceof FlowerBlock || state.getBlock() instanceof DoublePlantBlock;
	}

	/** Distance from a point to the nearest part of a box, so big mobs are hit when the dome touches them. */
	private static double distanceSqr(AABB box, Vec3 p) {
		double dx = p.x - Mth.clamp(p.x, box.minX, box.maxX);
		double dy = p.y - Mth.clamp(p.y, box.minY, box.maxY);
		double dz = p.z - Mth.clamp(p.z, box.minZ, box.maxZ);
		return dx * dx + dy * dy + dz * dz;
	}
}
