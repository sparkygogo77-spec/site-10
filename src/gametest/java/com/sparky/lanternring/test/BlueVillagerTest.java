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
				// Left: still a construct. Middle and right: suited, front and back.
				spawn(p, o[0].add(1.4, 0, 3.0), 0f, false);
				spawn(p, o[0].add(0, 0, 3.0), 0f, false).suitUp(p.level());
				spawn(p, o[0].add(-1.4, 0, 3.0), 180f, false).suitUp(p.level());
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
				CorpsVillager v = spawn(p, o[0].add(-7, 1.5, 5), 90f, true);
				v.suitUp(p.level());
				v.flyTo(o[0].add(9, 2, 5), false);
			});
			ctx.getInput().lookAt(0f, 8f);
			ctx.waitTicks(22);
			ctx.takeScreenshot("blue_villager_flying");
			world.getServer().runCommand("kill @e[type=lanternring:corps_villager]");

			// A founder with a build queued on its crew: it gathers a crew of three, they fly there
			// together, take a wide U round it and pour light in until it stands.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				CorpsVillager f = spawn(p, o[0].add(0, 0, 4), 0f, true);
				java.util.Map<BlockPos, net.minecraft.world.level.block.state.BlockState> tower = new java.util.LinkedHashMap<>();
				BlockPos base = BlockPos.containing(o[0]).offset(0, 0, 16);
				for (int y = 0; y < 9; y++) {
					for (int dx = -2; dx <= 2; dx++) {
						for (int dz = -2; dz <= 2; dz++) {
							boolean edge = Math.abs(dx) == 2 || Math.abs(dz) == 2;
							if (!edge && y > 0 && y < 8) continue;
							boolean corner = Math.abs(dx) == 2 && Math.abs(dz) == 2;
							tower.put(base.offset(dx, y, dz), (corner ? Blocks.SEA_LANTERN : Blocks.STAINED_GLASS.lightBlue()).defaultBlockState());
						}
					}
				}
				f.crew().order(com.sparky.lanternring.corps.BuildOrder.fixed("test tower", tower, 160, false));
				p.teleportTo(o[0].x + 14, o[0].y + 10, o[0].z - 6);
			});
			ctx.getInput().lookAt(35f, 20f);
			for (int i = 0; i < 8; i++) {
				ctx.waitTicks(40);
				ctx.takeScreenshot("blue_villager_crew_" + i);
			}
		}
	}
}
