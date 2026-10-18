package com.sparky.lanternring.client;

import com.sparky.lanternring.RingSlot;
import com.sparky.lanternring.item.PowerRingItem;
import java.util.HashMap;
import java.util.Map;
import net.minecraft.client.Minecraft;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

/**
 * Primed (J, 2026-10-16): while a ring bearer holds Shift (primed slams, hyper speed) the ring and the arm glow
 * stronger and more detailed, so you can see you're primed. Eases in and out; tracked for every player in view,
 * since a held Shift shows to others as crouching.
 */
public final class PrimedGlow {
	private static final float IN = 0.25f, OUT = 0.15f;
	/** Per player id: {last tick's level, this tick's level}. */
	private static final Map<Integer, float[]> LEVELS = new HashMap<>();

	static void tick(Minecraft mc) {
		if (mc.level == null) {
			LEVELS.clear();
			return;
		}
		LEVELS.keySet().removeIf(id -> !(mc.level.getEntity(id) instanceof Player));
		for (Player p : mc.level.players()) {
			float target = primed(p) ? 1f : 0f;
			float[] l = LEVELS.computeIfAbsent(p.getId(), id -> new float[2]);
			l[0] = l[1];
			l[1] = l[1] < target ? Math.min(target, l[1] + IN) : Math.max(target, l[1] - OUT);
			if (p == mc.player && l[1] >= 1f && l[0] < 1f) WhatsNewClient.tell("ring.primed_glow");
		}
	}

	private static boolean primed(Player p) {
		if (!p.isShiftKeyDown() || p.isSpectator() || p.isInvisible()) return false;
		ItemStack ring = RingSlot.ring(p);
		return ring.getItem() instanceof PowerRingItem && PowerRingItem.getCharge(ring) > 0;
	}

	/** How primed this player's ring glow is, 0 to 1, smoothed. */
	public static float level(Player p, float partial) {
		float[] l = p == null ? null : LEVELS.get(p.getId());
		if (l == null) return 0f;
		float v = Mth.lerp(partial, l[0], l[1]);
		return v * v * (3 - 2 * v);
	}

	private PrimedGlow() {
	}
}
