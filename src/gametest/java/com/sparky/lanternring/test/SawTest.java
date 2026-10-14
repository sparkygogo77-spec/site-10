package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.Saws;
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
import net.minecraft.world.phys.AABB;

/** The Saw: pick a block, drag to form it, hold left-click to spin it forward through a wall and a zombie. */
public class SawTest implements FabricClientGameTest {
	private static void report(TestSingleplayerContext world, BlockPos o, String when) {
		world.getServer().runOnServer(s -> {
			ServerPlayer p = s.getPlayerList().getPlayers().get(0);
			ServerLevel level = p.level();
			int trench = 0, wide = 0, wall = 0;
			for (BlockPos q : BlockPos.betweenClosed(o.offset(-1, -5, 0), o.offset(1, -1, 40))) {
				if (level.getBlockState(q).isAir()) {
					if (q.getX() == o.getX()) trench++;
					else wide++;
				}
			}
			for (BlockPos q : BlockPos.betweenClosed(o.offset(-3, 0, 16), o.offset(3, 5, 17))) {
				if (!level.getBlockState(q).isAir()) wall++;
			}
			var mobs = level.getEntitiesOfClass(Mob.class, new AABB(o).inflate(60));
			String zombie = mobs.isEmpty() ? "dead" : String.format("hp=%.1f", mobs.getFirst().getHealth());
			System.out.println("[saw] " + when + ": up=" + Saws.active(p) + " centre=" + (Saws.center(p) == null ? "-" : Saws.center(p).subtract(o.getX(), o.getY(), o.getZ()))
					+ " trench air (middle column)=" + trench + " air beside it=" + wide + " wall blocks left=" + wall + " zombie " + zombie);
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
			server.runCommand("execute at @p run fill ~-20 ~-8 ~-10 ~20 ~-1 ~50 stone");
			server.runCommand("execute at @p run fill ~-20 ~-3 ~-10 ~20 ~-1 ~50 dirt");
			server.runCommand("execute at @p run fill ~-20 ~-1 ~-10 ~20 ~-1 ~50 grass_block");
			server.runCommand("execute at @p run fill ~-20 ~ ~-10 ~20 ~30 ~50 air");
			server.runCommand("execute at @p run fill ~-3 ~ ~16 ~3 ~5 ~17 stone_bricks");
			server.runCommand("kill @e[type=!player]");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			BlockPos[] o = new BlockPos[1];
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				o[0] = p.blockPosition();
				ItemStack ring = Corps.GREEN.ring();
				ring.set(ModComponents.MODE, RingMode.SAW.ordinal());
				p.setItemInHand(InteractionHand.MAIN_HAND, ring);
			});
			server.runCommand("difficulty normal");
			server.runCommand("execute at @p run summon zombie ~ ~ ~24 {NoAI:1b,PersistenceRequired:1b}");
			// Pick the ground about 5 blocks ahead, then drag further out along it.
			ctx.getInput().lookAt(0f, 18f);
			ctx.waitTicks(10);
			ctx.getInput().holdKey(opt -> opt.keyUse);
			ctx.waitTicks(4);
			ctx.takeScreenshot("saw_picked");
			for (int i = 0; i < 6; i++) {
				ctx.getInput().lookAt(0f, 18f - i * 2f);
				ctx.waitTicks(1);
			}
			ctx.waitTicks(6);
			report(world, o[0], "formed");
			ctx.takeScreenshot("saw_formed");
			ctx.getInput().lookAt(0f, 25f);
			ctx.getInput().holdKey(opt -> opt.keyAttack);
			ctx.waitTicks(15);
			ctx.takeScreenshot("saw_spinning");
			ctx.waitTicks(25);
			ctx.takeScreenshot("saw_wall");
			report(world, o[0], "rolling");
			ctx.waitTicks(25);
			ctx.takeScreenshot("saw_zombie");
			ctx.getInput().releaseKey(opt -> opt.keyAttack);
			ctx.waitTicks(10);
			report(world, o[0], "stopped");
			// From the side, to see it half sunk and the trench behind it.
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				p.teleportTo(o[0].getX() + 14.5, o[0].getY() + 3, o[0].getZ() + 18.5);
			});
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(90f, 15f);
			ctx.waitTicks(10);
			ctx.takeScreenshot("saw_side");
			ctx.getInput().releaseKey(opt -> opt.keyUse);
			ctx.waitTicks(4);
			ctx.takeScreenshot("saw_dissolving");
			ctx.waitTicks(15);
			report(world, o[0], "released");
			ctx.takeScreenshot("saw_trench");
		}
	}
}
