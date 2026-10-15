package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.client.HitFx;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.level.block.Blocks;

/**
 * J's "glowing interference" (2026-10-15): green ring, underground, first person, punching a construct-brick wall
 * again and again as it shatters. The punch flare, the punch pixels and the shatter pixels must stay readable
 * without washing out the view.
 */
public class GlowInterferenceTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("effect give @a resistance infinite 255 true");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			BlockPos[] origin = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.GREEN.ring());
				BlockPos o = p.blockPosition().above(20);
				origin[0] = o;
				var level = p.level();
				// A dark stone cave, 9 wide, 6 high, 10 long.
				for (BlockPos pos : BlockPos.betweenClosed(o.offset(-7, -2, -4), o.offset(7, 8, 10))) {
					boolean inside = Math.abs(pos.getX() - o.getX()) <= 4 && pos.getY() >= o.getY() && pos.getY() <= o.getY() + 5
							&& pos.getZ() >= o.getZ() - 2 && pos.getZ() <= o.getZ() + 8;
					level.setBlock(pos, inside ? Blocks.AIR.defaultBlockState() : Blocks.STONE.defaultBlockState(), 2);
				}
				// A construct wall, 2 thick, 2 blocks ahead.
				for (BlockPos pos : BlockPos.betweenClosed(o.offset(-4, 0, 2), o.offset(4, 5, 3))) {
					level.setBlock(pos, Corps.GREEN.tint(ModRegistry.LIGHT_CONSTRUCT.defaultBlockState()), 3);
				}
				p.teleportTo(o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
			});
			ctx.getInput().lookAt(0f, 10f);
			ctx.waitTicks(20);
			ctx.takeScreenshot("glow_before");
			// Punching away at it as it breaks, like J.
			for (int i = 0; i < 5; i++) {
				ctx.getInput().pressKey(opt -> opt.keyAttack);
				ctx.waitTicks(i == 0 ? 2 : 4);
				if (i == 0) ctx.takeScreenshot("glow_punch_t2");
			}
			ctx.takeScreenshot("glow_punching");
			ctx.runOnClient(mc -> System.out.println("[glow] pixels flying while punching: " + HitFx.bits()));
			ctx.waitTicks(6);
			ctx.takeScreenshot("glow_after");
			ctx.runOnClient(mc -> System.out.println("[glow] pixels flying after: " + HitFx.bits()));

			// J's second shot: standing on a Bridge at dusk, the construct's light beams must not sweep across the view.
			world.getServer().runCommand("time set 12800");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos o = origin[0].above(40);
				var level = p.level();
				for (BlockPos pos : BlockPos.betweenClosed(o.offset(-1, -1, -2), o.offset(1, -1, 12))) {
					level.setBlock(pos, Corps.GREEN.tint(ModRegistry.LIGHT_CONSTRUCT.defaultBlockState()), 3);
				}
				p.teleportTo(o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
			});
			ctx.getInput().lookAt(0f, 25f);
			ctx.waitTicks(40);
			ctx.takeScreenshot("glow_bridge");
		}
	}
}
