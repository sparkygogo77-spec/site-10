package com.sparky.lanternring.test;

import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingTuning;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.animal.pig.Pig;

/**
 * The mode polish pass: the drill's burst at the end of its tunnel, the charged Shockwave
 * launching pigs, and the Anvil marker's crater outline and quicker drop.
 */
public class RingPolishTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 18000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(60);

			// Blast: a tap reaches 10 blocks into open air; the tip bursts at the end.
			mode(world, RingMode.BLAST);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, -8f);
			ctx.waitTicks(10);
			ctx.getInput().pressKey(o -> o.keyUse);
			for (int i = 1; i <= 5; i++) {
				ctx.waitTicks(1);
				ctx.takeScreenshot("polish_drill_end_" + i);
			}
			ctx.waitTicks(20);
			ctx.takeScreenshot("polish_drill_embers");

			// Shockwave: a tap, then a full charge, each throwing a ring of pigs up and away.
			mode(world, RingMode.PUSH);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(0f, 30f);
			shockwave(ctx, world, 0, "tap");
			shockwave(ctx, world, RingTuning.SHOCKWAVE_CHARGE.ticks() + 2, "charged");

			// Anvil: the marker with its dashed crater ring, then the drop.
			world.getServer().runCommand("kill @e[type=minecraft:pig]");
			flatten(world);
			mode(world, RingMode.ANVIL);
			ctx.getInput().lookAt(0f, 35f);
			ctx.waitTicks(10);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(12);
			ctx.takeScreenshot("polish_anvil_marker");
			ctx.getInput().releaseKey(o -> o.keyUse);
			for (int i = 1; i <= 6; i++) {
				ctx.waitTicks(3);
				ctx.takeScreenshot("polish_anvil_drop_" + (i * 3));
			}
			ctx.waitTicks(30);
			ctx.takeScreenshot("polish_anvil_landed");
		}
	}

	private static void shockwave(ClientGameTestContext ctx, TestSingleplayerContext world, int hold, String name) {
		world.getServer().runCommand("kill @e[type=minecraft:pig]");
		flatten(world);
		for (int[] at : new int[][] {{4, 3}, {-4, 4}, {0, 6}, {5, -2}, {-3, -5}, {9, 0}, {-10, 2}}) {
			world.getServer().runCommand("execute at @p run summon minecraft:pig ~" + at[0] + " ~ ~" + at[1] + "");
		}
		ctx.waitTicks(10);
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(Math.max(1, hold));
		ctx.getInput().releaseKey(o -> o.keyUse);
		ctx.waitTicks(5);
		ctx.takeScreenshot("polish_shockwave_" + name + "_growing");
		ctx.waitTicks(7);
		ctx.takeScreenshot("polish_shockwave_" + name + "_launched");
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			double top = 0;
			int hit = 0, total = 0;
			for (Pig pig : p.level().getEntitiesOfClass(Pig.class, p.getBoundingBox().inflate(40))) {
				total++;
				double up = pig.getY() - p.getY();
				if (up > 1) hit++;
				top = Math.max(top, up);
			}
			System.out.println("[ring-polish] shockwave " + name + ": " + hit + "/" + total + " pigs in the air, highest " + String.format("%.1f", top));
		});
		ctx.waitTicks(40);
	}

	/** Fresh flat grass round the player, so earlier shots' holes don't get in the way. */
	private static void flatten(TestSingleplayerContext world) {
		world.getServer().runCommand("execute at @p run fill ~-24 ~-1 ~-24 ~24 ~-1 ~24 minecraft:grass_block");
		world.getServer().runCommand("execute at @p run fill ~-24 ~ ~-24 ~24 ~12 ~24 air");
	}

	private static void mode(TestSingleplayerContext world, RingMode mode) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			p.getMainHandItem().set(ModComponents.MODE, mode.ordinal());
		});
	}
}
