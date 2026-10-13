package com.sparky.lanternring.test;

import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;

/** Photographs J's three signet rings on the knuckles-in fist, in first and third person. */
public class RingModelsTest implements FabricClientGameTest {
	private static final LabSettings.RingModel[] MODELS = {
			LabSettings.RingModel.FORGED, LabSettings.RingModel.CREST, LabSettings.RingModel.CREST_GOLD, LabSettings.RingModel.BEACON, LabSettings.RingModel.CROWN};

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(60);
			LabSettings lab = LabSettings.get();
			lab.handPose = LabSettings.HandPose.KNUCKLES_IN;
			lab.ringModel = LabSettings.RingModel.CREST;
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 15f);
			ctx.waitTicks(20);

			for (LabSettings.RingModel model : MODELS) {
				lab.ringModel = model;
				ctx.waitTicks(2);
				ctx.takeScreenshot("ring_" + model.name().toLowerCase() + "_fp");
			}
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(5);
			for (LabSettings.RingModel model : MODELS) {
				lab.ringModel = model;
				ctx.waitTicks(2);
				ctx.takeScreenshot("ring_" + model.name().toLowerCase() + "_fp_night");
			}
			world.getServer().runCommand("time set 6000");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(10);
			for (LabSettings.RingModel model : MODELS) {
				lab.ringModel = model;
				ctx.waitTicks(2);
				ctx.takeScreenshot("ring_" + model.name().toLowerCase() + "_tp");
			}
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
		}
	}
}
