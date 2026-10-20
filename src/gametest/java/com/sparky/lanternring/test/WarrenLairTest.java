package com.sparky.lanternring.test;

import com.sparky.lanternring.warren.WarrenEntrance;
import com.sparky.lanternring.warren.WarrenLair;
import com.sparky.lanternring.warren.WarrenSites;
import java.util.List;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;

/**
 * The Dread Warren lair in a real generated world: the Warren pinned at 256, 256 before the world is made, so the chunks
 * round it carve the lair as they generate. Down the length, up at the roof spikes, across, and in a den.
 */
public class WarrenLairTest implements FabricClientGameTest {
	/** The middle of region (0, 0): a real Warren keeps 200 blocks from its region's edges, its lair inside it. */
	private static final int[] SITE = {256, 256};

	@Override
	public void runTest(ClientGameTestContext ctx) {
		WarrenSites.testSite = SITE;
		WarrenSites.everywhereForTests = true;
		try (TestSingleplayerContext world = ctx.worldBuilder().setUseConsistentSettings(false).create()) {
			world.getServer().runCommand("gamemode spectator @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("effect give @a night_vision infinite 0 true");
			ctx.runOnClient(mc -> mc.options.renderDistance().set(12));
			BlockPos[] spot = new BlockPos[3];
			float[] yaw = new float[1];
			List<BlockPos>[] dens = new List[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				WarrenLair lair = WarrenLair.get(p.level().getSeed(), SITE);
				spot[0] = lair.standAt(-0.6, 0, 9);
				spot[1] = lair.standAt(0.6, 0.15, 7);
				spot[2] = lair.middle();
				yaw[0] = lair.lengthYaw();
				dens[0] = lair.denCentres();
				System.out.println("[WarrenLairTest] spots " + java.util.Arrays.toString(spot) + " yaw " + yaw[0] + " dens " + dens[0]);
				p.teleportTo(spot[0].getX() + 0.5, spot[0].getY(), spot[0].getZ() + 0.5);
			});
			// 1: from one end, down the whole length.
			ctx.getInput().lookAt(yaw[0], 10f);
			ctx.waitTicks(600);
			world.getServer().runOnServer(server -> {
				net.minecraft.server.level.ServerLevel l = server.overworld();
				WarrenLair lair = WarrenLair.get(l.getSeed(), SITE);
				int want = 0, has = 0;
				java.util.Map<String, Integer> what = new java.util.TreeMap<>();
				java.util.Set<String> chunks = new java.util.TreeSet<>();
				for (int x = SITE[0] - 40; x <= SITE[0] + 40; x += 4)
					for (int z = SITE[1] - 40; z <= SITE[1] + 40; z += 4)
						for (int y = -40; y <= 0; y += 4) {
							if (!lair.caveAir(x, y, z)) continue;
							want++;
							net.minecraft.world.level.block.state.BlockState b = l.getBlockState(new BlockPos(x, y, z));
							if (b.isAir()) has++;
							else {
								what.merge(b.getBlock().toString(), 1, Integer::sum);
								chunks.add((x >> 4) + "," + (z >> 4));
							}
						}
				System.out.println("[WarrenLairTest] cave air near the middle: " + has + " of " + want + " sampled cells are open; else "
						+ what + " in chunks " + chunks + "; chunks carved " + WarrenLair.CHUNKS);
			});
			ctx.takeScreenshot("warren_lair_1_length");
			// 2: from the other end, looking back, a little off the axis.
			world.getServer().runOnServer(server -> server.getPlayerList().getPlayers().get(0)
					.teleportTo(spot[1].getX() + 0.5, spot[1].getY(), spot[1].getZ() + 0.5));
			ctx.getInput().lookAt(yaw[0] + 180f, 6f);
			ctx.waitTicks(200);
			ctx.takeScreenshot("warren_lair_2_back");
			// 3: the roof and its spikes, from the middle.
			world.getServer().runOnServer(server -> server.getPlayerList().getPlayers().get(0)
					.teleportTo(spot[2].getX() + 0.5, spot[2].getY() + 4, spot[2].getZ() + 0.5));
			ctx.getInput().lookAt(yaw[0] + 30f, -50f);
			ctx.waitTicks(60);
			ctx.takeScreenshot("warren_lair_3_roof");
			// 4: inside a den, looking along it.
			world.getServer().runOnServer(server -> {
				BlockPos d = dens[0].get(0);
				server.getPlayerList().getPlayers().get(0).teleportTo(d.getX() + 0.5, d.getY(), d.getZ() + 0.5);
			});
			ctx.getInput().lookAt(yaw[0] + 90f, 12f);
			ctx.waitTicks(300);
			ctx.takeScreenshot("warren_lair_4_den");
			world.getServer().runOnServer(server -> System.out.println("[WarrenLairTest] entrances "
					+ WarrenEntrance.MADE.size() + ", tunnel stretches " + WarrenEntrance.TUNNELS.get()));
		} catch (Throwable t) {
			t.printStackTrace(System.out);
			throw t;
		} finally {
			WarrenSites.testSite = null;
			WarrenSites.everywhereForTests = false;
		}
	}
}
