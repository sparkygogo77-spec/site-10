package com.sparky.lanternring.test;

import com.sparky.lanternring.corps.DivingHawk;
import com.sparky.lanternring.corps.FlierHighway;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.entity.EntityTypeTest;

/**
 * The Blue Lantern flier highway and its armored diving hawks: the hawk close up perched and in
 * flight, the highway's lanes and pads over a floating spot, and a hawk stooping onto a husk.
 */
public class HawkHighwayTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			var server = world.getServer();
			server.runCommand("gamemode creative @a");
			server.runCommand("difficulty normal");
			server.runCommand("gamerule doDaylightCycle false");
			server.runCommand("gamerule doMobSpawning false");
			server.runCommand("time set 6000");
			ctx.waitTicks(40);
			server.runCommand("execute at @p run fill ~-30 ~-1 ~-30 ~30 ~-1 ~30 grass_block");
			server.runCommand("execute at @p run fill ~-30 ~ ~-30 ~30 ~30 ~30 air");
			server.runCommand("kill @e[type=!player]");

			// A hawk on the ground in front of the camera: the perched pose, side and front.
			server.runCommand("execute at @p run summon lanternring:diving_hawk ~ ~ ~5 {NoAI:1b,Rotation:[90f,0f]}");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 25f);
			ctx.waitTicks(30);
			ctx.takeScreenshot("hawk_perched_side");
			server.runCommand("execute as @e[type=lanternring:diving_hawk] at @s run tp @s ~ ~ ~ 180 0");
			ctx.waitTicks(10);
			ctx.takeScreenshot("hawk_perched_front");
			server.runCommand("kill @e[type=lanternring:diving_hawk]");

			// A wild hawk takes off and circles: flight poses.
			server.runCommand("execute at @p run summon lanternring:diving_hawk ~ ~ ~16");
			server.runCommand("gamemode spectator @p");
			ctx.getInput().lookAt(0f, -12f);
			for (int i = 0; i < 6; i++) {
				ctx.waitTicks(i == 0 ? 120 : 12);
				ctx.takeScreenshot("hawk_flight_" + i);
			}
			// A husk: it climbs, folds and stoops onto it with its lance.
			server.runCommand("execute at @p run summon husk ~3 ~ ~14");
			ctx.getInput().lookAt(0f, 5f);
			for (int i = 0; i < 10; i++) {
				ctx.waitTicks(8);
				ctx.takeScreenshot("hawk_hunt_" + i);
			}
			status(world, "after hunt");
			server.runCommand("kill @e[type=!player]");

			// The highway: a sky city built whole, then its lanes between the city's flier ports.
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				var city = com.sparky.lanternring.city.BlueCity.cityFor(p.level(), p.blockPosition());
				com.sparky.lanternring.city.BlueCity.buildAll(p.level(), city);
				FlierHighway.Network net = FlierHighway.buildNow(p.level(), city.anchor);
				p.teleportTo(city.anchor.getX() + 0.5, city.anchor.getY() + 40, city.anchor.getZ() - 60);
				System.out.println("[hawk] highway: " + net.pads.size() + " pads, " + net.lanes.size() + " lanes, route 0->2 "
						+ net.route(0, 2).size() + " points, city pads " + !net.ownPads);
			});
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 8f);
			ctx.waitTicks(60);
			ctx.takeScreenshot("highway_overview");
			for (int i = 0; i < 4; i++) {
				ctx.waitTicks(80);
				ctx.takeScreenshot("highway_hawks_" + i);
			}
			status(world, "on highway");

			// Riding: mount a hawk and fly.
			server.runCommand("gamemode creative @p");
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				DivingHawk hawk = FlierHighway.DIVING_HAWK.create(p.level(), EntitySpawnReason.COMMAND);
				hawk.snapTo(p.getX(), p.getY(), p.getZ(), p.getYRot(), 0f);
				p.level().addFreshEntity(hawk);
				p.startRiding(hawk);
			});
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(0f, 0f);
			ctx.getInput().holdKey(o -> o.keyUp);
			ctx.waitTicks(30);
			ctx.takeScreenshot("ride_cruise");
			ctx.getInput().lookAt(0f, 50f);
			ctx.waitTicks(25);
			ctx.takeScreenshot("ride_stoop");
			ctx.getInput().releaseKey(o -> o.keyUp);
			status(world, "riding");
		}
	}

	private static void status(TestSingleplayerContext world, String when) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			StringBuilder out = new StringBuilder();
			for (var e : p.level().getEntities(EntityTypeTest.forClass(net.minecraft.world.entity.LivingEntity.class), e -> e != p)) {
				out.append(e.getType().toShortString()).append(" hp=").append(Math.round(e.getHealth()))
						.append(e instanceof DivingHawk h ? " perched=" + h.perched() : "").append(" @").append(e.blockPosition().toShortString()).append("; ");
			}
			System.out.println("[hawk] " + when + ": " + out);
		});
	}
}
