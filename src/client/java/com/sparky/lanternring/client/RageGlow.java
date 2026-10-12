package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;

/**
 * The Red Lantern's rage: whoever holds a red ring is outlined in glowing red, like the game's
 * Glowing effect but in the corps' colour, seen through walls too. The wearer's own body only
 * shows it in third person. It's drawn by the game's entity outline pass (see EntityRendererMixin
 * and MinecraftMixin).
 */
public final class RageGlow {
	public static final int COLOR = 0xFFFF1A1A;

	private RageGlow() {
	}

	public static boolean glows(Entity entity) {
		return entity instanceof Player player && !player.isInvisible() && !player.isSpectator()
				&& Corps.held(player) == Corps.RED;
	}
}
