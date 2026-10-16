package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.client.LabSettings;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;

/**
 * The Red battery against the Dark Lantern in the same first-person charge (J, 2026-10-16: "red lantern
 * still huge"), carried at the hip as J picks, at rest and at the charge's peak, by a diamond block.
 */
public class RedSizeTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			world.getServer().runCommand("execute at @p run tp @p ~ ~ ~ 0 0");
			world.getServer().runCommand("execute at @p run fill ~-3 ~ ~1 ~3 ~3 ~6 air");
			world.getServer().runCommand("execute at @p run fill ~-1 ~ ~4 ~1 ~1 ~4 diamond_block");
			ctx.runOnClient(mc -> {
				mc.options.setCameraType(CameraType.FIRST_PERSON);
				LabSettings.get().redLantern = LabSettings.RedLantern.NEW;
				LabSettings.get().chargeStyle = LabSettings.ChargeStyle.LEAN;
			});
			for (Corps corps : new Corps[] {Corps.GREEN, Corps.RED}) {
				String name = corps == Corps.RED ? "red" : "dark";
				world.getServer().runOnServer(server -> {
					ServerPlayer p = player(server);
					p.setItemInHand(InteractionHand.MAIN_HAND, corps.ring());
					p.setItemInHand(InteractionHand.OFF_HAND, corps.lantern());
					PowerRingItem.setCharge(p.getMainHandItem(), 50);
				});
				ctx.getInput().lookAt(0f, 10f);
				ctx.waitTicks(40);
				ctx.getInput().holdKey(o -> o.keyAttack);
				ctx.waitTicks(1);
				ctx.getInput().holdKey(o -> o.keyUse);
				ctx.waitTicks(LanternCharge.hold() + LanternCharge.reach() + (LanternCharge.charge() - LanternCharge.reach()) / 2);
				ctx.takeScreenshot("size_" + name + "_charging");
				ctx.getInput().releaseKey(o -> o.keyUse);
				ctx.getInput().releaseKey(o -> o.keyAttack);
				ctx.waitTicks(LanternCharge.DEPLETE + 60);
			}
		}
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
