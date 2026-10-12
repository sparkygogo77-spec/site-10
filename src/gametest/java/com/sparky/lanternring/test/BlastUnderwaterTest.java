package com.sparky.lanternring.test;

import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.Blocks;

/** Fires the Blast in survival from inside a flooded basin with a sand seabed. */
public class BlastUnderwaterTest implements FabricClientGameTest {
	private static void report(TestSingleplayerContext world, BlockPos o, String when) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			var level = p.level();
			int sand = 0, stone = 0;
			for (int x = -20; x <= 20; x++)
				for (int y = -12; y <= 0; y++)
					for (int z = -10; z <= 50; z++) {
						var st = level.getBlockState(o.offset(x, y, z));
						if (st.is(Blocks.SAND)) sand++;
						else if (st.is(Blocks.STONE)) stone++;
					}
			System.out.println("[blast-underwater] " + when + ": sand=" + sand + " stone=" + stone + " pose=" + p.getPose() + " eyeInWater=" + p.isUnderWater()
					+ " using=" + p.isUsingItem() + " cooldown=" + p.getCooldowns().isOnCooldown(p.getMainHandItem()));
		});
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));

			// A sea 12 deep: stone, a sand seabed, water; the player floats in the middle.
			BlockPos[] origin = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos o = p.blockPosition().above(20);
				origin[0] = o;
				var level = p.level();
				for (int x = -22; x <= 22; x++)
					for (int y = -12; y <= 12; y++)
						for (int z = -12; z <= 52; z++) {
							boolean wall = Math.abs(x) == 22 || z == -12 || z == 52 || y == -12;
							level.setBlock(o.offset(x, y, z), wall ? Blocks.STONE.defaultBlockState()
									: y < -6 ? Blocks.STONE.defaultBlockState() : y < 0 ? Blocks.SAND.defaultBlockState()
									: y < 12 ? Blocks.WATER.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
						}
				p.teleportTo(o.getX() + 0.5, o.getY() + 6, o.getZ() + 0.5);
				p.getMainHandItem().set(ModComponents.MODE, RingMode.BLAST.ordinal());
			});
			world.getServer().runCommand("gamemode survival @a");
			ctx.getInput().lookAt(0f, 35f);
			ctx.waitTicks(40);
			report(world, origin[0], "before");
			ctx.takeScreenshot("blast_underwater_before");

			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(3);
			report(world, origin[0], "fire+3");
			ctx.takeScreenshot("blast_underwater_fire");
			ctx.waitTicks(30);
			report(world, origin[0], "fire+33");
			ctx.takeScreenshot("blast_underwater_after");

			// Again while swimming (sprinting underwater).
			ctx.getInput().holdKey(o -> o.keySprint);
			ctx.getInput().holdKey(o -> o.keyUp);
			ctx.waitTicks(30);
			report(world, origin[0], "swimming");
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(3);
			report(world, origin[0], "swim fire+3");
			ctx.takeScreenshot("blast_underwater_swim_fire");
			ctx.getInput().releaseKey(o -> o.keyUp);
			ctx.getInput().releaseKey(o -> o.keySprint);
			ctx.waitTicks(30);
			ctx.takeScreenshot("blast_underwater_swim_after");
		}
	}
}
