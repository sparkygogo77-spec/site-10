package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;

/** The pixel-grid Dark Lantern (the green ring's lantern with the Dark look): held, charging, placed. */
public class DarkLanternTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> com.sparky.lanternring.client.LabSettings.get().lanternModel = com.sparky.lanternring.client.LabSettings.LanternModel.DARK);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = player(server);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.GREEN.ring());
				p.setItemInHand(InteractionHand.OFF_HAND, Corps.GREEN.lantern());
			});
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			world.getServer().runOnServer(server -> PowerRingItem.setCharge(player(server).getMainHandItem(), 100));
			ctx.getInput().lookAt(0f, 15f);
			ctx.waitTicks(30);
			ctx.takeScreenshot("dark_lantern_held_day");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("dark_lantern_held_night");

			ctx.getInput().holdKey(o -> o.keyAttack);
			ctx.waitTicks(1);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(LanternCharge.hold() + LanternCharge.REACH);
			ctx.takeScreenshot("dark_lantern_charge_0");
			int build = LanternCharge.charge() - LanternCharge.REACH;
			ctx.waitTicks(build / 3);
			ctx.takeScreenshot("dark_lantern_charge_33");
			ctx.waitTicks(build / 3);
			ctx.takeScreenshot("dark_lantern_charge_66");
			ctx.waitTicks(build - 2 * (build / 3) - 14);
			ctx.takeScreenshot("dark_lantern_charge_peak");
			ctx.waitTicks(1);
			ctx.takeScreenshot("dark_lantern_charge_flash");
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.getInput().releaseKey(o -> o.keyAttack);
			ctx.waitTicks(20);
			ctx.takeScreenshot("dark_lantern_after");
			ctx.waitTicks(LanternCharge.DEPLETE + 10);

			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("execute at @p run tp @p ~ ~ ~ 180 0");
			world.getServer().runCommand("execute at @p run fill ~-2 ~ ~-4 ~2 ~3 ~-1 air");
			world.getServer().runCommand("execute at @p run setblock ~ ~ ~-3 minecraft:stone_bricks");
			world.getServer().runCommand("execute at @p run setblock ~ ~1 ~-3 lanternring:power_battery[corps=green,style=dark]");
			world.getServer().runOnServer(server -> player(server).setItemInHand(InteractionHand.OFF_HAND, ItemStack.EMPTY));
			ctx.getInput().lookAt(180f, 12f);
			ctx.waitTicks(20);
			ctx.takeScreenshot("dark_lantern_placed_day");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("dark_lantern_placed_night");
		}
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
