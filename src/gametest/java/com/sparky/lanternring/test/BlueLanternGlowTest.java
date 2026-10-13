package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.client.LabSettings;
import com.sparky.lanternring.client.LanternGlare;
import com.sparky.lanternring.item.PowerRingItem;
import java.lang.reflect.Method;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;

/**
 * The Blue Lantern's light: blinding at the climax of a charge, then winding quickly back down
 * (RingTuning.LANTERN_SETTLE) to a calm blue resting glow where the emblem on its lens shows.
 */
public class BlueLanternGlowTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 18000");
			world.getServer().runOnServer(server -> {
				player(server).setItemInHand(InteractionHand.MAIN_HAND, Corps.BLUE.ring());
				player(server).setItemInHand(InteractionHand.OFF_HAND, Corps.BLUE.lantern());
			});
			ctx.waitTicks(40);
			LabSettings.get().chargeStyle = LabSettings.ChargeStyle.FLOAT;
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 10f);
			ctx.waitTicks(10);
			world.getServer().runOnServer(server -> PowerRingItem.setCharge(player(server).getMainHandItem(), 10));
			ctx.takeScreenshot("blue_glow_rest_before");

			ctx.getInput().holdKey(o -> o.keyAttack);
			ctx.waitTicks(1);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(LanternCharge.done() + 2);
			ctx.takeScreenshot("blue_glow_flash");
			float peak = light(ctx);
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.getInput().releaseKey(o -> o.keyAttack);
			int settle = RingTuning.LANTERN_SETTLE.ticks();
			ctx.waitTicks(4 + settle / 2);
			ctx.takeScreenshot("blue_glow_winding_down");
			ctx.waitTicks(settle / 2 + 4);
			float rested = light(ctx);
			ctx.takeScreenshot("blue_glow_rested");
			System.out.println("[blue-glow-test] peak=" + peak + " rested=" + rested + " settle=" + settle);
			if (peak < 3f) throw new AssertionError("The lantern should blaze at the climax, got " + peak);
			if (rested > 0.7f) throw new AssertionError("The lantern should be back to its resting glow " + settle + " ticks after the flash, got " + rested);
		}
	}

	/** The lantern's light right now (LanternGlare.light; -1 means its plain idle glow). */
	private static float light(ClientGameTestContext ctx) {
		return ctx.computeOnClient(mc -> {
			try {
				Method m = LanternGlare.class.getDeclaredMethod("light", float.class);
				m.setAccessible(true);
				return (Float) m.invoke(null, 0f);
			} catch (ReflectiveOperationException e) {
				throw new RuntimeException(e);
			}
		});
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
