package com.sparky.lanternring.corps;

import com.sparky.lanternring.ModEffects;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.ally.DreadRunner;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * The fear the Dread Runner (ally/DreadRunner) leaves on the ground behind it: a strip of thin
 * yellow smoke, like the Fear Nuke's fear ground, curling with black shadow. Whoever stands in it,
 * the runner's owner included, is blinded by Fear Blind (FearBlindEffect): their screen goes dark
 * with sickly yellow light at its edges, and it fades a few seconds after they step out
 * (RingTuning.DREAD_BLIND). The fear lasts RingTuning.DREAD_TRAIL.
 */
public final class DreadTrails {
	/** How far from a patch of fear its blinding reaches, across and up. */
	private static final double RADIUS = 1.6;
	private static final double UP = 3;
	/** The same thin yellow smoke as the Fear Nuke's fear ground, and the shadow curling through it. */
	private static final DustParticleOptions SMOKE = new DustParticleOptions(0xE8C83A, 0.8f);
	private static final DustParticleOptions SHADOW = new DustParticleOptions(0x1C1606, 1.6f);

	private record Patch(ServerLevel level, Vec3 at, long until) {
	}

	private static final List<Patch> PATCHES = new ArrayList<>();

	private DreadTrails() {
	}

	public static void register() {
		ServerTickEvents.END_SERVER_TICK.register(DreadTrails::tick);
		ServerLifecycleEvents.SERVER_STOPPING.register(server -> PATCHES.clear());
	}

	/** Fear on the ground at this point (the runner drops one a block). */
	public static void drop(ServerLevel level, Vec3 at, Player owner) {
		PATCHES.add(new Patch(level, at, level.getGameTime() + Math.max(1, RingTuning.DREAD_TRAIL.ticks())));
		level.sendParticles(SHADOW, at.x, at.y + 0.3, at.z, 6, 0.6, 0.2, 0.6, 0.01);
		level.sendParticles(SMOKE, at.x, at.y + 0.1, at.z, 6, 0.7, 0.05, 0.7, 0.003);
	}

	/** Test hook: how many patches of fear are on the ground. */
	public static int count() {
		return PATCHES.size();
	}

	private static void tick(MinecraftServer server) {
		for (Iterator<Patch> it = PATCHES.iterator(); it.hasNext(); ) {
			Patch p = it.next();
			ServerLevel level = p.level;
			long now = level.getGameTime();
			if (now >= p.until || level.getServer() != server) {
				it.remove();
				continue;
			}
			// Each patch smokes and blinds every few ticks, not all on the same tick.
			int phase = (int) ((now + (long) (p.at.x * 7 + p.at.z * 13)) & 3);
			if (phase != 0) continue;
			Vec3 a = p.at;
			level.sendParticles(SMOKE, a.x, a.y + 0.08, a.z, 2, 0.6, 0.02, 0.6, 0.002);
			level.sendParticles(SHADOW, a.x, a.y + 0.25, a.z, 1, 0.5, 0.1, 0.5, 0.004);
			if (level.getRandom().nextInt(6) == 0) level.sendParticles(ParticleTypes.LARGE_SMOKE, a.x, a.y + 0.2, a.z, 1, 0.4, 0.05, 0.4, 0.01);
			int blind = Math.max(1, RingTuning.DREAD_BLIND.ticks());
			for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new AABB(a, a).inflate(RADIUS, 0.5, RADIUS).expandTowards(0, UP, 0),
					e -> e.isAlive() && !e.isSpectator() && !(e instanceof DreadRunner))) {
				e.addEffect(new MobEffectInstance(ModEffects.FEAR_BLIND, blind, 0, false, false, false));
				// Mobs don't see the screen: they get plain blindness and lose sight of their target.
				if (!(e instanceof Player)) e.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, blind, 0, false, false, false));
			}
		}
	}
}
