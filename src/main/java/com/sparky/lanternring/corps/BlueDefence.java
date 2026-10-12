package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingFx;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.block.LightConstructBlock;
import com.sparky.lanternring.net.RingFxPayload;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.npc.villager.AbstractVillager;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * Blue Lanterns under a Red raid: while sky raiders are near, each Blue villager raises domes of
 * blue hard light over the people who can't fight (ordinary villagers and children), and over a
 * Blue villager badly hurt in the fight, which heals inside it. The fighters stay out in the open
 * with the hawks and golems, beaming and lassoing the raiders. Domes fade on their own (the
 * construct lifetime) and are raised again while the raid goes on.
 */
public final class BlueDefence {
	/** How near a raider has to be for a Blue villager to defend, and how far round it shields people. */
	private static final double ALARM = 40, SHIELD = 24;
	/** Below this share of its health a Blue fighter takes cover under a dome of its own. */
	private static final float HURT = 0.4f;
	/** Who is under a dome now, and until when. */
	private static final Map<UUID, Long> DOMED = new HashMap<>();

	private BlueDefence() {
	}

	public static void init() {
		ServerTickEvents.END_SERVER_TICK.register(server -> {
			if (server.getTickCount() % 20 != 0) return;
			for (ServerLevel level : server.getAllLevels()) tick(level);
		});
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> DOMED.clear());
	}

	private static void tick(ServerLevel level) {
		List<? extends SkyRaider> raiders = level.getEntities(CorpsMobs.SKY_RAIDER, SkyRaider::isAlive);
		if (raiders.isEmpty()) return;
		long now = level.getGameTime();
		DOMED.values().removeIf(until -> until < now);
		for (SkyRaider raider : raiders) {
			for (CorpsVillager blue : level.getEntitiesOfClass(CorpsVillager.class, raider.getBoundingBox().inflate(ALARM),
					v -> v.isAlive() && v.corps() == Corps.BLUE && !v.isBaby())) {
				// A badly hurt fighter takes cover and heals.
				if (blue.getHealth() < blue.getMaxHealth() * HURT && !DOMED.containsKey(blue.getUUID())) {
					dome(level, blue, blue);
					blue.addEffect(new MobEffectInstance(MobEffects.REGENERATION, RingTuning.CONSTRUCT_LIFETIME.ticks(), 1));
				}
				for (AbstractVillager v : level.getEntitiesOfClass(AbstractVillager.class, blue.getBoundingBox().inflate(SHIELD),
						v -> v.isAlive() && !DOMED.containsKey(v.getUUID()) && (v.isBaby() || !(v instanceof CorpsVillager cv) || cv.corps() != Corps.BLUE))) {
					dome(level, blue, v);
				}
			}
		}
	}

	/** Raises a dome of hard light over {@code who}, beamed from {@code by}'s ring. */
	static void dome(ServerLevel level, CorpsVillager by, LivingEntity who) {
		DOMED.put(who.getUUID(), level.getGameTime() + RingTuning.CONSTRUCT_LIFETIME.ticks());
		Corps before = Corps.enter(Corps.BLUE);
		try {
			BlockState shell = Corps.state(ModRegistry.LIGHT_CONSTRUCT);
			BlockPos base = who.blockPosition();
			for (int dx = -3; dx <= 3; dx++) {
				for (int dy = 0; dy <= 3; dy++) {
					for (int dz = -3; dz <= 3; dz++) {
						double d = Math.sqrt(dx * dx + dy * dy * 1.3 + dz * dz);
						if (d < 2.4 || d > 3.3) continue;
						BlockPos p = base.offset(dx, dy, dz);
						BlockState now = level.getBlockState(p);
						if (!now.canBeReplaced() || !now.getFluidState().isEmpty()) continue;
						level.setBlockAndUpdate(p, shell.setValue(LightConstructBlock.RIM, dy == 0 || d > 3.1));
					}
				}
			}
			Vec3 c = who.getBoundingBox().getCenter();
			RingFx.send(level, RingFxPayload.Kind.CONSTRUCT, CorpsVillager.ringPos(by, 1f, c), c);
			level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), c.x, c.y + 1, c.z, 12, 1.5, 1.2, 1.5, 0.02);
		} finally {
			Corps.restore(before);
		}
		level.playSound(null, who.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.NEUTRAL, 1.2f, 1.3f);
	}
}
