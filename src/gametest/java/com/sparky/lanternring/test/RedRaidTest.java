package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.corps.CorpsMobs;
import com.sparky.lanternring.corps.CorpsVillager;
import com.sparky.lanternring.corps.SkyRaider;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.block.Blocks;

/** Sanctuary raiders go out and raid a Blue Lantern village; the fated side carries it (Red 60/40). */
public class RedRaidTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode spectator @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("difficulty hard");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			// Two raids, far apart: one Red is fated to win, one Blue is.
			for (boolean redFated : new boolean[] {true, false}) {
				SkyRaider[] captain = new SkyRaider[1];
				BlockPos[] village = new BlockPos[1];
				world.getServer().runOnServer(server -> {
					ServerPlayer p = server.getPlayerList().getPlayers().get(0);
					ServerLevel level = p.level();
					BlockPos b = p.blockPosition().offset(redFated ? 0 : 400, 0, 0).atY(p.blockPosition().getY() + 4);
					for (BlockPos pos : BlockPos.betweenClosed(b.offset(-30, -2, -60), b.offset(30, 30, 30))) {
						level.setBlock(pos, pos.getY() < b.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
					}
					village[0] = b;
					for (int i = 0; i < 4; i++) {
						CorpsVillager cv = CorpsMobs.CORPS_VILLAGER.create(level, EntitySpawnReason.MOB_SUMMONED);
						cv.setCorps(Corps.BLUE);
						cv.snapTo(b.getX() + 0.5 + (i - 1.5) * 3, b.getY(), b.getZ() + 0.5, 0f, 0f);
						level.addFreshEntity(cv);
						cv.suitUp(level);
					}
					BlockPos outpost = b.offset(0, 18, -50);
					List<SkyRaider> band = new ArrayList<>();
					for (int i = 0; i < 4; i++) {
						SkyRaider r = CorpsMobs.SKY_RAIDER.create(level, EntitySpawnReason.MOB_SUMMONED);
						r.sanctuary(outpost, i == 0);
						r.setItemSlot(net.minecraft.world.entity.EquipmentSlot.MAINHAND, Corps.RED.ring());
						r.snapTo(outpost.getX() + i, outpost.getY() + 2, outpost.getZ(), 0f, 0f);
						level.addFreshEntity(r);
						band.add(r);
					}
					captain[0] = band.getFirst();
					p.teleportTo(level, b.getX() + 0.5, b.getY() + 14, b.getZ() - 24.5, java.util.Set.of(), 0f, 25f, true);
				});
				ctx.waitTicks(20);
				world.getServer().runOnServer(server -> captain[0].startRaid(server.getPlayerList().getPlayers().get(0).level(), village[0], redFated));
				String tag = redFated ? "red_fated" : "blue_fated";
				for (int t = 0; t < 1400; t += 100) {
					ctx.waitTicks(100);
					if (t == 300) ctx.takeScreenshot("raid_" + tag);
					Boolean[] done = new Boolean[1];
					world.getServer().runOnServer(server -> done[0] = village[0].equals(SkyRaider.lastRaidAt) ? SkyRaider.lastRaidRed : null);
					if (done[0] != null) break;
				}
				world.getServer().runOnServer(server -> {
					ServerLevel level = server.getPlayerList().getPlayers().get(0).level();
					var box = new net.minecraft.world.phys.AABB(village[0]).inflate(100);
					System.out.println("[raid] " + tag + ": result=" + (village[0].equals(SkyRaider.lastRaidAt) ? SkyRaider.lastRaidRed ? "red won" : "blue won" : "none")
							+ " raiders=" + level.getEntitiesOfClass(SkyRaider.class, box, e -> e.isAlive()).size()
							+ " blue=" + level.getEntitiesOfClass(CorpsVillager.class, box, e -> e.isAlive() && e.corps() == Corps.BLUE).size());
				});
				ctx.takeScreenshot("raid_" + tag + "_end");
			}
		}
	}
}
