package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.corps.BlueSquad;
import com.sparky.lanternring.corps.CorpsVillager;
import com.sparky.lanternring.corps.RedRage;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;

/** Red rage on a player (tint, aura, blood), and a Blue rescue squad joining them because of it. */
public class BlueRecruitTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			BlockPos[] lantern = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos b = p.blockPosition().above(6);
				for (BlockPos pos : BlockPos.betweenClosed(b.offset(-50, -3, -30), b.offset(50, 25, 30))) {
					p.level().setBlock(pos, pos.getY() < b.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				lantern[0] = b.immutable();
				p.level().setBlock(b, ModRegistry.POWER_BATTERY.defaultBlockState().setValue(Corps.PROPERTY, Corps.BLUE), 3);
				p.teleportTo(b.getX() - 8.5, b.getY(), b.getZ() + 0.5);
			});
			ctx.waitTicks(10);
			world.getServer().runOnServer(server -> BlueSquad.callOut(server.getPlayerList().getPlayers().get(0).level(), lantern[0]));
			ctx.waitTicks(160);
			world.getServer().runOnServer(server -> RedRage.give(server.getPlayerList().getPlayers().get(0)));
			ctx.getInput().lookAt(90f, 0f);
			ctx.waitTicks(60);
			ctx.takeScreenshot("blue_recruit_rage_first_person");
			ctx.getInput().pressKey(o -> o.keyTogglePerspective);
			ctx.getInput().pressKey(o -> o.keyTogglePerspective);
			ctx.waitTicks(30);
			ctx.takeScreenshot("blue_recruit_rage_front");
			ctx.getInput().pressKey(o -> o.keyTogglePerspective);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				ServerLevel level = p.level();
				CorpsVillager f = level.getEntitiesOfClass(CorpsVillager.class, new AABB(lantern[0]).inflate(40), v -> v.squadRole() == BlueSquad.Role.FLYER).get(0);
				System.out.println("[BlueRecruitTest] talk " + f.mobInteract(p, InteractionHand.MAIN_HAND));
				// Walk off: the squad should come along.
				p.teleportTo(lantern[0].getX() + 35.5, lantern[0].getY(), lantern[0].getZ() + 0.5);
			});
			for (int i = 0; i < 4; i++) {
				ctx.waitTicks(60);
				int n = i;
				world.getServer().runOnServer(server -> {
					ServerPlayer p = server.getPlayerList().getPlayers().get(0);
					StringBuilder s = new StringBuilder();
					for (CorpsVillager v : p.level().getEntitiesOfClass(CorpsVillager.class, p.getBoundingBox().inflate(80), CorpsVillager::inSquad)) {
						s.append(v.squadRole()).append(String.format(" %.1f; ", v.distanceTo(p)));
					}
					System.out.println("[BlueRecruitTest] " + n + " from player: " + s);
				});
			}
			ctx.getInput().lookAt(-90f, -10f);
			ctx.waitTicks(10);
			ctx.takeScreenshot("blue_recruit_following");
		}
	}
}
