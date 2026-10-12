package com.sparky.lanternring.test;

import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.level.ServerPlayer;

/** Sizes a Build mode circle, clears it, flips through a few designs and their materials and builds one. */
public class BuildModeTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.getMainHandItem().set(ModComponents.MODE, RingMode.BUILD.ordinal());
				p.getAbilities().flying = true;
				p.onUpdateAbilities();
				p.teleportTo(p.getX(), p.getY() + 12, p.getZ());
			});
			ctx.waitTicks(20);
			// Look down ahead and hold to grow the circle.
			ctx.getInput().lookAt(0f, 50f);
			ctx.waitTicks(10);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(30);
			ctx.takeScreenshot("build_select_circle");
			ctx.waitTicks(20);
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.waitTicks(10);
			ctx.takeScreenshot("build_clearing");
			ctx.waitTicks(80);
			ctx.takeScreenshot("build_first_design");
			ctx.getInput().pressKey(o -> o.keyAttack);
			ctx.waitTicks(45);
			ctx.takeScreenshot("build_design_2");
			// The wheel scrolls designs too, and with crouch the materials of the one showing.
			for (int i = 0; i < 2; i++) {
				ctx.getInput().scroll(-1);
				ctx.waitTicks(45);
				ctx.takeScreenshot("build_scroll_" + (i + 1));
			}
			ctx.getInput().holdKey(o -> o.keyShift);
			for (int i = 0; i < 2; i++) {
				ctx.getInput().scroll(-1);
				ctx.waitTicks(45);
				ctx.takeScreenshot("build_material_" + (i + 1));
			}
			ctx.getInput().releaseKey(o -> o.keyShift);
			ctx.waitTicks(5);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(30);
			ctx.takeScreenshot("build_forming");
			ctx.waitTicks(200);
			ctx.takeScreenshot("build_done");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(0f, 30f);
			ctx.waitTicks(10);
			ctx.takeScreenshot("build_done_third");
		}
	}
}
