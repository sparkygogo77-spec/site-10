package com.sparky.lanternring;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.level.block.BonemealSource;
import net.minecraft.world.level.block.BonemealableBlock;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * The Blue Lantern's power (J, 2026-10-13: "Hope beacon"): with the blue lantern summoned, hold
 * the lantern key and a beacon of hope stands where you are for {@link RingTuning#HOPE_BEACON}.
 * Everyone who isn't a monster within {@link #RADIUS} blocks slowly heals, crops and saplings
 * grow, and bare dirt greens over. Holding the key again moves it to where you stand.
 */
public final class BlueBeacon {
	public static final int RADIUS = 12;
	/** Random ground spots tried for growth each tick. */
	private static final int GROW_TRIES = 6;

	private record Beacon(ServerLevel level, BlockPos pos, long started) {
	}

	private static final Map<UUID, Beacon> BEACONS = new HashMap<>();

	private BlueBeacon() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(BlueBeacon::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> BEACONS.clear());
	}

	public static boolean lit(ServerPlayer player) {
		return BEACONS.containsKey(player.getUUID());
	}

	static void start(ServerPlayer player) {
		ServerLevel level = player.level();
		BEACONS.put(player.getUUID(), new Beacon(level, player.blockPosition(), level.getGameTime()));
		player.sendOverlayMessage(Component.translatable("message.lanternring.hope_beacon").withStyle(ChatFormatting.AQUA));
		level.playSound(null, player.blockPosition(), SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 1.5f, 1.2f);
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Beacon> it = BEACONS.values().iterator(); it.hasNext(); ) {
			Beacon b = it.next();
			long t = b.level.getGameTime() - b.started;
			if (t > RingTuning.HOPE_BEACON.ticks() || !b.level.isLoaded(b.pos)) {
				it.remove();
				b.level.playSound(null, b.pos, SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 1.5f, 1.2f);
				continue;
			}
			glow(b, t);
			if (t % 20 == 0) heal(b);
			if (t % 80 == 40) b.level.playSound(null, b.pos, SoundEvents.BEACON_AMBIENT, SoundSource.PLAYERS, 1f, 1.3f);
			RandomSource random = b.level.getRandom();
			for (int i = 0; i < GROW_TRIES; i++) grow(b, random);
		}
	}

	/** A soft blue column over the spot, and motes drifting up at the edge of its reach. */
	private static void glow(Beacon b, long t) {
		Vec3 c = Vec3.atBottomCenterOf(b.pos);
		if (t % 2 == 0) {
			b.level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), c.x, c.y + 0.5 + (t % 40) * 0.15, c.z, 2, 0.15, 0.3, 0.15, 0.01);
		}
		if (t % 5 == 0) {
			double a = t * 0.31;
			b.level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), c.x + Math.cos(a) * RADIUS, c.y + 0.3, c.z + Math.sin(a) * RADIUS, 1, 0.1, 0.1, 0.1, 0.02);
		}
	}

	private static void heal(Beacon b) {
		AABB box = new AABB(b.pos).inflate(RADIUS);
		for (LivingEntity e : b.level.getEntitiesOfClass(LivingEntity.class, box, e -> e.isAlive() && !(e instanceof Enemy))) {
			if (e.distanceToSqr(Vec3.atCenterOf(b.pos)) > RADIUS * RADIUS) continue;
			e.addEffect(new MobEffectInstance(MobEffects.REGENERATION, 50, 0, true, true, true));
			if (e.getHealth() < e.getMaxHealth()) {
				b.level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), e.getX(), e.getY() + e.getBbHeight() * 0.6, e.getZ(), 3, 0.3, 0.4, 0.3, 0.01);
			}
		}
	}

	/** Picks a ground spot in reach: a plant there grows a step, bare dirt turns to grass. */
	private static void grow(Beacon b, RandomSource random) {
		int dx = random.nextInt(2 * RADIUS + 1) - RADIUS, dz = random.nextInt(2 * RADIUS + 1) - RADIUS;
		if (dx * dx + dz * dz > RADIUS * RADIUS) return;
		BlockPos top = b.level.getHeightmapPos(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, b.pos.offset(dx, 0, dz));
		if (Math.abs(top.getY() - b.pos.getY()) > RADIUS) return;
		BlockPos ground = top.below();
		BlockState plant = b.level.getBlockState(top);
		BlockState soil = b.level.getBlockState(ground);
		if (plant.getBlock() instanceof BonemealableBlock bm && !plant.is(Blocks.SHORT_GRASS) && !plant.is(Blocks.TALL_GRASS)) {
			// Crops, saplings, berries: about one growth step every few seconds each.
			if (random.nextFloat() < 0.25f && bm.isValidBonemealTarget(b.level, top, plant, BonemealSource.MOB)) {
				bm.performBonemeal(b.level, random, top, plant, BonemealSource.MOB);
				sparkle(b, top);
			}
		} else if (soil.is(Blocks.DIRT) && plant.isAir()) {
			b.level.setBlockAndUpdate(ground, Blocks.GRASS_BLOCK.defaultBlockState());
			sparkle(b, top);
		} else if (soil.is(Blocks.GRASS_BLOCK) && plant.isAir() && random.nextFloat() < 0.03f) {
			// Now and then a tuft of grass or a flower comes up.
			b.level.setBlockAndUpdate(top, random.nextInt(5) == 0 ? Blocks.CORNFLOWER.defaultBlockState() : Blocks.SHORT_GRASS.defaultBlockState());
			sparkle(b, top);
		}
	}

	private static void sparkle(Beacon b, BlockPos pos) {
		b.level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), pos.getX() + 0.5, pos.getY() + 0.3, pos.getZ() + 0.5, 4, 0.3, 0.2, 0.3, 0.01);
	}
}
