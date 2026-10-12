package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.monster.skeleton.Skeleton;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;

/** Raises a red ring's riot Shield (mid-raise and raised, first and third person), then holds it in front of a skeleton and its arrows come back. */
public class ShieldTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("difficulty normal");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(60);
			BlockPos[] origin = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos o = p.blockPosition().above(6);
				origin[0] = o;
				var level = p.level();
				for (int x = -12; x <= 12; x++)
					for (int y = -2; y <= 8; y++)
						for (int z = -6; z <= 20; z++)
							level.setBlock(o.offset(x, y, z), y < 0 ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				p.teleportTo(o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
				p.getMainHandItem().set(ModComponents.CORPS, Corps.RED);
				p.getMainHandItem().set(ModComponents.MODE, RingMode.SHIELD.ordinal());
				PowerRingItem.setCharge(p.getMainHandItem(), PowerRingItem.MAX_CHARGE);
			});
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(20);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(2);
			ctx.takeScreenshot("shield_raising_first_person");
			ctx.waitTicks(8);
			ctx.takeScreenshot("shield_first_person");
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.waitTicks(10);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(2);
			ctx.takeScreenshot("shield_raising_front");
			ctx.waitTicks(8);
			ctx.takeScreenshot("shield_front");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.waitTicks(5);
			ctx.takeScreenshot("shield_behind");
			ctx.getInput().lookAt(-60f, 0f);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.waitTicks(5);
			ctx.takeScreenshot("shield_side");
			ctx.getInput().lookAt(0f, 0f);

			world.getServer().runCommand("summon minecraft:skeleton " + (origin[0].getX() + 0.5) + " " + origin[0].getY() + " " + (origin[0].getZ() + 12.5));
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			for (int i = 0; i < 4; i++) {
				ctx.waitTicks(20);
				ctx.takeScreenshot("shield_skeleton_" + i);
			}
			ctx.waitTicks(80);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				var skeletons = p.level().getEntitiesOfClass(Skeleton.class, new AABB(p.blockPosition()).inflate(30));
				System.out.println("[shield] player health=" + p.getHealth() + " charge=" + PowerRingItem.getCharge(p.getMainHandItem())
						+ " skeletons=" + skeletons.size() + (skeletons.isEmpty() ? "" : " skeleton health=" + skeletons.get(0).getHealth()));
			});
			ctx.getInput().releaseKey(o -> o.keyUse);
		}
	}
}
