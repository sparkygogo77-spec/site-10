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
			ctx.getInput().releaseKey(opt -> opt.keyUp);
			ctx.getInput().holdKey(opt -> opt.keyRight);
			boolean[] cows = {false};
			for (int t = 8; t < 160; t += 4) {
				ctx.waitTicks(4);
				report(world, o[0], "jump t=" + t);
				if (t == 40) ctx.getInput().releaseKey(opt -> opt.keyRight);
				if (t == 60 && !cows[0]) {
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
				}
				if (t == 80) ctx.takeScreenshot("superjump_falling");
			}
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.takeScreenshot("superjump_landed");
			ctx.waitTicks(20);
			report(world, o[0], "after");
		}
	}
}
