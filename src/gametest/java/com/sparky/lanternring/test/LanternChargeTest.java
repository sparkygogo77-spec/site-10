package com.sparky.lanternring.test;

import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.client.LabSettings;
import com.sparky.lanternring.client.LanternFirstPerson;
import com.sparky.lanternring.client.RingFirstPerson;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.level.ServerPlayer;

/** Photographs the lantern in the off hand, then the hold-to-charge animation, and checks the ring fills. */
public class LanternChargeTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			world.getServer().runCommand("item replace entity @a weapon.offhand with lanternring:power_battery");
			ctx.waitTicks(60);
			LabSettings lab = LabSettings.get();
			lab.ringModel = LabSettings.RingModel.EMBLEM;
			lab.handPose = LabSettings.HandPose.FIST_DOWN;
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			setCharge(world, 100);
			ctx.getInput().lookAt(0f, 15f);
			ctx.waitTicks(20);
			shot(ctx, "lantern_idle");

			// Turn quickly: the lantern should swing.
			for (int i = 1; i <= 4; i++) {
				ctx.getInput().lookAt(i * 12f, 15f);
				ctx.waitTicks(1);
			}
			shot(ctx, "lantern_sway");
			ctx.getInput().lookAt(0f, 15f);
			ctx.waitTicks(30);

			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(5);
			shot(ctx, "lantern_idle_night");
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(20);
			shot(ctx, "lantern_hold_1s");
			ctx.waitTicks(LanternCharge.HOLD - 20 + 4);
			shot(ctx, "lantern_raising");
			ctx.waitTicks(LanternCharge.REACH);
			shot(ctx, "lantern_ring_in");
			ctx.waitTicks(LanternCharge.CHARGE - LanternCharge.REACH - 6);
			shot(ctx, "lantern_charging_peak");
			ctx.waitTicks(8);
			shot(ctx, "lantern_charged_flash");
			ctx.waitTicks(LanternCharge.SETTLE + 4);
			shot(ctx, "lantern_settled");
			ctx.getInput().releaseKey(o -> o.keyUse);
			int charge = world.getServer().computeOnServer(server ->
					PowerRingItem.getCharge(player(server).getMainHandItem()));
			if (charge != PowerRingItem.MAX_CHARGE) {
				throw new AssertionError("Ring should be full after charging from the lantern, but has " + charge);
			}

			// The same at day, in third person, mid-charge.
			world.getServer().runCommand("time set 6000");
			setCharge(world, 100);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(LanternCharge.HOLD + LanternCharge.REACH + 6);
			shot(ctx, "lantern_ring_in_day");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.waitTicks(2);
			shot(ctx, "lantern_charging_third_person");
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));

			// A quick tap still fires the ring (Beam costs 15).
			world.getServer().runOnServer(server -> player(server).getMainHandItem().set(ModComponents.MODE, 1));
			setCharge(world, 500);
			ctx.waitTicks(30);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(10);
			int afterTap = world.getServer().computeOnServer(server ->
					PowerRingItem.getCharge(player(server).getMainHandItem()));
			if (afterTap >= 500) throw new AssertionError("A tap with the lantern held should still fire the ring, charge " + afterTap);

			// Close-up of the ring on the fist without the lantern.
			world.getServer().runCommand("item replace entity @a weapon.offhand with minecraft:air");
			ctx.getInput().lookAt(0f, 40f);
			ctx.waitTicks(10);
			ctx.takeScreenshot("ring_emblem_fp");
		}
	}

	private static void shot(ClientGameTestContext ctx, String name) {
		ctx.takeScreenshot(name);
		System.out.println("[lantern-test] " + name + ": " + LanternFirstPerson.debug + " | " + RingFirstPerson.debug);
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}

	private static void setCharge(TestSingleplayerContext world, int charge) {
		world.getServer().runOnServer(server -> PowerRingItem.setCharge(player(server).getMainHandItem(), charge));
	}
}
