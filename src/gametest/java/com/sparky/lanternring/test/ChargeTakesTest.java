package com.sparky.lanternring.test;

import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;

/**
 * J's charge takes on the Dark Lantern: L1c (the fist driven into the port of the lantern on its block) and K3c (one
 * knee down, lift it to the chest). Third person from the side (the body stays square on to the lantern while the
 * camera turns), and L1c in first person; the light running down the glass shows as the charge rises.
 */
public class ChargeTakesTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 13000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			world.getServer().runCommand("item replace entity @a weapon.offhand with lanternring:power_battery");
			ctx.waitTicks(60);
			LabSettings.get().lanternModel = LabSettings.LanternModel.DARK;
			int hold = LanternCharge.hold(), seat = hold + LanternCharge.reach(), done = LanternCharge.done();

			// J's pick: the lantern stands on the real block in front of you.
			world.getServer().runCommand("execute as @p at @s align xyz run tp @s ~0.5 ~ ~0.5 0 0");
			world.getServer().runCommand("execute at @p run setblock ~ ~ ~1 minecraft:polished_andesite");
			ctx.waitTicks(5);
			LabSettings.get().chargeStyle = LabSettings.ChargeStyle.PUSH;
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			start(ctx, 0f);
			// Turn the camera to the side once the lantern is down: the body stays square on to it.
			ctx.waitTicks(4);
			ctx.runOnClient(mc -> mc.player.setYRot(-90f));
			ctx.waitTicks(seat - 4 + (done - seat) / 4);
			ctx.takeScreenshot("take_l1c_side_push1");
			ctx.waitTicks((done - seat) / 4);
			ctx.takeScreenshot("take_l1c_side_half");
			ctx.waitTicks((done - seat) / 2 - 10);
			ctx.takeScreenshot("take_l1c_side_full");
			stop(ctx);

			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			start(ctx, 15f);
			ctx.waitTicks(seat + (done - seat) * 2 / 3);
			ctx.takeScreenshot("take_l1c_first_person");
			stop(ctx);

			world.getServer().runCommand("execute at @p run setblock ~ ~ ~1 minecraft:air");
			LabSettings.get().chargeStyle = LabSettings.ChargeStyle.KNEEL;
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			start(ctx, 0f);
			ctx.waitTicks(4);
			ctx.runOnClient(mc -> mc.player.setYRot(-90f));
			ctx.waitTicks(seat - 4 - 6);
			ctx.takeScreenshot("take_k3c_side_grab");
			ctx.waitTicks(26);
			ctx.takeScreenshot("take_k3c_side_lifted");
			ctx.waitTicks(done - seat - 20 + 2);
			stop(ctx);
			ctx.waitTicks(12);
			ctx.takeScreenshot("take_k3c_side_standing");

			LabSettings.get().chargeStyle = LabSettings.ChargeStyle.HAND;
		}
	}

	private static void start(ClientGameTestContext ctx, float pitch) {
		ctx.runOnClient(mc -> {
			mc.player.setYRot(0f);
			mc.player.setXRot(pitch);
		});
		ctx.waitTicks(LanternCharge.DEPLETE + 10);
		ctx.getInput().holdKey(o -> o.keyAttack);
		ctx.waitTicks(1);
		ctx.getInput().holdKey(o -> o.keyUse);
	}

	private static void stop(ClientGameTestContext ctx) {
		ctx.getInput().releaseKey(o -> o.keyUse);
		ctx.getInput().releaseKey(o -> o.keyAttack);
	}
}
