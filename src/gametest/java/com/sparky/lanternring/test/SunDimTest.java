package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.client.SunDim;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.world.InteractionHand;

/**
 * The sun dims round a charging ring: photographs a sunny day before, during and after a charge,
 * and checks the dimming builds, holds while charging and goes once the charge ends. Also checks
 * the held ring hands a shader pack the dimming in its light colour.
 */
public class SunDimTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("weather clear");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			world.getServer().runCommand("item replace entity @a weapon.offhand with lanternring:power_battery");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(30f, 20f);
			ctx.waitTicks(60);
			setCharge(world, 100);
			ctx.takeScreenshot("sun_dim_before");

			ctx.getInput().holdKey(o -> o.keyAttack);
			ctx.waitTicks(1);
			ctx.getInput().holdKey(o -> o.keyUse);
			// Mid-charge the daylight is only draining; it plunges to black as the ring fills and flashes.
			int contact = LanternCharge.hold() + LanternCharge.reach();
			int mid = contact + (LanternCharge.done() - contact) / 2;
			ctx.waitTicks(mid);
			float half = ctx.computeOnClient(mc -> SunDim.level(0f));
			ctx.waitTicks(LanternCharge.done() - mid + 6);
			float full = ctx.computeOnClient(mc -> SunDim.level(0f));
			float keep = ctx.computeOnClient(mc -> SunDim.vanillaKeep(0f));
			ctx.takeScreenshot("sun_dim_charging");
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.getInput().releaseKey(o -> o.keyAttack);
			ctx.waitTicks(RingTuning.CHARGE_DIM_OUT.ticks() / 2);
			ctx.takeScreenshot("sun_dim_returning");
			// It stays black a moment after the burst before the light comes back.
			ctx.waitTicks(RingTuning.CHARGE_DIM_OUT.ticks() / 2 + 24);
			float after = ctx.computeOnClient(mc -> SunDim.level(0f));
			ctx.takeScreenshot("sun_dim_after");
			System.out.println("[sun-dim-test] half " + half + " full " + full + " keep " + keep + " after " + after);
			if (half < 0.15f || half > 0.8f) throw new AssertionError("The sun should only be draining halfway through the charge, but was " + half);
			if (full < 0.99f) throw new AssertionError("The sun should go black as the ring fills, but was " + full);
			if (keep > 1f - SunDim.MAX + 0.01f) throw new AssertionError("Sky light should drop while charging, kept " + keep);
			if (after > 0.01f) throw new AssertionError("The sun should come back once the charge ends, but was still " + after);

			// The patched shader pack reads the dimming from the held ring's light colour length.
			java.util.function.DoubleSupplier old = PowerRingItem.shaderSunDim;
			try {
				PowerRingItem.shaderSunDim = () -> 0.5;
				float len = ctx.computeOnClient(mc -> {
					PowerRingItem ring = (PowerRingItem) Corps.GREEN.ring().getItem();
					return ring.getLightColor(mc.player, mc.player.getItemInHand(InteractionHand.MAIN_HAND)).length();
				});
				if (Math.abs(len - 11f) > 0.01f) throw new AssertionError("Half dimmed should be a light colour 11 long, got " + len);
			} finally {
				PowerRingItem.shaderSunDim = old;
			}
		}
	}

	private static void setCharge(TestSingleplayerContext world, int charge) {
		world.getServer().runOnServer(server -> PowerRingItem.setCharge(server.getPlayerList().getPlayers().get(0).getMainHandItem(), charge));
	}
}
