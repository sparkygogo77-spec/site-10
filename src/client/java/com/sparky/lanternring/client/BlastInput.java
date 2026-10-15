package com.sparky.lanternring.client;

import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.AnvilInputPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.world.item.ItemStack;

/**
 * Blast mode with right-click held (see BlastDrills): a left-click launches the formed drill, a
 * double-click steers it toward the aim, and holding the second click keeps it steering (sent
 * every tick it's down). Crouch + left-click picks the level before launching. Left-click doesn't
 * hit or mine meanwhile (see MinecraftMixin via AnvilInput.ownsLeftClick).
 */
public final class BlastInput {
	/** Two presses this many ticks apart or closer are a double-click. */
	public static final int DOUBLE = 7;
	private static int clock;
	private static int lastPress = -100;
	/** The second click of a double-click is still down. */
	private static boolean steering;

	private BlastInput() {
	}

	/** Right-click is held with the ring in Blast mode. */
	public static boolean active(Minecraft mc) {
		if (mc.player == null || !mc.player.isUsingItem() || LanternCharge.started(mc.player)) return false;
		ItemStack used = mc.player.getUseItem();
		return used.getItem() instanceof PowerRingItem && PowerRingItem.getMode(used) == RingMode.BLAST;
	}

	/** Before vanilla handles the keys, which throws clicks away while an item is in use. */
	public static void startTick(Minecraft mc) {
		clock++;
		if (!active(mc) || mc.gui.screen() != null || !ClientPlayNetworking.canSend(AnvilInputPayload.TYPE)) {
			lastPress = -100;
			steering = false;
			return;
		}
		// Counting clicks (rather than watching the key) catches a click shorter than a tick.
		while (mc.options.keyAttack.consumeClick()) {
			if (mc.player.isShiftKeyDown()) {
				send(AnvilInputPayload.BLAST_CYCLE);
				AnvilInput.blastRestart = mc.player.getTicksUsingItem();
				lastPress = -100;
			} else if (clock - lastPress <= DOUBLE) {
				send(AnvilInputPayload.BLAST_STEER);
				steering = true;
				lastPress = -100;
			} else {
				send(AnvilInputPayload.BLAST_LAUNCH);
				steering = false;
				lastPress = clock;
			}
		}
		if (steering) {
			if (mc.options.keyAttack.isDown()) {
				send(AnvilInputPayload.BLAST_STEER_HOLD);
			} else {
				send(AnvilInputPayload.BLAST_STEER_STOP);
				steering = false;
			}
		}
	}

	private static void send(int action) {
		ClientPlayNetworking.send(new AnvilInputPayload(action));
	}
}
