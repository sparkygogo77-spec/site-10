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

			lasso(ctx, world);
			wall(ctx, world);
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

	/** Lasso: a slam down into the ground dents it and shakes the camera; a throw bounces before it pops. */
	private static void lasso(ClientGameTestContext ctx, TestSingleplayerContext world) {
		world.getServer().runCommand("kill @e[type=!minecraft:player]");
		world.getServer().runCommand("execute at @p run tp @p ~ ~ ~-30");
		ctx.waitTicks(10);
		flatten(world);
		world.getServer().runCommand("execute at @p run summon minecraft:pig ~ ~ ~7 {NoAI:1b}");
		mode(world, RingMode.TETHER);
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
		ctx.getInput().lookAt(0f, 10f);
		ctx.waitTicks(10);
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(15);
		ctx.getInput().lookAt(0f, -70f);
		ctx.waitTicks(12);
		ctx.getInput().lookAt(0f, 70f);
		ctx.waitTicks(2);
		ctx.takeScreenshot("polish_lasso_slam_1");
		ctx.waitTicks(2);
		ctx.takeScreenshot("polish_lasso_slam_2");
		ctx.waitTicks(10);
		ctx.takeScreenshot("polish_lasso_dent");
		ctx.getInput().releaseKey(o -> o.keyUse);
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			int holes = 0;
			var base = p.blockPosition();
			for (int x = -8; x <= 8; x++)
				for (int z = -2; z <= 14; z++)
					for (int y = -2; y <= -1; y++)
						if (p.level().getBlockState(base.offset(x, y, z)).isAir()) holes++;
			System.out.println("[ring-polish] lasso slam dented " + holes + " blocks of ground");
		});
		ctx.waitTicks(30);

		// A throw out over open ground: it should bounce a few times before it pops.
		world.getServer().runCommand("kill @e[type=minecraft:pig]");
		world.getServer().runCommand("execute at @p run tp @p ~ ~ ~-20");
		ctx.waitTicks(10);
		flatten(world);
		world.getServer().runCommand("execute at @p run summon minecraft:pig ~ ~ ~6");
		ctx.getInput().lookAt(0f, 10f);
		ctx.waitTicks(10);
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(15);
		ctx.getInput().lookAt(0f, -60f);
		ctx.waitTicks(8);
		ctx.getInput().lookAt(0f, 35f);
		ctx.waitTicks(1);
		ctx.getInput().releaseKey(o -> o.keyUse);
		StringBuilder track = new StringBuilder();
		for (int i = 0; i < 60; i++) {
			ctx.waitTicks(1);
			if (i == 20) ctx.takeScreenshot("polish_lasso_bounce");
			double y = world.getServer().computeOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				return p.level().getEntitiesOfClass(Pig.class, p.getBoundingBox().inflate(80)).stream().findFirst().map(pig -> pig.getY() - p.getY()).orElse(-99.0);
			});
			track.append(String.format(java.util.Locale.ROOT, "%.1f ", y));
		}
		System.out.println("[ring-polish] thrown pig height: " + track);
	}

	/** Wall: pinned where you aim, dragged out to size, upright and then tilted as a ramp. */
	private static void wall(ClientGameTestContext ctx, TestSingleplayerContext world) {
		world.getServer().runCommand("kill @e[type=!minecraft:player]");
		world.getServer().runCommand("execute at @p run tp @p ~ ~ ~-30");
		world.getServer().runCommand("time set 6000");
		ctx.waitTicks(10);
		flatten(world);
		mode(world, RingMode.WALL);
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
		// Upright: aim level, pin it, drag right and up.
		ctx.getInput().lookAt(0f, 12f);
		ctx.waitTicks(10);
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(3);
		ctx.takeScreenshot("polish_wall_small");
		ctx.getInput().lookAt(-25f, -15f);
		ctx.waitTicks(10);
		ctx.takeScreenshot("polish_wall_dragged");
		ctx.getInput().releaseKey(o -> o.keyUse);
		ctx.waitTicks(5);
		ctx.takeScreenshot("polish_wall_standing");
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			int bricks = 0;
			for (var pos : net.minecraft.core.BlockPos.betweenClosed(p.blockPosition().offset(-20, -2, -2), p.blockPosition().offset(20, 25, 40)))
				if (p.level().getBlockState(pos).is(com.sparky.lanternring.ModRegistry.CONSTRUCT_BRICK)) bricks++;
			System.out.println("[ring-polish] wall drawn: " + bricks + " bricks");
		});
		// Tilted: aim down at the ground ahead for a ramp-like slab.
		world.getServer().runCommand("execute at @p run tp @p ~ ~ ~-30");
		ctx.waitTicks(10);
		flatten(world);
		ctx.getInput().lookAt(0f, 60f);
		ctx.waitTicks(10);
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.getInput().lookAt(20f, 40f);
		ctx.waitTicks(10);
		ctx.getInput().releaseKey(o -> o.keyUse);
		ctx.getInput().lookAt(0f, 20f);
		ctx.waitTicks(5);
		ctx.takeScreenshot("polish_wall_tilted");
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
