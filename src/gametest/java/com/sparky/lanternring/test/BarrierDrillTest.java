package com.sparky.lanternring.test;

import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.client.LabFx;
import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.world.phys.Vec3;

/** J's Blender picks in game: the particle-barrier surfaces on a green Wall, and the D1-D3 Blast drills side on. */
public class BarrierDrillTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			world.getServer().runCommand("execute at @p run tp @p ~ ~ ~ 0 0");
			world.getServer().runCommand("execute at @p run fill ~-4 ~ ~5 ~4 ~4 ~5 lanternring:construct_brick");
			world.getServer().runCommand("execute at @p run fill ~-4 ~ ~6 ~4 ~4 ~6 lanternring:light_construct");
			ctx.getInput().lookAt(0f, 15f);
			for (LabSettings.BarrierSurface s : LabSettings.BarrierSurface.values()) {
				ctx.runOnClient(mc -> LabSettings.get().barrierSurface = s);
				// Constructs fade after a while: set the Wall again for each shot.
				world.getServer().runCommand("execute at @p run fill ~-4 ~ ~5 ~4 ~4 ~6 air");
				world.getServer().runCommand("execute at @p run fill ~-4 ~ ~5 ~4 ~4 ~5 lanternring:construct_brick");
				world.getServer().runCommand("execute at @p run fill ~-4 ~ ~6 ~4 ~4 ~6 lanternring:light_construct");
				ctx.waitTicks(40);
				ctx.takeScreenshot("barrier_" + s.name().toLowerCase());
			}
			ctx.runOnClient(mc -> LabSettings.get().barrierSurface = LabSettings.BarrierSurface.PICKED);
			world.getServer().runCommand("execute at @p run fill ~-30 ~ ~1 ~30 ~10 ~30 air");
			RingTuning.BLAST_DRILL_TIME.set(4);
			ctx.getInput().lookAt(0f, 0f);
			for (LabSettings.DrillModel d : LabSettings.DrillModel.values()) {
				ctx.runOnClient(mc -> LabSettings.get().drillModel = d);
				ctx.waitTicks(10);
				ctx.runOnClient(mc -> {
					Vec3 eye = mc.player.getEyePosition();
					LabFx.blast(eye.add(-20, 0, 9), eye.add(30, 0, 9), 0.3, 1);
				});
				ctx.waitTicks(46);
				ctx.takeScreenshot("drill_" + d.name().toLowerCase());
				ctx.waitTicks(60);
			}
			RingTuning.resetAll();
		}
	}
}
