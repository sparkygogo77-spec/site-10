package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.client.FirstPersonCombat;
import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.world.InteractionHand;

/**
 * First person (J, 2026-10-15): the ring-hand punch (pass 502 P1b step-in jab, P1c hook) and the flying flurry F2
 * (pass 520: jab, cross, spinning backfist) move both arms in view, at FOV 70 and 110, vanilla size and 1.3x.
 */
public class FirstPersonCombatTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			var server = world.getServer();
			server.runCommand("gamemode creative @a");
			server.runCommand("gamerule doDaylightCycle false");
			server.runCommand("time set 6000");
			server.runOnServer(s -> s.getPlayerList().getPlayers().get(0).setItemInHand(InteractionHand.MAIN_HAND, Corps.GREEN.ring()));
			ctx.runOnClient(mc -> {
				mc.options.setCameraType(CameraType.FIRST_PERSON);
				mc.options.fov().set(70);
			});
			ctx.getInput().lookAt(0f, 5f);
			ctx.waitTicks(40);
			LabSettings.Punch punch = ctx.computeOnClient(mc -> LabSettings.get().punch);
			LabSettings.FpArms arms = ctx.computeOnClient(mc -> LabSettings.get().fpArms);
			try {
				ctx.takeScreenshot("fp_combat_idle");
				punch(ctx, LabSettings.Punch.P1B, "fp_punch_p1b", 2, 3);
				punch(ctx, LabSettings.Punch.P1C, "fp_punch_p1c", 2, 3, 2);
				flurry(ctx, "fp_flurry", 1, 4, 3, 4, 4);
				ctx.runOnClient(mc -> mc.options.fov().set(110));
				punch(ctx, LabSettings.Punch.P1C, "fp_punch_p1c_fov110", 5);
				flurry(ctx, "fp_flurry_fov110", 5, 7);
				ctx.runOnClient(mc -> {
					mc.options.fov().set(70);
					LabSettings.get().fpArms = LabSettings.FpArms.BIGGER;
				});
				punch(ctx, LabSettings.Punch.P1B, "fp_punch_p1b_bigger", 2);
				flurry(ctx, "fp_flurry_bigger", 5, 7);
				ctx.waitTicks(80);
				boolean done =ctx.computeOnClient(mc -> FirstPersonCombat.now(mc.player, 0f) == null);
				if (!done) throw new AssertionError("The first-person flurry should end");
			} finally {
				ctx.runOnClient(mc -> {
					LabSettings.get().punch = punch;
					LabSettings.get().fpArms = arms;
				});
			}
		}
	}

	/** Throws the punch and takes a screenshot after each wait (ticks since the last). */
	private static void punch(ClientGameTestContext ctx, LabSettings.Punch take, String name, int... waits) {
		ctx.runOnClient(mc -> {
			LabSettings.get().punch = take;
			FirstPersonCombat.play(mc.player, false);
		});
		shots(ctx, name, waits);
		ctx.waitTicks(40);
	}

	private static void flurry(ClientGameTestContext ctx, String name, int... waits) {
		ctx.runOnClient(mc -> FirstPersonCombat.play(mc.player, true));
		shots(ctx, name, waits);
		ctx.waitTicks(60);
	}

	private static void shots(ClientGameTestContext ctx, String name, int... waits) {
		int at = 0;
		for (int w : waits) {
			ctx.waitTicks(w);
			at += w;
			boolean playing = ctx.computeOnClient(mc -> FirstPersonCombat.now(mc.player, 0f) != null);
			if (!playing) throw new AssertionError(name + " isn't playing in first person at tick " + at);
			ctx.takeScreenshot(name + "_t" + at);
		}
	}
}
