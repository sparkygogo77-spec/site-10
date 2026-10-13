package com.sparky.lanternring.test;

import com.mojang.blaze3d.platform.InputConstants;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.OrangeHorde;
import com.sparky.lanternring.corps.CorpsVillager;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Mob;

/**
 * The Orange Lantern's Horde: summon the orange lantern (R), hold R, and mobs crawl up out of the
 * ground a second apart, a fallen Blue villager among them in orange; hold R again to stop it.
 */
public class OrangeHordeTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = player(server);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.ORANGE.ring());
				p.setItemInHand(InteractionHand.OFF_HAND, Corps.ORANGE.lantern());
				p.setAttached(OrangeHorde.FALLEN_BLUE, 2);
			});
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 20f);
			ctx.getInput().pressKey(InputConstants.KEY_R);
			ctx.waitTicks(25);
			shot(ctx, "orange_lantern_summoned");

			ctx.getInput().holdKey(InputConstants.KEY_R);
			ctx.waitTicks(14);
			ctx.getInput().releaseKey(InputConstants.KEY_R);
			ctx.waitTicks(12);
			shot(ctx, "orange_horde_crawling");
			ctx.waitTicks(100);
			shot(ctx, "orange_horde_risen");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(0f, 35f);
			ctx.waitTicks(2);
			shot(ctx, "orange_horde_third_person");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));

			int[] counts = world.getServer().computeOnServer(server -> {
				ServerPlayer p = player(server);
				int horde = 0, villagers = 0;
				for (Mob m : p.level().getEntitiesOfClass(Mob.class, p.getBoundingBox().inflate(32), m -> m.entityTags().contains(OrangeHorde.TAG))) {
					horde++;
					if (m instanceof CorpsVillager cv && cv.corps() == Corps.ORANGE) villagers++;
				}
				return new int[] {horde, villagers};
			});
			System.out.println("[orange-horde-test] horde=" + counts[0] + " villagers=" + counts[1]);
			if (counts[0] < 5) throw new AssertionError("The Horde should have raised at least 5 mobs, found " + counts[0]);
			if (counts[1] < 1) throw new AssertionError("A fallen Blue villager should rise in orange");

			// Hold R again: it stops.
			ctx.getInput().holdKey(InputConstants.KEY_R);
			ctx.waitTicks(14);
			ctx.getInput().releaseKey(InputConstants.KEY_R);
			ctx.waitTicks(2);
			boolean running = world.getServer().computeOnServer(server -> OrangeHorde.running(player(server)));
			if (running) throw new AssertionError("Holding R again should stop the Horde");
		}
	}

	private static void shot(ClientGameTestContext ctx, String name) {
		ctx.takeScreenshot(name);
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
