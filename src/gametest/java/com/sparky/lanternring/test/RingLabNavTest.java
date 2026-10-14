package com.sparky.lanternring.test;

import com.mojang.blaze3d.platform.InputConstants;
import com.sparky.lanternring.client.LabSettings;
import com.sparky.lanternring.client.RingLabScreen;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.input.CharacterEvent;
import net.minecraft.client.input.KeyEvent;

/**
 * The Ring Lab overhaul (J, 2026-10-14): category tabs, one row per feature with ◀ value ▶, J's picks starred, search across
 * tabs, keyboard navigation, grouped report. Shots: the Movement tab, Tab to the next tab with a row stepped by the keys,
 * and "landing" typed into the search.
 */
public class RingLabNavTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(40);
			ctx.runOnClient(mc -> {
				LabSettings s = LabSettings.get();
				s.resetToPicks(LabSettings.OPTIONS);
				s.labTab = LabSettings.Group.MOVEMENT;
				s.labRow = 0;
				s.showOld = false;
			});
			RingLabScreen lab = ctx.computeOnClient(mc -> new RingLabScreen(null));
			ctx.setScreen(() -> lab);
			ctx.waitTicks(4);
			ctx.takeScreenshot("lab_nav_movement");

			// Tab to the next tab (Flight), Down a row, Right to step its take.
			ctx.runOnClient(mc -> {
				lab.keyPressed(new KeyEvent(InputConstants.KEY_TAB, 0, 0));
				lab.keyPressed(new KeyEvent(InputConstants.KEY_DOWN, 0, 0));
				lab.keyPressed(new KeyEvent(InputConstants.KEY_RIGHT, 0, 0));
			});
			ctx.waitTicks(3);
			ctx.takeScreenshot("lab_nav_flight_keys");
			ctx.runOnClient(mc -> {
				LabSettings s = LabSettings.get();
				if (s.labTab != LabSettings.Group.FLIGHT || s.labRow != 1) {
					throw new AssertionError("Ring Lab keys: tab " + s.labTab + " row " + s.labRow);
				}
			});

			// Two more tabs along: Combat, then Beams.
			ctx.runOnClient(mc -> lab.keyPressed(new KeyEvent(InputConstants.KEY_TAB, 0, 0)));
			ctx.waitTicks(3);
			ctx.takeScreenshot("lab_nav_combat");

			ctx.runOnClient(mc -> {
				for (char c : "landing".toCharArray()) lab.charTyped(new CharacterEvent(c));
			});
			ctx.waitTicks(3);
			ctx.takeScreenshot("lab_nav_search_landing");

			String report = ctx.computeOnClient(mc -> LabSettings.get().report());
			System.out.println("[ring lab] report:\n" + report);
			if (!report.contains("[Move]") || !report.contains("★")) throw new AssertionError("Ring Lab report isn't grouped and starred:\n" + report);
			ctx.runOnClient(mc -> LabSettings.get().resetToPicks(LabSettings.OPTIONS));
			ctx.setScreen(() -> null);
		}
	}
}
