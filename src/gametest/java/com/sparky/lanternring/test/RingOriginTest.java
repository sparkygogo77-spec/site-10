package com.sparky.lanternring.test;

import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.Blocks;

/**
 * Powers leave the ring: the first few ticks of the Beam, Blast and Wall in first person at a high
 * field of view and in third person (from the front, so the ring arm faces the camera), plus the Dome's feed and the Anvil's aim thread.
 */
public class RingOriginTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 13500");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(60);
			target(world);
			ctx.runOnClient(mc -> mc.options.fov().set(110));
			ctx.getInput().lookAt(0f, 5f);

			for (CameraType camera : new CameraType[] {CameraType.FIRST_PERSON, CameraType.THIRD_PERSON_FRONT}) {
				String view = camera == CameraType.FIRST_PERSON ? "fp" : "tp";
				ctx.runOnClient(mc -> mc.options.setCameraType(camera));
				shot(ctx, world, RingMode.BEAM, view + "_beam");
				shot(ctx, world, RingMode.BLAST, view + "_blast");
				target(world);
				shot(ctx, world, RingMode.WALL, view + "_wall");
				world.getServer().runCommand("execute at @p run fill ~-6 ~ ~1 ~6 ~9 ~6 air");
			}

			// Held: the Dome fed from the ring, the Anvil's thread to its marker.
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			mode(ctx, world, RingMode.DOME);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(12);
			ctx.takeScreenshot("tp_dome_held");
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.waitTicks(20);
			mode(ctx, world, RingMode.ANVIL);
			ctx.getInput().lookAt(0f, 30f);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(10);
			ctx.takeScreenshot("tp_anvil_aim");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.waitTicks(4);
			ctx.takeScreenshot("fp_anvil_aim");
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.waitTicks(40);
		}
	}

	private static void mode(ClientGameTestContext ctx, TestSingleplayerContext world, RingMode mode) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			p.getMainHandItem().set(ModComponents.MODE, mode.ordinal());
		});
		ctx.waitTicks(10);
	}

	/** Taps the power and grabs the first ticks as it leaves the ring. */
	private static void shot(ClientGameTestContext ctx, TestSingleplayerContext world, RingMode mode, String name) {
		mode(ctx, world, mode);
		ctx.waitTicks(20);
		ctx.getInput().pressKey(o -> o.keyUse);
		for (int i = 1; i <= 4; i++) {
			ctx.waitTicks(1);
			ctx.takeScreenshot(name + "_" + i);
		}
		ctx.waitTicks(30);
	}

	/** A stone wall 12 blocks ahead to hit. */
	private static void target(TestSingleplayerContext world) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			var feet = p.blockPosition();
			for (int x = -8; x <= 8; x++)
				for (int y = 0; y < 8; y++)
					p.level().setBlock(feet.offset(x, y, 12), Blocks.STONE.defaultBlockState(), 2);
		});
	}
}
