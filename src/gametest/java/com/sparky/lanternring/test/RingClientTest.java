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

			// Twin helix beam: grows out of the ring, holds on the target, then unravels.
			beam(ctx, world, LabSettings.UseFx.HELIX, CameraType.THIRD_PERSON_BACK, "beam_tp");
			beam(ctx, world, LabSettings.UseFx.HELIX, CameraType.FIRST_PERSON, "beam_fp");
			beam(ctx, world, LabSettings.UseFx.HELIX_RECALL, CameraType.THIRD_PERSON_BACK, "beam_recall_tp");
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
		}
	}

	/** Fires one beam at a fresh hill and photographs every tick of its life. */
	private static void beam(ClientGameTestContext ctx, TestSingleplayerContext world, LabSettings.UseFx fx, CameraType cam, String name) {
		targetWall(world);
		LabSettings.get().useFx = fx;
		mode(world, RingMode.BEAM);
		camera(ctx, cam);
		ctx.getInput().lookAt(0f, 0f);
		ctx.waitTicks(10);
		ctx.getInput().pressKey(o -> o.keyUse);
		for (int i = 1; i <= 9; i++) {
			ctx.waitTick();
			ctx.takeScreenshot(name + "_" + i);
		}
		ctx.waitTicks(20);
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

	/** A stone wall 22 blocks in front of the player, far enough to watch the beam travel. */
	private static void targetWall(TestSingleplayerContext world) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			BlockPos feet = p.blockPosition();
			for (int x = -4; x <= 4; x++)
				for (int y = -1; y < 7; y++)
					p.level().setBlockAndUpdate(feet.offset(x, y, 22), Blocks.STONE.defaultBlockState());
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
