package com.sparky.lanternring.test;

import com.mojang.blaze3d.platform.InputConstants;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;

/** The mode wheel: hold R with a ring, point at a mode, let go, and the ring switches to it. */
public class ModeWheelTest implements FabricClientGameTest {
	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}

	private void pick(ClientGameTestContext ctx, TestSingleplayerContext world, Corps corps, double dx, double dy, String name) {
		world.getServer().runOnServer(server -> player(server).setItemInHand(InteractionHand.MAIN_HAND, corps.ring()));
		ctx.waitTicks(5);
		ctx.getInput().holdKey(InputConstants.KEY_G);
		ctx.waitTicks(5);
		double[] size = ctx.computeOnClient(mc -> new double[] {mc.getWindow().getScreenWidth(), mc.getWindow().getScreenHeight()});
		ctx.getInput().setCursorPos(size[0] / 2 + dx * size[0], size[1] / 2 + dy * size[1]);
		ctx.waitTicks(3);
		ctx.takeScreenshot("mode_wheel_" + name);
		ctx.getInput().releaseKey(InputConstants.KEY_G);
		ctx.waitTicks(5);
		boolean open = ctx.computeOnClient(mc -> mc.gui.screen() != null);
		world.getServer().runOnServer(server -> System.out.println("[wheel] " + name + ": mode now "
				+ PowerRingItem.getMode(player(server).getMainHandItem()) + ", screen open=" + open));
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			pick(ctx, world, Corps.GREEN, 0.36, 0, "green_right");
			pick(ctx, world, Corps.GREEN, -0.2, 0.3, "green_lower_left");
			pick(ctx, world, Corps.RED, 0, 0.36, "red_bottom");
		}
	}
}
