package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.item.ConstructToolItem;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;

/** Tools mode: right-click puts the six construct tools in the hotbar, they mine like tools and cost charge, right-click again recalls them. */
public class ConstructToolsTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set noon");
			world.getServer().runCommand("gamemode survival @a");
			ctx.waitTicks(40);
			for (Corps corps : new Corps[] {Corps.GREEN, Corps.BLUE}) {
				BlockPos[] at = new BlockPos[1];
				Block block = corps == Corps.GREEN ? Blocks.STONE : Blocks.OAK_LOG;
				int toolSlot = corps == Corps.GREEN ? 2 : 3; // slot 1 sword, 2 pickaxe, 3 axe
				world.getServer().runOnServer(server -> {
					ServerPlayer p = server.getPlayerList().getPlayers().get(0);
					p.getInventory().clearContent();
					BlockPos b = p.blockPosition();
					for (BlockPos pos : BlockPos.betweenClosed(b.offset(-3, 0, -3), b.offset(3, 3, 3))) p.level().setBlock(pos, Blocks.AIR.defaultBlockState(), 2);
					at[0] = b.north(2).above();
					p.level().setBlock(at[0], block.defaultBlockState(), 3);
					p.teleportTo(b.getX() + 0.5, b.getY(), b.getZ() + 0.5);
					ItemStack ring = corps.ring();
					PowerRingItem.setCharge(ring, 500);
					ring.set(ModComponents.MODE, RingMode.TOOLS.ordinal());
					p.getInventory().setItem(0, ring);
					p.getInventory().setItem(8, new ItemStack(net.minecraft.world.item.Items.NETHERITE_PICKAXE));
					p.getInventory().setSelectedSlot(0);
				});
				ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
				ctx.getInput().lookAt(180f, -30f);
				ctx.waitTicks(10);
				ctx.getInput().pressKey(o -> o.keyUse);
				ctx.waitTicks(10);
				world.getServer().runOnServer(server -> {
					Inventory inv = server.getPlayerList().getPlayers().get(0).getInventory();
					StringBuilder s = new StringBuilder();
					for (int i = 0; i < 9; i++) s.append(i).append('=').append(inv.getItem(i).getItem()).append(' ');
					System.out.println("[ConstructToolsTest] " + corps + " hotbar after right-click: " + s);
				});
				ctx.takeScreenshot("construct_tools_" + corps.getSerializedName() + "_hotbar");
				if (corps == Corps.BLUE) {
					// Worn in the ring slot instead of carried: the tools stay and still draw on it.
					world.getServer().runOnServer(server -> {
						ServerPlayer p = server.getPlayerList().getPlayers().get(0);
						com.sparky.lanternring.RingSlot.setWorn(p, p.getInventory().getItem(0).copy());
						p.getInventory().setItem(0, ItemStack.EMPTY);
					});
				}
				ctx.runOnClient(mc -> mc.player.getInventory().setSelectedSlot(8));
				ctx.getInput().lookAt(180f, 10f);
				ctx.waitTicks(30); // the hand comes up as the attack recharges
				ctx.takeScreenshot("construct_tools_" + corps.getSerializedName() + "_vanilla");
				ctx.runOnClient(mc -> mc.player.getInventory().setSelectedSlot(toolSlot));
				ctx.getInput().lookAt(180f, 10f);
				ctx.waitTicks(30);
				ctx.takeScreenshot("construct_tools_" + corps.getSerializedName() + "_first");
				ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
				ctx.getInput().lookAt(150f, 35f);
				ctx.waitTicks(3);
				ctx.takeScreenshot("construct_tools_" + corps.getSerializedName() + "_third");
				ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
				ctx.waitTicks(3);
				ctx.takeScreenshot("construct_tools_" + corps.getSerializedName() + "_back");
				ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
				ctx.getInput().lookAt(180f, 10f);
				ctx.waitTicks(2);
				ctx.getInput().holdKey(o -> o.keyAttack);
				ctx.waitTicks(4);
				ctx.takeScreenshot("construct_tools_" + corps.getSerializedName() + "_mining");
				ctx.waitTicks(36);
				ctx.getInput().releaseKey(o -> o.keyAttack);
				world.getServer().runOnServer(server -> {
					ServerPlayer p = server.getPlayerList().getPlayers().get(0);
					System.out.println("[ConstructToolsTest] " + corps + ": block now " + p.level().getBlockState(at[0]).getBlock()
							+ ", ring charge " + PowerRingItem.getCharge(com.sparky.lanternring.RingSlot.ring(p).isEmpty() ? p.getInventory().getItem(0) : com.sparky.lanternring.RingSlot.ring(p)) + ", items " + p.getInventory().countItem(block.asItem()));
				});
				// Recall: back to the ring, right-click again.
				if (corps == Corps.BLUE) {
					world.getServer().runOnServer(server -> {
						ServerPlayer p = server.getPlayerList().getPlayers().get(0);
						p.getInventory().setItem(0, com.sparky.lanternring.RingSlot.worn(p).copy());
						com.sparky.lanternring.RingSlot.setWorn(p, ItemStack.EMPTY);
					});
				}
				ctx.runOnClient(mc -> mc.player.getInventory().setSelectedSlot(0));
				ctx.getInput().lookAt(180f, -30f);
				ctx.waitTicks(5);
				ctx.getInput().pressKey(o -> o.keyUse);
				ctx.waitTicks(10);
				world.getServer().runOnServer(server -> {
					Inventory inv = server.getPlayerList().getPlayers().get(0).getInventory();
					int tools = 0;
					for (int i = 0; i < inv.getContainerSize(); i++) if (inv.getItem(i).getItem() instanceof ConstructToolItem) tools++;
					System.out.println("[ConstructToolsTest] " + corps + ": tools left after recall " + tools);
				});
			}
		}
	}
}
