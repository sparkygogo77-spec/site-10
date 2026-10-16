package com.sparky.lanternring.test;

import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingMode;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;

/**
 * J (2026-10-16): "the dome should not continue under ground". Held next to a pit and looking down into it, the Dome
 * builds nothing below the player's feet.
 */
public class DomeAboveGroundTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			// Clear the air above and dig a pit in front of the player.
			world.getServer().runCommand("execute at @p run fill ~-12 ~ ~-12 ~12 ~12 ~12 air");
			world.getServer().runCommand("execute at @p run fill ~-6 ~-1 ~2 ~6 ~-6 ~9 air");
			ctx.waitTicks(60);
			world.getServer().runOnServer(server -> player(server).getMainHandItem().set(ModComponents.MODE, RingMode.DOME.ordinal()));
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(0f, 40f);
			ctx.waitTicks(10);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(15);
			ctx.takeScreenshot("dome_above_ground");
			int[] counts = world.getServer().computeOnServer(server -> {
				ServerPlayer p = player(server);
				BlockPos c = p.blockPosition();
				int above = 0, below = 0;
				for (BlockPos pos : BlockPos.betweenClosed(c.offset(-9, -9, -9), c.offset(9, 10, 9))) {
					if (!p.level().getBlockState(pos).is(ModRegistry.LIGHT_CONSTRUCT)) continue;
					if (pos.getY() < c.getY()) below++;
					else above++;
				}
				return new int[] {above, below};
			});
			ctx.getInput().releaseKey(o -> o.keyUse);
			System.out.println("[dome-above-ground] above=" + counts[0] + " below=" + counts[1]);
			if (counts[0] < 10) throw new AssertionError("The dome should still stand above the ground, found " + counts[0] + " blocks");
			if (counts[1] > 0) throw new AssertionError("The dome ran " + counts[1] + " blocks down below the player's feet");
		}
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
