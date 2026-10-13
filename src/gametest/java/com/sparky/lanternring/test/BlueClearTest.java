package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.corps.BlueSquad;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** Once the rescue spot is quiet, the squad lifts the lumpy ground round it out on hard-light platforms. */
public class BlueClearTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode spectator @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			BlockPos[] lantern = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos b = p.blockPosition().above(6);
				for (BlockPos pos : BlockPos.betweenClosed(b.offset(-40, -3, -40), b.offset(40, 30, 40))) {
					p.level().setBlock(pos, pos.getY() < b.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				// Lumpy ground: little mounds of earth and stone all round.
				for (int x = -26; x <= 26; x += 4) {
					for (int z = -26; z <= 26; z += 4) {
						if (Math.abs(x) <= 3 && Math.abs(z) <= 3) continue;
						BlockState s = (x + z) % 8 == 0 ? Blocks.STONE.defaultBlockState() : Blocks.DIRT.defaultBlockState();
						for (int y = 0; y < 1 + Math.floorMod(x * 7 + z * 3, 2); y++) p.level().setBlock(b.offset(x, y, z), s, 2);
					}
				}
				lantern[0] = b.immutable();
				p.level().setBlock(b, ModRegistry.POWER_BATTERY.defaultBlockState().setValue(Corps.PROPERTY, Corps.BLUE), 3);
				p.teleportTo(b.getX() - 6.5, b.getY() + 22, b.getZ() + 0.5);
			});
			ctx.getInput().lookAt(-90f, 55f);
			world.getServer().runOnServer(server -> BlueSquad.callOut(server.getPlayerList().getPlayers().get(0).level(), lantern[0]));
			ctx.waitTicks(300);
			ctx.takeScreenshot("blue_clear_before");
			for (int i = 0; i < 10; i++) {
				ctx.waitTicks(30);
				ctx.takeScreenshot("blue_clear_" + i);
			}
			ctx.waitTicks(600);
			world.getServer().runOnServer(server -> {
				ServerLevel level = server.getPlayerList().getPlayers().get(0).level();
				int mounds = 0;
				for (BlockPos pos : BlockPos.betweenClosed(lantern[0].offset(-30, 0, -30), lantern[0].offset(30, 2, 30))) {
					BlockState s = level.getBlockState(pos);
					if (s.is(Blocks.DIRT) || s.is(Blocks.STONE)) mounds++;
				}
				int stored = 0;
				if (level.getBlockEntity(lantern[0].relative(Direction.EAST, 2)) instanceof ChestBlockEntity c) {
					for (int i = 0; i < c.getContainerSize(); i++) stored += c.getItem(i).getCount();
				}
				System.out.println("[BlueClearTest] mound blocks left " + mounds + ", in the chest " + stored);
			});
			ctx.takeScreenshot("blue_clear_after");
		}
	}
}
