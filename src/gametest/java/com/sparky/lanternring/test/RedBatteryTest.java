package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.client.LabSettings;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;

/**
 * The Red corps' final battery from Blender: held (its cover crumbling as the charge builds), placed,
 * the Ring Lab's Classic pick, and the Rage Bull in J's Red construct looks (R1 magma, R2 bloodfire).
 */
public class RedBatteryTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> LabSettings.get().redLantern = LabSettings.RedLantern.NEW);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = player(server);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.RED.ring());
				p.setItemInHand(InteractionHand.OFF_HAND, Corps.RED.lantern());
			});
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			world.getServer().runOnServer(server -> PowerRingItem.setCharge(player(server).getMainHandItem(), 100));
			ctx.getInput().lookAt(0f, 15f);
			ctx.waitTicks(30);
			ctx.takeScreenshot("red_battery_held");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("red_battery_held_night");

			ctx.getInput().holdKey(o -> o.keyAttack);
			ctx.waitTicks(1);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(LanternCharge.hold() + LanternCharge.reach());
			ctx.takeScreenshot("red_battery_charge_0");
			int build = LanternCharge.charge() - LanternCharge.reach();
			ctx.waitTicks(build / 4);
			ctx.takeScreenshot("red_battery_charge_25");
			ctx.waitTicks(build / 4);
			ctx.takeScreenshot("red_battery_charge_50");
			ctx.waitTicks(build / 2 - 14);
			ctx.takeScreenshot("red_battery_charge_peak");
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.getInput().releaseKey(o -> o.keyAttack);
			ctx.waitTicks(40);
			ctx.takeScreenshot("red_battery_after");
			ctx.waitTicks(LanternCharge.DEPLETE + 10);

			ctx.runOnClient(mc -> LabSettings.get().redLantern = LabSettings.RedLantern.CLASSIC);
			ctx.waitTicks(5);
			ctx.takeScreenshot("red_battery_classic_pick");
			ctx.runOnClient(mc -> LabSettings.get().redLantern = LabSettings.RedLantern.NEW);

			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("execute at @p run tp @p ~ ~ ~ 180 0");
			world.getServer().runCommand("execute at @p run fill ~-3 ~ ~-4 ~3 ~3 ~-1 air");
			world.getServer().runCommand("execute at @p run setblock ~-1 ~ ~-3 lanternring:power_battery[corps=red,style=stone]");
			world.getServer().runCommand("execute at @p run setblock ~1 ~ ~-3 lanternring:power_battery[corps=red,style=classic]");
			world.getServer().runOnServer(server -> player(server).setItemInHand(InteractionHand.OFF_HAND, ItemStack.EMPTY));
			ctx.getInput().lookAt(180f, 20f);
			ctx.waitTicks(20);
			ctx.takeScreenshot("red_battery_placed");

			// The Rage Bull in each Red look, side on.
			RingTuning.RAGE_BULL_RUN.set(12);
			for (LabSettings.RedLook look : new LabSettings.RedLook[] {LabSettings.RedLook.R1, LabSettings.RedLook.R2}) {
				ctx.runOnClient(mc -> LabSettings.get().redLook = look);
				world.getServer().runCommand("kill @e[type=!player]");
				world.getServer().runOnServer(server -> {
					ServerPlayer p = player(server);
					var ring = Corps.RED.ring();
					ring.set(ModComponents.MODE, RingMode.BLAST.ordinal());
					ring.set(ModComponents.BLAST_LEVEL, 4);
					p.setItemInHand(InteractionHand.MAIN_HAND, ring);
				});
				world.getServer().runCommand("execute at @p run fill ~-30 ~ ~-30 ~30 ~12 ~30 air");
				world.getServer().runCommand("execute at @p run tp @p ~ ~ ~ -90 0");
				ctx.getInput().lookAt(-90f, 0f);
				ctx.waitTicks(10);
				ctx.getInput().holdKey(k -> k.keyUse);
				ctx.waitTicks(5);
				ctx.getInput().releaseKey(k -> k.keyUse);
				ctx.waitTicks(3);
				world.getServer().runCommand("execute at @p run tp @p ~ ~ ~-24 0 0");
				ctx.getInput().lookAt(0f, -8f);
				ctx.waitTicks(10);
				ctx.takeScreenshot("rage_bull_" + look.name().toLowerCase());
				ctx.waitTicks(150);
			}
		}
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
