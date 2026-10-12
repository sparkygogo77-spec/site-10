package com.sparky.lanternring.test;

import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingTuning;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.Blocks;

/**
 * A Bridge built across a lava pool: when it fades, the lava it stood in comes back (it used to
 * leave a trench of air, since lava doesn't flow back by itself).
 */
public class ConstructRestoreTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(40);
			// Hover over a lava pool: the bridge goes in at foot level - 1, the top layer of lava.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.getAbilities().flying = true;
				p.onUpdateAbilities();
				p.teleportTo(p.getX(), p.getY() + 3, p.getZ());
				p.getMainHandItem().set(ModComponents.MODE, RingMode.BRIDGE.ordinal());
			});
			ctx.waitTicks(5);
			world.getServer().runCommand("execute at @p run fill ~-4 ~-3 ~-2 ~4 ~-1 ~16 lava");
			RingTuning.CONSTRUCT_LIFETIME.set(3);
			RingTuning.DISMISS_TIME.set(0.5);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(0f, 30f);
			ctx.waitTicks(10);
			int before = lava(world);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(10);
			ctx.takeScreenshot("restore_bridge_over_lava");
			int during = lava(world);
			ctx.waitTicks(120);
			ctx.takeScreenshot("restore_bridge_gone");
			int after = lava(world);
			RingTuning.resetAll();
			if (during >= before) throw new AssertionError("The bridge wasn't built over the lava (" + before + " -> " + during + ")");
			if (after != before) throw new AssertionError("Lava under the bridge didn't come back: " + before + " sources before, " + after + " after");
		}
	}

	/** Lava sources in the pool's top layer. */
	private static int lava(TestSingleplayerContext world) {
		return world.getServer().computeOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			BlockPos feet = p.blockPosition();
			int n = 0;
			for (BlockPos pos : BlockPos.betweenClosed(feet.offset(-4, -1, -2), feet.offset(4, -1, 16))) {
				if (p.level().getBlockState(pos).is(Blocks.LAVA) && p.level().getFluidState(pos).isSource()) n++;
			}
			return n;
		});
	}
}
