package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.block.LanternStyle;
import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Crouch-placing lanterns: a red lantern with a green ring on (it used to refuse), and a green
 * lantern in the Ring Lab's Torus style, which must place as the Torus it shows in the hand.
 */
public class LanternPlaceTest implements FabricClientGameTest {
	private static void place(ClientGameTestContext ctx, TestSingleplayerContext world, String lantern, LabSettings.LanternModel model,
			String expectCorps, String expectStyle) {
		world.getServer().runCommand("setblock ~ ~ ~ air");
		world.getServer().runCommand("execute at @p run fill ~-3 ~ ~-3 ~3 ~2 ~3 air");
		world.getServer().runCommand("item replace entity @a weapon.offhand with " + lantern);
		LabSettings.get().lanternModel = model;
		ctx.waitTicks(5);
		ctx.getInput().holdKey(o -> o.keyShift);
		ctx.waitTicks(3);
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(RingTuning.LANTERN_PLACE_HOLD.ticks() + 10);
		ctx.getInput().releaseKey(o -> o.keyUse);
		ctx.getInput().releaseKey(o -> o.keyShift);
		ctx.waitTicks(10);
		world.getServer().runOnServer(server -> {
			var player = server.getPlayerList().getPlayers().get(0);
			BlockState found = null;
			for (BlockPos p : BlockPos.betweenClosed(player.blockPosition().offset(-3, -1, -3), player.blockPosition().offset(3, 2, 3))) {
				BlockState s = player.level().getBlockState(p);
				if (s.is(ModRegistry.POWER_BATTERY)) found = s;
			}
			if (found == null) throw new AssertionError("no lantern placed for " + lantern);
			String got = found.getValue(Corps.PROPERTY).getSerializedName() + "/" + found.getValue(LanternStyle.PROPERTY).getSerializedName();
			System.out.println("[place] " + lantern + " -> " + got);
			if (!got.equals(expectCorps + "/" + expectStyle)) throw new AssertionError("placed " + got + ", expected " + expectCorps + "/" + expectStyle);
		});
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			world.getServer().runCommand("execute at @p run tp @p ~ ~ ~ 0 0");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 60f);
			place(ctx, world, "lanternring:power_battery[block_state={corps:\"red\"}]", LabSettings.LanternModel.CLASSIC, "red", "classic");
			ctx.getInput().lookAt(0f, 35f);
			ctx.waitTicks(5);
			ctx.takeScreenshot("lantern_place_red");
			ctx.getInput().lookAt(0f, 60f);
			place(ctx, world, "lanternring:power_battery", LabSettings.LanternModel.TORUS, "green", "torus");
			ctx.getInput().lookAt(0f, 35f);
			ctx.waitTicks(5);
			ctx.takeScreenshot("lantern_place_torus");
		}
	}
}
