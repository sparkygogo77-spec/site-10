package com.sparky.lanternring.test;

import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;

/** The Shoulder lean charge style (J's L3): first person docked, then the lean and the push from behind and in front. */
public class LeanChargeTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set noon");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			world.getServer().runCommand("item replace entity @a weapon.offhand with lanternring:power_battery");
			ctx.waitTicks(60);
			LabSettings.get().lanternModel = LabSettings.LanternModel.CLASSIC;
			LabSettings.get().chargeStyle = LabSettings.ChargeStyle.LEAN;
			CameraType[] views = {CameraType.FIRST_PERSON, CameraType.THIRD_PERSON_BACK, CameraType.THIRD_PERSON_FRONT};
			for (CameraType view : views) {
				ctx.runOnClient(mc -> mc.options.setCameraType(view));
				ctx.getInput().lookAt(0f, 10f);
				ctx.waitTicks(LanternCharge.DEPLETE + 10);
				String name = view.name().toLowerCase();
				ctx.getInput().holdKey(o -> o.keyAttack);
				ctx.waitTicks(1);
				ctx.getInput().holdKey(o -> o.keyUse);
				int span = LanternCharge.done() - LanternCharge.hold();
				ctx.waitTicks(LanternCharge.hold() + span / 6);
				ctx.takeScreenshot("lean_" + name + "_lean");
				ctx.waitTicks(span / 3);
				ctx.takeScreenshot("lean_" + name + "_push");
				ctx.getInput().releaseKey(o -> o.keyUse);
				ctx.getInput().releaseKey(o -> o.keyAttack);
			}
			LabSettings.get().chargeStyle = LabSettings.ChargeStyle.HAND;
		}
	}
}
