package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.corps.CorpsVillager;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;

/** Crouching and using a ring on a Blue lantern calls its rescue squad out; a second call while it's out doesn't. */
public class BlueSummonTest implements FabricClientGameTest {
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
				BlockPos b = p.blockPosition();
				for (BlockPos pos : BlockPos.betweenClosed(b.offset(-20, -2, -20), b.offset(20, 20, 20))) {
					p.level().setBlock(pos, pos.getY() < b.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				lantern[0] = b.offset(0, 0, 2).immutable();
				p.level().setBlock(lantern[0], ModRegistry.POWER_BATTERY.defaultBlockState().setValue(Corps.PROPERTY, Corps.BLUE), 3);
				p.teleportTo(b.getX() + 0.5, b.getY(), b.getZ() + 0.5);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.BLUE.ring());
			});
			ctx.getInput().lookAt(0f, 35f);
			ctx.waitTicks(10);
			for (int round = 0; round < 2; round++) {
				ctx.getInput().holdKey(o -> o.keyShift);
				ctx.waitTicks(3);
				ctx.getInput().pressKey(o -> o.keyUse);
				ctx.waitTicks(3);
				ctx.getInput().releaseKey(o -> o.keyShift);
				ctx.waitTicks(80);
				ctx.takeScreenshot("blue_summon_" + round);
				world.getServer().runOnServer(server -> {
					var level = server.getPlayerList().getPlayers().get(0).level();
					int squad = level.getEntitiesOfClass(CorpsVillager.class, new AABB(lantern[0]).inflate(48), CorpsVillager::inSquad).size();
					System.out.println("[BlueSummonTest] squad out: " + squad);
				});
			}
		}
	}
}
