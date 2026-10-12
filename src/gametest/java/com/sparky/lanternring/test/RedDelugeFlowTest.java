package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.ModFluids;
import com.sparky.lanternring.RingMode;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.level.block.Blocks;

/**
 * The red Lava Deluge from start to finish on a grass field, a frame every few ticks: the pool
 * spreads, the waves roll out and thin away at their edge, fire only starts where the liquid has
 * been, and the pool drains without its sunk layer popping away at the end.
 */
public class RedDelugeFlowTest implements FabricClientGameTest {
	/** Fire found further from the burst than the liquid has ever reached is fire out of nowhere. */
	private static final int[] reach = {0};

	private static void report(TestSingleplayerContext world, BlockPos o, String when) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			var level = p.level();
			int ember = 0, fire = 0, below = 0, stray = 0;
			int far = 0;
			for (BlockPos pos : BlockPos.betweenClosed(o.offset(-30, -6, -6), o.offset(30, 12, 54))) {
				int d = (int) Math.ceil(Math.sqrt(Math.pow(pos.getX() - o.getX(), 2) + Math.pow(pos.getZ() - (o.getZ() + 24), 2)));
				var fluid = level.getFluidState(pos);
				if (fluid.getType() == ModFluids.EMBER_SOURCE || fluid.getType() == ModFluids.EMBER_FLOWING) {
					ember++;
					if (pos.getY() < o.getY()) below++;
					far = Math.max(far, d);
				}
				if (level.getBlockState(pos).is(Blocks.FIRE)) {
					fire++;
					if (d > reach[0] + 1) stray++;
				}
			}
			reach[0] = Math.max(reach[0], far);
			System.out.println("[redflow] " + when + ": ember=" + ember + " sunk=" + below + " reach=" + reach[0]
					+ " fire=" + fire + " strayFire=" + stray);
		});
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));

			BlockPos[] origin = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.RED.ring());
				BlockPos o = p.blockPosition().above(10);
				origin[0] = o;
				var level = p.level();
				for (int x = -30; x <= 30; x++)
					for (int y = -6; y <= 24; y++)
						for (int z = -6; z <= 54; z++) {
							level.setBlock(o.offset(x, y, z), y < -3 ? Blocks.STONE.defaultBlockState()
									: y < -1 ? Blocks.DIRT.defaultBlockState()
									: y == -1 ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
						}
				p.teleportTo(o.getX() + 0.5, o.getY() + 9, o.getZ() - 4.5);
				p.getAbilities().flying = true;
				p.onUpdateAbilities();
				p.getMainHandItem().set(ModComponents.MODE, RingMode.DELUGE.ordinal());
				p.getMainHandItem().set(ModComponents.DELUGE_LEVEL, 1);
			});
			// Aim at the field 24 blocks out.
			ctx.getInput().lookAt(0f, 20f);
			ctx.waitTicks(20);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(10);
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.getInput().lookAt(0f, 28f);
			for (int i = 0; i < 40; i++) {
				ctx.waitTicks(6);
				report(world, origin[0], "t" + (i * 6 + 6));
				if (i % 2 == 1 || i < 8) ctx.takeScreenshot("redflow_" + String.format("%02d", i));
			}
			ctx.waitTicks(40);
			report(world, origin[0], "end");
			ctx.takeScreenshot("redflow_end");
		}
	}
}
