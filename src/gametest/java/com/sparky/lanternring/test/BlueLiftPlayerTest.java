package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.corps.BlueSquad;
import com.sparky.lanternring.corps.CorpsVillager;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/** A player crouching near a rescue flyer is lifted in; talking to the warrior lets everyone out. */
public class BlueLiftPlayerTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents.AFTER_DAMAGE.register((e, src, base, taken, blocked) -> {
				if (e instanceof ServerPlayer) System.out.println("[BlueLiftPlayerTest] player hurt " + taken + " by " + src.getMsgId() + " from " + src.getEntity());
			});
			BlockPos[] lantern = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos b = p.blockPosition();
				for (BlockPos pos : BlockPos.betweenClosed(b.offset(-40, -3, -40), b.offset(40, 30, 40))) {
					p.level().setBlock(pos, pos.getY() < b.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				lantern[0] = b.immutable();
				p.level().setBlock(b, ModRegistry.POWER_BATTERY.defaultBlockState().setValue(Corps.PROPERTY, Corps.BLUE), 3);
				Mob cow = EntityTypes.COW.create(p.level(), EntitySpawnReason.MOB_SUMMONED);
				cow.snapTo(b.getX() + 16.5, b.getY(), b.getZ() + 8.5, 0f, 0f);
				p.level().addFreshEntity(cow);
				p.teleportTo(b.getX() + 0.5, b.getY(), b.getZ() + 18.5);
				BlueSquad.callOut(p.level(), b);
			});
			ctx.waitTicks(140);
			// Stand well outside the walls, across from the spot they picked.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				double x = 0, z = 0;
				int n = 0;
				for (BlockPos q : BlockPos.betweenClosed(lantern[0].offset(-30, -2, -30), lantern[0].offset(30, 3, 30))) {
					if (p.level().getBlockState(q).is(ModRegistry.LIGHT_CONSTRUCT)) {
						x += q.getX();
						z += q.getZ();
						n++;
					}
				}
				Vec3 l = Vec3.atBottomCenterOf(lantern[0]);
				Vec3 away = n == 0 ? new Vec3(0, 0, 1) : l.subtract(x / n, l.y, z / n).multiply(1, 0, 1).normalize();
				p.teleportTo(l.x + away.x * 16, l.y, l.z + away.z * 16);
				System.out.println("[BlueLiftPlayerTest] walls " + n + ", standing at " + p.position().subtract(l));
			});
			ctx.getInput().lookAt(180f, -20f);
			ctx.waitTicks(10);
			ctx.getInput().holdKey(o -> o.keyShift);
			for (int i = 0; i < 25; i++) {
				ctx.waitTicks(16);
				if (i % 3 == 0) ctx.takeScreenshot("blue_lift_player_" + i);
				if (i % 5 == 0) world.getServer().runOnServer(server -> {
					ServerPlayer p = server.getPlayerList().getPlayers().get(0);
					System.out.println("[BlueLiftPlayerTest] crouching " + p.isShiftKeyDown() + " at " + p.position().subtract(Vec3.atBottomCenterOf(lantern[0])));
				});
			}
			ctx.getInput().releaseKey(o -> o.keyShift);
			ctx.waitTicks(100);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				var level = p.level();
				int dome = 0;
				for (BlockPos q : BlockPos.betweenClosed(lantern[0].offset(-30, -2, -30), lantern[0].offset(30, 12, 30))) {
					if (level.getBlockState(q).is(ModRegistry.LIGHT_CONSTRUCT)) dome++;
				}
				System.out.println("[BlueLiftPlayerTest] player at " + p.position().subtract(Vec3.atBottomCenterOf(lantern[0])) + " health " + p.getHealth()
						+ ", construct blocks " + dome);
				var warrior = level.getEntitiesOfClass(CorpsVillager.class, new AABB(lantern[0]).inflate(48), v -> v.squadRole() == BlueSquad.Role.WARRIOR);
				if (!warrior.isEmpty()) warrior.get(0).mobInteract(p, InteractionHand.MAIN_HAND);
			});
			ctx.waitTicks(20);
			ctx.takeScreenshot("blue_lift_released");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				int dome = 0;
				for (BlockPos q : BlockPos.betweenClosed(lantern[0].offset(-30, -2, -30), lantern[0].offset(30, 12, 30))) {
					if (p.level().getBlockState(q).is(ModRegistry.LIGHT_CONSTRUCT)) dome++;
				}
				System.out.println("[BlueLiftPlayerTest] after talking to the warrior: construct blocks " + dome);
			});
			ctx.waitTicks(200);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				int dome = 0;
				for (BlockPos q : BlockPos.betweenClosed(lantern[0].offset(-30, -2, -30), lantern[0].offset(30, 12, 30))) {
					if (p.level().getBlockState(q).is(ModRegistry.LIGHT_CONSTRUCT)) dome++;
				}
				System.out.println("[BlueLiftPlayerTest] 10 s later: construct blocks " + dome);
			});
		}
	}
}
