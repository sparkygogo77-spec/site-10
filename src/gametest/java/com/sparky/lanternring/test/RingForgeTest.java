package com.sparky.lanternring.test;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;

/**
 * Photographs the Ring Forge placed (day, night, from the side and above) and held, then forges a
 * ring from an emerald block with a Power Battery beside it.
 */
public class RingForgeTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("execute at @p run tp @p ~ ~ ~ 0 0");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:ring_forge");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			world.getServer().runCommand("execute at @p run fill ~-4 ~ ~1 ~4 ~5 ~8 air");
			world.getServer().runCommand("execute at @p run setblock ~ ~ ~3 lanternring:ring_forge");
			world.getServer().runCommand("execute at @p run summon minecraft:marker ~ ~ ~ {Tags:[\"start\"]}");
			world.getServer().runCommand("execute at @p run setblock ~2 ~ ~3 lanternring:power_battery");
			ctx.getInput().lookAt(0f, 25f);
			ctx.waitTicks(20);
			ctx.takeScreenshot("forge_front");
			ctx.getInput().lookAt(0f, 5f);
			ctx.waitTicks(5);
			ctx.takeScreenshot("forge_held");
			world.getServer().runCommand("time set 18000");
			ctx.getInput().lookAt(0f, 25f);
			ctx.waitTicks(10);
			ctx.takeScreenshot("forge_night");
			world.getServer().runCommand("time set 6000");
			// From the side: the emblem turns to follow.
			world.getServer().runCommand("execute at @p run tp @p ~3 ~ ~3 90 20");
			ctx.waitTicks(10);
			ctx.takeScreenshot("forge_side");
			world.getServer().runCommand("execute at @p run tp @p ~-3 ~2 ~-3 0 45");
			ctx.waitTicks(10);
			ctx.takeScreenshot("forge_above");
			// Forge a ring.
			world.getServer().runCommand("execute at @e[tag=start] run tp @p ~ ~ ~1 0 30");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with minecraft:emerald_block");
			ctx.waitTicks(10);
			ctx.takeScreenshot("forge_before_forging");
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(6);
			ctx.takeScreenshot("forge_forging");
		}
	}
}
