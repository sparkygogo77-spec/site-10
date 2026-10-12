package com.sparky.lanternring.test;

import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.client.LabFx;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

/** The Blast's drill boring into a long stone hill, from behind, from the side and at night. */
public class BlastDrillTest implements FabricClientGameTest {
	private static BlockPos feet;

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(60);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.getMainHandItem().set(ModComponents.MODE, RingMode.BLAST.ordinal());
			});

			// At the default speed: the tunnel opens a few blocks at a time behind the tip.
			hill(world);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(20);
			fire(ctx, 0);
			for (int i = 1; i <= 12; i++) {
				ctx.waitTicks(1);
				count(world, "fp tick " + i);
				if (i <= 6 || i % 3 == 0) ctx.takeScreenshot("drill_fp_" + i);
			}

			// Slowed down, from behind, so the spin and the uneven blades show.
			RingTuning.BLAST_DRILL_TIME.set(4);
			hill(world);
			ctx.waitTicks(20);
			fire(ctx, 0);
			for (int i = 1; i <= 8; i++) {
				ctx.waitTicks(i == 1 ? 3 : 2);
				ctx.takeScreenshot("drill_back_" + i);
			}
			count(world, "slow back");
			ctx.waitTicks(80);

			// Side on: a client-only drill crossing in front of the camera, nothing is broken.
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			world.getServer().runCommand("execute at @p run fill ~-30 ~ ~1 ~30 ~10 ~30 air");
			ctx.waitTicks(10);
			ctx.runOnClient(mc -> {
				Vec3 eye = mc.player.getEyePosition();
				LabFx.blast(eye.add(-20, 0, 9), eye.add(30, 0, 9), 0.3, 1);
			});
			for (int i = 1; i <= 6; i++) {
				ctx.waitTicks(i == 1 ? 40 : 6);
				ctx.takeScreenshot("drill_side_" + i);
			}

			// At night, default speed, from behind.
			RingTuning.resetAll();
			world.getServer().runCommand("time set 18000");
			hill(world);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.waitTicks(20);
			fire(ctx, 0);
			for (int i = 1; i <= 4; i++) {
				ctx.waitTicks(2);
				ctx.takeScreenshot("drill_night_" + i);
			}
			ctx.waitTicks(30);
			ctx.takeScreenshot("drill_night_after");

			// Level 3 (two left-clicks while holding): a 7x7 tunnel and a fatter drill.
			world.getServer().runCommand("time set 6000");
			hill(world);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.waitTicks(20);
			fire(ctx, 2);
			for (int i = 1; i <= 3; i++) {
				ctx.waitTicks(3);
				ctx.takeScreenshot("drill_level3_" + i);
			}
			ctx.waitTicks(30);
			ctx.takeScreenshot("drill_level3_after");
			// A quick tap only reaches 10 blocks.
			hill(world);
			ctx.waitTicks(20);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(30);
			count(world, "tap");
			ctx.takeScreenshot("drill_tap");
		}
	}

	/** Holds right-click to a full charge, left-clicking clicks times first to pick the level, then lets go. */
	private static void fire(ClientGameTestContext ctx, int clicks) {
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(2);
		for (int i = 0; i < clicks; i++) {
			ctx.getInput().pressKey(o -> o.keyAttack);
			ctx.waitTicks(2);
		}
		ctx.waitTicks(RingTuning.BLAST_CHARGE.ticks() + 2);
		ctx.takeScreenshot("blast_charged_" + clicks);
		ctx.getInput().releaseKey(o -> o.keyUse);
	}

	/** A stone hill 40 blocks deep in front of the player. */
	private static void hill(TestSingleplayerContext world) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			feet = p.blockPosition();
			var level = p.level();
			for (int x = -8; x <= 8; x++)
				for (int y = -1; y < 10; y++)
					for (int z = 4; z < 44; z++)
						level.setBlock(feet.offset(x, y, z), (y + z) % 5 == 0 ? Blocks.DIRT.defaultBlockState() : Blocks.STONE.defaultBlockState(), 2);
		});
	}

	/** How deep the tunnel at eye level reaches right now. */
	private static void count(TestSingleplayerContext world, String when) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			int depth = 0;
			for (int z = 4; z < 44; z++) {
				if (p.level().getBlockState(feet.offset(0, 1, z)).isAir() || p.level().getBlockState(feet.offset(0, 1, z)).is(com.sparky.lanternring.ModRegistry.BLAST_GLOW)) depth = z;
				else break;
			}
			System.out.println("[blast-drill] " + when + ": tunnel open to z+" + depth);
		});
	}
}
