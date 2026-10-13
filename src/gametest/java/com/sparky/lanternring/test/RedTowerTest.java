package com.sparky.lanternring.test;

import com.sparky.lanternring.corps.RedTower;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.animal.cow.Cow;
import net.minecraft.world.phys.AABB;

/** J's C3 Split claw: the Red tower rises with its steak farms, and its field fills with chained, enraged monsters. */
public class RedTowerTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode spectator @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			BlockPos[] at = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				at[0] = p.blockPosition().immutable();
				RedTower.raiseAt(p.level(), at[0]);
				p.teleportTo(at[0].getX() + 0.5, at[0].getY() + 30, at[0].getZ() - 80.5);
			});
			ctx.getInput().lookAt(0f, 10f);
			for (int i = 0; i < 3; i++) {
				ctx.waitTicks(70);
				ctx.takeScreenshot("red_tower_rising_" + i);
			}
			ctx.waitTicks(100);
			ctx.takeScreenshot("red_tower_built");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.teleportTo(at[0].getX() + 0.5, at[0].getY() + 8, at[0].getZ() - 48.5);
			});
			ctx.getInput().lookAt(30f, 15f);
			ctx.waitTicks(80);
			ctx.takeScreenshot("red_tower_field");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.teleportTo(at[0].getX() + 26.5, at[0].getY() + 16, at[0].getZ() + 2.5);
			});
			ctx.getInput().lookAt(90f, 25f);
			ctx.waitTicks(40);
			ctx.takeScreenshot("red_tower_farm");
			world.getServer().runOnServer(server -> {
				ServerLevel level = server.getPlayerList().getPlayers().get(0).level();
				AABB area = new AABB(at[0]).inflate(60, 60, 60);
				var chained = level.getEntitiesOfClass(Mob.class, area, RedTower::chained);
				long leashed = chained.stream().filter(Mob::isLeashed).count();
				int cows = level.getEntitiesOfClass(Cow.class, area, c -> true).size();
				System.out.println("[RedTowerTest] built " + RedTower.sites(level).get(0).built() + " posts "
						+ RedTower.posts(level, RedTower.sites(level).get(0)).size() + " chained " + chained.size()
						+ " leashed " + leashed + " cows " + cows + " floor " + level.getBlockState(RedTower.sites(level).get(0).anchor()));
			});
		}
	}
}
