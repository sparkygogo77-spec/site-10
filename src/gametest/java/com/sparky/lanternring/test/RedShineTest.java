package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;

/**
 * The Red battery's re-baked crimson stone (J, 2026-10-15: "shine like these diamond blocks"),
 * held in first person next to diamond blocks, by day and by night, and placed beside one.
 */
public class RedShineTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> {
				LabSettings.get().redLantern = LabSettings.RedLantern.NEW;
				LabSettings.get().chargeStyle = LabSettings.ChargeStyle.HAND;
			});
			world.getServer().runCommand("execute at @p run tp @p ~ ~ ~ 0 0");
			world.getServer().runCommand("execute at @p run fill ~-3 ~ ~1 ~3 ~3 ~5 air");
			world.getServer().runCommand("execute at @p run fill ~-2 ~ ~3 ~2 ~ ~3 diamond_block");
			world.getServer().runCommand("execute at @p run fill ~-2 ~1 ~3 ~2 ~1 ~3 diamond_block");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.RED.ring());
				p.setItemInHand(InteractionHand.OFF_HAND, Corps.RED.lantern());
			});
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 10f);
			ctx.waitTicks(60);
			ctx.takeScreenshot("red_shine_held");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("red_shine_held_night");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("execute at @p run setblock ~ ~ ~2 lanternring:power_battery[corps=red,style=stone]");
			world.getServer().runOnServer(server -> server.getPlayerList().getPlayers().get(0).setItemInHand(InteractionHand.OFF_HAND, net.minecraft.world.item.ItemStack.EMPTY));
			ctx.getInput().lookAt(0f, 30f);
			ctx.waitTicks(20);
			ctx.takeScreenshot("red_shine_placed");
		}
	}
}
