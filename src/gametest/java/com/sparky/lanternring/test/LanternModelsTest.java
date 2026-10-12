package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.world.InteractionHand;

/** The mesh-built corps lanterns (Blue, Violet, Orange): held with their ring, then placed, by day and by night. */
public class LanternModelsTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			for (Corps corps : new Corps[] {Corps.BLUE, Corps.VIOLET, Corps.ORANGE}) {
				String name = corps.getSerializedName();
				world.getServer().runOnServer(server -> {
					var p = server.getPlayerList().getPlayers().get(0);
					p.setItemInHand(InteractionHand.MAIN_HAND, corps.ring());
					p.setItemInHand(InteractionHand.OFF_HAND, corps.lantern());
				});
				world.getServer().runCommand("execute at @p run tp @p ~ ~ ~ 180 0");
				ctx.getInput().lookAt(180f, 5f);
				ctx.waitTicks(30);
				ctx.takeScreenshot("lantern_model_" + name + "_held");
				world.getServer().runCommand("execute at @p run fill ~-2 ~ ~-3 ~2 ~2 ~-1 air");
				world.getServer().runCommand("execute at @p run setblock ~ ~ ~-2 lanternring:power_battery[corps=" + name + "]");
				world.getServer().runOnServer(server -> server.getPlayerList().getPlayers().get(0).setItemInHand(InteractionHand.OFF_HAND, net.minecraft.world.item.ItemStack.EMPTY));
				ctx.getInput().lookAt(180f, 38f);
				ctx.waitTicks(20);
				ctx.takeScreenshot("lantern_model_" + name + "_placed");
				world.getServer().runCommand("time set 18000");
				ctx.waitTicks(10);
				ctx.takeScreenshot("lantern_model_" + name + "_placed_night");
				world.getServer().runCommand("time set 6000");
				world.getServer().runCommand("execute at @p run setblock ~ ~ ~-2 air");
			}
		}
	}
}
