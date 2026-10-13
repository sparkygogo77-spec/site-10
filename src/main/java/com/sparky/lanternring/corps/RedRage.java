package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModEffects;
import com.sparky.lanternring.ally.ConstructAlly;
import com.sparky.lanternring.ally.RageBull;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;

/**
 * Where Red rage comes from (J, 2026-10-13: 36): a player hurt by a Red Lantern, anything it made
 * or brought (constructs, rage wardens, bulls and cats), or a Red ring's own light, has rage on
 * them for a while (ModEffects.RAGE).
 */
public final class RedRage {
	/** How long the rage lasts after the last Red hit. */
	public static final int TICKS = 20 * 120;

	private RedRage() {
	}

	public static void register() {
		ServerLivingEntityEvents.AFTER_DAMAGE.register((entity, source, base, taken, blocked) -> {
			if (!(entity instanceof ServerPlayer p) || taken <= 0) return;
			if (red(source.getEntity()) || red(source.getDirectEntity())) give(p);
		});
	}

	public static void give(LivingEntity e) {
		e.addEffect(new MobEffectInstance(ModEffects.RAGE, TICKS, 0, false, false, true));
	}

	public static boolean raging(LivingEntity e) {
		return e.hasEffect(ModEffects.RAGE);
	}

	/** Whether this is a Red Lantern or something of theirs. */
	static boolean red(Entity e) {
		if (e == null) return false;
		if (e instanceof ConstructAlly a) return a.corps() == Corps.RED;
		if (e instanceof CorpsVillager v) return v.corps() == Corps.RED;
		if (e instanceof CorpsGolem g) return g.corps() == Corps.RED;
		if (e instanceof RageWarden || e instanceof RageBull || e instanceof RageCat) return true;
		return e instanceof Player p && Corps.held(p) == Corps.RED;
	}
}
