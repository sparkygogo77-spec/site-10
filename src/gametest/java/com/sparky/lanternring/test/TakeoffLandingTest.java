package com.sparky.lanternring.test;

import com.sparky.lanternring.client.LabSettings;
import com.sparky.lanternring.client.TakeoffMoves;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;

/**
 * Pass 403 and 404 (build order 2026-10-14, section 1): the standing double-jump take-off S1 at its hero hover, the
 * R3 running dart at the end of its 6-tick arc (ring arm leading, A2 free arm); pass 405 and J's report #2: shift's
 * hyper speed, and J's L4 double-tap landing (0.3 blocks of carry, 2026-10-15) while flying forward and from a hover,
 * each touching down within 0.30 s and close.
 */
public class TakeoffLandingTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			var server = world.getServer();
			server.runCommand("gamemode creative @a");
			server.runCommand("gamerule doDaylightCycle false");
			server.runCommand("gamerule doMobSpawning false");
			server.runCommand("time set 6000");
			server.runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(60);
			BlockPos feet = server.computeOnServer(s -> s.getPlayerList().getPlayers().get(0).blockPosition());
			int x = feet.getX(), y = feet.getY() + 30, z = feet.getZ();
			// A wide stone floor in the sky, clear above.
			server.runCommand("forceload add " + (x - 24) + " " + (z - 24) + " " + (x + 24) + " " + (z + 64));
			server.runCommand("fill " + (x - 12) + " " + (y - 1) + " " + (z - 12) + " " + (x + 12) + " " + (y - 1) + " " + (z + 60) + " stone");
			server.runCommand("fill " + (x - 12) + " " + y + " " + (z - 12) + " " + (x + 12) + " " + (y + 12) + " " + (z + 60) + " air");
			ctx.runOnClient(mc -> {
				LabSettings.get().takeoff = LabSettings.Takeoff.F2;
				LabSettings.get().takeoffStand = LabSettings.TakeoffStand.S1;
				LabSettings.get().freeArm = LabSettings.FreeArm.A2;
				LabSettings.get().armLead = LabSettings.ArmLead.D1;
				// The run-up for the dart mustn't arm a super jump.
				LabSettings.get().superSprint = LabSettings.SuperSprint.OFF;
			});

			// S1: standing, double-tap jump; the puff to 3.2 blocks, then the hero hover.
			ground(ctx, server, x, y, z, 0f);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.getInput().lookAt(0f, 10f);
			ctx.waitTicks(5);
			doubleTapJump(ctx);
			boolean hover = false;
			for (int i = 0; i < 20 && !hover; i++) {
				ctx.waitTicks(1);
				hover = ctx.computeOnClient(mc -> TakeoffMoves.hovering());
			}
			ctx.waitTicks(6);
			double hoverHeight = ctx.computeOnClient(mc -> mc.player.getY()) - y;
			ctx.takeScreenshot("takeoff_s1_hover");
			log(ctx, "s1 hover=" + hover + " height=" + String.format("%.2f", hoverHeight));

			// R3: sprint, double jump; flat at 5 blocks 6 ticks later. Looked at from the side once it is under way.
			ground(ctx, server, x, y, z - 10, 0f);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().holdKey(o -> o.keyUp);
			ctx.getInput().holdKey(o -> o.keySprint);
			ctx.waitTicks(15);
			doubleTapJump(ctx);
			ctx.getInput().releaseKey(o -> o.keyUp);
			ctx.getInput().releaseKey(o -> o.keySprint);
			int darted = -1;
			for (int i = 0; i < 10 && darted < 0; i++) {
				String state = ctx.computeOnClient(mc -> TakeoffMoves.state());
				if (state.startsWith("dart")) darted = Integer.parseInt(state.substring(5));
				else ctx.waitTicks(1);
			}
			ctx.getInput().lookAt(90f, 15f);
			if (darted >= 0 && darted < 6) ctx.waitTicks(6 - darted);
			double dartHeight = ctx.computeOnClient(mc -> mc.player.getY()) - y;
			ctx.takeScreenshot("takeoff_r3_arc_tick6");
			log(ctx, "r3 darted=" + darted + " height=" + String.format("%.2f", dartHeight));

			// Shift while flying forward is hyper speed now (J's report #2), past the old glide's 1.62 blocks a tick.
			server.runCommand("tp @p " + (x + 0.5) + " " + (y + 10) + " " + (z - 8.5) + " 0 0");
			ctx.runOnClient(mc -> {
				mc.player.getAbilities().flying = true;
				mc.player.onUpdateAbilities();
			});
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(5);
			ctx.getInput().holdKey(o -> o.keyUp);
			ctx.getInput().holdKey(o -> o.keyShift);
			ctx.waitTicks(14);
			float hyper = ctx.computeOnClient(mc -> com.sparky.lanternring.client.FastFlight.hyper() ? com.sparky.lanternring.client.FastFlight.speed() : 0f);
			ctx.getInput().releaseKey(o -> o.keyShift);
			ctx.getInput().holdKey(o -> o.keySprint);
			log(ctx, "hyper speed " + String.format("%.2f", hyper));

			// L4 while flying forward: forward and sprint held through the double tap; it brakes, drops straight in and
			// touches down 6 ticks after the tap, carried at most 0.3 blocks.
			server.runCommand("tp @p " + (x + 0.5) + " " + (y + 4) + " " + (z - 8.5) + " 0 0");
			ctx.waitTicks(10);
			double speed = ctx.computeOnClient(mc -> Math.hypot(mc.player.getX() - mc.player.xo, mc.player.getZ() - mc.player.zo));
			log(ctx, "flying forward at " + String.format("%.2f", speed * 20) + " b/s");
			double[] l4 = landing(ctx, LabSettings.SoftLanding.L4);
			ctx.getInput().releaseKey(o -> o.keyUp);
			ctx.getInput().releaseKey(o -> o.keySprint);
			ctx.getInput().lookAt(90f, 15f);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.takeScreenshot("landing_l4_absorb");
			ctx.waitTicks(10);
			ctx.takeScreenshot("landing_l4_stand");

			// L4 from a hover: straight down, 6 ticks. Flight goes on well clear of the ground, so it isn't a take-off.
			server.runCommand("tp @p " + (x + 0.5) + " " + (y + 30) + " " + (z + 20.5) + " 0 0");
			ctx.waitTicks(14);
			ctx.runOnClient(mc -> {
				mc.player.getAbilities().flying = true;
				mc.player.onUpdateAbilities();
			});
			ctx.waitTicks(10);
			server.runCommand("tp @p " + (x + 0.5) + " " + (y + 4) + " " + (z + 20.5) + " 0 0");
			ctx.waitTicks(10);
			double[] still = landing(ctx, LabSettings.SoftLanding.L4);
			ctx.takeScreenshot("landing_l4_hover_absorb");

			boolean l4ok = l4[0] > 0 && l4[0] <= 7 && l4[1] <= 0.31, stillOk = still[0] > 0 && still[0] <= 7 && still[1] < 0.1;
			if (!hover || hoverHeight < 2.5 || darted < 0 || dartHeight < 3 || hyper < 2 || !l4ok || !stillOk) {
				throw new AssertionError("take-off and landing: hover=" + hover + " height=" + hoverHeight + " darted=" + darted
						+ " dartHeight=" + dartHeight + " hyper=" + hyper + " l4=" + l4[0] + "/" + l4[1] + " still=" + still[0] + "/" + still[1]);
			}
		}
	}

	/**
	 * Double-taps jump in take "take" and waits for touchdown: {ticks from the drop's start to touchdown (-1: none),
	 * blocks carried across the ground}.
	 */
	private static double[] landing(ClientGameTestContext ctx, LabSettings.SoftLanding take) {
		ctx.runOnClient(mc -> LabSettings.get().softLanding = take);
		doubleTapJump(ctx);
		double[] from = null;
		int ticks = 0;
		for (int i = 0; i < 30; i++) {
			String state = ctx.computeOnClient(mc -> TakeoffMoves.state());
			if (state.startsWith("descend") && from == null) {
				from = ctx.computeOnClient(mc -> new double[] {TakeoffMoves.landStart().x, TakeoffMoves.landStart().z});
				ticks = Integer.parseInt(state.substring(8));
			}
			if (state.startsWith("runout") && from != null) {
				double[] at = ctx.computeOnClient(mc -> new double[] {mc.player.getX(), mc.player.getZ()});
				double carry = Math.hypot(at[0] - from[0], at[1] - from[1]);
				log(ctx, take + " touched after " + ticks + " carried " + String.format("%.2f", carry));
				return new double[] {ticks, carry};
			}
			ctx.waitTicks(1);
			if (from != null) ticks++;
		}
		log(ctx, take + " never touched");
		return new double[] {-1, 99};
	}

	/** Back on the floor at x, z, not flying, facing yaw. */
	private static void ground(ClientGameTestContext ctx, TestServerContext server, int x, int y, int z, float yaw) {
		ctx.runOnClient(mc -> {
			mc.player.getAbilities().flying = false;
			mc.player.onUpdateAbilities();
		});
		server.runCommand("tp @p " + (x + 0.5) + " " + y + " " + (z + 0.5) + " " + yaw + " 0");
		ctx.waitTicks(15);
	}

	/** Two taps of jump, 3 ticks apart: a jump and the second jump (vanilla's double-tap). */
	private static void doubleTapJump(ClientGameTestContext ctx) {
		for (int i = 0; i < 2; i++) {
			ctx.getInput().holdKey(o -> o.keyJump);
			ctx.waitTicks(1);
			ctx.getInput().releaseKey(o -> o.keyJump);
			ctx.waitTicks(2);
		}
	}

	private static void log(ClientGameTestContext ctx, String what) {
		String where = ctx.computeOnClient(mc -> String.format("x=%.1f y=%.1f z=%.1f flying=%s move=%s",
				mc.player.getX(), mc.player.getY(), mc.player.getZ(), mc.player.getAbilities().flying, TakeoffMoves.state()));
		System.out.println("[takeoff landing test] " + what + " " + where);
	}
}
