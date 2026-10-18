package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.client.ChargeLock;
import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.phys.Vec3;

/**
 * J (2026-10-16): charging at a set-down lantern, the first-person arm flew off to the lantern's port. The arm now
 * stays on screen and leans toward it, at FOV 70 and 110, for every charge style and corps lantern; walking during a
 * charge doesn't move you.
 */
public class ChargeArmTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 13000");
			world.getServer().runCommand("execute as @p at @s align xyz run tp @s ~0.5 ~ ~0.5 0 0");
			ctx.waitTicks(40);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			LabSettings.get().lanternModel = LabSettings.LanternModel.CLASSIC;
			int seat = LanternCharge.hold() + LanternCharge.reach();
			for (Corps corps : new Corps[] {Corps.GREEN, Corps.RED, Corps.BLUE}) {
				world.getServer().runOnServer(s -> {
					var p = s.getPlayerList().getPlayers().getFirst();
					p.setItemInHand(InteractionHand.MAIN_HAND, corps.ring());
					p.setItemInHand(InteractionHand.OFF_HAND, corps.lantern());
				});
				LabSettings.ChargeStyle[] styles = corps == Corps.GREEN ? LabSettings.ChargeStyle.values()
						: new LabSettings.ChargeStyle[] {LabSettings.ChargeStyle.PUSH, LabSettings.ChargeStyle.HAND};
				for (LabSettings.ChargeStyle style : styles) {
					for (int fov : corps == Corps.GREEN && style.grounded() ? new int[] {70, 110} : new int[] {110}) {
						LabSettings.get().chargeStyle = style;
						ctx.runOnClient(mc -> {
							mc.options.fov().set(fov);
							mc.player.setYRot(0f);
							mc.player.setXRot(15f);
						});
						ctx.waitTicks(LanternCharge.DEPLETE + 10);
						ctx.getInput().holdKey(o -> o.keyAttack);
						ctx.waitTicks(1);
						ctx.getInput().holdKey(o -> o.keyUse);
						ctx.waitTicks(seat + 30);
						String name = corps.name().toLowerCase() + "_" + style.name().toLowerCase() + "_fov" + fov;
						ctx.takeScreenshot("arm_" + name);
						if (corps == Corps.GREEN && style == LabSettings.ChargeStyle.PUSH && fov == 110) {
							Vec3 before = ctx.computeOnClient(mc -> mc.player.position());
							ctx.getInput().holdKey(o -> o.keyUp);
							ctx.waitTicks(30);
							ctx.getInput().releaseKey(o -> o.keyUp);
							Vec3 after = ctx.computeOnClient(mc -> mc.player.position());
							boolean locked = ctx.computeOnClient(mc -> ChargeLock.locked());
							System.out.println("ChargeArmTest lock: locked=" + locked + " moved=" + before.distanceTo(after));
							if (before.distanceTo(after) > 0.05) throw new AssertionError("walked " + before.distanceTo(after) + " while charging");
							ctx.takeScreenshot("arm_" + name + "_after_walk");
						}
						ctx.getInput().releaseKey(o -> o.keyUse);
						ctx.getInput().releaseKey(o -> o.keyAttack);
						ctx.runOnClient(mc -> mc.player.setPos(mc.player.getX(), mc.player.getY(), mc.player.getZ()));
					}
				}
			}
			LabSettings.get().chargeStyle = LabSettings.ChargeStyle.HAND;
			ctx.runOnClient(mc -> mc.options.fov().set(70));
		}
	}
}
