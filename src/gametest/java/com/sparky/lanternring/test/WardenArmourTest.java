package com.sparky.lanternring.test;

import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;

/**
 * Blender pass 838 R4b: the Warden construct as the real warden under W1 weave plate armour. A still warden (no AI) seen
 * forming, then from the front and the side, and the hard-light SKIN look for comparison.
 */
public class WardenArmourTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			var server = world.getServer();
			server.runCommand("gamemode creative @a");
			server.runCommand("gamerule doDaylightCycle false");
			server.runCommand("gamerule doMobSpawning false");
			server.runCommand("time set 6000");
			ctx.waitTicks(60);
			server.runCommand("execute at @p run fill ~-12 ~-1 ~-12 ~12 ~-1 ~12 grass_block");
			server.runCommand("execute at @p run fill ~-12 ~ ~-12 ~12 ~12 ~12 air");
			server.runCommand("kill @e[type=!player]");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.runOnClient(mc -> LabSettings.get().constructWarden = LabSettings.ConstructWarden.R4B);
			// Facing the player (who looks along +Z), 6 blocks ahead.
			server.runCommand("execute at @p run summon lanternring:warden_construct ~ ~ ~6 {NoAI:1b,Rotation:[180f,0f]}");
			ctx.getInput().lookAt(0f, 10f);
			ctx.waitTicks(10);
			ctx.takeScreenshot("warden_armour_forming");
			ctx.waitTicks(30);
			ctx.takeScreenshot("warden_armour_front");
			// From the side: stand off to the left, looking across at it.
			server.runCommand("execute at @e[type=lanternring:warden_construct,limit=1] run tp @p ~-6 ~ ~ -90 10");
			ctx.waitTicks(5);
			ctx.takeScreenshot("warden_armour_side");
			ctx.runOnClient(mc -> LabSettings.get().constructWarden = LabSettings.ConstructWarden.SKIN);
			ctx.waitTicks(3);
			ctx.takeScreenshot("warden_skin_side");
			ctx.runOnClient(mc -> LabSettings.get().constructWarden = LabSettings.ConstructWarden.R4B);
		}
	}
}
