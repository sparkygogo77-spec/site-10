package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.world.InteractionHand;

/**
 * The mesh-built lanterns (the Nebula with its solid light for Green, then Blue, Violet, Orange): held
 * with their ring (the Nebula also mid-charge), then placed, by day and by night.
 */
public class LanternModelsTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			LabSettings.get().lanternModel = LabSettings.LanternModel.NEBULA;
			for (Corps corps : new Corps[] {Corps.GREEN, Corps.BLUE, Corps.VIOLET, Corps.ORANGE}) {
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
				if (corps == Corps.GREEN) {
					ctx.getInput().holdKey(o -> o.keyAttack);
					ctx.waitTicks(1);
					ctx.getInput().holdKey(o -> o.keyUse);
					for (int i = 1; i <= 2; i++) {
						ctx.waitTicks(LanternCharge.done() * 2 / 5);
						ctx.takeScreenshot("lantern_model_" + name + "_charge_" + i);
					}
					ctx.getInput().releaseKey(o -> o.keyUse);
					ctx.getInput().releaseKey(o -> o.keyAttack);
					ctx.waitTicks(40);
				}
				world.getServer().runCommand("execute at @p run fill ~-2 ~ ~-3 ~2 ~2 ~-1 air");
				world.getServer().runCommand("execute at @p run setblock ~ ~ ~-2 lanternring:power_battery[corps=" + name
						+ (corps == Corps.GREEN ? ",style=nebula" : "") + "]");
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
