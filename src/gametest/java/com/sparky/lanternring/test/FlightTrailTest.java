package com.sparky.lanternring.test;

import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;

/** The ring glowing on the hand at night, and the streak of light behind the fast glide. */
public class FlightTrailTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 18000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(60);
			LabSettings lab = LabSettings.get();
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 15f);
			ctx.waitTicks(20);
			for (LabSettings.RingModel model : new LabSettings.RingModel[] {LabSettings.RingModel.FORGED, LabSettings.RingModel.CREST}) {
				lab.ringModel = model;
				ctx.waitTicks(2);
				ctx.takeScreenshot("glow_ring_" + model.name().toLowerCase() + "_night");
			}
			lab.ringModel = LabSettings.RingModel.FORGED;

			world.getServer().runCommand("execute at @p run tp @p ~ ~25 ~");
			// Wait until the client is up there too: flying switched on while still on the ground turns straight off.
			ctx.waitTicks(5);
			ctx.runOnClient(mc -> {
				mc.player.getAbilities().flying = true;
				mc.player.onUpdateAbilities();
			});
			ctx.waitTicks(10);
			ctx.getInput().lookAt(0f, 0f);
			ctx.getInput().holdKey(o -> o.keyUp);
			ctx.getInput().holdKey(o -> o.keySprint);
			ctx.waitTicks(30);
			ctx.runOnClient(mc -> System.out.println("[trail test] y=" + mc.player.getY() + " flying=" + mc.player.getAbilities().flying
					+ " sprinting=" + mc.player.isSprinting() + " ground=" + mc.player.onGround() + " speed=" + mc.player.getDeltaMovement().length()));
			ctx.takeScreenshot("trail_first_person");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			// Bank round a turn, so the streak curves out to the side where the camera sees it.
			for (int i = 0; i < 8; i++) {
				ctx.getInput().lookAt(i * 6f, 0f);
				ctx.waitTicks(1);
			}
			ctx.takeScreenshot("trail_turn_back");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			for (int i = 8; i < 16; i++) {
				ctx.getInput().lookAt(i * 6f, 0f);
				ctx.waitTicks(1);
			}
			ctx.takeScreenshot("trail_turn_front");
			ctx.getInput().releaseKey(o -> o.keySprint);
			ctx.getInput().releaseKey(o -> o.keyUp);
			ctx.waitTicks(10);
			ctx.takeScreenshot("trail_gone");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
		}
	}
}
