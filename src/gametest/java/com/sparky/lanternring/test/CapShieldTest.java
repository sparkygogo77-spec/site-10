package com.sparky.lanternring.test;

import com.sparky.lanternring.hero.HeroItems;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.zombie.Zombie;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;

/** Captain America's Shield: held, blocking, thrown so it ricochets between zombies and back, and the slam. */
public class CapShieldTest implements FabricClientGameTest {
	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}

	private static void report(TestSingleplayerContext world, BlockPos o, String when) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = player(server);
			StringBuilder hp = new StringBuilder();
			for (LivingEntity z : p.level().getEntitiesOfClass(Zombie.class, new AABB(o).inflate(30))) {
				hp.append(String.format(" %.0f@(%.1f,%.1f)", z.getHealth(), z.getX() - o.getX(), z.getZ() - o.getZ()));
			}
			System.out.println("[capshield] " + when + ": main=" + p.getMainHandItem().getItem() + " zombies=" + hp);
		});
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("effect give @a resistance infinite 255 true");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			BlockPos[] origin = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = player(server);
				p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(HeroItems.CAP_SHIELD));
				BlockPos o = p.blockPosition().above(10);
				origin[0] = o;
				var level = p.level();
				for (BlockPos pos : BlockPos.betweenClosed(o.offset(-20, -3, -20), o.offset(20, 10, 20))) {
					level.setBlock(pos, pos.getY() < o.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				p.teleportTo(o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
			});
			world.getServer().runCommand("kill @e[type=!player]");
			BlockPos o = origin[0];
			// Zombies in an arc ahead (south, +z), frozen so the bounces are easy to follow.
			int[][] spots = {{0, 9}, {-5, 11}, {5, 12}, {-2, 15}, {3, 6}};
			for (int[] s : spots) {
				world.getServer().runCommand("summon zombie " + (o.getX() + s[0] + 0.5) + " " + o.getY() + " " + (o.getZ() + s[1] + 0.5) + " {NoAI:1b,Health:40f,attributes:[{id:\"minecraft:max_health\",base:40}]}");
			}
			ctx.getInput().lookAt(0f, 8f);
			ctx.waitTicks(30);
			ctx.takeScreenshot("capshield_held");
			ctx.getInput().holdKey(o2 -> o2.keyUse);
			ctx.waitTicks(15);
			ctx.takeScreenshot("capshield_blocking");
			ctx.getInput().releaseKey(o2 -> o2.keyUse);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.waitTicks(10);
			ctx.takeScreenshot("capshield_third_person");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.waitTicks(5);
			report(world, o, "before throw");

			ctx.getInput().holdKey(o2 -> o2.keyShift);
			ctx.waitTicks(3);
			ctx.getInput().pressKey(o2 -> o2.keyUse);
			ctx.getInput().releaseKey(o2 -> o2.keyShift);
			ctx.waitTicks(4);
			ctx.takeScreenshot("capshield_thrown");
			ctx.waitTicks(6);
			ctx.takeScreenshot("capshield_ricochet");
			ctx.waitTicks(8);
			ctx.takeScreenshot("capshield_ricochet_2");
			ctx.waitTicks(60);
			report(world, o, "after throw");
			ctx.takeScreenshot("capshield_caught");

			// Slam from 6 blocks up among two fresh zombies.
			world.getServer().runCommand("kill @e[type=zombie]");
			world.getServer().runCommand("summon zombie " + (o.getX() + 2.5) + " " + o.getY() + " " + (o.getZ() + 0.5) + " {NoAI:1b}");
			world.getServer().runCommand("summon zombie " + (o.getX() - 1.5) + " " + o.getY() + " " + (o.getZ() + 3.5) + " {NoAI:1b}");
			world.getServer().runOnServer(server -> player(server).teleportTo(o.getX() + 0.5, o.getY() + 6, o.getZ() + 0.5));
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(0f, 30f);
			ctx.waitTicks(2);
			ctx.getInput().holdKey(o2 -> o2.keyShift);
			ctx.waitTicks(2);
			ctx.getInput().pressKey(o2 -> o2.keyUse);
			ctx.getInput().releaseKey(o2 -> o2.keyShift);
			ctx.waitTicks(5);
			ctx.takeScreenshot("capshield_slam");
			ctx.waitTicks(10);
			report(world, o, "after slam");
			world.getServer().runOnServer(server -> System.out.println("[capshield] player hp after slam=" + player(server).getHealth()));
		}
	}
}
