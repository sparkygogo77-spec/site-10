package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.ally.RageBull;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/**
 * The Red ring's Blast level 4, the Rage Bull: one run straight south and one diagonal (south-east)
 * into a big stone block, with a cross-section of each tunnel printed to show it is round.
 */
public class RageBullTest implements FabricClientGameTest {
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
			RingTuning.RAGE_BULL_RUN.set(12);
			BlockPos[] origin = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = player(server);
				var ring = Corps.RED.ring();
				ring.set(ModComponents.MODE, RingMode.BLAST.ordinal());
				ring.set(ModComponents.BLAST_LEVEL, 4);
				p.setItemInHand(InteractionHand.MAIN_HAND, ring);
				BlockPos o = p.blockPosition();
				origin[0] = o;
				var level = p.level();
				// A stone block 23 high in front of the player, with dirt stripes to read depth by.
				for (BlockPos pos : BlockPos.betweenClosed(o.offset(-40, -1, 2), o.offset(55, 22, 60))) {
					level.setBlock(pos, (pos.getX() + pos.getZ()) % 6 == 0 ? Blocks.DIRT.defaultBlockState() : Blocks.STONE.defaultBlockState(), 2);
				}
				for (BlockPos pos : BlockPos.betweenClosed(o.offset(-40, 0, -12), o.offset(55, 22, 1))) {
					level.setBlock(pos, Blocks.AIR.defaultBlockState(), 2);
				}
			});
			world.getServer().runCommand("kill @e[type=!player]");
			BlockPos o = origin[0];
			// Pigs in a pocket in the straight run's path, to be trampled.
			world.getServer().runCommand("fill " + (o.getX() - 26) + " " + o.getY() + " " + (o.getZ() + 26) + " " + (o.getX() - 17) + " " + (o.getY() + 3) + " " + (o.getZ() + 29) + " air");
			for (int i = 0; i < 4; i++) world.getServer().runCommand("summon pig " + (o.getX() - 24 + i * 2) + " " + o.getY() + " " + (o.getZ() + 27));

			// Straight south, from x-22.
			Vec3 a = new Vec3(o.getX() - 21.5, o.getY(), o.getZ() + 0.5);
			run(ctx, world, a, 0f, "south");
			// Diagonal, south-east, from x+8.
			Vec3 b = new Vec3(o.getX() + 8.5, o.getY(), o.getZ() + 0.5);
			run(ctx, world, b, -45f, "diagonal");
			pigs(world);

			// In the open, seen side on from 40 blocks away, so the whole bull shows.
			world.getServer().runOnServer(server -> player(server).teleportTo(o.getX() - 20.5, o.getY(), o.getZ() - 6.5));
			ctx.getInput().lookAt(-90f, 0f);
			ctx.waitTicks(10);
			ctx.getInput().holdKey(k -> k.keyUse);
			ctx.waitTicks(5);
			ctx.getInput().releaseKey(k -> k.keyUse);
			ctx.waitTicks(5);
			world.getServer().runOnServer(server -> player(server).teleportTo(o.getX() - 2.5, o.getY(), o.getZ() - 45.5));
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, -12f);
			for (int i = 1; i <= 4; i++) {
				ctx.waitTicks(i == 1 ? 5 : 12);
				ctx.takeScreenshot("rage_bull_side_" + i);
			}
			// Head on, from further along its path.
			world.getServer().runOnServer(server -> player(server).teleportTo(o.getX() + 40.5, o.getY(), o.getZ() - 6.5));
			ctx.getInput().lookAt(90f, -10f);
			ctx.waitTicks(10);
			ctx.takeScreenshot("rage_bull_front");
			ctx.waitTicks(120);
			ctx.takeScreenshot("rage_bull_side_fading");
		}
	}

	private static void run(ClientGameTestContext ctx, TestSingleplayerContext world, Vec3 at, float yaw, String name) {
		world.getServer().runOnServer(server -> player(server).teleportTo(at.x, at.y, at.z));
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
		ctx.getInput().lookAt(yaw, 5f);
		ctx.waitTicks(20);
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(15);
		ctx.getInput().releaseKey(o -> o.keyUse);
		for (int i = 1; i <= 5; i++) {
			ctx.waitTicks(i == 1 ? 5 : 25);
			ctx.takeScreenshot("rage_bull_" + name + "_" + i);
			report(world, name + " " + i);
		}
		ctx.waitTicks(200);
		report(world, name + " end");
		// The finished tunnel, from its mouth, then a cross-section.
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
		world.getServer().runOnServer(server -> player(server).teleportTo(at.x, at.y, at.z));
		ctx.getInput().lookAt(yaw, 0f);
		ctx.waitTicks(20);
		ctx.takeScreenshot("rage_bull_" + name + "_tunnel");
		Vec3 dir = Vec3.directionFromRotation(0, yaw);
		section(world, at, dir, 22, name);
		section(world, at, dir, 34, name);
	}

	private static void pigs(TestSingleplayerContext world) {
		world.getServer().runOnServer(server -> System.out.println("[rage-bull] pigs left: "
				+ player(server).level().getEntitiesOfClass(net.minecraft.world.entity.animal.pig.Pig.class, new AABB(player(server).blockPosition()).inflate(150)).size()));
	}

	private static void report(TestSingleplayerContext world, String when) {
		world.getServer().runOnServer(server -> {
			var level = player(server).level();
			StringBuilder s = new StringBuilder();
			for (RageBull bull : level.getEntitiesOfClass(RageBull.class, new AABB(player(server).blockPosition()).inflate(120))) {
				s.append(String.format(" bull at (%.1f, %.2f, %.1f) stopped=%d", bull.getX(), bull.getY(), bull.getZ(), bull.stopped()));
			}
			System.out.println("[rage-bull] " + when + ":" + s);
		});
	}

	/** Prints the tunnel's cross-section `along` blocks from where it started: # stone, . air. */
	private static void section(TestSingleplayerContext world, Vec3 from, Vec3 dir, double along, String name) {
		world.getServer().runOnServer(server -> {
			var level = player(server).level();
			Vec3 side = new Vec3(-dir.z, 0, dir.x);
			Vec3 c = from.add(dir.scale(along));
			StringBuilder s = new StringBuilder("[rage-bull] " + name + " section at " + along + ":\n");
			int air = 0;
			for (int y = 21; y >= -1; y--) {
				for (int x = -12; x <= 12; x++) {
					Vec3 p = c.add(side.scale(x));
					BlockPos pos = BlockPos.containing(p.x, from.y + y, p.z);
					boolean open = !level.getBlockState(pos).isSolidRender();
					if (open) air++;
					s.append(open ? '.' : '#');
				}
				s.append('\n');
			}
			System.out.println(s + "[rage-bull] " + name + " open cells: " + air);
		});
	}
}
