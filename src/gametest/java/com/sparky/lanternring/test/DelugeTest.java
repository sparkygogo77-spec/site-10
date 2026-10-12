package com.sparky.lanternring.test;

import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.ModFluids;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingTuning;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.Blocks;

/** Drops a level 3 Deluge on a grass field: the ball's bottom crashing down, the ring's glow, the burst, the green flood, a swim, the drain. */
public class DelugeTest implements FabricClientGameTest {
	private static void report(TestSingleplayerContext world, BlockPos o, String when) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			var level = p.level();
			int sources = 0, flowing = 0;
			for (BlockPos pos : BlockPos.betweenClosed(o.offset(-40, -12, -15), o.offset(40, 16, 65))) {
				var fluid = level.getFluidState(pos);
				if (fluid.getType() == ModFluids.SOURCE) sources++;
				else if (fluid.getType() == ModFluids.FLOWING) flowing++;
			}
			System.out.println("[deluge] " + when + ": sources=" + sources + " flowing=" + flowing
					+ " inWater=" + p.isInWater() + " underWater=" + p.isUnderWater());
		});
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));

			BlockPos[] origin = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos o = p.blockPosition().above(10);
				origin[0] = o;
				var level = p.level();
				for (int x = -40; x <= 40; x++)
					for (int y = -4; y <= 30; y++)
						for (int z = -15; z <= 65; z++) {
							level.setBlock(o.offset(x, y, z), y < -1 ? Blocks.STONE.defaultBlockState()
									: y == -1 ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
						}
				// A couple of steps so the flood has something to run down.
				for (int x = 6; x <= 12; x++)
					for (int z = 20; z <= 26; z++) level.setBlock(o.offset(x, 0, z), Blocks.STONE.defaultBlockState(), 2);
				p.teleportTo(o.getX() + 0.5, o.getY() + 4, o.getZ() - 6.5);
				p.getAbilities().flying = true;
				p.onUpdateAbilities();
				p.getMainHandItem().set(ModComponents.MODE, RingMode.DELUGE.ordinal());
				p.getMainHandItem().set(ModComponents.DELUGE_LEVEL, 2);
			});
			for (int[] at : new int[][] {{4, 18}, {-6, 22}, {10, 28}, {-12, 14}, {0, 32}}) {
				world.getServer().runCommand("summon minecraft:pig " + (origin[0].getX() + at[0]) + " " + origin[0].getY() + " " + (origin[0].getZ() + at[1]));
			}
			ctx.getInput().lookAt(0f, 14f);
			ctx.waitTicks(30);

			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(12);
			ctx.takeScreenshot("deluge_marker");
			ctx.getInput().releaseKey(o -> o.keyUse);
			// The ball forms up high while the ring glows; its bottom crashes down and the top left
			// floating dissolves from its top surface down as the bottom falls.
			ctx.getInput().lookAt(0f, -20f);
			for (int i = 0; i < 16; i++) {
				ctx.waitTicks(1);
				ctx.takeScreenshot("deluge_drop_" + i);
			}
			ctx.getInput().lookAt(0f, 14f);
			ctx.waitTicks(10);
			report(world, origin[0], "flooded");
			ctx.takeScreenshot("deluge_flood");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("deluge_flood_night");
			world.getServer().runCommand("time set 6000");

			// Swim in it.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos o = origin[0];
				p.getAbilities().flying = false;
				p.onUpdateAbilities();
				p.teleportTo(o.getX() + 0.5, o.getY() + 0.1, o.getZ() + 14.5);
			});
			ctx.getInput().lookAt(0f, 10f);
			ctx.waitTicks(20);
			report(world, origin[0], "wading");
			ctx.takeScreenshot("deluge_wading");
			world.getServer().runOnServer(server -> server.getPlayerList().getPlayers().get(0).setPose(net.minecraft.world.entity.Pose.SWIMMING));
			ctx.getInput().holdKey(o -> o.keyShift);
			ctx.waitTicks(10);
			ctx.takeScreenshot("deluge_eye_level");
			ctx.getInput().releaseKey(o -> o.keyShift);

			// Level 3 lasts 25 s from the burst; about 6 s have gone.
			ctx.waitTicks(20 * 14);
			report(world, origin[0], "20s");
			ctx.waitTicks(20 * 3);
			report(world, origin[0], "23s");
			ctx.takeScreenshot("deluge_draining");
			ctx.waitTicks(20 * 4);
			report(world, origin[0], "27s");
			ctx.takeScreenshot("deluge_drained");
		}
	}
}
