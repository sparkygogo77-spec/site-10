package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.ModEffects;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.Terror;
import com.sparky.lanternring.city.CityBlocks;
import com.sparky.lanternring.corps.FearNuke;
import com.sparky.lanternring.corps.HopeDrop;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ambient.Bat;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;

/** The Blue Hope Drop: a container round a mob, and a dome. */
public class AerialDropsTest implements FabricClientGameTest {
	private static ServerPlayer player(TestSingleplayerContext world) {
		ServerPlayer[] p = new ServerPlayer[1];
		world.getServer().runOnServer(s -> p[0] = s.getPlayerList().getPlayers().get(0));
		return p[0];
	}

	private static void count(TestSingleplayerContext world, BlockPos o, String when) {
		world.getServer().runOnServer(s -> {
			ServerLevel level = s.getPlayerList().getPlayers().get(0).level();
			int bricks = 0, walls = 0, panes = 0;
			for (BlockPos p : BlockPos.betweenClosed(o.offset(-30, -2, -30), o.offset(30, 12, 30))) {
				var st = level.getBlockState(p);
				if (st.is(CityBlocks.HOPE_BRICKS)) bricks++;
				else if (st.is(CityBlocks.HOPE_BRICK_WALL)) walls++;
				else if (st.is(Blocks.STAINED_GLASS_PANE.blue())) panes++;
			}
			System.out.println("[aerial] " + when + ": hope bricks=" + bricks + " walls=" + walls + " panes=" + panes);
		});
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			var server = world.getServer();
			server.runCommand("gamemode creative @a");
			server.runCommand("difficulty normal");
			server.runCommand("gamerule doDaylightCycle false");
			server.runCommand("gamerule doMobSpawning false");
			server.runCommand("time set 6000");
			ctx.waitTicks(60);
			server.runCommand("execute at @p run fill ~-40 ~-1 ~-40 ~40 ~-1 ~40 grass_block");
			server.runCommand("execute at @p run fill ~-40 ~ ~-40 ~40 ~30 ~40 air");
			server.runCommand("kill @e[type=!player]");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			BlockPos[] o = new BlockPos[1];
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				o[0] = p.blockPosition();
				ItemStack ring = Corps.BLUE.ring();
				ring.set(ModComponents.MODE, RingMode.AERIAL.ordinal());
				p.setItemInHand(InteractionHand.MAIN_HAND, ring);
			});
			ctx.getInput().lookAt(0f, 20f);
			ctx.waitTicks(10);

			// ---- Blue: a container round a zombie, and a dome.
			server.runCommand("execute at @p run summon zombie ~-6 ~ ~14 {NoAI:1b}");
			ctx.waitTicks(5);
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				Mob zombie = p.level().getEntitiesOfClass(Mob.class, new AABB(p.blockPosition()).inflate(30)).getFirst();
				System.out.println("[aerial] cage=" + HopeDrop.drop(p.level(), p, zombie.blockPosition(), true));
				System.out.println("[aerial] dome=" + HopeDrop.drop(p.level(), p, o[0].offset(8, 0, 16), false));
			});
			ctx.waitTicks(14);
			ctx.takeScreenshot("hope_drop_falling");
			ctx.waitTicks(30);
			ctx.takeScreenshot("hope_drop_hard_light");
			ctx.waitTicks(40);
			ctx.takeScreenshot("hope_drop_setting");
			ctx.waitTicks(60);
			count(world, o[0], "blue set");
			ctx.takeScreenshot("hope_drop_set");
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				p.teleportTo(o[0].getX() + 8.5, o[0].getY(), o[0].getZ() + 15.5);
			});
			ctx.getInput().lookAt(0f, -15f);
			ctx.waitTicks(20);
			ctx.takeScreenshot("hope_drop_inside_dome");

			// The Yellow Fear Nuke has its own test now (FearNukeTest).
		}
	}
}
