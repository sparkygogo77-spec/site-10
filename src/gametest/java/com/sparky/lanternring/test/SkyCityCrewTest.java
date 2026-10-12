package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.city.BlueCity;
import com.sparky.lanternring.city.CityData;
import com.sparky.lanternring.city.CityPlanner;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

/**
 * End to end: a Blue founder whose floating village stands gathers a crew of three, they fly up,
 * take their U and the sky city's pieces go up one after another. Prints "SKYCREW ..." lines.
 */
public class SkyCityCrewTest implements FabricClientGameTest {
	private static BlockPos home;

	private static void log(String s) {
		System.out.println("SKYCREW " + s);
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode spectator @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			world.getServer().runOnServer(server -> {
				RingTuning.CORPS_BUILD.set(5);
				RingTuning.CITY_PIECE.set(5);
				RingTuning.CITY_SET.set(0.5);
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				home = p.blockPosition();
				BlockPos island = home.above(30);
				String pos = "[I;%d,%d,%d]";
				server.getCommands().performPrefixedCommand(server.createCommandSourceStack(), ("summon lanternring:corps_villager %d %d %d {Corps:%d,"
						+ "CorpsStage:2,CorpsFounder:1,CorpsHouses:3,CorpsIslandHouses:4,CorpsIslandBuilt:1b,CorpsHome:" + pos + ",CorpsIsland:" + pos + "}")
						.formatted(home.getX(), home.getY(), home.getZ() + 4, Corps.BLUE.ordinal(), home.getX(), island.getY() + 1, home.getZ(),
								island.getX(), island.getY(), island.getZ()));
				p.teleportTo(p.level(), home.getX() + 45.5, home.getY() + 50, home.getZ() - 55, java.util.Set.of(), 40f, 10f, true);
			});
			int lastBuilt = -1;
			for (int i = 0; i < 40; i++) {
				ctx.waitTicks(60);
				String line = world.getServer().computeOnServer(server -> {
					ServerLevel level = server.overworld();
					CityData.City city = CityData.get(level).near(home, 80);
					if (city == null) return "no city yet";
					return CityPlanner.describe(level, city) + " | active " + city.active() + " formed " + city.formed();
				});
				log("t=" + (i + 1) * 60 + " " + line);
				int built = world.getServer().computeOnServer(server -> {
					CityData.City city = CityData.get(server.overworld()).near(home, 80);
					if (city == null) return 0;
					int n = 0;
					for (BlueCity.Piece piece : BlueCity.Piece.values()) if (city.has(piece)) n++;
					return n;
				});
				if (built != lastBuilt && built > 0) {
					ctx.takeScreenshot("skycrew_" + built);
					lastBuilt = built;
				}
				if (i % 8 == 4) ctx.takeScreenshot("skycrew_t" + i);
				if (built >= 3) break;
			}
			log(lastBuilt >= 2 ? "PASS crew built " + lastBuilt + " pieces" : "FAIL crew built " + lastBuilt + " pieces");
		}
	}
}
