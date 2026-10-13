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
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/** The Blue Lantern rescue squad flies out of a Blue lantern and clears the monsters round it. */
public class BlueSquadTest implements FabricClientGameTest {
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
				p.teleportTo(b.getX() - 14.5, b.getY() + 6, b.getZ() + 0.5);
			});
			ctx.getInput().lookAt(-90f, 15f);
			ctx.waitTicks(20);
			world.getServer().runOnServer(server -> BlueSquad.callOut(server.getPlayerList().getPlayers().get(0).level(), lantern[0]));
			for (int i = 0; i < 8; i++) {
				ctx.waitTicks(8);
				ctx.takeScreenshot("blue_squad_emerge_" + i);
			}
			ctx.waitTicks(40);
			ctx.takeScreenshot("blue_squad_ready");
			// Husks (they don't burn in daylight) come at the lantern from two sides.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				Vec3 c = Vec3.atBottomCenterOf(lantern[0]);
				for (int i = 0; i < 4; i++) spawn(p, EntityTypes.HUSK, c.add(-3 + i * 2, 0, 22));
				for (int i = 0; i < 3; i++) spawn(p, EntityTypes.HUSK, c.add(20, 0, -4 + i * 3));
				spawn(p, EntityTypes.HUSK, c.add(-26, 0, -20));
			});
			for (int i = 0; i < 16; i++) {
				ctx.waitTicks(10);
				ctx.takeScreenshot("blue_squad_fight_" + i);
			}
			ctx.waitTicks(300);
			world.getServer().runOnServer(server -> {
				ServerLevel level = server.getPlayerList().getPlayers().get(0).level();
				AABB box = new AABB(lantern[0]).inflate(40);
				int monsters = level.getEntitiesOfClass(Mob.class, box, m -> m.isAlive() && m instanceof Enemy).size();
				var squad = level.getEntitiesOfClass(CorpsVillager.class, box, CorpsVillager::inSquad);
				var mounts = level.getEntitiesOfClass(BlueRavager.class, box, BlueRavager::isAlive);
				StringBuilder s = new StringBuilder();
				for (CorpsVillager v : squad) {
					s.append(v.squadRole()).append(v.getVehicle() instanceof BlueRavager ? "(mounted)" : "")
							.append(v.flying() ? "(flying)" : "").append(" at ").append(v.position().subtract(Vec3.atBottomCenterOf(lantern[0]))).append("; ");
				}
				System.out.println("[BlueSquadTest] squad " + squad.size() + ", ravagers " + mounts.size() + ", monsters left " + monsters + ": " + s);
			});
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.teleportTo(lantern[0].getX() - 10.5, lantern[0].getY() + 4, lantern[0].getZ() + 6.5);
			});
			ctx.getInput().lookAt(-120f, 15f);
			ctx.waitTicks(30);
			ctx.takeScreenshot("blue_squad_after");
		}
	}

	private static Mob spawn(ServerPlayer p, EntityType<? extends Mob> type, Vec3 at) {
		Mob m = type.create(p.level(), EntitySpawnReason.MOB_SUMMONED);
		m.snapTo(at.x, at.y, at.z, 180f, 0f);
		p.level().addFreshEntity(m);
		return m;
	}
}
