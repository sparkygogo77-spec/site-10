package com.sparky.lanternring.test;

import com.sparky.lanternring.client.LabSettings;
import com.sparky.lanternring.client.RingFirstPerson;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import org.joml.Vector3f;

/** Photographs J's three signet rings on the knuckles-in fist, in first and third person. */
public class RingModelsTest implements FabricClientGameTest {
	private static final LabSettings.RingModel[] MODELS = {
			LabSettings.RingModel.CREST, LabSettings.RingModel.CREST_GOLD, LabSettings.RingModel.BEACON};

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

			// A few fist poses side by side, to pick the one that shows the ring best.
			Vector3f fist = new Vector3f(RingFirstPerson.FIST);
			Vector3f elbow = new Vector3f(RingFirstPerson.ELBOW);
			Vector3f back = new Vector3f(RingFirstPerson.BACK);
			float[][] poses = {
					{0.28f, -0.22f, -0.6f, 0.5f, -0.9f, -1.0f, 0f, 1f, -0.6f},
					{0.28f, -0.22f, -0.6f, 0.5f, -0.9f, -1.0f, -1f, 0f, 0f},
					{0.28f, -0.22f, -0.6f, 0.5f, -0.9f, -1.0f, 1f, 0f, 0f},
					{0.3f, -0.2f, -0.6f, 0.75f, -0.7f, -0.9f, 0f, 1f, -0.6f},
					{0.3f, -0.2f, -0.6f, 0.75f, -0.7f, -0.9f, -0.4f, -1f, 0.2f},
			};
			for (int i = 0; i < poses.length; i++) {
				float[] p = poses[i];
				RingFirstPerson.FIST.set(p[0], p[1], p[2]);
				RingFirstPerson.ELBOW.set(p[3], p[4], p[5]);
				RingFirstPerson.BACK.set(p[6], p[7], p[8]);
				ctx.waitTicks(2);
				ctx.takeScreenshot("ring_pose_" + (char) ('a' + i));
			}
			RingFirstPerson.FIST.set(fist);
			RingFirstPerson.ELBOW.set(elbow);
			RingFirstPerson.BACK.set(back);

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
