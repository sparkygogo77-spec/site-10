package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.corps.HoardRain;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;

/** The Orange Hoard Rain: gold bars, gold and diamond blocks and swords fall round a marker, hurt the mobs under them, then fade. */
public class HoardRainTest implements FabricClientGameTest {
	private static void report(TestSingleplayerContext world, BlockPos o, String when) {
		world.getServer().runOnServer(s -> {
			ServerPlayer p = s.getPlayerList().getPlayers().get(0);
			AABB box = new AABB(o).inflate(30);
			int pieces = p.level().getEntitiesOfClass(Display.class, box).size();
			var mobs = p.level().getEntitiesOfClass(Mob.class, box);
			float hp = 0;
			for (Mob m : mobs) hp += m.getHealth();
			System.out.println("[hoard] " + when + ": pieces=" + pieces + " mobs alive=" + mobs.size() + " total hp=" + hp
					+ " player hp=" + p.getHealth());
		});
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			var server = world.getServer();
			server.runCommand("gamemode survival @a");
			server.runCommand("difficulty normal");
			server.runCommand("gamerule doDaylightCycle false");
			server.runCommand("gamerule doMobSpawning false");
			server.runCommand("time set 6000");
			ctx.waitTicks(60);
			server.runCommand("execute at @p run fill ~-30 ~-1 ~-30 ~30 ~-1 ~30 grass_block");
			server.runCommand("execute at @p run fill ~-30 ~ ~-30 ~30 ~30 ~30 air");
			server.runCommand("kill @e[type=!player]");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			BlockPos[] o = new BlockPos[1];
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				o[0] = p.blockPosition();
				ItemStack ring = Corps.ORANGE.ring();
				ring.set(ModComponents.MODE, RingMode.AERIAL.ordinal());
				p.setItemInHand(InteractionHand.MAIN_HAND, ring);
			});
			for (int i = 0; i < 12; i++) {
				int x = -6 + (i % 4) * 4, z = 12 + (i / 4) * 3;
				server.runCommand("execute at @p run summon " + (i % 3 == 0 ? "cow" : "zombie") + " ~" + x + " ~ ~" + z + " {NoAI:1b,PersistenceRequired:1b}");
			}
			ctx.getInput().lookAt(0f, -5f);
			ctx.waitTicks(10);
			report(world, o[0], "before");
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				System.out.println("[hoard] dropped=" + HoardRain.drop(p.level(), p, o[0].offset(0, 0, 16)));
			});
			ctx.waitTicks(22);
			ctx.takeScreenshot("hoard_rain_falling");
			ctx.waitTicks(20);
			ctx.takeScreenshot("hoard_rain_pouring");
			ctx.waitTicks(40);
			report(world, o[0], "after the rain");
			ctx.takeScreenshot("hoard_rain_landed");
			ctx.getInput().lookAt(0f, 30f);
			ctx.waitTicks(3);
			ctx.takeScreenshot("hoard_rain_pile");
			ctx.waitTicks(140);
			report(world, o[0], "faded");
			ctx.takeScreenshot("hoard_rain_faded");
		}
	}
}
