package com.sparky.lanternring.test;

import com.mojang.blaze3d.platform.InputConstants;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternSlot;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingTuning;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;

/**
 * The Red Lantern's self-destruct: summon the red lantern (R), hold R, and after the rage builds you
 * die and every lantern within 15 blocks is gone, while one further off survives.
 */
public class RedSelfDestructTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doImmediateRespawn false");
			world.getServer().runCommand("time set 6000");
			BlockPos[] spots = world.getServer().computeOnServer(server -> {
				ServerPlayer p = player(server);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.RED.ring());
				p.setItemInHand(InteractionHand.OFF_HAND, Corps.RED.lantern());
				BlockPos at = p.blockPosition();
				BlockPos near1 = at.offset(4, 0, 6), near2 = at.offset(-8, 0, 3), far = at.offset(20, 0, 0);
				for (BlockPos b : new BlockPos[] {near1, near2, far}) p.level().setBlock(b, ModRegistry.POWER_BATTERY.defaultBlockState(), 3);
				return new BlockPos[] {near1, near2, far};
			});
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(30f, 15f);
			ctx.getInput().pressKey(InputConstants.KEY_R);
			ctx.waitTicks(25);
			shot(ctx, "red_lantern_summoned");
			ctx.getInput().holdKey(InputConstants.KEY_R);
			ctx.waitTicks(14);
			ctx.getInput().releaseKey(InputConstants.KEY_R);
			ctx.waitTicks(RingTuning.RED_SELF_DESTRUCT.ticks() / 2);
			shot(ctx, "red_self_destruct_building");
			ctx.waitTicks(RingTuning.RED_SELF_DESTRUCT.ticks() / 2 + 2);
			shot(ctx, "red_self_destruct_burst");
			ctx.waitTicks(20);
			shot(ctx, "red_self_destruct_dead");

			boolean[] r = world.getServer().computeOnServer(server -> {
				ServerPlayer p = player(server);
				var level = p.level();
				return new boolean[] {
						p.isDeadOrDying(),
						level.getBlockState(spots[0]).is(ModRegistry.POWER_BATTERY) || level.getBlockState(spots[1]).is(ModRegistry.POWER_BATTERY),
						level.getBlockState(spots[2]).is(ModRegistry.POWER_BATTERY),
						LanternSlot.lantern(p).isEmpty()};
			});
			System.out.println("[red-self-destruct-test] dead=" + r[0] + " nearLeft=" + r[1] + " farLeft=" + r[2] + " slotEmpty=" + r[3]);
			if (!r[0]) throw new AssertionError("The self-destruct should kill its bearer");
			if (r[1]) throw new AssertionError("Lanterns within 15 blocks should be destroyed");
			if (!r[2]) throw new AssertionError("A lantern 20 blocks away should survive");
			if (!r[3]) throw new AssertionError("The bearer's own lantern should be gone");
		}
	}

	private static void shot(ClientGameTestContext ctx, String name) {
		ctx.takeScreenshot(name);
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
