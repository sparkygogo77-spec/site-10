package com.sparky.lanternring.test;

import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.client.RingLabScreen;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

/** The Beam's charging glow on the hand (first and third person) and the HUD charge meter in each mode. */
public class ChargeMeterTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("effect give @a resistance 1000 4 true");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(60);
			ring(world, RingMode.BEAM, 1);
			RingTuning.BEAM_CHARGE.set(3);

			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 10f);
			ctx.waitTicks(20);
			ctx.takeScreenshot("meter_beam_idle");
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(15);
			ctx.takeScreenshot("charge_fp_25");
			ctx.waitTicks(20);
			ctx.takeScreenshot("charge_fp_60");
			ctx.waitTicks(20);
			ctx.takeScreenshot("charge_fp_95");
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.waitTicks(40);

			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(30);
			ctx.takeScreenshot("charge_front_50");
			ctx.waitTicks(25);
			ctx.takeScreenshot("charge_front_95");
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.waitTicks(40);

			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(50);
			ctx.takeScreenshot("charge_front_night");
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.waitTicks(10);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(50);
			ctx.takeScreenshot("charge_fp_night");
			ctx.getInput().releaseKey(o -> o.keyUse);
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);

			for (int size : new int[] {1, 3, 5}) {
				ring(world, RingMode.ANVIL, size);
				ctx.waitTicks(10);
				ctx.takeScreenshot("meter_anvil_" + size);
			}
			for (RingMode mode : new RingMode[] {RingMode.DOME, RingMode.TETHER, RingMode.BLAST}) {
				ring(world, mode, 1);
				ctx.waitTicks(10);
				ctx.takeScreenshot("meter_" + mode.name().toLowerCase());
			}
			ctx.setScreen(() -> new RingLabScreen(null));
			ctx.waitTicks(5);
			ctx.takeScreenshot("lab_menu");
			ctx.setScreen(() -> null);
		}
	}

	private static void ring(TestSingleplayerContext world, RingMode mode, int anvilSize) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = player(server);
			ItemStack ring = p.getMainHandItem();
			ring.set(ModComponents.MODE, mode.ordinal());
			ring.set(ModComponents.ANVIL_SIZE, anvilSize);
			PowerRingItem.setCharge(ring, 640);
		});
	}

	private static ServerPlayer player(MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
