package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.ModEffects;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.ally.DreadRunner;
import com.sparky.lanternring.client.FearBlind;
import com.sparky.lanternring.corps.DreadTrails;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;

/**
 * The Yellow ring's Blast level 4, the Dread Runner: it sprints south into a stone wall, breaking
 * a tunnel, and leaves fear on the ground; the player then walks into the fear and is blinded.
 */
public class DreadRunnerTest implements FabricClientGameTest {
	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			BlockPos[] origin = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = player(server);
				var ring = Corps.YELLOW.ring();
				ring.set(ModComponents.MODE, RingMode.BLAST.ordinal());
				ring.set(ModComponents.BLAST_LEVEL, 4);
				p.setItemInHand(InteractionHand.MAIN_HAND, ring);
				BlockPos o = p.blockPosition();
				origin[0] = o;
				var level = p.level();
				for (BlockPos pos : BlockPos.betweenClosed(o.offset(-30, -1, -30), o.offset(30, 10, 70))) {
					level.setBlock(pos, pos.getY() < o.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				// A stone wall 6 thick across its path.
				for (BlockPos pos : BlockPos.betweenClosed(o.offset(-8, 0, 16), o.offset(8, 7, 21))) {
					level.setBlock(pos, Blocks.STONE.defaultBlockState(), 2);
				}
			});
			world.getServer().runCommand("kill @e[type=!player]");
			BlockPos o = origin[0];
			for (int i = 0; i < 3; i++) world.getServer().runCommand("summon pig " + (o.getX() - 1 + i) + " " + o.getY() + " " + (o.getZ() + 10));
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(0f, 8f);
			ctx.waitTicks(20);
			ctx.getInput().holdKey(k -> k.keyUse);
			ctx.waitTicks(RingTuning.BLAST_CHARGE.ticks() + 5);
			ctx.getInput().releaseKey(k -> k.keyUse);
			for (int i = 1; i <= 4; i++) {
				ctx.waitTicks(i == 1 ? 6 : 10);
				ctx.takeScreenshot("dread_runner_" + i);
				report(world, "run " + i);
			}
			// Side on, to see the sprint.
			world.getServer().runOnServer(server -> player(server).teleportTo(o.getX() + 14.5, o.getY(), o.getZ() + 6.5));
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(110f, 5f);
			ctx.waitTicks(2);
			ctx.takeScreenshot("dread_runner_side");
			ctx.waitTicks(80);
			report(world, "end");
			world.getServer().runOnServer(server -> {
				var level = player(server).level();
				int open = 0;
				for (BlockPos pos : BlockPos.betweenClosed(o.offset(-1, 0, 16), o.offset(1, 3, 21))) if (level.getBlockState(pos).isAir()) open++;
				System.out.println("[dread-runner] tunnel through the wall: " + open + "/72 open; pigs left "
						+ level.getEntitiesOfClass(net.minecraft.world.entity.animal.pig.Pig.class, new AABB(o).inflate(80)).size()
						+ "; fear patches " + DreadTrails.count());
			});
			// The fear left behind, looking down the tunnel.
			world.getServer().runOnServer(server -> player(server).teleportTo(o.getX() + 0.5, o.getY(), o.getZ() - 4.5));
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(0f, 20f);
			ctx.waitTicks(10);
			ctx.takeScreenshot("dread_runner_fear_trail");
			// Into the fear: the runner's own owner is spared.
			world.getServer().runOnServer(server -> player(server).teleportTo(o.getX() + 0.5, o.getY(), o.getZ() + 8.5));
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.waitTicks(20);
			ctx.runOnClient(mc -> System.out.println("[dread-runner] owner in the fear: blind " + FearBlind.blind()
					+ " effect " + (mc.player.getEffect(ModEffects.FEAR_BLIND) != null)));
			// What anyone else in it sees.
			world.getServer().runOnServer(server -> player(server).addEffect(new net.minecraft.world.effect.MobEffectInstance(ModEffects.FEAR_BLIND,
					Math.max(1, com.sparky.lanternring.RingTuning.DREAD_BLIND.ticks()), 0, false, false, false)));
			ctx.waitTicks(10);
			ctx.takeScreenshot("dread_runner_blind");
			ctx.runOnClient(mc -> System.out.println("[dread-runner] someone else in the fear: blind " + FearBlind.blind()));
			// Out of it: it fades.
			world.getServer().runOnServer(server -> player(server).teleportTo(o.getX() + 20.5, o.getY(), o.getZ() - 10.5));
			ctx.waitTicks(30);
			ctx.takeScreenshot("dread_runner_blind_fading");
			ctx.runOnClient(mc -> System.out.println("[dread-runner] stepped out: blind " + FearBlind.blind()));
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> System.out.println("[dread-runner] later: blind " + FearBlind.blind()));
		}
	}

	private static void report(TestSingleplayerContext world, String when) {
		world.getServer().runOnServer(server -> {
			StringBuilder s = new StringBuilder();
			for (DreadRunner r : player(server).level().getEntitiesOfClass(DreadRunner.class, new AABB(player(server).blockPosition()).inflate(120))) {
				s.append(String.format(" runner at (%.1f, %.2f, %.1f) stopped=%d", r.getX(), r.getY(), r.getZ(), r.stopped()));
			}
			System.out.println("[dread-runner] " + when + ":" + s);
		});
	}
}
