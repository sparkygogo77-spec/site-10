package com.sparky.lanternring.test;

import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.PortalExit;
import com.sparky.lanternring.RingMode;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.HopperBlockEntity;

/** Opens a portal to an exit by a chest, walks through it, then lets the Loot Golem fill the chest. */
public class PortalGolemTest implements FabricClientGameTest {
	private static void report(TestSingleplayerContext world, BlockPos chest, String when) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			Container c = HopperBlockEntity.getContainerAt(p.level(), chest);
			int items = 0;
			if (c != null) for (int i = 0; i < c.getContainerSize(); i++) items += c.getItem(i).getCount();
			int drops = p.level().getEntitiesOfClass(ItemEntity.class, p.getBoundingBox().inflate(30)).size();
			System.out.println("[portal-golem] " + when + ": player=" + p.blockPosition() + " chestItems=" + items + " drops=" + drops);
		});
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));

			BlockPos[] chest = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos o = p.blockPosition().above(30);
				var level = p.level();
				for (int x = -30; x <= 30; x++)
					for (int z = -30; z <= 30; z++) {
						level.setBlock(o.offset(x, -1, z), Blocks.STONE.defaultBlockState(), 2);
						for (int y = 0; y < 6; y++) level.setBlock(o.offset(x, y, z), Blocks.AIR.defaultBlockState(), 2);
					}
				// The chest 20 blocks east, the exit just west of it facing west (yaw 90).
				chest[0] = o.offset(20, 0, 0);
				level.setBlock(chest[0], Blocks.CHEST.defaultBlockState(), 3);
				p.getMainHandItem().set(ModComponents.PORTAL_EXIT, new PortalExit(GlobalPos.of(level.dimension(), chest[0].west()), 90f));
				p.getMainHandItem().set(ModComponents.MODE, RingMode.PORTAL.ordinal());
				p.teleportTo(o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
			});
			// Face south, looking down at the floor ahead, and tap to open a portal there.
			ctx.getInput().lookAt(0f, 25f);
			ctx.waitTicks(20);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(10);
			ctx.takeScreenshot("portal_open");
			ctx.getInput().lookAt(0f, 5f);
			ctx.waitTicks(5);
			ctx.takeScreenshot("portal_front");
			report(world, chest[0], "opened");
			ctx.getInput().holdKey(o -> o.keyUp);
			ctx.waitTicks(40);
			ctx.getInput().releaseKey(o -> o.keyUp);
			report(world, chest[0], "walked through");
			ctx.takeScreenshot("portal_came_out");

			// Turn round to see the exit, then the golem.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.teleportTo(chest[0].getX() - 6.5, chest[0].getY(), chest[0].getZ() + 0.5);
				p.getMainHandItem().set(ModComponents.MODE, RingMode.GOLEM.ordinal());
				var level = p.level();
				for (int i = 0; i < 30; i++) {
					ItemStack stack = new ItemStack(i % 3 == 0 ? Items.COBBLESTONE : i % 3 == 1 ? Items.OAK_LOG : Items.IRON_INGOT, 64);
					ItemEntity e = new ItemEntity(level, p.getX() - 4 - (i % 6), p.getY() + 0.5, p.getZ() - 5 + (i / 6) * 2, stack);
					level.addFreshEntity(e);
				}
			});
			ctx.getInput().lookAt(90f, 10f);
			ctx.waitTicks(20);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(30);
			ctx.takeScreenshot("golem_collecting");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.waitTicks(30);
			ctx.takeScreenshot("golem_collecting_third");
			report(world, chest[0], "golem+60");
			for (int i = 0; i < 6; i++) {
				ctx.waitTicks(20);
				ctx.takeScreenshot("golem_trip_" + i);
				report(world, chest[0], "golem trip " + i);
			}
			ctx.waitTicks(100);
			report(world, chest[0], "golem end");
		}
	}
}
