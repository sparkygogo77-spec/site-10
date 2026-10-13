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

/** Super sprint, then a crouch-charged super jump and its landing quake bouncing the cows round it. */
public class SuperJumpTest implements FabricClientGameTest {
	private static void report(TestSingleplayerContext world, BlockPos o, String when) {
		world.getServer().runOnServer(s -> {
			ServerPlayer p = s.getPlayerList().getPlayers().get(0);
			StringBuilder cows = new StringBuilder();
			for (Cow c : p.level().getEntitiesOfClass(Cow.class, new AABB(o).inflate(30))) {
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

			// Super sprint: how far a 30-tick sprint goes (vanilla sprint is about 5.6 blocks a second).
			report(world, o[0], "before sprint");
			ctx.getInput().holdKey(opt -> opt.keyUp);
			ctx.getInput().holdKey(opt -> opt.keySprint);
			ctx.waitTicks(10);
			report(world, o[0], "sprint start");
			ctx.waitTicks(30);
			report(world, o[0], "sprint +30 ticks");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.takeScreenshot("superjump_sprint");
			ctx.getInput().releaseKey(opt -> opt.keySprint);
			ctx.getInput().releaseKey(opt -> opt.keyUp);
			ctx.waitTicks(10);

			// Back to the start, with cows round where the jump will land.
			server.runOnServer(s -> s.getPlayerList().getPlayers().get(0).teleportTo(o[0].getX() + 0.5, o[0].getY(), o[0].getZ() + 0.5));
			server.runCommand("execute at @p run summon cow ~3 ~ ~");
			server.runCommand("execute at @p run summon cow ~-6 ~ ~2");
			server.runCommand("execute at @p run summon cow ~2 ~ ~9");
			server.runCommand("execute at @p run summon cow ~-1 ~ ~-13");
			ctx.waitTicks(20);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.getInput().holdKey(opt -> opt.keyShift);
			ctx.waitTicks(12);
			ctx.takeScreenshot("superjump_windup_armed");
			ctx.waitTicks(20);
			ctx.takeScreenshot("superjump_windup_full");
			ctx.getInput().holdKey(opt -> opt.keyJump);
			ctx.waitTicks(2);
			ctx.getInput().releaseKey(opt -> opt.keyJump);
			ctx.getInput().releaseKey(opt -> opt.keyShift);
			ctx.takeScreenshot("superjump_launch");
			ctx.waitTicks(6);
			ctx.takeScreenshot("superjump_rising");
			for (int t = 0; t < 70; t += 2) {
				ctx.waitTicks(2);
				report(world, o[0], "jump t=" + (t + 10));
				if (t == 30) ctx.takeScreenshot("superjump_falling");
				if (t == 40) ctx.takeScreenshot("superjump_touchdown");
				if (t == 40) {
					// Turn the head (and camera) sideways; the body lags behind, so the landing shows side on.
					ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
					ctx.getInput().lookAt(90f, 10f);
				}
				if (t == 42 || t == 46) ctx.takeScreenshot("superjump_landing_side_" + t);
			}
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.takeScreenshot("superjump_landed");
			ctx.waitTicks(4);
			ctx.takeScreenshot("superjump_quake");
			ctx.waitTicks(30);
			report(world, o[0], "after");
		}
	}
}
