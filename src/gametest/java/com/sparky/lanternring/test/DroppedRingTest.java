package com.sparky.lanternring.test;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;

/** A dropped ring is the real 3D ring, glowing and lighting the floor of a dark room (DroppedRingRenderer, DroppedRingLight). */
public class DroppedRingTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			// A sealed stone room: no sky or torch light, only the ring's own.
			world.getServer().runCommand("execute at @p run tp @p ~ ~ ~ 180 0");
			world.getServer().runCommand("execute at @p run fill ~-4 ~-1 ~-6 ~4 ~4 ~2 minecraft:stone");
			world.getServer().runCommand("execute at @p run fill ~-3 ~ ~-5 ~3 ~3 ~1 air");
			world.getServer().runCommand("execute at @p run summon item ~ ~ ~-3 {Item:{id:\"lanternring:power_ring\",count:1},PickupDelay:32767}");
			world.getServer().runCommand("execute at @p run summon item ~2 ~ ~-4 {Item:{id:\"lanternring:power_ring\",count:1,components:{\"lanternring:corps\":\"blue\"}},PickupDelay:32767}");
			ctx.getInput().lookAt(180f, 35f);
			ctx.waitTicks(40);
			ctx.takeScreenshot("dropped_ring_dark");
			ctx.waitTicks(25);
			ctx.takeScreenshot("dropped_ring_dark_turned");
			world.getServer().runCommand("execute at @p run tp @p ~ ~ ~-1.8 180 60");
			ctx.waitTicks(10);
			ctx.takeScreenshot("dropped_ring_close");
		}
	}
}
