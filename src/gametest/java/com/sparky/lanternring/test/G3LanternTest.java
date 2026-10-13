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

/**
 * The Dark Lantern's G3 R4 charge (J's pick from Blender): the ring seating in the port, the light
 * spreading from it through the 12 s charge, then the climax, the let-go flash and the slow fade.
 */
public class G3LanternTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> com.sparky.lanternring.client.LabSettings.get().lanternModel = com.sparky.lanternring.client.LabSettings.LanternModel.DARK);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = player(server);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.GREEN.ring());
				p.setItemInHand(InteractionHand.OFF_HAND, Corps.GREEN.lantern());
				PowerRingItem.setCharge(p.getMainHandItem(), 10);
			});
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 15f);
			ctx.waitTicks(30);
			// At rest the glass never goes fully dark, and a low light moves with you.
			ctx.takeScreenshot("g3_idle");

			int seat = LanternCharge.hold() + LanternCharge.reach();
			int span = LanternCharge.done() - seat;
			ctx.getInput().holdKey(o -> o.keyAttack);
			ctx.waitTicks(1);
			ctx.getInput().holdKey(o -> o.keyUse);
			int[] at = {seat - 6, seat + 2, seat + 20, seat + 60, seat + span / 4, seat + span / 2, seat + 3 * span / 4, LanternCharge.done() - 2};
			for (int i = 0; i < at.length; i++) {
				waitHeld(ctx, at[i]);
				ctx.takeScreenshot(String.format("g3_charge_%02d", i));
			}
			waitHeld(ctx, LanternCharge.done() + 1);
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.getInput().releaseKey(o -> o.keyAttack);
			// The afterglow: the climax, the let-go flash and the slow fade.
			int[] after = {18, 40, 72, 110, 160, 210};
			int waited = 1;
			for (int i = 0; i < after.length; i++) {
				ctx.waitTicks(after[i] - waited);
				waited = after[i];
				ctx.takeScreenshot(String.format("g3_after_%02d", i));
			}
		}
	}

	private static void waitHeld(ClientGameTestContext ctx, int ticks) {
		for (int i = 0; i < 600; i++) {
			int held = ctx.computeOnClient(mc -> mc.player.isUsingItem() ? 72000 - mc.player.getUseItemRemainingTicks() : -1);
			if (held >= ticks) return;
			ctx.waitTicks(1);
		}
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
