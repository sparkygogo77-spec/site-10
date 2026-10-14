package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;

/** A Green or Blue ring forms J's T3/U3 construct tool as you mine (29a) and mines like it. */
public class ConstructToolsTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set noon");
			world.getServer().runCommand("gamemode survival @a");
			ctx.waitTicks(40);
			BlockPos[] at = new BlockPos[1];
			Object[][] cases = {{Corps.GREEN, Blocks.STONE, "pickaxe"}, {Corps.BLUE, Blocks.OAK_LOG, "axe"}, {Corps.GREEN, Blocks.DIRT, "shovel"},
					{Corps.BLUE, Blocks.OBSIDIAN, "hammer"}};
			for (Object[] c : cases) {
				Corps corps = (Corps) c[0];
				Block block = (Block) c[1];
				String name = (String) c[2];
				world.getServer().runOnServer(server -> {
					ServerPlayer p = server.getPlayerList().getPlayers().get(0);
					BlockPos b = p.blockPosition();
					for (BlockPos pos : BlockPos.betweenClosed(b.offset(-3, 0, -3), b.offset(3, 3, 3))) p.level().setBlock(pos, Blocks.AIR.defaultBlockState(), 2);
					at[0] = b.north(2).above();
					p.level().setBlock(at[0], block.defaultBlockState(), 3);
					p.teleportTo(b.getX() + 0.5, b.getY(), b.getZ() + 0.5);
					ItemStack ring = corps.ring();
					PowerRingItem.setCharge(ring, 500);
					p.getInventory().setItem(p.getInventory().getSelectedSlot(), ring);
				});
				ctx.getInput().lookAt(180f, 10f);
				ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
				ctx.waitTicks(10);
				ctx.getInput().holdKey(o -> o.keyAttack);
				ctx.waitTicks(4);
				ctx.takeScreenshot("construct_tool_" + name + "_first");
				ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
				ctx.waitTicks(3);
				ctx.takeScreenshot("construct_tool_" + name + "_third");
				ctx.waitTicks(80);
				ctx.getInput().releaseKey(o -> o.keyAttack);
				world.getServer().runOnServer(server -> {
					ServerPlayer p = server.getPlayerList().getPlayers().get(0);
					System.out.println("[ConstructToolsTest] " + name + ": block now " + p.level().getBlockState(at[0]).getBlock()
							+ ", charge " + PowerRingItem.getCharge(p.getMainHandItem()) + ", items " + p.getInventory().countItem(block.asItem()));
				});
			}
		}
	}
}
