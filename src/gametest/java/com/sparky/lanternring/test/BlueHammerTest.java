package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
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

/** The rescue squad's warrior leaps at monsters and brings its hammer of light down on them. */
public class BlueHammerTest implements FabricClientGameTest {
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
				p.teleportTo(b.getX() + 0.5, b.getY() + 7, b.getZ() - 14.5);
			});
			ctx.getInput().lookAt(0f, 25f);
			ctx.waitTicks(20);
			world.getServer().runOnServer(server -> BlueSquad.callOut(server.getPlayerList().getPlayers().get(0).level(), lantern[0]));
			ctx.waitTicks(140);
			// A tight pack of husks walks in near the warrior's side.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				CorpsVillager w = p.level().getEntitiesOfClass(CorpsVillager.class, new AABB(lantern[0]).inflate(40), v -> v.squadRole() == BlueSquad.Role.WARRIOR).get(0);
				Vec3 c = w.position();
				System.out.println("[BlueHammerTest] warrior at " + c.subtract(Vec3.atBottomCenterOf(lantern[0])));
				for (int i = 0; i < 8; i++) {
					Mob m = EntityTypes.HUSK.create(p.level(), EntitySpawnReason.MOB_SUMMONED);
					m.snapTo(c.x - 4 + i, c.y, c.z + 6 + (i % 3), 0f, 0f);
					p.level().addFreshEntity(m);
				}
			});
			for (int i = 0; i < 40; i++) {
				ctx.waitTicks(2);
				int n = i;
				world.getServer().runOnServer(server -> {
					ServerLevel level = server.getPlayerList().getPlayers().get(0).level();
					AABB box = new AABB(lantern[0]).inflate(40);
					StringBuilder s = new StringBuilder();
					for (CorpsVillager v : level.getEntitiesOfClass(CorpsVillager.class, box, v -> v.squadRole() == BlueSquad.Role.WARRIOR)) {
						s.append("warrior y+").append(String.format("%.2f", v.getY() - lantern[0].getY())).append(' ');
					}
					for (Mob m : level.getEntitiesOfClass(Mob.class, box, m -> m.isAlive() && m instanceof Enemy)) {
						s.append(String.format("%.0f/", m.getHealth()));
					}
					System.out.println("[BlueHammerTest] " + n + " " + s);
				});
				ctx.takeScreenshot("blue_hammer_" + i);
			}
		}
	}
}
