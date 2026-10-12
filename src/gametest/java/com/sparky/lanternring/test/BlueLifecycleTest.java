package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.city.BlueCity;
import com.sparky.lanternring.city.CityData;
import com.sparky.lanternring.city.CityPlanner;
import com.sparky.lanternring.corps.CorpsGolem;
import com.sparky.lanternring.corps.CorpsVillager;
import com.sparky.lanternring.corps.DivingHawk;
import java.util.List;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.npc.villager.Villager;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;

/**
 * The whole Blue Lantern life, start to finish, with nothing set up by hand: a plain villager
 * takes the oath at a Blue lantern, founds its village, its crew builds the ground houses, rises
 * and raises the floating island and its houses, then the sky city piece by piece, and once the
 * ports stand the flier highway and its hawks. Logs "BLUELIFE ..." lines every 3 s and fails on
 * a stage that stops moving.
 */
public class BlueLifecycleTest implements FabricClientGameTest {
	private static BlockPos home;

	private static void log(String s) {
		System.out.println("BLUELIFE " + s);
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
				RingTuning.LANTERN_OATH.set(1);
				RingTuning.CORPS_BUILD.set(5);
				RingTuning.CORPS_BUILD_TIME.set(2);
				RingTuning.CITY_PIECE.set(5);
				RingTuning.CITY_SET.set(0.5);
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				ServerLevel level = p.level();
				home = p.blockPosition();
				level.setBlock(home.offset(2, 0, 0), ModRegistry.POWER_BATTERY.defaultBlockState().setValue(Corps.PROPERTY, Corps.BLUE), 3);
				Villager v = EntityTypes.VILLAGER.create(level, EntitySpawnReason.MOB_SUMMONED);
				v.snapTo(home.getX() + 0.5, home.getY(), home.getZ() + 1.5, 0f, 0f);
				level.addFreshEntity(v);
				p.teleportTo(level, home.getX() + 22.5, home.getY() + 24, home.getZ() - 28, java.util.Set.of(), 35f, 25f, true);
			});
			String last = "";
			int still = 0, shot = 0;
			boolean moved = false;
			for (int i = 1; i <= 160; i++) {
				ctx.waitTicks(60);
				if (!moved) {
					// The oath only happens with a player near; then step back to watch the city.
					moved = true;
					world.getServer().runOnServer(server -> {
						ServerPlayer p = server.getPlayerList().getPlayers().get(0);
						p.teleportTo(p.level(), home.getX() + 30.5, home.getY() + 48, home.getZ() - 40, java.util.Set.of(), 37f, 22f, true);
					});
				}
				String line = world.getServer().computeOnServer(server -> describe(server.overworld()));
				log("t=" + i * 3 + "s " + line);
				// The progress part (everything before the crew's phase) must keep changing.
				String progress = line.contains(" crew ") ? line.substring(0, line.indexOf(" crew ")) : line;
				if (progress.equals(last)) {
					if (++still >= 20) {
						log("FAIL stalled for 60 s at: " + line);
						ctx.takeScreenshot("bluelife_stalled");
						return;
					}
				} else {
					still = 0;
					last = progress;
				}
				if (i % 10 == 0) ctx.takeScreenshot("bluelife_" + shot++);
				if (line.contains("hawks 4") && line.contains("city 13/13")) {
					log("PASS the whole Blue life ran: " + line);
					ctx.takeScreenshot("bluelife_done");
					return;
				}
			}
			log("FAIL ran out of time");
		}
	}

	private static String describe(ServerLevel level) {
		AABB box = new AABB(home).inflate(120, 120, 120);
		List<CorpsVillager> blues = level.getEntitiesOfClass(CorpsVillager.class, box, v -> v.isAlive() && v.corps() == Corps.BLUE);
		CorpsVillager founder = blues.stream().filter(CorpsVillager::leads).findFirst().orElse(null);
		int golems = level.getEntitiesOfClass(CorpsGolem.class, box, g -> g.isAlive()).size();
		int hawks = level.getEntitiesOfClass(DivingHawk.class, box, h -> h.isAlive()).size();
		StringBuilder s = new StringBuilder("blues " + blues.size());
		if (founder == null) return s.append(" (no founder)").toString();
		s.append(" stage ").append(founder.stage()).append(" island ").append(founder.island() != null);
		CityData.City city = CityData.get(level).near(founder.homePos(), 80);
		if (city != null) {
			int built = 0;
			for (BlueCity.Piece p : BlueCity.Piece.values()) if (city.has(p)) built++;
			s.append(" city ").append(built).append("/").append(BlueCity.Piece.values().length).append(" active ").append(city.active())
					.append(" formed ").append(city.formed());
		}
		s.append(" hawks ").append(hawks).append(" golems ").append(golems).append(" builds ").append(founder.crew().finished());
		s.append(" crew ").append(founder.crew().phase())
				.append(" members ").append(founder.crew().members().size())
				.append(" founder at ").append(founder.blockPosition().toShortString()).append(founder.flying() ? " flying" : " walking");
		if (city != null && level.getGameTime() % 600 < 60) s.append(" | ").append(CityPlanner.describe(level, city));
		return s.toString();
	}
}
