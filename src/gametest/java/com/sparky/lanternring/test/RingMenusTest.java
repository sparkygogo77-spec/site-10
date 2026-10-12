package com.sparky.lanternring.test;

import com.sparky.lanternring.client.RingLabScreen;
import com.sparky.lanternring.client.RingTuningScreen;
import com.sparky.lanternring.client.UpdateScreen;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.gui.screens.Screen;

/** The Ring Lab, Durations and Updates pages at a small GUI: every button on screen, lists scrolled. */
public class RingMenusTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(40);
			RingLabScreen lab = ctx.computeOnClient(mc -> new RingLabScreen(null));
			ctx.setScreen(() -> lab);
			ctx.waitTicks(4);
			ctx.takeScreenshot("menus_lab");
			scroll(ctx, lab, -10);
			ctx.takeScreenshot("menus_lab_scrolled");

			RingTuningScreen tuning = ctx.computeOnClient(mc -> new RingTuningScreen(null));
			ctx.setScreen(() -> tuning);
			ctx.waitTicks(4);
			ctx.takeScreenshot("menus_durations");
			scroll(ctx, tuning, -100);
			ctx.takeScreenshot("menus_durations_end");

			ctx.setScreen(() -> new UpdateScreen(null));
			ctx.waitTicks(4);
			ctx.takeScreenshot("menus_updates");
			ctx.setScreen(() -> null);
		}
	}

	/** Turns the mouse wheel over the middle of the open screen (negative scrolls down). */
	private static void scroll(ClientGameTestContext ctx, Screen screen, int clicks) {
		ctx.runOnClient(mc -> {
			for (int i = 0; i < Math.abs(clicks); i++) {
				screen.mouseScrolled(screen.width / 2.0, screen.height / 2.0, 0, Math.signum(clicks));
			}
		});
		ctx.waitTicks(3);
	}
}
