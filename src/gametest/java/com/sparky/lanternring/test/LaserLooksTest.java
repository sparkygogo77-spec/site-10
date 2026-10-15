package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.client.LabFx;
import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.level.block.Blocks;

/**
 * J's eight pass 836 ring lasers (Ring Lab > Beams > Beam look): each fired by the Ring Lab preview and shot while it
 * holds, in first person and from the side, then H3 and C3 in yellow to check the corps colour.
 */
public class LaserLooksTest implements FabricClientGameTest {
	private static void fire(ClientGameTestContext ctx, LabSettings.BeamLook look) {
		ctx.runOnClient(mc -> {
			LabSettings.get().beamLook = look;
			LabFx.preview("beam");
		});
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 13000");
			ctx.waitTicks(60);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.GREEN.ring());
				BlockPos o = p.blockPosition().above(10);
				var level = p.level();
				for (BlockPos pos : BlockPos.betweenClosed(o.offset(-8, -2, -8), o.offset(8, 8, 20))) {
					level.setBlock(pos, pos.getY() < o.getY() ? Blocks.STONE.defaultBlockState()
							: pos.getZ() == o.getZ() + 16 ? Blocks.DEEPSLATE.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				p.teleportTo(o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
			});
			world.getServer().runCommand("kill @e[type=!player]");
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(20);
			for (LabSettings.BeamLook look : LabSettings.BeamLook.values()) {
				if (look == LabSettings.BeamLook.HELIX) continue;
				String name = look.name().toLowerCase(java.util.Locale.ROOT);
				ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
				ctx.waitTicks(2);
				fire(ctx, look);
				ctx.waitTicks(3);
				ctx.takeScreenshot("laser_" + name + "_fp");
				ctx.waitTicks(15);
				// From the side: fire ahead, then turn away so the beam runs across the view.
				fire(ctx, look);
				ctx.waitTicks(1);
				ctx.getInput().lookAt(-50f, 0f);
				ctx.waitTicks(2);
				ctx.takeScreenshot("laser_" + name + "_side");
				ctx.waitTicks(15);
				ctx.getInput().lookAt(0f, 0f);
			}
			world.getServer().runOnServer(server -> server.getPlayerList().getPlayers().get(0)
					.setItemInHand(InteractionHand.MAIN_HAND, Corps.YELLOW.ring()));
			ctx.waitTicks(10);
			for (LabSettings.BeamLook look : new LabSettings.BeamLook[] {LabSettings.BeamLook.H3_BRAID, LabSettings.BeamLook.C3_HEX_TUBE}) {
				fire(ctx, look);
				ctx.waitTicks(1);
				ctx.getInput().lookAt(-50f, 0f);
				ctx.waitTicks(2);
				ctx.takeScreenshot("laser_" + look.name().toLowerCase(java.util.Locale.ROOT) + "_yellow_side");
				ctx.waitTicks(15);
				ctx.getInput().lookAt(0f, 0f);
			}
			ctx.runOnClient(mc -> LabSettings.get().beamLook = LabSettings.BeamLook.HELIX);
		}
	}
}
