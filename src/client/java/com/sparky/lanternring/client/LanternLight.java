package com.sparky.lanternring.client;

import com.sparky.lanternring.ModRegistry;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LightBlock;
import net.minecraft.world.level.block.state.BlockState;

/**
 * J: the lantern always gives off a low light. While you carry a Power Battery a level-6 light
 * moves with you: an invisible light block placed only in your own client's world, in the air
 * where your head is, and taken away again as you move on or put the lantern away. The server
 * never sees it, so nothing in the world changes.
 */
public final class LanternLight {
	/** The light level round you while you carry a lantern. */
	public static final int LEVEL = 6;
	private static BlockPos placed;
	private static ClientLevel placedIn;

	private LanternLight() {
	}

	public static void tick(Minecraft mc) {
		LocalPlayer player = mc.player;
		BlockPos want = null;
		if (player != null && mc.level != null && !player.isSpectator()
				&& (player.getOffhandItem().is(ModRegistry.POWER_BATTERY_ITEM) || player.getMainHandItem().is(ModRegistry.POWER_BATTERY_ITEM))) {
			BlockPos head = BlockPos.containing(player.getEyePosition());
			if (head.equals(placed) && mc.level == placedIn) return;
			if (mc.level.getBlockState(head).isAir()) want = head;
		}
		if (want != null && want.equals(placed) && mc.level == placedIn) return;
		clear();
		if (want != null) {
			mc.level.setBlock(want, Blocks.LIGHT.defaultBlockState().setValue(LightBlock.LEVEL, LEVEL), 3);
			placed = want;
			placedIn = mc.level;
		}
	}

	/** Takes our light away again (only if it's still ours: the server may have put something there). */
	private static void clear() {
		if (placed != null && placedIn != null && placedIn == Minecraft.getInstance().level) {
			BlockState there = placedIn.getBlockState(placed);
			if (there.is(Blocks.LIGHT)) placedIn.setBlock(placed, Blocks.AIR.defaultBlockState(), 3);
		}
		placed = null;
		placedIn = null;
	}
}
