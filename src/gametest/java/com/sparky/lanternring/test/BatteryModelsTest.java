package com.sparky.lanternring.test;

import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;

/**
 * Photographs each Power Battery look: held in the off hand by day and night, and as dropped items
 * and item frames turned to show the front, side and back.
 */
public class BatteryModelsTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			world.getServer().runCommand("item replace entity @a weapon.offhand with lanternring:power_battery");
			world.getServer().runCommand("execute at @p run tp @p ~ ~ ~ 0 0");
			ctx.waitTicks(60);
			LabSettings lab = LabSettings.get();
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));

			// A wall of item frames close in front: front, side and back views.
			world.getServer().runCommand("execute at @p run fill ~-4 ~ ~1 ~4 ~4 ~4 air");
			world.getServer().runCommand("execute at @p run fill ~-4 ~ ~3 ~4 ~3 ~3 minecraft:smooth_stone");
			for (int i = 0; i < 3; i++) {
				world.getServer().runCommand("execute at @p run summon minecraft:item_frame ~" + (i - 1) + " ~1 ~2 {Facing:2,Fixed:1b,ItemRotation:" + (i * 2)
						+ ",Item:{id:\"lanternring:power_battery\",count:1}}");
			}
			for (LabSettings.LanternModel model : LabSettings.LanternModel.values()) {
				lab.lanternModel = model;
				String n = model.name().toLowerCase();
				world.getServer().runCommand("time set 6000");
				ctx.getInput().lookAt(0f, 20f);
				ctx.waitTicks(10);
				ctx.takeScreenshot("battery_" + n + "_frames");
				ctx.getInput().lookAt(0f, -10f);
				ctx.waitTicks(10);
				ctx.takeScreenshot("battery_" + n + "_held");
				world.getServer().runCommand("time set 18000");
				ctx.waitTicks(5);
				ctx.takeScreenshot("battery_" + n + "_held_night");
			}
		}
	}
}
