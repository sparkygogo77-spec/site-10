package com.sparky.lanternring.client;

import com.sparky.lanternring.item.PowerRingItem;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;

/**
 * Whoever holds a power ring glows in its corps' colour: a soft enchantment-like glint over their
 * body (RingAuraLayer, and on your own arm in first person). There is no hard outline any more
 * (a render state's outline colour alone draws one in 26.3, so none is set).
 */
public final class RageGlow {
	private RageGlow() {
	}

	public static boolean glows(Entity entity) {
		return entity instanceof Player player && !player.isInvisible() && !player.isSpectator()
				&& (com.sparky.lanternring.RingSlot.ring(player).getItem() instanceof PowerRingItem);
	}
}
