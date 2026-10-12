package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.city.CityBlocks;
import com.sparky.lanternring.corps.CorpsMobs;
import com.sparky.lanternring.corps.CorpsVillager;
import com.sparky.lanternring.corps.SkyBuilds;
import com.sparky.lanternring.designs.Blueprint;
import com.sparky.lanternring.designs.HopeArchitecture;
import java.util.Map;
import java.util.Random;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * The Blue Lantern's own buildings: each design forms as blue hard light and sets into Hope Quartz.
 * Also a ring bearer under a roof flying up: it slips out from under the eave instead of hanging
 * against the ceiling (J's founder never reached its island, 2026-10-12).
 */
public class HopeBuildingsTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode spectator @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			BlockPos[] o = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				ServerLevel level = p.level();
				BlockPos b = p.blockPosition();
				for (BlockPos pos : BlockPos.betweenClosed(b.offset(-36, -2, -10), b.offset(36, 30, 50))) {
					level.setBlock(pos, pos.getY() < b.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				o[0] = b.below();
				// The three designs side by side, door toward the camera (-z), forming over 4 s.
				Random r = new Random(7);
				Blueprint[] designs = {HopeArchitecture.rotunda(11, r), HopeArchitecture.prism(11, r), HopeArchitecture.arch(11, r)};
				int x = o[0].getX() - 22;
				for (Blueprint bp : designs) {
					Map<BlockPos, BlockState> blocks = SkyBuilds.place(bp, x, o[0].getY(), o[0].getZ() + 18, Rotation.CLOCKWISE_180);
					SkyBuilds.start(level, blocks, 80, Corps.BLUE, true, null);
					x += bp.w + 4;
				}
				p.teleportTo(o[0].getX(), o[0].getY() + 9, o[0].getZ() - 6);
			});
			ctx.getInput().lookAt(0f, 22f);
			ctx.waitTicks(50);
			ctx.takeScreenshot("hope_buildings_forming");
			ctx.waitTicks(150);
			ctx.takeScreenshot("hope_buildings_set");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("hope_buildings_night");
			world.getServer().runCommand("time set 6000");
			world.getServer().runOnServer(server -> {
				ServerLevel level = server.overworld();
				int quartz = 0, light = 0;
				for (BlockPos pos : BlockPos.betweenClosed(o[0].offset(-30, 0, 10), o[0].offset(30, 25, 40))) {
					BlockState s = level.getBlockState(pos);
					if (s.is(CityBlocks.SKY_LIGHT)) light++;
					if (s.is(CityBlocks.HOPE_QUARTZ) || s.is(CityBlocks.HOPE_QUARTZ_BRICKS) || s.is(CityBlocks.HOPE_QUARTZ_PILLAR)) quartz++;
				}
				if (light > 0 || quartz < 50) throw new AssertionError("Hope buildings didn't set: " + light + " still light, " + quartz + " quartz");
			});

			// A bearer standing under a roof is told to fly straight up through it.
			double[] start = new double[1];
			CorpsVillager[] v = new CorpsVillager[1];
			world.getServer().runOnServer(server -> {
				ServerLevel level = server.overworld();
				BlockPos h = o[0].offset(0, 1, -4);
				for (BlockPos pos : BlockPos.betweenClosed(h.offset(-2, 3, -2), h.offset(2, 3, 2))) level.setBlock(pos, Blocks.OAK_PLANKS.defaultBlockState(), 2);
				CorpsVillager f = CorpsMobs.CORPS_VILLAGER.create(level, EntitySpawnReason.MOB_SUMMONED);
				f.setCorps(Corps.GREEN);
				f.snapTo(h.getX() + 0.5, h.getY(), h.getZ() + 0.5, 0f, 0f);
				level.addFreshEntity(f);
				f.flyTo(Vec3.atBottomCenterOf(h).add(0, 20, 0), false);
				start[0] = f.getY();
				v[0] = f;
			});
			ctx.waitTicks(200);
			world.getServer().runOnServer(server -> {
				if (v[0].getY() < start[0] + 15) throw new AssertionError("Bearer stuck under the roof at y " + v[0].getY());
			});
		}
	}
}
