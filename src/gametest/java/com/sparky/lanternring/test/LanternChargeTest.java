package com.sparky.lanternring.test;

import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.client.LabSettings;
import com.sparky.lanternring.client.LanternFirstPerson;
import com.sparky.lanternring.client.RingFirstPerson;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;

/**
 * Photographs the lantern in the off hand, then the left + right click charge animation, and checks the
 * ring fills; then checks the lantern stays out of the ring's way, sets down on a double-click and
 * hold, and never stays in the main hand.
 */
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
			lab.ringModel = LabSettings.RingModel.CREST;
			RingFirstPerson.recordDebug = true;
			lab.handPose = LabSettings.HandPose.RING_FORWARD;
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
			ctx.getInput().holdKey(o -> o.keyAttack);
			ctx.waitTicks(1);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(4);
			shot(ctx, "lantern_hold_start");
			ctx.waitTicks(LanternCharge.hold());
			shot(ctx, "lantern_raising");
			ctx.waitTicks(LanternCharge.REACH);
			shot(ctx, "lantern_ring_in");
			ctx.waitTicks(LanternCharge.charge() - LanternCharge.REACH - 6);
			shot(ctx, "lantern_charging_peak");
			ctx.waitTicks(8);
			shot(ctx, "lantern_charged_flash");
			ctx.waitTicks(LanternCharge.SETTLE + 4);
			shot(ctx, "lantern_settled");
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.getInput().releaseKey(o -> o.keyAttack);
			int charge = world.getServer().computeOnServer(server ->
					PowerRingItem.getCharge(player(server).getMainHandItem()));
			if (charge != PowerRingItem.MAX_CHARGE) {
				throw new AssertionError("Ring should be full after charging from the lantern, but has " + charge);
			}

			// The same at day, in third person, mid-charge (after the recharge cooldown).
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(25);
			setCharge(world, 100);
			ctx.getInput().holdKey(o -> o.keyAttack);
			ctx.waitTicks(1);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(LanternCharge.hold() + LanternCharge.REACH + 6);
			shot(ctx, "lantern_ring_in_day");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.waitTicks(2);
			shot(ctx, "lantern_charging_third_person");
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.getInput().releaseKey(o -> o.keyAttack);
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

			// A crouched tap changes mode with the lantern held (Beam -> Wall).
			ctx.waitTicks(20);
			ctx.getInput().holdKey(o -> o.keyShift);
			ctx.waitTicks(2);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(4);
			ctx.getInput().releaseKey(o -> o.keyShift);
			ctx.waitTicks(4);
			RingMode afterCrouchTap = world.getServer().computeOnServer(server -> PowerRingItem.getMode(player(server).getMainHandItem()));
			if (afterCrouchTap != RingMode.WALL) throw new AssertionError("A crouched tap should change mode to Wall, got " + afterCrouchTap);

			// Held modes work straight away with the lantern in the off hand: the Lasso holds, no charge starts.
			world.getServer().runOnServer(server -> player(server).getMainHandItem().set(ModComponents.MODE, RingMode.TETHER.ordinal()));
			setCharge(world, 500);
			ctx.waitTicks(30);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(LanternCharge.done() + 10);
			String lasso = world.getServer().computeOnServer(server -> {
				ServerPlayer p = player(server);
				return p.isUsingItem() + " " + LanternCharge.isCharging(p) + " " + PowerRingItem.getCharge(p.getMainHandItem());
			});
			ctx.getInput().releaseKey(o -> o.keyUse);
			System.out.println("[lantern-test] lasso hold: " + lasso);
			if (!lasso.startsWith("true false ") || lasso.endsWith(" 500") || lasso.endsWith(" 1000")) {
				throw new AssertionError("The Lasso should hold (and pay) with the lantern in the off hand, not charge: " + lasso);
			}

			// In Lasso mode the double-click gathers a group, so it never sets the lantern down.
			ctx.getInput().lookAt(0f, 55f);
			ctx.waitTicks(30);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(2);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(RingTuning.LANTERN_PLACE_HOLD.ticks() + 6);
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.waitTicks(4);
			if (batteriesNear(world) != 0) throw new AssertionError("A double-click in Lasso mode shouldn't set the lantern down");

			// One click doesn't set the lantern down; a double-click and hold does.
			world.getServer().runOnServer(server -> player(server).getMainHandItem().set(ModComponents.MODE, RingMode.BEAM.ordinal()));
			ctx.waitTicks(30);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(RingTuning.LANTERN_PLACE_HOLD.ticks() + 10);
			if (batteriesNear(world) != 0) throw new AssertionError("A single click shouldn't set the lantern down");
			ctx.waitTicks(30);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(2);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(RingTuning.LANTERN_PLACE_HOLD.ticks() + 6);
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.waitTicks(4);
			shot(ctx, "lantern_set_down");
			if (batteriesNear(world) != 1) throw new AssertionError("Double-click and hold should set the lantern down");
			boolean offhandEmpty = world.getServer().computeOnServer(server -> player(server).getOffhandItem().isEmpty());
			if (!offhandEmpty) throw new AssertionError("The placed lantern should leave the off hand");

			// The lantern never stays in the main hand: it moves itself to the off hand.
			world.getServer().runCommand("item replace entity @a hotbar.1 with lanternring:power_battery");
			ctx.getInput().pressKey(o -> o.keyHotbarSlots[1]);
			ctx.waitTicks(10);
			String hands = world.getServer().computeOnServer(server ->
					player(server).getMainHandItem().getItem() + " / " + player(server).getOffhandItem().getItem());
			System.out.println("[lantern-test] after selecting the lantern: " + hands);
			if (!hands.endsWith("lanternring:power_battery")) throw new AssertionError("The lantern should move to the off hand: " + hands);
			ctx.getInput().pressKey(o -> o.keyHotbarSlots[0]);
			ctx.waitTicks(5);

			// Close-up of the ring on the fist without the lantern.
			world.getServer().runCommand("item replace entity @a weapon.offhand with minecraft:air");
			ctx.getInput().lookAt(0f, 40f);
			ctx.waitTicks(10);
			shot(ctx, "ring_crest_close_fp");
		}
	}

	private static void shot(ClientGameTestContext ctx, String name) {
		ctx.takeScreenshot(name);
		System.out.println("[lantern-test] " + name + ": " + LanternFirstPerson.debug + " | " + RingFirstPerson.debug);
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}

	private static int batteriesNear(TestSingleplayerContext world) {
		return world.getServer().computeOnServer(server -> {
			ServerPlayer p = player(server);
			int found = 0;
			for (BlockPos pos : BlockPos.betweenClosed(p.blockPosition().offset(-6, -3, -6), p.blockPosition().offset(6, 3, 6))) {
				if (p.level().getBlockState(pos).is(ModRegistry.POWER_BATTERY)) found++;
			}
			return found;
		});
	}

	private static void setCharge(TestSingleplayerContext world, int charge) {
		world.getServer().runOnServer(server -> PowerRingItem.setCharge(player(server).getMainHandItem(), charge));
	}
}
