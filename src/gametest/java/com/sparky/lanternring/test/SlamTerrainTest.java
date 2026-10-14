package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.client.CombatFx;
import com.sparky.lanternring.client.CombatInput;
import com.sparky.lanternring.client.LabSettings;
import com.sparky.lanternring.client.PowerSlide;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;

/**
 * J's in-game report (2026-10-14): the flight slams (H5, H3) and the power slide on ground that isn't a flat test floor.
 * Bumpy grass with plants on it: the slam's 7x7 crater must open on every column, whatever its height, and a second
 * super jump sliding through the first one's trench must still slide and clear.
 */
public class SlamTerrainTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			var server = world.getServer();
			server.runCommand("gamemode survival @a");
			server.runCommand("difficulty peaceful");
			server.runCommand("gamerule doDaylightCycle false");
			server.runCommand("gamerule doMobSpawning false");
			server.runCommand("time set 6000");
			ctx.waitTicks(60);
			BlockPos[] o = new BlockPos[1];
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				o[0] = p.blockPosition();
				ItemStack ring = Corps.GREEN.ring();
				ring.set(ModComponents.CHARGE, PowerRingItem.MAX_CHARGE);
				ring.set(ModComponents.FLIGHT, true);
				p.setItemInHand(InteractionHand.MAIN_HAND, ring);
			});
			int x = o[0].getX(), y = o[0].getY(), z = o[0].getZ();
			server.runCommand(String.format("forceload add %d %d %d %d", x - 40, z - 40, x + 40, z + 110));
			server.runCommand(String.format("fill %d %d %d %d %d %d dirt", x - 40, y - 5, z - 40, x + 40, y - 1, z + 110));
			server.runCommand(String.format("fill %d %d %d %d %d %d grass_block", x - 40, y - 1, z - 40, x + 40, y - 1, z + 110));
			server.runCommand(String.format("fill %d %d %d %d %d %d air", x - 40, y, z - 40, x + 40, y + 40, z + 110));
			// Bumps a block up and dips a block down, in a fixed pattern, with grass and flowers on top.
			server.runOnServer(s -> {
				ServerLevel level = s.getPlayerList().getPlayers().get(0).level();
				var grass = net.minecraft.world.level.block.Blocks.GRASS_BLOCK.defaultBlockState();
				var air = net.minecraft.world.level.block.Blocks.AIR.defaultBlockState();
				var plant = net.minecraft.world.level.block.Blocks.SHORT_GRASS.defaultBlockState();
				for (int dx = -30; dx <= 30; dx++) {
					for (int dz = -30; dz <= 110; dz++) {
						// Flat ground east of x - 5 for the super jumps' run-up; they land on the bumps.
						if (dx > -5 && dz < 70) continue;
						int h = Math.floorMod(dx * 7 + dz * 13 + (dx * dz) % 5, 5);
						BlockPos top = new BlockPos(x + dx, y - 1, z + dz);
						if (h == 0) {
							level.setBlock(top.above(), grass, 2);
							top = top.above();
						} else if (h == 1) {
							level.setBlock(top, air, 2);
							level.setBlock(top.below(), grass, 2);
							top = top.below();
						}
						if (Math.floorMod(dx + dz * 3, 4) == 0) level.setBlock(top.above(), plant, 2);
					}
				}
			});
			server.runCommand("kill @e[type=!player]");
			ctx.waitTicks(10);

			String h5 = slam(ctx, world, x - 14, y, z + 14, LabSettings.FlightSlam.H5);
			String h3 = slam(ctx, world, x - 14, y, z - 14, LabSettings.FlightSlam.H3);

			// Two super jumps along the same line: the second lands in the first one's trench.
			float first = jump(ctx, world, o[0], 95, "first");
			float second = jump(ctx, world, o[0], 95, "second");
			System.out.println(String.format("[slam terrain] slides: first %.2f second %.2f", first, second));
			if (h5 != null || h3 != null || first < 2 || second < 2) {
				throw new AssertionError("slam terrain: " + h5 + " " + h3 + " slides " + first + " " + second);
			}
		}
	}

	/** The top non-air block's height in each column of the 7x7 round c (plants don't count). */
	private static int[] heights(ServerLevel level, BlockPos c) {
		int[] out = new int[49];
		int i = 0;
		for (int dx = -3; dx <= 3; dx++) {
			for (int dz = -3; dz <= 3; dz++) {
				out[i++] = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, c.getX() + dx, c.getZ() + dz);
			}
		}
		return out;
	}

	/** Dives at 70 degrees from 24 blocks up and slams; returns null, or what went wrong. */
	private static String slam(ClientGameTestContext ctx, TestSingleplayerContext world, int x, int y, int z, LabSettings.FlightSlam take) {
		var server = world.getServer();
		String name = take.name().toLowerCase();
		ctx.runOnClient(mc -> LabSettings.get().flightSlam = take);
		server.runCommand(String.format("tp @p %.1f %d %.1f 0 70", x + 0.5, y + 24, z + 0.5));
		ctx.waitTicks(5);
		ctx.runOnClient(mc -> {
			mc.player.getAbilities().flying = true;
			mc.player.onUpdateAbilities();
			mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);
		});
		ctx.waitTicks(5);
		ctx.getInput().lookAt(0f, 70f);
		ctx.getInput().holdKey(opt -> opt.keyUp);
		ctx.getInput().holdKey(opt -> opt.keySprint);
		boolean fired = false;
		for (int t = 0; t < 80 && !fired; t++) {
			ctx.waitTick();
			fired = ctx.computeOnClient(mc -> CombatInput.locked());
		}
		ctx.getInput().releaseKey(opt -> opt.keyUp);
		ctx.getInput().releaseKey(opt -> opt.keySprint);
		if (!fired) return name + " never fired";
		for (int t = 0; t < 10 && !ctx.computeOnClient(mc -> mc.player.onGround()); t++) ctx.waitTick();
		double[] feet = ctx.computeOnClient(mc -> new double[] {mc.player.getX(), mc.player.getY(), mc.player.getZ()});
		BlockPos c = BlockPos.containing(feet[0], feet[1] - 0.5, feet[2]);
		int[][] before = new int[1][];
		server.runOnServer(s -> before[0] = heights(s.getPlayerList().getPlayers().get(0).level(), c));
		ctx.getInput().lookAt(0f, 50f);
		ctx.waitTicks(6);
		int craters = ctx.computeOnClient(mc -> CombatFx.craters());
		ctx.takeScreenshot("terrain_slam_" + name + "_lit");
		ctx.waitTicks(30);
		ctx.takeScreenshot("terrain_slam_" + name + "_crater");
		int[] opened = {0};
		server.runOnServer(s -> {
			int[] after = heights(s.getPlayerList().getPlayers().get(0).level(), c);
			for (int i = 0; i < after.length; i++) if (after[i] < before[0][i]) opened[0]++;
		});
		System.out.println(String.format("[slam terrain] %s: touchdown y %.2f, columns opened %d of 48, craters drawn %d", name, feet[1] - y, opened[0], craters));
		ctx.runOnClient(mc -> mc.player.setDeltaMovement(Vec3.ZERO));
		return opened[0] >= 44 && craters > 0 ? null : name + ": opened " + opened[0] + " craters " + craters;
	}

	/** Sprints, super jumps north to south from 30 blocks back, and lands; returns how far it slid. */
	private static float jump(ClientGameTestContext ctx, TestSingleplayerContext world, BlockPos o, int sprint, String name) {
		world.getServer().runOnServer(s -> s.getPlayerList().getPlayers().get(0).teleportTo(o.getX() + 10.5, o.getY(), o.getZ() - 30.5));
		ctx.getInput().lookAt(0f, 0f);
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
		ctx.waitTicks(15);
		ctx.getInput().holdKey(opt -> opt.keyUp);
		ctx.getInput().holdKey(opt -> opt.keySprint);
		ctx.waitTicks(sprint);
		ctx.getInput().holdKey(opt -> opt.keyJump);
		ctx.waitTicks(2);
		ctx.getInput().releaseKey(opt -> opt.keyJump);
		ctx.getInput().releaseKey(opt -> opt.keySprint);
		boolean landed = false;
		for (int t = 0; t < 240 && !landed; t++) {
			ctx.waitTick();
			landed = ctx.computeOnClient(mc -> PowerSlide.locked());
		}
		ctx.getInput().releaseKey(opt -> opt.keyUp);
		Vec3 touch = ctx.computeOnClient(mc -> mc.player.position());
		ctx.getInput().lookAt(0f, 35f);
		ctx.waitTicks(3);
		ctx.takeScreenshot("terrain_slide_" + name + "_skid");
		ctx.waitTicks(6);
		ctx.takeScreenshot("terrain_slide_" + name + "_halt");
		// From above, to see the trench and its lining.
		ctx.getInput().lookAt(180f, 80f);
		ctx.waitTicks(2);
		ctx.takeScreenshot("terrain_slide_" + name + "_above");
		ctx.getInput().lookAt(0f, 35f);
		ctx.waitTicks(20);
		ctx.takeScreenshot("terrain_slide_" + name + "_after");
		Vec3 end = ctx.computeOnClient(mc -> mc.player.position());
		float slid = (float) Math.sqrt(Math.pow(end.x - touch.x, 2) + Math.pow(end.z - touch.z, 2));
		System.out.println(String.format("[slam terrain] slide %s: landed %s touchdown (%.2f, %.2f, %.2f) slid %.2f end y %.2f", name, landed,
				touch.x - o.getX(), touch.y - o.getY(), touch.z - o.getZ(), slid, end.y - o.getY()));
		return landed ? slid : -1;
	}
}
