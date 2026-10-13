package com.sparky.lanternring;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.monster.Creeper;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.phys.AABB;

/**
 * The Violet Lantern's power (J, 2026-10-13: "Love charm"): with the violet lantern summoned, hold
 * the lantern key and love washes out {@link #RADIUS} blocks. Monsters caught in it stop fighting
 * for {@link RingTuning#LOVE_CHARM} (they forget their targets and won't pick new ones), and
 * animals that are old enough fall in love.
 */
public final class VioletCharm {
	public static final int RADIUS = 16;
	private static final Map<UUID, Charmed> CHARMED = new HashMap<>();

	private record Charmed(ServerLevel level, long until) {
	}

	private VioletCharm() {
	}

	static void register() {
		ServerTickEvents.END_SERVER_TICK.register(VioletCharm::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> CHARMED.clear());
	}

	public static boolean charmed(Entity e) {
		return CHARMED.containsKey(e.getUUID());
	}

	static void start(ServerPlayer player) {
		ServerLevel level = player.level();
		long until = level.getGameTime() + RingTuning.LOVE_CHARM.ticks();
		AABB box = player.getBoundingBox().inflate(RADIUS);
		int monsters = 0;
		for (Mob mob : level.getEntitiesOfClass(Mob.class, box, m -> m.isAlive() && m.distanceToSqr(player) <= RADIUS * RADIUS)) {
			if (mob instanceof Enemy) {
				CHARMED.put(mob.getUUID(), new Charmed(level, until));
				calm(mob);
				monsters++;
			} else if (mob instanceof Animal a && !a.isBaby() && a.canFallInLove()) {
				a.setInLove(player);
			} else {
				continue;
			}
			level.sendParticles(ParticleTypes.HEART, mob.getX(), mob.getY() + mob.getBbHeight() + 0.3, mob.getZ(), 3, 0.3, 0.2, 0.3, 0.02);
		}
		// A ring of violet light rolling out over the ground.
		for (int i = 0; i < 48; i++) {
			double a = i * Math.PI * 2 / 48;
			level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.VIOLET), player.getX() + Math.cos(a) * 2, player.getY() + 0.3, player.getZ() + Math.sin(a) * 2,
					0, Math.cos(a), 0.02, Math.sin(a), 0.6);
		}
		player.sendOverlayMessage(Component.translatable("message.lanternring.love_charm", monsters).withStyle(ChatFormatting.LIGHT_PURPLE));
		level.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 2f, 1.4f);
		level.playSound(null, player.blockPosition(), SoundEvents.ALLAY_AMBIENT_WITH_ITEM, SoundSource.PLAYERS, 1.5f, 0.9f);
	}

	private static void calm(Mob mob) {
		if (mob.getTarget() != null) mob.setTarget(null);
		mob.setAggressive(false);
		mob.getBrain().eraseMemory(MemoryModuleType.ATTACK_TARGET);
		mob.getBrain().eraseMemory(MemoryModuleType.ANGRY_AT);
		if (mob instanceof Creeper c) c.setSwellDir(-1);
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Map.Entry<UUID, Charmed>> it = CHARMED.entrySet().iterator(); it.hasNext(); ) {
			Map.Entry<UUID, Charmed> e = it.next();
			Charmed c = e.getValue();
			Entity entity = c.level.getEntity(e.getKey());
			long now = c.level.getGameTime();
			if (!(entity instanceof Mob mob) || !mob.isAlive() || now >= c.until) {
				it.remove();
				continue;
			}
			calm(mob);
			if (now % 30 == mob.getId() % 30) {
				c.level.sendParticles(ParticleTypes.HEART, mob.getX(), mob.getY() + mob.getBbHeight() + 0.3, mob.getZ(), 1, 0.2, 0.1, 0.2, 0.01);
			}
		}
	}
}
