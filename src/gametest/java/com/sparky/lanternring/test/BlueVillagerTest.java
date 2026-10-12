package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.corps.CorpsMobs;
import com.sparky.lanternring.corps.CorpsVillager;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

/** The Blue Lantern villagers in their suit from J's sheet: front and back, flying, and building in a U of three. */
public class BlueVillagerTest implements FabricClientGameTest {
	private static CorpsVillager spawn(ServerPlayer p, Vec3 at, float yaw, boolean ai) {
		CorpsVillager v = CorpsMobs.CORPS_VILLAGER.create(p.level(), EntitySpawnReason.MOB_SUMMONED);
		v.setCorps(Corps.BLUE);
		v.setCustomName(null);
		v.snapTo(at.x, at.y, at.z, yaw, 0f);
		v.setYHeadRot(yaw);
		v.setYBodyRot(yaw);
		v.setNoAi(!ai);
		p.level().addFreshEntity(v);
		return v;
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode spectator @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			Vec3[] o = new Vec3[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos b = p.blockPosition().above(6);
				for (BlockPos pos : BlockPos.betweenClosed(b.offset(-40, -3, -40), b.offset(40, 40, 40))) {
					p.level().setBlock(pos, pos.getY() < b.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				o[0] = Vec3.atBottomCenterOf(b);
				p.teleportTo(o[0].x, o[0].y + 0.3, o[0].z);
				spawn(p, o[0].add(-0.7, 0, 2.6), 180f, false);
				spawn(p, o[0].add(0.7, 0, 2.6), 0f, false);
			});
			ctx.getInput().lookAt(0f, 12f);
			ctx.waitTicks(30);
			ctx.takeScreenshot("blue_villager_front_back");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("blue_villager_night");
			world.getServer().runCommand("kill @e[type=lanternring:corps_villager]");
			world.getServer().runCommand("time set 6000");

			// Flying past: the lean and trailing legs.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				CorpsVillager v = spawn(p, o[0].add(-6, 2, 6), 90f, true);
				v.flyTo(o[0].add(8, 3, 6), false);
			});
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(30);
			ctx.takeScreenshot("blue_villager_flying");
			world.getServer().runCommand("kill @e[type=lanternring:corps_villager]");

			// A founder: it gathers a crew of three and they build in a wide U.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				spawn(p, o[0].add(0, 0, 4), 0f, true);
				p.teleportTo(o[0].x, o[0].y + 12, o[0].z - 22);
			});
			ctx.getInput().lookAt(0f, 22f);
			for (int i = 0; i < 6; i++) {
				ctx.waitTicks(50);
				ctx.takeScreenshot("blue_villager_crew_" + i);
			}
		}
	}
}
