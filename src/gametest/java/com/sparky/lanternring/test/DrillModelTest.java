package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.client.CorpsTint;
import com.sparky.lanternring.client.LabFx;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.world.phys.Vec3;

/** The Blast drill's spiral flutes up close, side on and from the tip, green and red (client-only drills). */
public class DrillModelTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			world.getServer().runCommand("execute at @p run fill ~-30 ~ ~-30 ~30 ~12 ~30 air");
			world.getServer().runOnServer(server -> {
				var p = server.getPlayerList().getPlayers().get(0);
				p.getAbilities().flying = true;
				p.onUpdateAbilities();
				p.teleportTo(p.getX(), p.getY() + 2, p.getZ());
			});
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(20);
			for (Corps corps : new Corps[] {Corps.GREEN, Corps.RED}) {
				String name = corps.getSerializedName();
				// Side on, crawling past 5 blocks away.
				ctx.runOnClient(mc -> {
					Vec3 eye = mc.player.getEyePosition();
					Corps before = CorpsTint.enter(corps);
					LabFx.blast(eye.add(-6, 0, 5), eye.add(30, 0, 5), 0.1, 1);
					CorpsTint.restore(before);
				});
				ctx.waitTicks(55);
				ctx.takeScreenshot("drill_" + name + "_side");
				ctx.waitTicks(3);
				ctx.takeScreenshot("drill_" + name + "_side_turned");
				ctx.waitTicks(320);
				// Coming at the camera at an angle, tip first.
				ctx.runOnClient(mc -> {
					Vec3 eye = mc.player.getEyePosition();
					Corps before = CorpsTint.enter(corps);
					LabFx.blast(eye.add(5, -1, 26), eye.add(1.5, -1, 3), 0.1, 1);
					CorpsTint.restore(before);
				});
				ctx.waitTicks(140);
				ctx.takeScreenshot("drill_" + name + "_tip");
				ctx.waitTicks(160);
			}
		}
	}
}
