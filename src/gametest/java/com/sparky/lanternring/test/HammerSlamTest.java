package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.HammerSlams;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;

/** The Hammer mode: aim the landing, let go, leap and smash (survival, so fall damage would show). */
public class HammerSlamTest implements FabricClientGameTest {
	private static void report(TestSingleplayerContext world, BlockPos o, String when) {
		world.getServer().runOnServer(s -> {
			ServerPlayer p = s.getPlayerList().getPlayers().get(0);
			ServerLevel level = p.level();
			int holes = 0;
			for (BlockPos q : BlockPos.betweenClosed(o.offset(-12, -4, 0), o.offset(12, -1, 30))) {
				if (level.getBlockState(q).isAir()) holes++;
			}
			var mobs = level.getEntitiesOfClass(Mob.class, new AABB(o).inflate(40));
			String zombie = mobs.isEmpty() ? "dead" : String.format("hp=%.1f at %s", mobs.getFirst().getHealth(), mobs.getFirst().blockPosition().subtract(o));
			System.out.println("[hammer] " + when + ": player at " + p.blockPosition().subtract(o) + " hp=" + p.getHealth()
					+ " leaping=" + HammerSlams.leaping(p) + " crater blocks=" + holes + " zombie " + zombie);
		});
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			var server = world.getServer();
			server.runCommand("gamemode survival @a");
			server.runCommand("difficulty peaceful");
			server.runCommand("gamerule doDaylightCycle false");
			server.runCommand("gamerule doMobSpawning false");
			server.runCommand("time set 6000");
			ctx.waitTicks(60);
			server.runCommand("execute at @p run fill ~-30 ~-5 ~-10 ~30 ~-1 ~40 dirt");
			server.runCommand("execute at @p run fill ~-30 ~-1 ~-10 ~30 ~-1 ~40 grass_block");
			server.runCommand("execute at @p run fill ~-30 ~ ~-10 ~30 ~30 ~40 air");
			server.runCommand("kill @e[type=!player]");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			BlockPos[] o = new BlockPos[1];
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				o[0] = p.blockPosition();
				ItemStack ring = Corps.BLUE.ring();
				ring.set(ModComponents.MODE, RingMode.HAMMER.ordinal());
				p.setItemInHand(InteractionHand.MAIN_HAND, ring);
				p.level().setBlock(o[0].offset(-6, -1, 18), Blocks.BEDROCK.defaultBlockState(), 3);
			});
			server.runCommand("difficulty normal");
			server.runCommand("execute at @p run summon zombie ~ ~ ~18 {NoAI:1b,PersistenceRequired:1b}");
			// About 16 blocks out, straight ahead.
			ctx.getInput().lookAt(0f, 6f);
			ctx.waitTicks(10);
			report(world, o[0], "before");
			ctx.getInput().holdKey(opt -> opt.keyUse);
			ctx.waitTicks(12);
			ctx.takeScreenshot("hammer_aim");
			ctx.getInput().releaseKey(opt -> opt.keyUse);
			ctx.waitTicks(6);
			ctx.takeScreenshot("hammer_rising");
			report(world, o[0], "rising");
			ctx.waitTicks(10);
			ctx.takeScreenshot("hammer_swing");
			ctx.waitTicks(6);
			ctx.takeScreenshot("hammer_smash");
			ctx.waitTicks(30);
			report(world, o[0], "landed");
			ctx.takeScreenshot("hammer_crater");

		}
	}
}
