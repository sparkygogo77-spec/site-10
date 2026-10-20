package com.sparky.lanternring.test;

import com.sparky.lanternring.warren.WarrenEntrance;
import com.sparky.lanternring.warren.WarrenSites;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.structures.MineshaftPieces;
import net.minecraft.world.level.levelgen.structure.structures.MineshaftStructure;

/**
 * Pass v2.0114 · Warren mineshaft entrance: an ordinary vanilla corridor in a block of stone with ours on its dead end
 * (W1a7c: inside, where it becomes ours), then down the round tunnel, the first cave, and a cutaway of the whole thing
 * (W1a7a). Also places a real mineshaft with every dead end allowed, to check the worldgen hook adds pieces.
 */
public class WarrenEntranceTest implements FabricClientGameTest {
	private static final int BASE = 20;

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode spectator @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("effect give @a night_vision infinite 0 true");
			ctx.waitTicks(40);
			BlockPos[] start = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				ServerLevel level = p.level();
				BlockState stone = Blocks.STONE.defaultBlockState();
				BlockPos.MutableBlockPos m = new BlockPos.MutableBlockPos();
				for (int x = -13; x <= 13; x++)
					for (int z = -6; z <= 72; z++)
						for (int y = BASE - 24; y <= BASE + 8; y++) level.setBlock(m.set(x, y, z), stone, 2);
				// An ordinary corridor heading south, three 5-block sections, ending in a dead end at z = 14.
				MineshaftPieces.MineShaftCorridor corridor = new MineshaftPieces.MineShaftCorridor(0, RandomSource.create(7),
						new BoundingBox(-1, BASE, 0, 1, BASE + 2, 14), Direction.SOUTH, MineshaftStructure.Type.NORMAL);
				start[0] = WarrenEntrance.startPast(corridor.getBoundingBox(), Direction.SOUTH);
				WarrenEntrance ours = new WarrenEntrance(start[0], Direction.SOUTH, 2, 20261020L);
				for (StructurePiece piece : new StructurePiece[] {corridor, ours}) {
					BoundingBox b = piece.getBoundingBox();
					piece.postProcess(level, level.structureManager(), level.getChunkSource().getGenerator(), RandomSource.create(1),
							b.inflatedBy(4), new net.minecraft.world.level.ChunkPos(start[0].getX() >> 4, start[0].getZ() >> 4), start[0]);
				}
				System.out.println("[WarrenEntranceTest] ours " + ours.getBoundingBox() + " block 3 past the end "
						+ level.getBlockState(start[0].offset(0, 2, 2)) + ", tunnel lining "
						+ level.getBlockState(start[0].offset(2, 0, 14)));
				p.teleportTo(0.5, BASE, 9.5);
			});
			// 1: in the mine, looking along it at the dead end that carries on.
			ctx.getInput().lookAt(0f, 8f);
			ctx.waitTicks(60);
			ctx.takeScreenshot("warren_entrance_1_mine");
			// 2: past the dark frames, down the round tunnel.
			world.getServer().runOnServer(server -> server.getPlayerList().getPlayers().get(0)
					.teleportTo(start[0].getX() + 0.5, start[0].getY(), start[0].getZ() + 7.5));
			ctx.getInput().lookAt(0f, 28f);
			ctx.waitTicks(40);
			ctx.takeScreenshot("warren_entrance_2_tunnel");
			// 3: in the first cave, looking back up at the tunnel's mouth.
			world.getServer().runOnServer(server -> server.getPlayerList().getPlayers().get(0)
					.teleportTo(start[0].getX() + 0.5, start[0].getY() - 9, start[0].getZ() + 34.5));
			ctx.getInput().lookAt(180f, -10f);
			ctx.waitTicks(40);
			ctx.takeScreenshot("warren_entrance_3_cave");
			// 4: cut away the east half and look at the whole thing from the side (W1a7a).
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				ServerLevel level = p.level();
				BlockPos.MutableBlockPos m = new BlockPos.MutableBlockPos();
				for (int x = 1; x <= 13; x++)
					for (int z = -6; z <= 72; z++)
						for (int y = BASE - 24; y <= BASE + 8; y++) level.setBlock(m.set(x, y, z), Blocks.AIR.defaultBlockState(), 2);
				p.teleportTo(38.5, BASE - 6, 26.5);
			});
			ctx.getInput().lookAt(90f, 4f);
			ctx.waitTicks(60);
			ctx.takeScreenshot("warren_entrance_4_cutaway");
			// The worldgen hook's choice: a mine with a dead end and a corridor that carries on into another piece.
			world.getServer().runOnServer(server -> {
				net.minecraft.world.level.levelgen.structure.pieces.StructurePiecesBuilder builder =
						new net.minecraft.world.level.levelgen.structure.pieces.StructurePiecesBuilder();
				builder.addPiece(new MineshaftPieces.MineShaftCorridor(0, RandomSource.create(3),
						new BoundingBox(1000, 0, 0, 1002, 2, 14), Direction.SOUTH, MineshaftStructure.Type.NORMAL));
				builder.addPiece(new MineshaftPieces.MineShaftCorridor(0, RandomSource.create(4),
						new BoundingBox(2000, 0, 0, 2002, 2, 14), Direction.SOUTH, MineshaftStructure.Type.NORMAL));
				builder.addPiece(new MineshaftPieces.MineShaftCorridor(1, RandomSource.create(5),
						new BoundingBox(1995, 0, 15, 2009, 2, 17), Direction.EAST, MineshaftStructure.Type.NORMAL));
				int before = WarrenEntrance.MADE.size();
				WarrenSites.everywhereForTests = true;
				WarrenEntrance.attach(builder, 1L, net.minecraft.world.level.LevelHeightAccessor.create(-64, 384));
				WarrenSites.everywhereForTests = false;
				System.out.println("[WarrenEntranceTest] hook made " + WarrenEntrance.MADE.subList(before, WarrenEntrance.MADE.size())
						+ " (want x=1001 z=15 and the east corridor's end x=2010, not x=2001)");
			});
		}
	}
}
