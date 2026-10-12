package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;

/** The ring wearer's soft glint: on your own arm in first person, and over the body from the front, by day and night. */
public class RingAuraTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 18000");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.RED.ring());
			});
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 10f);
			ctx.waitTicks(60);
			ctx.takeScreenshot("aura_red_first_person_night");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.waitTicks(10);
			ctx.takeScreenshot("aura_red_front_night");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("aura_red_front_day");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.waitTicks(10);
			ctx.takeScreenshot("aura_red_first_person_day");
			world.getServer().runOnServer(server -> server.getPlayerList().getPlayers().get(0).setItemInHand(InteractionHand.MAIN_HAND, Corps.GREEN.ring()));
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.waitTicks(10);
			ctx.takeScreenshot("aura_green_front_day");
		}
	}
}
