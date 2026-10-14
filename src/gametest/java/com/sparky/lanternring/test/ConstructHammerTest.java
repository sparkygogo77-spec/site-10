package com.sparky.lanternring.test;

import com.sparky.lanternring.ConstructHammers;
import com.sparky.lanternring.Corps;
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
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;

/** The construct hammer (pass 503 R2): a tap in Hammer mode, overhead onto the ground, then from the side into a wall. */
public class ConstructHammerTest implements FabricClientGameTest {
	private static void report(TestSingleplayerContext world, BlockPos o, String when) {
		world.getServer().runOnServer(s -> {
			ServerPlayer p = s.getPlayerList().getPlayers().get(0);
			ServerLevel level = p.level();
			int holes = 0;
			for (BlockPos q : BlockPos.betweenClosed(o.offset(-6, -3, -2), o.offset(6, 4, 12))) {
				if (level.getBlockState(q).isAir() && q.getY() < o.getY()) holes++;
				if (level.getBlockState(q).isAir() && q.getZ() == o.getZ() + 6 && q.getX() >= o.getX() - 2 && q.getX() <= o.getX() + 2 && q.getY() >= o.getY() && q.getY() < o.getY() + 4) holes++;
			}
			var pigs = level.getEntitiesOfClass(Animal.class, new AABB(o).inflate(40));
			String pig = pigs.isEmpty() ? "none" : String.format("hp=%.1f at %s v=%s", pigs.getFirst().getHealth(),
					pigs.getFirst().position().subtract(net.minecraft.world.phys.Vec3.atBottomCenterOf(o)), pigs.getFirst().getDeltaMovement());
			System.out.println("[construct hammer] " + when + ": swinging=" + ConstructHammers.swinging(p) + " holes=" + holes + " pig " + pig);
		});
	}

	private static void tap(ClientGameTestContext ctx) {
		ctx.getInput().holdKey(opt -> opt.keyUse);
		ctx.waitTicks(2);
		ctx.getInput().releaseKey(opt -> opt.keyUse);
	}

	private static void film(ClientGameTestContext ctx, TestSingleplayerContext world, BlockPos o, String name) {
		ctx.waitTicks(12);
		ctx.takeScreenshot(name + "_forming");
		ctx.waitTicks(10);
		ctx.takeScreenshot(name + "_formed");
		ctx.waitTicks(5);
		ctx.takeScreenshot(name + "_swing");
		ctx.waitTicks(3);
		report(world, o, name + " hit");
		ctx.takeScreenshot(name + "_hit");
		ctx.waitTicks(4);
		ctx.takeScreenshot(name + "_crater");
		ctx.waitTicks(14);
		ctx.takeScreenshot(name + "_break");
		ctx.waitTicks(10);
		report(world, o, name + " after");
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			var server = world.getServer();
			server.runCommand("gamemode survival @a");
			server.runCommand("gamerule doDaylightCycle false");
			server.runCommand("gamerule doMobSpawning false");
			server.runCommand("time set 6000");
			ctx.waitTicks(60);
			server.runCommand("execute at @p run fill ~-20 ~-5 ~-10 ~20 ~-1 ~30 dirt");
			server.runCommand("execute at @p run fill ~-20 ~-1 ~-10 ~20 ~-1 ~30 grass_block");
			server.runCommand("execute at @p run fill ~-20 ~ ~-10 ~20 ~20 ~30 air");
			server.runCommand("kill @e[type=!player]");
			BlockPos[] o = new BlockPos[1];
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				o[0] = p.blockPosition();
				ItemStack ring = Corps.GREEN.ring();
				ring.set(ModComponents.MODE, RingMode.HAMMER.ordinal());
				p.setItemInHand(InteractionHand.MAIN_HAND, ring);
			});
			server.runCommand("execute at @p run summon pig ~ ~ ~4");
			// R2a: overhead onto the ground 4 blocks ahead, watched from the side.
			ctx.getInput().lookAt(0f, 22f);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.waitTicks(10);
			report(world, o[0], "before");
			tap(ctx);
			film(ctx, world, o[0], "hammer_ground");

			// R2b: a wall 3 high 6 blocks ahead, struck from the side.
			server.runCommand("kill @e[type=!player]");
			server.runOnServer(s -> s.getPlayerList().getPlayers().get(0).teleportTo(o[0].getX() + 0.5, o[0].getY(), o[0].getZ() + 2.5));
			server.runCommand("fill " + (o[0].getX() - 3) + " " + o[0].getY() + " " + (o[0].getZ() + 6) + " " + (o[0].getX() + 3) + " "
					+ (o[0].getY() + 3) + " " + (o[0].getZ() + 6) + " stone_bricks");
			server.runCommand("summon pig " + (o[0].getX() + 0.5) + " " + o[0].getY() + " " + (o[0].getZ() + 5.3));
			ctx.getInput().lookAt(0f, 5f);
			ctx.waitTicks(10);
			tap(ctx);
			film(ctx, world, o[0], "hammer_wall");

			// First person, onto the ground again.
			server.runCommand("kill @e[type=!player]");
			server.runOnServer(s -> s.getPlayerList().getPlayers().get(0).teleportTo(o[0].getX() - 7.5, o[0].getY(), o[0].getZ() - 4.5));
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 30f);
			ctx.waitTicks(10);
			tap(ctx);
			film(ctx, world, o[0], "hammer_fp");
		}
	}
}
