package com.sparky.lanternring.test;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;

/**
 * Photographs the Great Power Battery and the Lava Font (dry, then filled by pouring a lava
 * bucket in), by day and night, with the Ring Forge for scale.
 */
public class BigBatteryTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("execute at @p run tp @p ~ ~ ~ 0 0");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			world.getServer().runCommand("execute at @p run fill ~-4 ~ ~1 ~4 ~5 ~8 air");
			world.getServer().runCommand("execute at @p run setblock ~-1 ~ ~3 lanternring:great_battery");
			world.getServer().runCommand("execute at @p run setblock ~1 ~ ~3 lanternring:lava_font");
			world.getServer().runCommand("execute at @p run setblock ~3 ~ ~4 lanternring:ring_forge");
			world.getServer().runCommand("execute at @p run summon minecraft:item ~-3 ~ ~2 {Item:{id:\"lanternring:lava_font\",count:1},PickupDelay:32767,Age:-32768}");
			ctx.getInput().lookAt(0f, 30f);
			ctx.waitTicks(20);
			ctx.takeScreenshot("big_battery_dry");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with minecraft:lava_bucket");
			ctx.getInput().lookAt(-23f, 11f);
			ctx.waitTicks(5);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(10);
			ctx.getInput().lookAt(0f, 30f);
			ctx.waitTicks(5);
			ctx.takeScreenshot("big_battery_filled");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("big_battery_night");
			world.getServer().runCommand("execute at @p run tp @p ~ ~1 ~1 0 60");
			ctx.waitTicks(10);
			ctx.takeScreenshot("big_battery_above");
		}
	}
}
