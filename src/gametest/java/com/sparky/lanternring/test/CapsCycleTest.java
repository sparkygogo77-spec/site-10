package com.sparky.lanternring.test;

import com.mojang.blaze3d.platform.InputConstants;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;

/** Caps Lock steps the ring to its next mode and shows the wheel; holding Shift makes the ring and arm glow stronger. */
public class CapsCycleTest implements FabricClientGameTest {
	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}

	private static String mode(TestSingleplayerContext world) {
		return world.getServer().computeOnServer(server -> PowerRingItem.getMode(player(server).getMainHandItem()).toString());
	}

	private static void tap(ClientGameTestContext ctx, int key) {
		ctx.getInput().holdKey(key);
		ctx.waitTicks(2);
		ctx.getInput().releaseKey(key);
		ctx.waitTicks(4);
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("time set 18000");
			world.getServer().runOnServer(server -> player(server).setItemInHand(InteractionHand.MAIN_HAND, Corps.GREEN.ring()));
			ctx.waitTicks(40);
			String start = mode(world);
			tap(ctx, InputConstants.KEY_CAPSLOCK);
			String once = mode(world);
			boolean open = ctx.computeOnClient(mc -> mc.gui.screen() != null);
			ctx.takeScreenshot("caps_cycle_wheel");
			tap(ctx, InputConstants.KEY_CAPSLOCK);
			String twice = mode(world);
			System.out.println("[caps] start=" + start + " once=" + once + " twice=" + twice + " wheel open after release=" + open);
			if (start.equals(once) || once.equals(twice) || !open) throw new AssertionError("Caps Lock didn't step the mode with the wheel up");
			ctx.waitTicks(45);
			boolean closed = ctx.computeOnClient(mc -> mc.gui.screen() == null);
			System.out.println("[caps] wheel closed by itself=" + closed);
			if (!closed) throw new AssertionError("cycling wheel never closed by itself");

			ctx.takeScreenshot("primed_glow_off");
			ctx.getInput().holdKey(o -> o.keyShift);
			ctx.waitTicks(12);
			ctx.takeScreenshot("primed_glow_on");
			ctx.getInput().releaseKey(o -> o.keyShift);
			ctx.waitTicks(5);
		}
	}
}
