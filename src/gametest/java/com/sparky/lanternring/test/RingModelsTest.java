package com.sparky.lanternring.test;

import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;

/**
 * Photographs the worn rings on the knuckles-in fist, in first and third person, including J's square emblem
 * picks from Blender pass 596 (P03, N01, N04). Those light up in stages (the gem's table first, then the inlays),
 * so they get a light-up sequence first and are photographed once fully lit.
 */
public class RingModelsTest implements FabricClientGameTest {
	private static final LabSettings.RingModel[] MODELS = {
			LabSettings.RingModel.FORGED, LabSettings.RingModel.CREST, LabSettings.RingModel.CREST_GOLD, LabSettings.RingModel.BEACON, LabSettings.RingModel.CROWN, LabSettings.RingModel.SQUARE,
			LabSettings.RingModel.P03, LabSettings.RingModel.N01, LabSettings.RingModel.N04};

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
			// Over a second on another ring, so P03 (the default, maybe drawn while the world loaded) lights up afresh.
			ctx.waitTicks(30);

			// P03 lighting up: the table first (tick 3), the light spreading out (8, 14), the swell (30).
			lab.ringModel = LabSettings.RingModel.P03;
			int at = 0;
			for (int tick : new int[] {3, 8, 14, 30}) {
				ctx.waitTicks(tick - at);
				at = tick;
				ctx.takeScreenshot("ring_p03_lightup_" + tick);
			}
			for (LabSettings.RingModel model : MODELS) {
				lab.ringModel = model;
				ctx.waitTicks(settle(model));
				ctx.takeScreenshot("ring_" + model.name().toLowerCase() + "_fp");
			}
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(5);
			for (LabSettings.RingModel model : MODELS) {
				lab.ringModel = model;
				ctx.waitTicks(settle(model));
				ctx.takeScreenshot("ring_" + model.name().toLowerCase() + "_fp_night");
			}
			world.getServer().runCommand("time set 6000");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(10);
			for (LabSettings.RingModel model : MODELS) {
				lab.ringModel = model;
				ctx.waitTicks(settle(model));
				ctx.takeScreenshot("ring_" + model.name().toLowerCase() + "_tp");
			}
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
		}
	}

	/** Ticks to wait after switching: the 596 rings light up over about 2 s (RingModels.lightUp) if unseen for a second. */
	private static int settle(LabSettings.RingModel model) {
		return switch (model) {
			case P03, N01, N04 -> 50;
			default -> 2;
		};
	}
}
