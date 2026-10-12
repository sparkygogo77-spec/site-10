package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingMode;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.monster.illager.Vindicator;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;

/** The Violet Lantern's Crystal Prison: a vindicator sealed in violet crystal, held, then shattered early. */
public class CrystalPrisonTest implements FabricClientGameTest {
	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}

	private static void report(TestSingleplayerContext world, BlockPos o, String when) {
		world.getServer().runOnServer(server -> {
			var level = player(server).level();
			int crystal = 0;
			for (BlockPos pos : BlockPos.betweenClosed(o.offset(-4, -2, 2), o.offset(4, 5, 12))) {
				if (level.getBlockState(pos).is(ModRegistry.LIGHT_CONSTRUCT)) crystal++;
			}
			StringBuilder mobs = new StringBuilder();
			for (Vindicator v : level.getEntitiesOfClass(Vindicator.class, new AABB(o).inflate(20))) {
				mobs.append(String.format(" (%.2f,%.2f,%.2f)", v.getX() - o.getX(), v.getY() - o.getY(), v.getZ() - o.getZ()));
			}
			System.out.println("[prison] " + when + ": crystal blocks=" + crystal + " vindicator at" + mobs
					+ " charge=" + player(server).getMainHandItem().get(ModComponents.CHARGE));
		});
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("effect give @a resistance infinite 255 true");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			BlockPos[] origin = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = player(server);
				var ring = Corps.VIOLET.ring();
				ring.set(ModComponents.MODE, RingMode.CRYSTAL_PRISON.ordinal());
				p.setItemInHand(InteractionHand.MAIN_HAND, ring);
				BlockPos o = p.blockPosition().above(10);
				origin[0] = o;
				var level = p.level();
				for (BlockPos pos : BlockPos.betweenClosed(o.offset(-15, -3, -15), o.offset(15, 10, 15))) {
					level.setBlock(pos, pos.getY() < o.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				p.teleportTo(o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
			});
			world.getServer().runCommand("kill @e[type=!player]");
			BlockPos o = origin[0];
			world.getServer().runCommand("summon vindicator " + (o.getX() + 0.5) + " " + o.getY() + " " + (o.getZ() + 7.5));
			ctx.getInput().lookAt(0f, 12f);
			ctx.waitTicks(10);
			ctx.getInput().pressKey(opt -> opt.keyUse);
			ctx.waitTicks(10);
			ctx.takeScreenshot("crystal_prison_sealed");
			report(world, o, "sealed");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			world.getServer().runOnServer(server -> player(server).teleportTo(o.getX() + 4.5, o.getY(), o.getZ() + 3.5));
			ctx.waitTicks(40);
			ctx.takeScreenshot("crystal_prison_side");
			report(world, o, "after 2 s");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			world.getServer().runOnServer(server -> player(server).teleportTo(o.getX() + 0.5, o.getY(), o.getZ() + 0.5));
			ctx.getInput().lookAt(0f, 12f);
			ctx.waitTicks(5);
			ctx.getInput().pressKey(opt -> opt.keyUse);
			ctx.waitTicks(3);
			ctx.takeScreenshot("crystal_prison_shatter");
			ctx.waitTicks(10);
			report(world, o, "shattered");
		}
	}
}
