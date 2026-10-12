package com.sparky.lanternring.test;

import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.city.BlueCity;
import com.sparky.lanternring.city.CityBuilds;
import com.sparky.lanternring.city.CityData;
import com.sparky.lanternring.city.CityPlanner;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.npc.villager.Villager;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

/**
 * The Blue sky city's systems: the planner's order, a piece forming as blue light and setting
 * into Skystone, resuming from the saved block after its builders leave, repairs, and the whole
 * city from outside. Results print as "SKYCITY ..." lines.
 */
public class SkyCityTest implements FabricClientGameTest {
	private static final List<Villager> BUILDERS = new ArrayList<>();
	private static CityData.City city;
	private static CityBuilds.Job job;

	private static void log(String s) {
		System.out.println("SKYCITY " + s);
	}

	private static void check(boolean ok, String what) {
		log((ok ? "PASS " : "FAIL ") + what);
		if (!ok) throw new AssertionError(what);
	}

	private static void spawnBuilders(ServerLevel level, Vec3 focus) {
		BUILDERS.clear();
		// A wide U facing the piece.
		double[][] at = {{-7, 4, -3}, {0, 5, -8}, {7, 4, -3}};
		for (double[] o : at) {
			Villager v = EntityTypes.VILLAGER.create(level, EntitySpawnReason.COMMAND);
			v.snapTo(focus.x + o[0], focus.y + o[1], focus.z + o[2] - 10, 0f, 0f);
			v.setNoAi(true);
			v.setNoGravity(true);
			level.addFreshEntity(v);
			BUILDERS.add(v);
		}
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("gamemode spectator @a");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			world.getServer().runOnServer(server -> {
				RingTuning.CITY_PIECE.set(4);
				RingTuning.CITY_SET.set(1);
				ServerLevel level = server.overworld();
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos village = p.blockPosition();
				city = BlueCity.cityFor(level, village);
				check(BlueCity.cityFor(level, village.offset(10, 0, 10)) == city, "a nearby village shares the city");
				check(city.anchor.getY() > village.getY() + 20, "city floats high over the village");
				check(CityPlanner.choose(level, city) == BlueCity.Piece.FOUNDATION, "foundation first");
				spawnBuilders(level, BlueCity.focus(city.anchor, BlueCity.Piece.FOUNDATION));
				job = BlueCity.buildNext(level, city, BUILDERS);
				check(job != null && job.piece() == BlueCity.Piece.FOUNDATION, "building the foundation");
				p.teleportTo(level, city.anchor.getX() + 0.5, city.anchor.getY() + 8, city.anchor.getZ() - 34, java.util.Set.of(), 0f, 15f, true);
			});
			ctx.waitTicks(45);
			ctx.takeScreenshot("skycity_forming");
			ctx.waitTicks(150);
			world.getServer().runOnServer(server -> {
				ServerLevel level = server.overworld();
				check(city.has(BlueCity.Piece.FOUNDATION), "foundation finished and saved");
				check(level.getBlockState(city.anchor.offset(3, 0, 0)).is(com.sparky.lanternring.city.CityBlocks.SKYSTONE_TILES), "light set into skystone");
				check(CityPlanner.choose(level, city) == BlueCity.Piece.SPIRE, "spire next");
				job = BlueCity.buildNext(level, city, BUILDERS);
			});
			ctx.waitTicks(30);
			ctx.takeScreenshot("skycity_spire_forming");
			world.getServer().runOnServer(server -> {
				// The builders leave half way: the job waits, then is put away with its progress saved.
				log("spire formed so far " + city.formed());
				check(city.formed() > 0, "spire progress saved");
				for (Villager v : BUILDERS) v.discard();
			});
			ctx.waitTicks(230);
			world.getServer().runOnServer(server -> {
				ServerLevel level = server.overworld();
				int saved = city.formed();
				check(!CityBuilds.running(job), "idle job put away");
				spawnBuilders(level, BlueCity.focus(city.anchor, BlueCity.Piece.SPIRE));
				job = BlueCity.buildNext(level, city, BUILDERS);
				check(job.piece() == BlueCity.Piece.SPIRE && city.formed() == saved, "spire resumes from block " + saved);
			});
			ctx.waitTicks(160);
			world.getServer().runOnServer(server -> {
				ServerLevel level = server.overworld();
				check(city.has(BlueCity.Piece.SPIRE), "spire finished");
				log(CityPlanner.describe(level, city));
				BlueCity.Piece next = CityPlanner.choose(level, city);
				log("next " + next);
				check(next == BlueCity.Piece.TOWER_1, "with people and no beds, a dwelling tower comes next");
				BlueCity.buildAll(level, city);
				check(city.complete(), "whole city built");
				check(CityPlanner.choose(level, city) == null, "nothing left to build");
				// Knock the lamp off the crown: the planner repairs it.
				level.setBlock(city.anchor.offset(0, 58, 0), Blocks.AIR.defaultBlockState(), 3);
				check(CityPlanner.choose(level, city) == BlueCity.Piece.CROWN, "broken crown gets repaired");
				for (Villager v : BUILDERS) v.discard();
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.teleportTo(level, city.anchor.getX() + 50.5, city.anchor.getY() + 30, city.anchor.getZ() - 60, java.util.Set.of(), 40f, 9f, true);
			});
			ctx.waitTicks(80);
			world.getServer().runOnServer(server -> {
				// Garden water stays in its channels: none below the disc.
				ServerLevel level = server.overworld();
				int spilt = 0;
				for (BlockPos pos : BlockPos.betweenClosed(city.anchor.offset(-32, -40, -32), city.anchor.offset(32, -1, 32))) {
					if (!level.getFluidState(pos).isEmpty()) {
						if (spilt++ < 5) log("water at " + pos.subtract(city.anchor).toShortString());
					}
				}
				for (BlockPos pos : BlockPos.betweenClosed(city.anchor.offset(-16, 1, -16), city.anchor.offset(16, 1, 16))) {
					if (!level.getFluidState(pos).isEmpty() && !level.getFluidState(pos).isSource()) {
						if (spilt++ < 10) log("flowing at " + pos.subtract(city.anchor).toShortString());
					}
				}
				check(spilt == 0, "no water spills from the gardens");
			});
			ctx.takeScreenshot("skycity_whole");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("skycity_night");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.teleportTo(server.overworld(), city.anchor.getX() + 30.5, city.anchor.getY() + 16, city.anchor.getZ() - 30, java.util.Set.of(), 45f, 12f, true);
			});
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			ctx.takeScreenshot("skycity_close");
		}
	}
}
