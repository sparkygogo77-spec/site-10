package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.corps.BlueRavager;
import com.sparky.lanternring.corps.BlueSquad;
import com.sparky.lanternring.corps.CorpsVillager;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/** The lance rider's ravager flies lance passes through monsters; when the beast dies, its rider fights on as a flyer. */
public class BlueLanceTest implements FabricClientGameTest {
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
				p.teleportTo(b.getX() - 22.5, b.getY() + 8, b.getZ() + 0.5);
			});
			ctx.getInput().lookAt(-90f, 15f);
			world.getServer().runOnServer(server -> BlueSquad.callOut(server.getPlayerList().getPlayers().get(0).level(), lantern[0]));
			ctx.waitTicks(160);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				Vec3 c = Vec3.atBottomCenterOf(lantern[0]);
				for (int i = 0; i < 6; i++) {
					Mob m = EntityTypes.HUSK.create(p.level(), EntitySpawnReason.MOB_SUMMONED);
					m.snapTo(c.x - 6 + i * 2, c.y, c.z + 20, 0f, 0f);
					p.level().addFreshEntity(m);
				}
			});
			for (int i = 0; i < 24; i++) {
				ctx.waitTicks(5);
				int n = i;
				world.getServer().runOnServer(server -> {
					ServerLevel level = server.getPlayerList().getPlayers().get(0).level();
					AABB box = new AABB(lantern[0]).inflate(40);
					StringBuilder s = new StringBuilder();
					for (BlueRavager r : level.getEntitiesOfClass(BlueRavager.class, box, BlueRavager::isAlive)) {
						s.append(String.format("ravager y+%.1f soaring %s riders %d; ", r.getY() - lantern[0].getY(), r.soaring(), r.getPassengers().size()));
					}
					for (Mob m : level.getEntitiesOfClass(Mob.class, box, m -> m.isAlive() && m instanceof Enemy)) s.append(String.format("%.0f/", m.getHealth()));
					System.out.println("[BlueLanceTest] " + n + " " + s);
				});
				if (i % 3 == 0) ctx.takeScreenshot("blue_lance_" + i);
			}
			world.getServer().runOnServer(server -> {
				ServerLevel level = server.getPlayerList().getPlayers().get(0).level();
				for (BlueRavager r : level.getEntitiesOfClass(BlueRavager.class, new AABB(lantern[0]).inflate(40), BlueRavager::isAlive)) r.kill(level);
			});
			ctx.waitTicks(60);
			world.getServer().runOnServer(server -> {
				ServerLevel level = server.getPlayerList().getPlayers().get(0).level();
				StringBuilder s = new StringBuilder();
				for (CorpsVillager v : level.getEntitiesOfClass(CorpsVillager.class, new AABB(lantern[0]).inflate(40), CorpsVillager::inSquad)) {
					s.append(v.squadRole()).append(v.flying() ? "(flying) " : " ");
				}
				System.out.println("[BlueLanceTest] after the beast died: " + s);
			});
			ctx.takeScreenshot("blue_lance_split");
		}
	}
}
