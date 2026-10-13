package com.sparky.lanternring;

import com.sparky.lanternring.block.PowerFontBlock;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * The Red Lantern's power (J, 2026-10-13): with the red lantern summoned, hold the lantern key and
 * it self-destructs. Rage builds for {@link RingTuning#RED_SELF_DESTRUCT}, then it bursts: you die,
 * your lantern is gone, and so is every other lantern within {@link #RADIUS} blocks: placed ones,
 * great batteries, dropped ones, and the ones other players hold or have summoned. The ground
 * isn't touched.
 */
public final class RedSelfDestruct {
	public static final int RADIUS = 15;
	private static final Map<UUID, Long> FUSES = new HashMap<>();

	private RedSelfDestruct() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(RedSelfDestruct::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> FUSES.clear());
	}

	public static boolean burning(ServerPlayer player) {
		return FUSES.containsKey(player.getUUID());
	}

	/** Lights the fuse (holding the key again doesn't call it off: rage doesn't turn back). */
	static void start(ServerPlayer player) {
		if (burning(player)) return;
		FUSES.put(player.getUUID(), player.level().getGameTime());
		player.sendOverlayMessage(Component.translatable("message.lanternring.self_destruct").withStyle(ChatFormatting.DARK_RED));
		player.level().playSound(null, player.blockPosition(), SoundEvents.WARDEN_HEARTBEAT, SoundSource.PLAYERS, 2f, 0.8f);
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Map.Entry<UUID, Long>> it = FUSES.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<UUID, Long> e = it.next();
			ServerPlayer player = server.getPlayerList().getPlayer(e.getKey());
			if (player == null || !player.isAlive()) {
				it.remove();
				continue;
			}
			ServerLevel level = (ServerLevel) player.level();
			long t = level.getGameTime() - e.getValue();
			int fuse = Math.max(1, RingTuning.RED_SELF_DESTRUCT.ticks());
			Vec3 mid = player.position().add(0, 1, 0);
			if (t < fuse) {
				// Rage gathering into the bearer, faster and faster, with a quickening heartbeat.
				float k = t / (float) fuse;
				int count = 2 + (int) (10 * k);
				level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.RED), mid.x, mid.y, mid.z, count, 1.5 - k, 1.2 - k * 0.8, 1.5 - k, 0.02);
				int beat = Math.max(3, (int) (16 * (1f - k)));
				if (t % beat == 0) level.playSound(null, player.blockPosition(), SoundEvents.WARDEN_HEARTBEAT, SoundSource.PLAYERS, 2f, 0.8f + k);
				continue;
			}
			it.remove();
			burst(level, player);
		}
	}

	private static void burst(ServerLevel level, ServerPlayer player) {
		Vec3 mid = player.position().add(0, 1, 0);
		int destroyed = destroyLanterns(level, player);
		// Your own lantern goes with you.
		player.removeAttached(LanternSlot.SLOT);
		OrangeHorde.stop(player);
		level.sendParticles(ParticleTypes.EXPLOSION_EMITTER, mid.x, mid.y, mid.z, 3, 1.5, 1, 1.5, 0);
		level.sendParticles(ModParticles.of(ModParticles.SHARD, Corps.RED), mid.x, mid.y, mid.z, 200, 1, 1, 1, 0.8);
		level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.RED), mid.x, mid.y, mid.z, 120, 3, 2, 3, 0.3);
		level.playSound(null, player.blockPosition(), SoundEvents.GENERIC_EXPLODE.value(), SoundSource.PLAYERS, 4f, 0.6f);
		level.playSound(null, player.blockPosition(), SoundEvents.WARDEN_SONIC_BOOM, SoundSource.PLAYERS, 3f, 0.7f);
		if (destroyed > 0) {
			player.sendSystemMessage(Component.translatable("message.lanternring.self_destruct_lanterns", destroyed).withStyle(ChatFormatting.DARK_RED));
		}
		player.hurtServer(level, level.damageSources().genericKill(), Float.MAX_VALUE);
	}

	/** Every lantern within RADIUS of the bearer is gone; returns how many. */
	private static int destroyLanterns(ServerLevel level, ServerPlayer bearer) {
		BlockPos at = bearer.blockPosition();
		int n = 0;
		// Placed lanterns and great batteries.
		for (BlockPos pos : BlockPos.betweenClosed(at.offset(-RADIUS, -RADIUS, -RADIUS), at.offset(RADIUS, RADIUS, RADIUS))) {
			if (pos.distSqr(at) > RADIUS * RADIUS) continue;
			BlockState state = level.getBlockState(pos);
			if (!state.is(ModRegistry.POWER_BATTERY) && !(state.getBlock() instanceof PowerFontBlock)) continue;
			level.setBlock(pos, Blocks.AIR.defaultBlockState(), 3);
			shatter(level, Vec3.atCenterOf(pos));
			n++;
		}
		AABB box = bearer.getBoundingBox().inflate(RADIUS);
		// Dropped lanterns.
		for (ItemEntity item : level.getEntitiesOfClass(ItemEntity.class, box, i -> i.getItem().is(ModRegistry.POWER_BATTERY_ITEM))) {
			if (item.distanceTo(bearer) > RADIUS) continue;
			shatter(level, item.position());
			n += item.getItem().getCount();
			item.discard();
		}
		// Lanterns other players hold or have summoned.
		for (Player other : level.getEntitiesOfClass(Player.class, box, p -> p != bearer)) {
			if (other.distanceTo(bearer) > RADIUS) continue;
			for (InteractionHand hand : InteractionHand.values()) {
				if (!other.getItemInHand(hand).is(ModRegistry.POWER_BATTERY_ITEM)) continue;
				n += other.getItemInHand(hand).getCount();
				other.setItemInHand(hand, net.minecraft.world.item.ItemStack.EMPTY);
				shatter(level, other.position().add(0, 1, 0));
			}
			if (LanternSlot.out(other)) {
				other.removeAttached(LanternSlot.SLOT);
				if (other instanceof ServerPlayer sp) OrangeHorde.stop(sp);
				shatter(level, other.position().add(0, 1.2, 0));
				n++;
			}
		}
		return n;
	}

	private static void shatter(ServerLevel level, Vec3 at) {
		level.sendParticles(ModParticles.of(ModParticles.SHARD, Corps.RED), at.x, at.y, at.z, 30, 0.3, 0.3, 0.3, 0.2);
		level.playSound(null, BlockPos.containing(at), SoundEvents.GLASS_BREAK, SoundSource.BLOCKS, 1.2f, 0.7f);
	}
}
