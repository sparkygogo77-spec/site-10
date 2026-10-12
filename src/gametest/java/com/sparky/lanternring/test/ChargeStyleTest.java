package com.sparky.lanternring.test;

import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;

/** Photographs each lantern charge style at rest and with the ring docked mid-charge. */
public class ChargeStyleTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 13000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			world.getServer().runCommand("item replace entity @a weapon.offhand with lanternring:power_battery");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			LabSettings.get().lanternModel = LabSettings.LanternModel.CLASSIC;
			for (LabSettings.ChargeStyle style : System.getenv("STYLE_ONLY") != null
					? new LabSettings.ChargeStyle[] {LabSettings.ChargeStyle.valueOf(System.getenv("STYLE_ONLY"))} : LabSettings.ChargeStyle.values()) {
				LabSettings.get().chargeStyle = style;
				ctx.getInput().lookAt(0f, 10f);
				ctx.waitTicks(LanternCharge.DEPLETE + 10);
				String name = style.name().toLowerCase();
				ctx.takeScreenshot("style_" + name + "_rest");
				ctx.getInput().holdKey(o -> o.keyAttack);
				ctx.waitTicks(1);
				ctx.getInput().holdKey(o -> o.keyUse);
				ctx.waitTicks(LanternCharge.hold() + LanternCharge.REACH + 10);
				ctx.takeScreenshot("style_" + name + "_docked");
				ctx.getInput().releaseKey(o -> o.keyUse);
				ctx.getInput().releaseKey(o -> o.keyAttack);
			}
			LabSettings.get().chargeStyle = LabSettings.ChargeStyle.HAND;
		}
	}
}
