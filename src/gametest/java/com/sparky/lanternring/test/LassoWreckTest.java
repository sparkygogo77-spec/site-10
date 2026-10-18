package com.sparky.lanternring.test;

import com.sparky.lanternring.Lasso;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.client.LassoFx;
import java.util.Locale;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

/**
 * Lasso wreck (J, 2026-10-16): swinging the bubble through a wall breaks it and flings the blocks
 * along the swing; letting go deconstructs the sphere; a mob thrown into a hillside gouges a crater.
 */
public class LassoWreckTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(40);
			world.getServer().runCommand("execute at @p run fill ~-30 ~-1 ~-30 ~30 ~-1 ~60 grass_block");
			world.getServer().runCommand("execute at @p run fill ~-30 ~ ~-30 ~30 ~20 ~60 air");
			world.getServer().runCommand("kill @e[type=!player]");
			world.getServer().runOnServer(server -> player(server).getMainHandItem().set(ModComponents.MODE, RingMode.TETHER.ordinal()));
			BlockPos feet = world.getServer().computeOnServer(s -> player(s).blockPosition());

			// 1. A stone wall to the right of the catch: swing the bubble through it.
			world.getServer().runCommand("execute at @p run fill ~-5 ~ ~1 ~-2 ~3 ~2 stone");
			world.getServer().runCommand("execute at @p run summon minecraft:pig ~ ~ ~4 {NoAI:1b}");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(0f, 15f);
			ctx.waitTicks(10);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(10);
			ctx.getInput().lookAt(0f, 8f);
			ctx.waitTicks(15);
			int before = stone(world, feet.offset(-5, 0, 1), feet.offset(-2, 3, 2));
			for (int i = 1; i <= 8; i++) {
				ctx.getInput().lookAt(i * 12f, 8f);
				ctx.waitTicks(1);
				if (i == 5) ctx.takeScreenshot("lasso_wreck_swing");
			}
			ctx.waitTicks(2);
			ctx.takeScreenshot("lasso_wreck_debris");
			int after = stone(world, feet.offset(-5, 0, 1), feet.offset(-2, 3, 2));
			// Debris flies the way the bubble was swinging: round from in front towards the right, which
			// at the wall (60-80 degrees round) is mostly back towards -z, and a little -x.
			Vec3 fly = world.getServer().computeOnServer(s -> {
				Vec3 sum = Vec3.ZERO;
				int n = 0;
				for (Entity e : player(s).level().getAllEntities()) {
					if (e instanceof FallingBlockEntity f) {
						sum = sum.add(f.position().subtract(Vec3.atCenterOf(feet.offset(-3, 1, 2))));
						n++;
					}
				}
				return n == 0 ? new Vec3(Double.NaN, 0, 0) : sum.scale(1.0 / n);
			});
			double flyX = fly.x;
			System.out.println(String.format(Locale.ROOT, "[lasso wreck] wall stone %d -> %d, debris mean offset from wall (%.2f %.2f %.2f)", before, after, fly.x, fly.y, fly.z));
			if (after > before - 6) throw new AssertionError("Swinging the bubble through the wall broke only " + (before - after) + " blocks");
			if (!(fly.z < -0.5)) throw new AssertionError("Wall debris didn't fly the way the bubble swung (mean offset " + fly + ")");
			boolean stillHeld = world.getServer().computeOnServer(s -> Lasso.heldCenter(player(s)) != null);
			if (!stillHeld) throw new AssertionError("Wrecking through the wall dropped the catch");

			// 2. Let go while still: the sphere deconstructs instead of popping or lingering.
			ctx.waitTicks(20);
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.waitTicks(2);
			int[] counts = ctx.computeOnClient(mc -> LassoFx.debugCounts());
			ctx.takeScreenshot("lasso_wreck_release_dissolve");
			System.out.println("[lasso wreck] after release: bubbles " + counts[0] + ", dissolving " + counts[1]);
			if (counts[0] != 0 || counts[1] != 1) throw new AssertionError("Letting go didn't deconstruct the sphere (bubbles " + counts[0] + ", dissolving " + counts[1] + ")");
			ctx.waitTicks(40);

			// 3. A hillside ahead: fling a pig into it with the wheel and let go mid-flight.
			world.getServer().runCommand("kill @e[type=!player]");
			world.getServer().runCommand("execute at @p run fill ~-8 ~ ~13 ~8 ~8 ~22 dirt");
			world.getServer().runCommand("execute at @p run summon minecraft:pig ~ ~ ~4 {NoAI:1b}");
			ctx.getInput().lookAt(0f, 15f);
			ctx.waitTicks(10);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(10);
			ctx.getInput().lookAt(0f, -4f);
			ctx.waitTicks(15);
			int hill = dirt(world, feet.offset(-8, 0, 13), feet.offset(8, 8, 22));
			ctx.getInput().scroll(4);
			ctx.waitTicks(2);
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.waitTicks(3);
			int[] thrown = ctx.computeOnClient(mc -> LassoFx.debugCounts());
			ctx.takeScreenshot("lasso_wreck_thrown");
			ctx.waitTicks(12);
			ctx.takeScreenshot("lasso_wreck_crater_hit");
			ctx.waitTicks(40);
			ctx.getInput().lookAt(0f, 20f);
			ctx.waitTicks(5);
			ctx.takeScreenshot("lasso_wreck_crater");
			int hillAfter = dirt(world, feet.offset(-8, 0, 13), feet.offset(8, 8, 22));
			System.out.println(String.format(Locale.ROOT, "[lasso wreck] thrown: bubbles %d dissolving %d; hill dirt %d -> %d", thrown[0], thrown[1], hill, hillAfter));
			if (thrown[0] != 0) throw new AssertionError("A thrown mob still flies inside a drawn bubble");
			if (hillAfter > hill - 8) throw new AssertionError("The thrown pig only knocked " + (hill - hillAfter) + " blocks out of the hillside");

			// 4. A glancing hit on flat ground, travelling +x and down: the gouge runs long along x.
			world.getServer().runCommand("kill @e[type=!player]");
			world.getServer().runCommand("execute at @p run fill ~-12 ~-4 ~-12 ~12 ~-1 ~-4 dirt");
			BlockPos hitAt = feet.offset(-6, 0, -8);
			world.getServer().runOnServer(s -> Lasso.testCrater(player(s), Vec3.atBottomCenterOf(hitAt), new Vec3(2.2, -0.9, 0), new Vec3(0, -1, 0), 0.8));
			int[] extent = world.getServer().computeOnServer(s -> {
				int minX = 99, maxX = -99, minZ = 99, maxZ = -99;
				for (BlockPos p : BlockPos.betweenClosed(feet.offset(-12, -4, -12), feet.offset(12, -1, -4))) {
					if (!player(s).level().getBlockState(p).isAir()) continue;
					minX = Math.min(minX, p.getX());
					maxX = Math.max(maxX, p.getX());
					minZ = Math.min(minZ, p.getZ());
					maxZ = Math.max(maxZ, p.getZ());
				}
				return new int[] {maxX - minX + 1, maxZ - minZ + 1};
			});
			world.getServer().runCommand("execute at @p run tp @p ~-10 ~3 ~-14 -50 30");
			ctx.waitTicks(30);
			ctx.takeScreenshot("lasso_wreck_crater_glancing");
			System.out.println("[lasso wreck] glancing crater: " + extent[0] + " long (x) by " + extent[1] + " wide (z)");
			if (extent[0] <= extent[1] + 1) throw new AssertionError("The glancing crater isn't longer along the travel (" + extent[0] + " x " + extent[1] + ")");
		}
	}

	private static int stone(TestSingleplayerContext world, BlockPos a, BlockPos b) {
		return count(world, a, b, true);
	}

	private static int dirt(TestSingleplayerContext world, BlockPos a, BlockPos b) {
		return count(world, a, b, false);
	}

	private static int count(TestSingleplayerContext world, BlockPos a, BlockPos b, boolean stone) {
		return world.getServer().computeOnServer(s -> {
			int n = 0;
			for (BlockPos p : BlockPos.betweenClosed(a, b)) {
				if (player(s).level().getBlockState(p).is(stone ? Blocks.STONE : Blocks.DIRT)) n++;
			}
			return n;
		});
	}

	private static ServerPlayer player(MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
