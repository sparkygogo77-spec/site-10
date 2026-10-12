package com.sparky.lanternring.test;

import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.Blocks;

/** Boots the real client, puts the ring on, and photographs each Ring Lab version and power. */
public class RingClientTest implements FabricClientGameTest {
	private static final int RIGHT_MOUSE = 1;

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(60);
			LabSettings lab = LabSettings.get();
			lab.handPose = LabSettings.HandPose.FIST_DOWN;
			lab.ringGlow = LabSettings.RingGlow.AURA;
			ctx.getInput().lookAt(0f, 10f);

			world.getServer().runCommand("time set 18000");
			lab.ringModel = LabSettings.RingModel.SIGNET;
			camera(ctx, CameraType.FIRST_PERSON);


			// Held 7x7 wall, at night so the glow shows.
			mode(world, RingMode.WALL);
			ctx.getInput().lookAt(0f, 0f);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(10);
			ctx.takeScreenshot("wall_held_night");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(4);
			ctx.takeScreenshot("wall_held_day");
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.waitTicks(5);
			ctx.takeScreenshot("wall_released");

			// Dome into a stone hill.
			hill(world);
			ctx.waitTicks(10);
			mode(world, RingMode.DOME);
			ctx.getInput().lookAt(0f, 0f);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(10);
			ctx.takeScreenshot("dome_fp");
			camera(ctx, CameraType.THIRD_PERSON_BACK);
			ctx.waitTicks(4);
			ctx.takeScreenshot("dome_tp_back");
			ctx.getInput().lookAt(0f, 80f);
			ctx.waitTicks(10);
			ctx.takeScreenshot("dome_tp_looking_down");
			ctx.getInput().releaseKey(o -> o.keyUse);
			camera(ctx, CameraType.FIRST_PERSON);
			ctx.waitTicks(10);
			ctx.takeScreenshot("dome_released");

			// Blast into a fresh hill.
			hill(world);
			ctx.waitTicks(10);
			mode(world, RingMode.BLAST);
			ctx.getInput().lookAt(0f, 0f);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(3);
			ctx.takeScreenshot("blast_fire");
			ctx.waitTicks(25);
			ctx.takeScreenshot("blast_after");

			// Shockwave: a dome grows out and throws a ring of pigs back as it reaches them.
			world.getServer().runCommand("time set 18000");
			world.getServer().runCommand("execute at @p run fill ~-12 ~ ~-12 ~12 ~6 ~12 air");
			for (int[] at : new int[][] {{4, 3}, {-4, 4}, {0, 6}, {5, -2}, {-3, -5}}) {
				world.getServer().runCommand("execute at @p run summon minecraft:pig ~" + at[0] + " ~ ~" + at[1]);
			}
			mode(world, RingMode.PUSH);
			camera(ctx, CameraType.THIRD_PERSON_BACK);
			ctx.getInput().lookAt(0f, 30f);
			ctx.waitTicks(10);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(4);
			ctx.takeScreenshot("shockwave_growing");
			ctx.waitTicks(5);
			ctx.takeScreenshot("shockwave_full");
			ctx.waitTicks(10);
			ctx.takeScreenshot("shockwave_after");
			camera(ctx, CameraType.FIRST_PERSON);

			flight(ctx, world);
		}
	}

	/** Ring flight poses from the front: hovering, a slow lean with trailing legs, and the sprint glide. */
	private static void flight(ClientGameTestContext ctx, TestSingleplayerContext world) {
		world.getServer().runCommand("time set 6000");
		world.getServer().runCommand("execute at @p run tp @p ~ ~20 ~");
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			p.getAbilities().flying = true;
			p.onUpdateAbilities();
		});
		ctx.runOnClient(mc -> mc.player.getAbilities().flying = true);
		ctx.getInput().lookAt(0f, 10f);
		camera(ctx, CameraType.THIRD_PERSON_FRONT);
		ctx.waitTicks(20);
		ctx.takeScreenshot("fly_hover");

		ctx.getInput().holdKey(o -> o.keyUp);
		ctx.waitTicks(15);
		ctx.takeScreenshot("fly_slow_forward");
		ctx.getInput().holdKey(o -> o.keyRight);
		ctx.waitTicks(10);
		ctx.takeScreenshot("fly_slow_strafe");
		ctx.getInput().releaseKey(o -> o.keyRight);

		ctx.getInput().holdKey(o -> o.keySprint);
		ctx.waitTicks(15);
		ctx.takeScreenshot("fly_fast_front");
		camera(ctx, CameraType.THIRD_PERSON_BACK);
		ctx.waitTicks(5);
		ctx.takeScreenshot("fly_fast_back");
		ctx.getInput().lookAt(0f, 50f);
		ctx.waitTicks(10);
		ctx.takeScreenshot("fly_fast_dive");
		ctx.getInput().releaseKey(o -> o.keySprint);
		ctx.getInput().releaseKey(o -> o.keyUp);

		ctx.getInput().lookAt(0f, 10f);
		ctx.waitTicks(25);
		ctx.takeScreenshot("fly_stopped_back");
		camera(ctx, CameraType.FIRST_PERSON);
	}

	private static void camera(ClientGameTestContext ctx, CameraType type) {
		ctx.runOnClient(mc -> mc.options.setCameraType(type));
	}

	private static void mode(TestSingleplayerContext world, RingMode mode) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			p.getMainHandItem().set(ModComponents.MODE, mode.ordinal());
		});
	}

	/** A 13x8x12 stone hill (with a bedrock pillar) a few blocks in front of the player (+Z). */
	private static void hill(TestSingleplayerContext world) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			BlockPos feet = p.blockPosition();
			var level = p.level();
			for (int x = -6; x <= 6; x++)
				for (int y = 0; y < 8; y++)
					for (int z = 4; z < 16; z++)
						level.setBlockAndUpdate(feet.offset(x, y, z), (x == 0 && z == 6) ? Blocks.BEDROCK.defaultBlockState()
								: (y + z) % 5 == 0 ? Blocks.DIRT.defaultBlockState() : Blocks.STONE.defaultBlockState());
		});
	}
}
