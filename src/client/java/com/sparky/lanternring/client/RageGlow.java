package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.item.PowerRingItem;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;

/**
 * Whoever holds a power ring glows in its corps' colour: outlined like the game's Glowing effect
 * (seen through walls; see EntityRendererMixin and MinecraftMixin), and wrapped in a flame aura
 * (RingAuraLayer), which is the part shader packs keep. The wearer's own body only shows it in
 * third person.
 */
public final class RageGlow {
	private RageGlow() {
	}

	public static boolean glows(Entity entity) {
		return entity instanceof Player player && !player.isInvisible() && !player.isSpectator()
				&& (player.getMainHandItem().getItem() instanceof PowerRingItem || player.getOffhandItem().getItem() instanceof PowerRingItem);
	}

	/** The outline's colour: the held ring's corps. */
	public static int color(Entity entity) {
		return 0xFF000000 | Corps.held((Player) entity).rgb;
	}
}
