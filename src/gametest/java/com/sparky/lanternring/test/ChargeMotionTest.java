package com.sparky.lanternring.test;

import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.client.LabSettings;
import com.sparky.lanternring.client.LanternFirstPerson;
import com.sparky.lanternring.client.RingFirstPerson;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;

/**
 * Photographs the lantern charge frame by frame in slow motion: the ring hand bending to show the
 * ring, lining up and being pulled onto the port, the hold, and the snap off at 100%; in first
 * person, then from the front and back in third person.
 */
public class ChargeMotionTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		double reachBefore = RingTuning.CHARGE_REACH.seconds();
		double timeBefore = RingTuning.CHARGE_TIME.seconds();
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			world.getServer().runCommand("item replace entity @a weapon.offhand with lanternring:power_battery");
			ctx.waitTicks(60);
			LabSettings.get().chargeStyle = LabSettings.ChargeStyle.HAND;
			LabSettings.get().lanternModel = LabSettings.LanternModel.CLASSIC;
			RingFirstPerson.recordDebug = true;
			// Slow motion, so each frame lands on its moment.
			RingTuning.CHARGE_REACH.set(3);
			RingTuning.CHARGE_TIME.set(6);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			// J plays at Quake Pro, where the hands (always drawn at 70) look big next to the world.
			ctx.runOnClient(mc -> mc.options.fov().set(110));
			ctx.getInput().lookAt(0f, 15f);
			ctx.waitTicks(20);

			int hold = LanternCharge.hold();
			int reach = LanternCharge.reach();
			int done = LanternCharge.done();
			setCharge(world, 100);
			start(ctx);
			int[] frames = {hold, hold + reach / 5, hold + 2 * reach / 5, hold + 3 * reach / 5, hold + 4 * reach / 5,
					hold + reach - 3, hold + reach + 6, done - 3, done + 1, done + 4, done + 12};
			for (int i = 0; i < frames.length; i++) {
				waitHeld(ctx, frames[i]);
				shot(ctx, String.format("charge_motion_%02d", i));
			}
			stop(ctx);
			if (System.getenv("SWEEP") != null) {
				ctx.waitTicks(LanternCharge.DEPLETE + 20);
				setCharge(world, 100);
				start(ctx);
				waitHeld(ctx, hold + reach + 12);
				for (float roll : new float[] {-60f, -30f, 0f, 30f, 60f, 90f}) {
					RingFirstPerson.pressRoll = roll;
					ctx.waitTicks(1);
					shot(ctx, "charge_motion_roll_" + (int) roll);
				}
				RingFirstPerson.pressRoll = 90f;
				stop(ctx);
			}

			// Third person, ring on the port and on the way.
			ctx.waitTicks(LanternCharge.DEPLETE + 20);
			for (CameraType camera : new CameraType[] {CameraType.THIRD_PERSON_FRONT, CameraType.THIRD_PERSON_BACK}) {
				String side = camera == CameraType.THIRD_PERSON_FRONT ? "front" : "back";
				ctx.runOnClient(mc -> mc.options.setCameraType(camera));
				ctx.getInput().lookAt(0f, 5f);
				setCharge(world, 100);
				ctx.waitTicks(10);
				// Carried out in front, before charging.
				shot(ctx, "charge_motion_tp_" + side + "_carry");
				start(ctx);
				ctx.waitTicks(hold + reach * 2 / 5);
				shot(ctx, "charge_motion_tp_" + side + "_show");
				ctx.waitTicks(reach - reach * 2 / 5 + 4);
				shot(ctx, "charge_motion_tp_" + side + "_port");
				stop(ctx);
				ctx.waitTicks(LanternCharge.DEPLETE + 20);
			}
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));

			// Floating: no hand on the lantern; it swings back on its handle when the ring hits.
			LabSettings.get().chargeStyle = LabSettings.ChargeStyle.FLOAT;
			ctx.getInput().lookAt(0f, 15f);
			setCharge(world, 100);
			ctx.waitTicks(10);
			start(ctx);
			int contact = hold + reach;
			int[] swing = {contact - 2, contact + 2, contact + 5, contact + 9, contact + 16};
			for (int i = 0; i < swing.length; i++) {
				waitHeld(ctx, swing[i]);
				shot(ctx, String.format("charge_motion_float_%02d", i));
			}
			stop(ctx);
			ctx.waitTicks(LanternCharge.DEPLETE + 20);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.getInput().lookAt(0f, 5f);
			ctx.waitTicks(10);
			shot(ctx, "charge_motion_tp_float");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			LabSettings.get().chargeStyle = LabSettings.ChargeStyle.HAND;
		} finally {
			RingTuning.CHARGE_REACH.set(reachBefore);
			RingTuning.CHARGE_TIME.set(timeBefore);
		}
	}

	/** Waits until right-click has been held {@code ticks} ticks (screenshots let ticks go by, so count them). */
	private static void waitHeld(ClientGameTestContext ctx, int ticks) {
		for (int i = 0; i < 400; i++) {
			int held = ctx.computeOnClient(mc -> mc.player.isUsingItem() ? 72000 - mc.player.getUseItemRemainingTicks() : -1);
			if (held >= ticks) return;
			ctx.waitTicks(1);
		}
	}

	private static void start(ClientGameTestContext ctx) {
		ctx.getInput().holdKey(o -> o.keyAttack);
		ctx.waitTicks(1);
		ctx.getInput().holdKey(o -> o.keyUse);
	}

	private static void stop(ClientGameTestContext ctx) {
		ctx.getInput().releaseKey(o -> o.keyUse);
		ctx.getInput().releaseKey(o -> o.keyAttack);
	}

	private static void shot(ClientGameTestContext ctx, String name) {
		ctx.runOnClient(mc -> System.out.println("[charge-motion] " + name + " held=" + (mc.player.isUsingItem() ? 72000 - mc.player.getUseItemRemainingTicks() : -1)
				+ " | " + LanternFirstPerson.debug + " | " + RingFirstPerson.debug));
		ctx.takeScreenshot(name);
	}

	private static void setCharge(TestSingleplayerContext world, int charge) {
		world.getServer().runOnServer(server -> PowerRingItem.setCharge(server.getPlayerList().getPlayers().get(0).getMainHandItem(), charge));
	}
}
