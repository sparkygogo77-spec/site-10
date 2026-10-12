package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;

/**
 * The pixel-grid Blue Lantern: held at rest by day and night, through a whole charge (the window
 * halos swelling and whitening), then placed by day and night.
 */
public class BlueLanternTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			if (System.getProperty("lanternring.shaderTest") != null) withShaders(ctx);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = player(server);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.BLUE.ring());
				p.setItemInHand(InteractionHand.OFF_HAND, Corps.BLUE.lantern());
			});
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			world.getServer().runOnServer(server -> PowerRingItem.setCharge(player(server).getMainHandItem(), 100));
			ctx.getInput().lookAt(0f, 15f);
			ctx.waitTicks(30);
			ctx.takeScreenshot("blue_lantern_held_day");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("blue_lantern_held_night");

			ctx.getInput().holdKey(o -> o.keyAttack);
			ctx.waitTicks(1);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(LanternCharge.hold() + LanternCharge.REACH);
			ctx.takeScreenshot("blue_lantern_charge_0");
			int build = LanternCharge.charge() - LanternCharge.REACH;
			ctx.waitTicks(build / 3);
			ctx.takeScreenshot("blue_lantern_charge_33");
			ctx.waitTicks(build / 3);
			ctx.takeScreenshot("blue_lantern_charge_66");
			ctx.waitTicks(build - 2 * (build / 3) - 14);
			ctx.takeScreenshot("blue_lantern_charge_peak");
			ctx.waitTicks(1);
			ctx.takeScreenshot("blue_lantern_charge_flash");
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.getInput().releaseKey(o -> o.keyAttack);
			ctx.waitTicks(20);
			ctx.takeScreenshot("blue_lantern_after");
			ctx.waitTicks(LanternCharge.DEPLETE + 10);

			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("execute at @p run tp @p ~ ~ ~ 180 0");
			world.getServer().runCommand("execute at @p run fill ~-2 ~ ~-4 ~2 ~3 ~-1 air");
			world.getServer().runCommand("execute at @p run setblock ~ ~ ~-3 minecraft:stone_bricks");
			world.getServer().runCommand("execute at @p run setblock ~ ~1 ~-3 lanternring:power_battery[corps=blue]");
			world.getServer().runOnServer(server -> player(server).setItemInHand(InteractionHand.OFF_HAND, ItemStack.EMPTY));
			ctx.getInput().lookAt(180f, 12f);
			ctx.waitTicks(20);
			ctx.takeScreenshot("blue_lantern_placed_day");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("blue_lantern_placed_night");
		}
	}

	/**
	 * For local runs with Iris and a Complementary pack in the test game folder: waits for the
	 * mod to write the "+ Lantern Ring" copy of the pack, then has Iris load it.
	 */
	private static void withShaders(ClientGameTestContext ctx) {
		java.nio.file.Path copy = net.fabricmc.loader.api.FabricLoader.getInstance().getGameDir()
				.resolve("shaderpacks/ComplementaryUnbound_r5.8.1 + Lantern Ring.zip");
		for (int i = 0; i < 60 && !java.nio.file.Files.exists(copy); i++) ctx.waitTicks(20);
		ctx.runOnClient(mc -> {
			try {
				Class.forName("net.irisshaders.iris.Iris").getMethod("reload").invoke(null);
			} catch (ReflectiveOperationException e) {
				throw new RuntimeException("Iris reload failed", e);
			}
		});
		ctx.waitTicks(100);
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
