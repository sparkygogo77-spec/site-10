package com.sparky.lanternring.test;

import com.mojang.blaze3d.platform.InputConstants;
import com.sparky.lanternring.client.LabSettings;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;

/**
 * Omega beams: hold the key at a zombie behind a wall. The pair of lasers leaves the eyes on one
 * zigzagging route round the wall and burns the zombie to embers, then ash (it must be gone). Then
 * E2 smoulder at a bare wall: the eyes build up, and the pair burns one or two blocks out of it.
 * Then two long zigzag shots (pass 506: Z2, Z3) seen from the side.
 */
public class OmegaBeamsTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 18000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			world.getServer().runCommand("execute at @p run fill ~-16 ~ ~-16 ~16 ~14 ~16 air");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> {
				mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);
				LabSettings.get().omegaStart = LabSettings.OmegaStart.E1;
			});

			// A zombie 12 blocks out, behind a wall 3 high that the beams have to go round.
			world.getServer().runCommand("execute at @p run fill ~-3 ~ ~6 ~3 ~2 ~6 minecraft:stone");
			world.getServer().runCommand("execute at @p run summon minecraft:zombie ~ ~ ~12 {NoAI:1b,PersistenceRequired:1b}");
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(10);
			// The start from the front, to see the eyes; then from behind and to the side, to see the beams.
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.getInput().holdKey(InputConstants.KEY_Z);
			ctx.waitTicks(1);
			ctx.takeScreenshot("omega_e1_snap");
			ctx.waitTicks(2);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(-40f, 25f);
			ctx.waitTicks(4);
			ctx.takeScreenshot("omega_beams_flying");
			ctx.waitTicks(8);
			ctx.takeScreenshot("omega_beams_round_wall");
			ctx.waitTicks(10);
			ctx.takeScreenshot("omega_zombie_embers");
			ctx.waitTicks(30);
			ctx.getInput().releaseKey(InputConstants.KEY_Z);
			ctx.waitTicks(30);
			ctx.takeScreenshot("omega_zombie_ash");
			int zombies = count(world, EntityTypes.ZOMBIE);
			int wall = stone(world, 6);
			System.out.println("[omega test] zombies left " + zombies + ", wall blocks " + wall + " of 21");
			if (zombies != 0) throw new AssertionError("The beams should have burnt the zombie to ash");

			// E2 smoulder at a bare wall: the eyes build up, then each beam burns a block out of it.
			ctx.runOnClient(mc -> LabSettings.get().omegaStart = LabSettings.OmegaStart.E2);
			world.getServer().runCommand("execute at @p run fill ~-16 ~ ~-16 ~16 ~14 ~16 air");
			world.getServer().runCommand("execute at @p run fill ~-4 ~ ~8 ~4 ~4 ~8 minecraft:stone");
			ctx.waitTicks(5);
			int before = stone(world, 8);
			ctx.getInput().lookAt(0f, 0f);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.waitTicks(3);
			ctx.getInput().holdKey(InputConstants.KEY_Z);
			ctx.waitTicks(12);
			ctx.takeScreenshot("omega_e2_smoulder");
			ctx.waitTicks(10);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(-35f, 20f);
			for (int i = 0; i < 6; i++) {
				ctx.waitTicks(4);
				ctx.takeScreenshot("omega_wall_embers_" + i);
			}
			ctx.getInput().releaseKey(InputConstants.KEY_Z);
			ctx.waitTicks(30);
			ctx.takeScreenshot("omega_wall_burnt");
			int after = stone(world, 8);
			System.out.println("[omega test] wall " + before + " -> " + after);
			if (before - after < 1 || before - after > 2) throw new AssertionError("The pair should burn one or two blocks: " + before + " -> " + after);

			// Pass 506: the lightning zigzag on a long shot, Z2 (J's pick) then Z3's wilder route, seen from the side.
			for (LabSettings.OmegaZig zig : new LabSettings.OmegaZig[] {LabSettings.OmegaZig.Z2, LabSettings.OmegaZig.Z3}) {
				ctx.runOnClient(mc -> {
					LabSettings.get().omegaStart = LabSettings.OmegaStart.E1;
					LabSettings.get().omegaZig = zig;
				});
				world.getServer().runCommand("execute at @p run fill ~-16 ~ ~-16 ~16 ~14 ~16 air");
				world.getServer().runCommand("execute at @p run fill ~-4 ~ ~16 ~4 ~4 ~16 minecraft:stone");
				ctx.getInput().lookAt(0f, 0f);
				ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
				ctx.waitTicks(5);
				ctx.getInput().holdKey(InputConstants.KEY_Z);
				ctx.waitTicks(4);
				ctx.getInput().lookAt(-70f, 15f);
				ctx.waitTicks(3);
				ctx.takeScreenshot("omega_zigzag_" + zig.name().toLowerCase() + "_a");
				ctx.waitTicks(4);
				ctx.takeScreenshot("omega_zigzag_" + zig.name().toLowerCase() + "_b");
				ctx.getInput().releaseKey(InputConstants.KEY_Z);
				ctx.waitTicks(30);
			}
		}
	}

	private static int count(TestSingleplayerContext world, EntityType<?> type) {
		int[] n = {0};
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			n[0] = p.level().getEntities(type, new AABB(p.blockPosition()).inflate(40), e -> true).size();
		});
		return n[0];
	}

	private static int stone(TestSingleplayerContext world, int z) {
		int[] n = {0};
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			BlockPos c = p.blockPosition();
			for (BlockPos pos : BlockPos.betweenClosed(c.offset(-5, 0, z), c.offset(5, 5, z))) {
				if (p.level().getBlockState(pos).is(Blocks.STONE)) n[0]++;
			}
		});
		return n[0];
	}
}
