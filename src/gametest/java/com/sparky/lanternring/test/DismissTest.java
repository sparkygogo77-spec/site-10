package com.sparky.lanternring.test;

import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingTuning;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;

/**
 * Letting go of a construct: the Lasso's bubble and the Dome come apart from their far side and
 * their light streams back into the ring. The dismissal is slowed down here so the frames catch it
 * half done; the Dome's blocks must go a few at a time, then all of them.
 */
public class DismissTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 18000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			world.getServer().runCommand("execute at @p run fill ~-20 ~ ~-20 ~20 ~12 ~20 air");
			ctx.waitTicks(60);
			RingTuning.DISMISS_TIME.set(1.2);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));

			// The Lasso: catch a pig, hold it a moment, let go without swinging.
			world.getServer().runCommand("execute at @p run summon minecraft:pig ~ ~ ~9 {NoAI:1b,NoGravity:1b}");
			mode(world, RingMode.TETHER);
			ctx.getInput().lookAt(0f, 8f);
			ctx.waitTicks(10);
			ctx.getInput().holdKey(o -> o.keyUse);
			// Let go before the reel brings it all the way in, so the bubble is still out in front.
			ctx.waitTicks(3);
			ctx.takeScreenshot("dismiss_lasso_held");
			ctx.getInput().releaseKey(o -> o.keyUse);
			for (int i = 0; i < 4; i++) {
				ctx.waitTicks(i == 0 ? 3 : 5);
				ctx.takeScreenshot("dismiss_lasso_" + i);
			}
			world.getServer().runCommand("kill @e[type=minecraft:pig]");

			// The Dome: hold it up, let go, count its blocks as it comes apart.
			mode(world, RingMode.DOME);
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(10);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(10);
			ctx.takeScreenshot("dismiss_dome_held");
			int held = domeBlocks(world);
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.waitTicks(10);
			ctx.takeScreenshot("dismiss_dome_half");
			int half = domeBlocks(world);
			ctx.waitTicks(30);
			ctx.takeScreenshot("dismiss_dome_gone");
			int gone = domeBlocks(world);
			System.out.println("[dismiss test] dome blocks held " + held + ", 10 ticks after letting go " + half + ", after " + gone);
			if (held == 0 || half == 0 || half >= held || gone != 0) {
				throw new AssertionError("Dome should come apart a few blocks at a time: " + held + " / " + half + " / " + gone);
			}
		}
	}

	private static int domeBlocks(TestSingleplayerContext world) {
		int[] n = {0};
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			BlockPos c = p.blockPosition();
			for (BlockPos pos : BlockPos.betweenClosed(c.offset(-9, -3, -9), c.offset(9, 10, 9))) {
				if (p.level().getBlockState(pos).is(ModRegistry.LIGHT_CONSTRUCT)) n[0]++;
			}
		});
		return n[0];
	}

	private static void mode(TestSingleplayerContext world, RingMode mode) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			p.getMainHandItem().set(ModComponents.MODE, mode.ordinal());
		});
	}
}
