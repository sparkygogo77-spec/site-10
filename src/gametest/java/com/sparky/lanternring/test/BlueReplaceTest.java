package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.corps.BlueSquad;
import com.sparky.lanternring.corps.CorpsMobs;
import com.sparky.lanternring.corps.CorpsVillager;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;

/** A Red Lantern villager in the clearing is fought; a fallen squad member is replaced after a while. */
public class BlueReplaceTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode spectator @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			BlockPos[] lantern = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos b = p.blockPosition().above(6);
				for (BlockPos pos : BlockPos.betweenClosed(b.offset(-40, -3, -40), b.offset(40, 30, 40))) {
					p.level().setBlock(pos, pos.getY() < b.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				lantern[0] = b.immutable();
				p.level().setBlock(b, ModRegistry.POWER_BATTERY.defaultBlockState().setValue(Corps.PROPERTY, Corps.BLUE), 3);
				p.teleportTo(b.getX() - 20.5, b.getY() + 8, b.getZ() + 0.5);
			});
			ctx.getInput().lookAt(-90f, 15f);
			world.getServer().runOnServer(server -> BlueSquad.callOut(server.getPlayerList().getPlayers().get(0).level(), lantern[0]));
			ctx.waitTicks(160);
			world.getServer().runOnServer(server -> {
				ServerLevel level = server.getPlayerList().getPlayers().get(0).level();
				CorpsVillager red = CorpsMobs.CORPS_VILLAGER.create(level, EntitySpawnReason.MOB_SUMMONED);
				red.setCorps(Corps.RED);
				red.snapTo(lantern[0].getX() + 8.5, lantern[0].getY(), lantern[0].getZ() + 8.5, 0f, 0f);
				level.addFreshEntity(red);
			});
			ctx.waitTicks(30);
			world.getServer().runOnServer(server -> {
				ServerLevel level = server.getPlayerList().getPlayers().get(0).level();
				for (CorpsVillager v : level.getEntitiesOfClass(CorpsVillager.class, new AABB(lantern[0]).inflate(40), CorpsVillager::inSquad)) {
					System.out.println("[BlueReplaceTest] " + v.squadRole() + " focus " + v.squadFocus());
				}
			});
			ctx.takeScreenshot("blue_replace_red");
			world.getServer().runOnServer(server -> {
				ServerLevel level = server.getPlayerList().getPlayers().get(0).level();
				for (CorpsVillager v : level.getEntitiesOfClass(CorpsVillager.class, new AABB(lantern[0]).inflate(40), v -> v.squadRole() == BlueSquad.Role.WARRIOR)) v.kill(level);
			});
			ctx.waitTicks(1240);
			world.getServer().runOnServer(server -> {
				ServerLevel level = server.getPlayerList().getPlayers().get(0).level();
				StringBuilder s = new StringBuilder();
				for (CorpsVillager v : level.getEntitiesOfClass(CorpsVillager.class, new AABB(lantern[0]).inflate(40), CorpsVillager::inSquad)) s.append(v.squadRole()).append(' ');
				System.out.println("[BlueReplaceTest] after the warrior fell and a minute passed: " + s);
			});
			ctx.takeScreenshot("blue_replace_after");
		}
	}
}
