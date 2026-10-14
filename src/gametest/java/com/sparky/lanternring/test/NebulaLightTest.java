package com.sparky.lanternring.test;

import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;

/**
 * The Nebula battery's light wrapped in the green construct look (J's picks L1 Column and L4 Core &amp;
 * cage, 2026-10-14): held by day and night, mid-charge, in a second look, and placed.
 */
public class NebulaLightTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			world.getServer().runCommand("item replace entity @a weapon.offhand with lanternring:power_battery");
			world.getServer().runCommand("execute at @p run tp @p ~ ~ ~ 180 0");
			ctx.waitTicks(60);
			LabSettings lab = LabSettings.get();
			lab.lanternModel = LabSettings.LanternModel.NEBULA;
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			for (LabSettings.NebulaLight take : LabSettings.NebulaLight.values()) {
				lab.nebulaLight = take;
				lab.constructLook = LabSettings.ConstructLook.W1_NEON;
				String n = take.name().toLowerCase();
				world.getServer().runCommand("time set 6000");
				ctx.getInput().lookAt(180f, 5f);
				ctx.waitTicks(20);
				ctx.takeScreenshot("nebula_" + n + "_held");
				world.getServer().runCommand("time set 18000");
				ctx.waitTicks(5);
				ctx.takeScreenshot("nebula_" + n + "_held_night");
				lab.constructLook = LabSettings.ConstructLook.X5_EMERALD;
				ctx.waitTicks(5);
				ctx.takeScreenshot("nebula_" + n + "_held_x5");
				lab.constructLook = LabSettings.ConstructLook.W1_NEON;
				ctx.getInput().holdKey(o -> o.keyAttack);
				ctx.waitTicks(1);
				ctx.getInput().holdKey(o -> o.keyUse);
				ctx.waitTicks(LanternCharge.done() * 3 / 4);
				ctx.takeScreenshot("nebula_" + n + "_charge");
				ctx.getInput().releaseKey(o -> o.keyUse);
				ctx.getInput().releaseKey(o -> o.keyAttack);
				ctx.waitTicks(60);
			}
			world.getServer().runCommand("item replace entity @a weapon.offhand with air");
			world.getServer().runCommand("execute at @p run fill ~-2 ~ ~-3 ~2 ~2 ~-1 air");
			world.getServer().runCommand("execute at @p run setblock ~ ~ ~-2 lanternring:power_battery[corps=green,style=nebula]");
			world.getServer().runCommand("time set 6000");
			ctx.getInput().lookAt(180f, 38f);
			ctx.waitTicks(20);
			ctx.takeScreenshot("nebula_placed");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("nebula_placed_night");
		}
	}
}
