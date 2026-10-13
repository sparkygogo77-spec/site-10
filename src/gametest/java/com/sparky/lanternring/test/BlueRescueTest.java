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

/** After the squad clears its lantern, the flyers lift animals and villagers in bubbles to a walled, domed spot. */
public class BlueRescueTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode spectator @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents.AFTER_DEATH.register((e, src) ->
					System.out.println("[BlueRescueTest] died: " + e.getType().toShortString() + " by " + src.getMsgId() + " from " + src.getEntity() + " at " + e.position()));
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
			// Animals and villagers scattered round the lantern, and one husk to clear first.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				Vec3 c = Vec3.atBottomCenterOf(lantern[0]);
				spawn(p, EntityTypes.COW, c.add(18, 0, 6));
				spawn(p, EntityTypes.SHEEP, c.add(-16, 0, 12));
				spawn(p, EntityTypes.PIG, c.add(4, 0, -20));
				spawn(p, EntityTypes.CAT, c.add(-12, 0, -14));
				spawn(p, EntityTypes.CHICKEN, c.add(22, 0, -10));
				spawn(p, EntityTypes.VILLAGER, c.add(-20, 0, -2));
				spawn(p, EntityTypes.VILLAGER, c.add(10, 0, 20));
				spawn(p, EntityTypes.HUSK, c.add(0, 0, 24));
			});
			for (int i = 0; i < 30; i++) {
				ctx.waitTicks(20);
				if (i % 2 == 0) ctx.takeScreenshot("blue_rescue_" + i);
			}
			ctx.waitTicks(400);
			world.getServer().runOnServer(server -> {
				ServerLevel level = server.getPlayerList().getPlayers().get(0).level();
				AABB box = new AABB(lantern[0]).inflate(40);
				StringBuilder s = new StringBuilder();
				for (Mob m : level.getEntitiesOfClass(Mob.class, box, m -> m.isAlive() && !(m instanceof CorpsVillager cv && cv.inSquad()) && !(m instanceof BlueRavager))) {
					s.append(m.getType().toShortString()).append(" at ").append(m.blockPosition().subtract(lantern[0])).append("; ");
				}
				System.out.println("[BlueRescueTest] " + s);
			});
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.teleportTo(lantern[0].getX() - 20.5, lantern[0].getY() + 14, lantern[0].getZ() + 0.5);
			});
			ctx.getInput().lookAt(-90f, 30f);
			ctx.waitTicks(30);
			ctx.takeScreenshot("blue_rescue_above");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.teleportTo(lantern[0].getX() - 10.5, lantern[0].getY() + 4, lantern[0].getZ() + 6.5);
			});
			ctx.getInput().lookAt(-120f, 15f);
			ctx.waitTicks(30);
			ctx.takeScreenshot("blue_rescue_after");
		}
	}

	private static Mob spawn(ServerPlayer p, EntityType<? extends Mob> type, Vec3 at) {
		Mob m = type.create(p.level(), EntitySpawnReason.MOB_SUMMONED);
		m.snapTo(at.x, at.y, at.z, 180f, 0f);
		p.level().addFreshEntity(m);
		return m;
	}
}
