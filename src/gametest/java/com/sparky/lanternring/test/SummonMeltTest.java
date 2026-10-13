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

/** The summoned lantern after a charge: it breaks into construct matter and melts away (J), never shrinks. */
public class SummonMeltTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> com.sparky.lanternring.client.LabSettings.get().chargeStyle = com.sparky.lanternring.client.LabSettings.ChargeStyle.SUMMON);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.GREEN.ring());
				p.setItemInHand(InteractionHand.OFF_HAND, Corps.GREEN.lantern());
				PowerRingItem.setCharge(p.getMainHandItem(), 100);
			});
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 15f);
			ctx.waitTicks(20);
			ctx.getInput().holdKey(o -> o.keyAttack);
			ctx.waitTicks(1);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(LanternCharge.done() + 2);
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.getInput().releaseKey(o -> o.keyAttack);
			for (int i = 0; i < 6; i++) {
				ctx.takeScreenshot("summon_melt_" + i);
				ctx.waitTicks(LanternCharge.SETTLE / 2);
			}
		}
	}
}
