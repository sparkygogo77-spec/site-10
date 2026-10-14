package com.sparky.lanternring.test;

import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.client.FastFlight;
import com.sparky.lanternring.client.FlightMoves;
import com.sparky.lanternring.client.LabSettings;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;

/**
 * J's movement and flight hand-off (2026-10-14): the S1/S5 sprint run with the ring in hand (and the
 * lantern carried), the F2 rocket takeoff, low ground flight halting against a wall with its barrier
 * imprint, and the sonic boom in the fast glide.
 */
public class MoveFlightTest implements FabricClientGameTest {
	private static final int WALL_AT = 40;

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 13000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			world.getServer().runCommand("item replace entity @a weapon.offhand with lanternring:power_battery");
			ctx.waitTicks(60);
			BlockPos feet = world.getServer().computeOnServer(server -> {
				var p = server.getPlayerList().getPlayers().get(0);
				p.getMainHandItem().set(ModComponents.CHARGE, PowerRingItem.MAX_CHARGE);
				p.getMainHandItem().set(ModComponents.FLIGHT, true);
				return p.blockPosition();
			});
			int x = feet.getX(), y = feet.getY() + 30, z = feet.getZ();
			// A flat stone runway in the sky, a one-block step on it, and a stone wall at its end.
			world.getServer().runCommand("forceload add " + (x - 16) + " " + (z - 16) + " " + (x + 16) + " " + (z + WALL_AT + 16));
			world.getServer().runCommand("fill " + (x - 6) + " " + (y - 1) + " " + (z - 4) + " " + (x + 6) + " " + (y - 1) + " " + (z + WALL_AT) + " stone");
			world.getServer().runCommand("fill " + (x - 6) + " " + y + " " + (z + 22) + " " + (x + 6) + " " + y + " " + (z + WALL_AT) + " stone");
			world.getServer().runCommand("fill " + (x - 6) + " " + (y + 1) + " " + (z + WALL_AT - 2) + " " + (x + 6) + " " + (y + 6) + " " + (z + WALL_AT) + " stone");

			// The sprint run, ring held out and the lantern carried.
			world.getServer().runCommand("tp @p " + (x + 0.5) + " " + y + " " + (z + 0.5) + " 0 0");
			ctx.waitTicks(10);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.getInput().lookAt(0f, 10f);
			ctx.getInput().holdKey(o -> o.keyUp);
			ctx.getInput().holdKey(o -> o.keySprint);
			ctx.waitTicks(14);
			ctx.takeScreenshot("move_sprint_s5a");
			LabSettings.get().sprintCarry = LabSettings.SprintCarry.S5B;
			ctx.waitTicks(3);
			ctx.takeScreenshot("move_sprint_s5b");
			LabSettings.get().sprintCarry = LabSettings.SprintCarry.S5A;

			// Ground flight: double-tap jump while sprinting and looking down (pass 403: looking ahead darts up
			// instead); it rides the step and halts at the wall.
			ctx.getInput().lookAt(0f, 30f);
			doubleTapJump(ctx);
			ctx.waitTicks(6);
			log(ctx, "ground start");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.waitTicks(4);
			ctx.takeScreenshot("move_ground_skim");
			// From above, so the laid-out body shows its length.
			ctx.getInput().lookAt(0f, 75f);
			ctx.waitTicks(2);
			ctx.takeScreenshot("move_ground_skim_above");
			ctx.getInput().lookAt(0f, 10f);
			boolean halted = false;
			for (int i = 0; i < 120; i++) {
				ctx.waitTicks(1);
				boolean near = ctx.computeOnClient(mc -> mc.player.getZ() > z + WALL_AT - 7.5);
				if (near) {
					halted = true;
					break;
				}
			}
			ctx.waitTicks(2);
			ctx.takeScreenshot("move_ground_impact");
			ctx.waitTicks(3);
			ctx.takeScreenshot("move_ground_impact_2");
			log(ctx, "halted=" + halted);
			ctx.getInput().releaseKey(o -> o.keySprint);
			ctx.getInput().releaseKey(o -> o.keyUp);
			ctx.waitTicks(25);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(3);
			ctx.takeScreenshot("move_ground_imprint");
			log(ctx, "after halt");

			// The standing take-off from a double jump (pass 403 S1: a puff up to a 3.2-block hover; it replaced F2).
			ctx.runOnClient(mc -> {
				mc.player.getAbilities().flying = false;
				mc.player.onUpdateAbilities();
			});
			world.getServer().runCommand("tp @p " + (x + 0.5) + " " + y + " " + (z + 2.5) + " 180 0");
			ctx.waitTicks(15);
			double startY = ctx.computeOnClient(mc -> mc.player.getY());
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			doubleTapJump(ctx);
			ctx.waitTicks(5);
			ctx.takeScreenshot("move_takeoff_plant");
			ctx.waitTicks(10);
			ctx.takeScreenshot("move_takeoff_rocket");
			ctx.waitTicks(14);
			ctx.takeScreenshot("move_takeoff_pitch_over");
			ctx.waitTicks(8);
			double rose = ctx.computeOnClient(mc -> mc.player.getY()) - startY;
			log(ctx, "takeoff rose " + rose);

			// The sonic boom: the fast glide passes 1.1 blocks a tick (ring flight's speed: creative flies slower).
			world.getServer().runCommand("gamemode survival @a");
			ctx.waitTicks(10);
			ctx.runOnClient(mc -> {
				mc.player.getAbilities().flying = true;
				mc.player.onUpdateAbilities();
			});
			ctx.waitTicks(5);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.getInput().lookAt(180f, 0f);
			ctx.getInput().holdKey(o -> o.keyUp);
			ctx.getInput().holdKey(o -> o.keySprint);
			boolean boomed = false;
			for (int i = 0; i < 120 && !boomed; i++) {
				ctx.waitTicks(1);
				boomed = ctx.computeOnClient(mc -> FastFlight.speed() > 1.1f);
			}
			ctx.waitTicks(3);
			ctx.takeScreenshot("move_sonic_boom");
			ctx.waitTicks(10);
			ctx.takeScreenshot("move_trail_fast");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			// Bank round a turn, so the trail curves out to the side where the camera sees it.
			for (int i = 0; i < 8; i++) {
				ctx.getInput().lookAt(180f + i * 6f, 0f);
				ctx.waitTicks(1);
			}
			ctx.takeScreenshot("move_trail_back");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.waitTicks(2);
			ctx.takeScreenshot("move_trail_first_person");
			ctx.getInput().releaseKey(o -> o.keySprint);
			ctx.getInput().releaseKey(o -> o.keyUp);
			log(ctx, "boomed=" + boomed);
			if (!halted || rose < 2.5 || !boomed) throw new AssertionError("move flight: halted=" + halted + " rose=" + rose + " boomed=" + boomed);
		}
	}

	/** Vanilla's double-tap of jump that switches flight on. */
	private static void doubleTapJump(ClientGameTestContext ctx) {
		for (int i = 0; i < 2; i++) {
			ctx.getInput().holdKey(o -> o.keyJump);
			ctx.waitTicks(1);
			ctx.getInput().releaseKey(o -> o.keyJump);
			ctx.waitTicks(2);
		}
	}

	private static void log(ClientGameTestContext ctx, String what) {
		String where = ctx.computeOnClient(mc -> String.format("x=%.1f y=%.1f z=%.1f flying=%s ground=%s controls=%s speed=%.2f",
				mc.player.getX(), mc.player.getY(), mc.player.getZ(), mc.player.getAbilities().flying, FlightMoves.grounded(),
				FlightMoves.controls(), mc.player.getDeltaMovement().length()));
		System.out.println("[move flight test] " + what + " " + where);
	}
}
