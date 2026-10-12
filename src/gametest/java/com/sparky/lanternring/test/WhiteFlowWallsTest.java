package com.sparky.lanternring.test;

import com.sparky.lanternring.HeldConstructs;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

/**
 * The White Constructs pack: six Wall-mode walls built edge to edge (three across, two high), so
 * the flowing smoke must run across every block seam without a break. Shots from afar, up close on
 * a seam, a moment later (the smoke has moved), and at night.
 */
public class WhiteFlowWallsTest implements FabricClientGameTest {
	private static final String PACK = "lanternring:constructs_white_flow";

	@Override
	public void runTest(ClientGameTestContext ctx) {
		ctx.runOnClient(mc -> {
			var repo = mc.getResourcePackRepository();
			if (!repo.getAvailableIds().contains(PACK)) {
				throw new AssertionError("pack " + PACK + " missing; have " + repo.getAvailableIds());
			}
			List<String> on = new ArrayList<>(repo.getSelectedIds());
			on.add(PACK);
			repo.setSelected(on);
			mc.reloadResourcePacks();
		});
		ctx.waitTicks(120);
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			Vec3[] eye = new Vec3[2];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.getAbilities().flying = true;
				BlockPos b = p.blockPosition().above(4);
				for (BlockPos pos : BlockPos.betweenClosed(b.offset(-30, -3, -30), b.offset(30, 30, 30))) {
					p.level().setBlock(pos, pos.getY() < b.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				// Walls go up WALL_DISTANCE in front, 9 wide and 9 tall: stand at three spots 9 apart,
				// on the ground and 9 up, facing south, and put one up at each.
				for (int row = 0; row < 2; row++) {
					for (int col = -1; col <= 1; col++) {
						p.snapTo(b.getX() + 0.5 + col * 9, b.getY() + row * 9, b.getZ() + 0.5, 0f, 0f);
						HeldConstructs.placeWall(p.level(), p);
					}
				}
				eye[0] = new Vec3(b.getX() + 0.5, b.getY() + 7.5, b.getZ() - 17.5);
				// Up close on a seam where four walls meet (x between walls, y = 9).
				eye[1] = new Vec3(b.getX() + 5.0, b.getY() + 7.4, b.getZ() - 1.5);
				p.teleportTo(eye[0].x, eye[0].y, eye[0].z);
			});
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(30);
			ctx.takeScreenshot("white_flow_walls_day");
			ctx.waitTicks(60);
			ctx.takeScreenshot("white_flow_walls_day_later");
			world.getServer().runOnServer(server -> server.getPlayerList().getPlayers().get(0)
					.teleportTo(eye[1].x, eye[1].y, eye[1].z));
			ctx.getInput().lookAt(0f, -8f);
			ctx.waitTicks(20);
			ctx.takeScreenshot("white_flow_walls_seam");
			world.getServer().runOnServer(server -> server.getPlayerList().getPlayers().get(0)
					.teleportTo(eye[0].x, eye[0].y, eye[0].z));
			ctx.getInput().lookAt(0f, 0f);
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(20);
			ctx.takeScreenshot("white_flow_walls_night");
		}
	}
}
