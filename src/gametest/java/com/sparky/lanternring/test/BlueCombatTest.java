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
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/** Blue Lantern villagers fighting: ring on the hand, the arm aimed, beams with blasts, and a lassoed mob swung and flung. */
public class BlueCombatTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode spectator @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			Vec3[] o = new Vec3[1];
			CorpsVillager[] v = new CorpsVillager[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos b = p.blockPosition().above(6);
				for (BlockPos pos : BlockPos.betweenClosed(b.offset(-48, -3, -48), b.offset(48, 40, 48))) {
					p.level().setBlock(pos, pos.getY() < b.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				o[0] = Vec3.atBottomCenterOf(b);
				CorpsVillager cv = CorpsMobs.CORPS_VILLAGER.create(p.level(), EntitySpawnReason.MOB_SUMMONED);
				cv.setCorps(Corps.BLUE);
				cv.setCustomName(null);
				cv.snapTo(o[0].x, o[0].y, o[0].z + 4, 0f, 0f);
				p.level().addFreshEntity(cv);
				cv.suitUp(p.level());
				v[0] = cv;
			});
			// Close up on the ring hand: the ring on its finger, then the arm coming up at a husk and firing.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.teleportTo(o[0].x - 2.6, o[0].y + 1.3, o[0].z + 4.6);
			});
			ctx.getInput().lookAt(-90f, 8f);
			ctx.waitTicks(30);
			ctx.takeScreenshot("blue_combat_ring_close");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				spawn(p, EntityTypes.HUSK, o[0].add(0, 0, 13)).setNoAi(true);
			});
			for (int i = 0; i < 6; i++) {
				ctx.waitTicks(5);
				ctx.takeScreenshot("blue_combat_ring_aim_" + i);
			}
			world.getServer().runCommand("kill @e[type=minecraft:husk]");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.teleportTo(o[0].x - 15, o[0].y + 3, o[0].z + 11);
			});
			ctx.getInput().lookAt(-90f, 6f);
			ctx.waitTicks(30);
			ctx.takeScreenshot("blue_combat_ring_idle");

			// Husks (they don't burn in daylight) walk up: it holds its ground and fires.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				for (int i = 0; i < 3; i++) spawn(p, EntityTypes.HUSK, o[0].add(-2 + i * 2, 0, 16));
			});
			for (int i = 0; i < 10; i++) {
				ctx.waitTicks(6);
				ctx.takeScreenshot("blue_combat_" + i);
			}
			ctx.waitTicks(60);
			for (int i = 10; i < 22; i++) {
				ctx.waitTicks(6);
				ctx.takeScreenshot("blue_combat_" + i);
			}
			// A big one gets the charged Beam.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				spawn(p, EntityTypes.RAVAGER, o[0].add(0, 0, 18));
			});
			for (int i = 22; i < 34; i++) {
				ctx.waitTicks(8);
				ctx.takeScreenshot("blue_combat_" + i);
			}
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				int left = p.level().getEntitiesOfClass(Mob.class, new AABB(BlockPos.containing(o[0])).inflate(80),
						m -> m.isAlive() && !(m instanceof CorpsVillager)).size();
				System.out.println("[BlueCombatTest] villager health " + v[0].getHealth() + "/" + v[0].getMaxHealth()
						+ ", alive " + v[0].isAlive() + ", monsters left " + left + ", at " + v[0].position().subtract(o[0]));
			});
		}
	}

	private static Mob spawn(ServerPlayer p, EntityType<? extends Mob> type, Vec3 at) {
		Mob m = type.create(p.level(), EntitySpawnReason.MOB_SUMMONED);
		m.snapTo(at.x, at.y, at.z, 180f, 0f);
		p.level().addFreshEntity(m);
		return m;
	}
}
