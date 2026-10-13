package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.animal.cow.Cow;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;

/** A super sprint building up, then a sprint-charged super jump steered in the air, and its landing quake bouncing the cows round it. */
public class SuperJumpTest implements FabricClientGameTest {
	private static void report(TestSingleplayerContext world, BlockPos o, String when) {
		world.getServer().runOnServer(s -> {
			ServerPlayer p = s.getPlayerList().getPlayers().get(0);
			StringBuilder cows = new StringBuilder();
			for (Cow c : p.level().getEntitiesOfClass(Cow.class, p.getBoundingBox().inflate(30))) {
				cows.append(String.format(" cow(%.1f,%.3f,%.1f)", c.getX() - o.getX(), c.getY() - o.getY(), c.getZ() - o.getZ()));
			}
			System.out.println(String.format("[superjump] %s: player (%.2f, %.2f, %.2f) hp=%.1f charge=%d%s", when, p.getX() - o.getX(), p.getY() - o.getY(),
					p.getZ() - o.getZ(), p.getHealth(), PowerRingItem.getCharge(p.getMainHandItem()), cows));
		});
	}

	/** How the ground round the player came out: charred, blackstone, and the crater dug out of the original surface (o's floor). */
	private static void ground(TestSingleplayerContext world, BlockPos o, String when) {
		world.getServer().runOnServer(s -> {
			ServerPlayer p = s.getPlayerList().getPlayers().get(0);
			int coarse = 0, black = 0, top = 0, second = 0, third = 0;
			BlockPos c = new BlockPos(p.getBlockX(), o.getY() - 1, p.getBlockZ());
			for (BlockPos q : BlockPos.betweenClosed(c.offset(-30, -5, -30), c.offset(30, 0, 30))) {
				var st = p.level().getBlockState(q);
				if (st.is(net.minecraft.world.level.block.Blocks.COARSE_DIRT)) coarse++;
				else if (st.is(net.minecraft.world.level.block.Blocks.BLACKSTONE)) black++;
				else if (st.isAir() && q.distManhattan(c) <= 14) {
					if (q.getY() == c.getY()) top++;
					else if (q.getY() == c.getY() - 1) second++;
					else if (q.getY() == c.getY() - 2) third++;
				}
			}
			long debris = p.level().getEntitiesOfClass(net.minecraft.world.entity.Display.BlockDisplay.class, p.getBoundingBox().inflate(20)).size();
			System.out.println("[superjump] " + when + ": coarse dirt=" + coarse + " blackstone=" + black + " crater layers=" + top + "/" + second + "/" + third
					+ " debris displays left=" + debris);
		});
	}

	/** Whether the player is standing again (server side). */
	private static boolean grounded(TestSingleplayerContext world) {
		boolean[] on = {false};
		world.getServer().runOnServer(s -> on[0] = s.getPlayerList().getPlayers().get(0).onGround());
		return on[0];
	}

	/** Waits for the landing, then screenshots the pad forming, the held landing and the stand-up. */
	private static void landing(ClientGameTestContext ctx, TestSingleplayerContext world, BlockPos o, String name) {
		for (int t = 0; t < 200 && !grounded(world); t += 1) ctx.waitTick();
		ctx.getInput().releaseKey(opt -> opt.keyUp);
		report(world, o, name + " touchdown");
		ctx.waitTicks(3);
		ctx.takeScreenshot("superjump_" + name + "_pad_forming");
		ctx.waitTicks(7);
		ctx.takeScreenshot("superjump_" + name + "_landing_pose");
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
		ctx.takeScreenshot("superjump_" + name + "_landing_front");
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
		ctx.waitTicks(16);
		ctx.takeScreenshot("superjump_" + name + "_standing");
		ctx.waitTicks(30);
		ctx.takeScreenshot("superjump_" + name + "_after_fade");
	}

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
			server.runCommand("execute at @p run fill ~-30 ~-5 ~-30 ~30 ~-1 ~60 dirt");
			server.runCommand("execute at @p run fill ~-30 ~-1 ~-30 ~30 ~-1 ~60 grass_block");
			server.runCommand("execute at @p run fill ~-30 ~ ~-30 ~30 ~40 ~60 air");
			server.runCommand("kill @e[type=!player]");
			BlockPos[] o = new BlockPos[1];
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				o[0] = p.blockPosition();
				ItemStack ring = Corps.GREEN.ring();
				ring.set(ModComponents.CHARGE, PowerRingItem.MAX_CHARGE);
				p.setItemInHand(InteractionHand.MAIN_HAND, ring);
			});
			ctx.getInput().lookAt(0f, 0f);
			server.runOnServer(s -> s.getPlayerList().getPlayers().get(0).teleportTo(o[0].getX() + 0.5, o[0].getY(), o[0].getZ() - 24.5));
			ctx.waitTicks(10);

			// Super sprint builds up: distance per 10 ticks over a 5 s run (vanilla sprint is 2.8 blocks per 10 ticks).
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			report(world, o[0], "run t=0");
			ctx.getInput().holdKey(opt -> opt.keyUp);
			ctx.getInput().holdKey(opt -> opt.keySprint);
			for (int t = 10; t <= 90; t += 10) {
				ctx.waitTicks(10);
				report(world, o[0], "run t=" + t);
				if (t == 20) ctx.takeScreenshot("superjump_run_building");
				if (t == 60) ctx.takeScreenshot("superjump_run_top_speed");
			}
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.takeScreenshot("superjump_run_front");
			// Fully charged: jump, then steer right in the air.
			ctx.getInput().holdKey(opt -> opt.keyJump);
			ctx.waitTicks(2);
			ctx.getInput().releaseKey(opt -> opt.keyJump);
			ctx.getInput().releaseKey(opt -> opt.keySprint);
			ctx.takeScreenshot("superjump_launch");
			ctx.waitTicks(6);
			ctx.takeScreenshot("superjump_rising");
			ctx.waitTicks(1);
			ctx.takeScreenshot("superjump_rising_trail");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.waitTicks(1);
			ctx.takeScreenshot("superjump_rising_arm_front");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().releaseKey(opt -> opt.keyUp);
			ctx.getInput().holdKey(opt -> opt.keyRight);
			boolean[] cows = {false};
			for (int t = 8; t < 60; t += 4) {
				ctx.waitTicks(4);
				report(world, o[0], "jump t=" + t);
				if (t == 40) ctx.getInput().releaseKey(opt -> opt.keyRight);
			}
			cows[0] = true;
			// Cows round the spot below, for the landing quake to bounce.
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				for (int[] d : new int[][] {{3, 0}, {-6, 2}, {2, 9}, {-1, -13}}) {
					Cow c = net.minecraft.world.entity.EntityTypes.COW.create(p.level(), net.minecraft.world.entity.EntitySpawnReason.COMMAND);
					c.setPos(p.getX() + d[0], o[0].getY(), p.getZ() + d[1]);
					p.level().addFreshEntity(c);
				}
			});
			ctx.waitTicks(14);
			ctx.takeScreenshot("superjump_falling");
			ctx.waitTicks(6);
			ctx.takeScreenshot("superjump_falling_buildup");
			landing(ctx, world, o[0], "normal");
			ground(world, o[0], "normal landing");

			// A primed landing: a short run and jump, left-click held on the way down.
			server.runCommand("kill @e[type=cow]");
			ctx.runOnClient(mc -> {
				com.sparky.lanternring.client.LabSettings lab = com.sparky.lanternring.client.LabSettings.get();
				lab.superLanding = com.sparky.lanternring.client.LabSettings.SuperLanding.E2;
				lab.superWall = com.sparky.lanternring.client.LabSettings.SuperWall.W1;
				lab.superFallArm = com.sparky.lanternring.client.LabSettings.SuperFallArm.D1B;
			});
			server.runOnServer(s -> s.getPlayerList().getPlayers().get(0).teleportTo(o[0].getX() + 15.5, o[0].getY(), o[0].getZ() - 24.5));
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(10);
			ctx.getInput().holdKey(opt -> opt.keyUp);
			ctx.getInput().holdKey(opt -> opt.keySprint);
			ctx.waitTicks(40);
			ctx.getInput().holdKey(opt -> opt.keyJump);
			ctx.waitTicks(2);
			ctx.getInput().releaseKey(opt -> opt.keyJump);
			ctx.getInput().releaseKey(opt -> opt.keySprint);
			ctx.getInput().releaseKey(opt -> opt.keyUp);
			ctx.waitTicks(10);
			ctx.getInput().holdKey(opt -> opt.keyAttack);
			for (int t = 0; t < 24; t += 4) {
				ctx.waitTicks(4);
				report(world, o[0], "primed t=" + t);
				if (t == 16) ctx.takeScreenshot("superjump_primed_shell");
			}
			landing(ctx, world, o[0], "primed");
			ctx.getInput().releaseKey(opt -> opt.keyAttack);
			ground(world, o[0], "primed landing");

			// The deeper fall: a short jump off a ledge ten blocks up, landing well below the take-off (E3, guard walls, deep crater).
			ctx.runOnClient(mc -> com.sparky.lanternring.client.LabSettings.get().superLanding = com.sparky.lanternring.client.LabSettings.SuperLanding.E1);
			server.runCommand(String.format("fill %d %d %d %d %d %d stone", o[0].getX() - 17, o[0].getY() + 9, o[0].getZ() - 31, o[0].getX() - 13,
					o[0].getY() + 9, o[0].getZ() - 8));
			server.runOnServer(s -> s.getPlayerList().getPlayers().get(0).teleportTo(o[0].getX() - 14.5, o[0].getY() + 10, o[0].getZ() - 19.5));
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(10);
			ctx.getInput().holdKey(opt -> opt.keyUp);
			ctx.getInput().holdKey(opt -> opt.keySprint);
			ctx.waitTicks(30);
			ctx.getInput().holdKey(opt -> opt.keyJump);
			ctx.waitTicks(2);
			ctx.getInput().releaseKey(opt -> opt.keyJump);
			ctx.getInput().releaseKey(opt -> opt.keySprint);
			// Steering on ahead, off the ledge.
			ctx.waitTicks(6);
			landing(ctx, world, o[0], "deep");
			ground(world, o[0], "deep landing");
		}
	}
}
