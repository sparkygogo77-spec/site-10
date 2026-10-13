package com.sparky.lanternring.test;

import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RamBarrier;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.client.LabSettings;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;

/**
 * Fast flight's ram barrier: it forms ahead of the glide, blows a zombie on a pillar off it into
 * the ground, then shatters against a stone wall and knocks a hole in it.
 */
public class RamBarrierTest implements FabricClientGameTest {
	private static final int FLY = 25;
	private static final int ZOMBIE_AT = 55;
	private static final int WALL_AT = 110;
	/** How far along the wall the second, big-crater run goes. */
	private static final int CRATER_X = 30;

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 18000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(60);
			BlockPos feet = world.getServer().computeOnServer(server -> {
				ServerPlayer p = player(server);
				p.getMainHandItem().set(ModComponents.CHARGE, PowerRingItem.MAX_CHARGE);
				p.getMainHandItem().set(ModComponents.FLIGHT, true);
				return p.blockPosition();
			});
			int x = feet.getX(), y = feet.getY(), z = feet.getZ();
			world.getServer().runCommand("forceload add " + (x - 16) + " " + z + " " + (x + 48) + " " + (z + WALL_AT + 16));
			// A zombie on a stone pillar in the flight path, and a stone wall further on.
			world.getServer().runCommand("fill " + x + " " + y + " " + (z + ZOMBIE_AT) + " " + x + " " + (y + FLY - 4) + " " + (z + ZOMBIE_AT) + " stone");
			world.getServer().runCommand("summon zombie " + (x + 0.5) + " " + (y + FLY - 3) + " " + (z + ZOMBIE_AT + 0.5) + " {PersistenceRequired:1b}");
			// Held in place on its pillar but still free to be thrown (NoAI mobs ignore knockback).
			world.getServer().runCommand("effect give @e[type=zombie] slowness 120 255 true");
			world.getServer().runCommand("fill " + (x - 8) + " " + y + " " + (z + WALL_AT) + " " + (x + CRATER_X + 10) + " " + (y + FLY + 8) + " " + (z + WALL_AT + 4) + " stone");
			RingTuning.RAM_BARRIER_FORM.set(0.5);
			world.getServer().runCommand("tp @p " + (x + 0.5) + " " + (y + FLY) + " " + (z + 0.5) + " 0 0");
			ctx.waitTicks(5);
			ctx.runOnClient(mc -> {
				mc.player.getAbilities().flying = true;
				mc.player.onUpdateAbilities();
				mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);
			});
			ctx.waitTicks(10);
			ctx.getInput().lookAt(0f, 0f);
			ctx.getInput().holdKey(o -> o.keyUp);
			ctx.getInput().holdKey(o -> o.keySprint);

			boolean formed = waitFor(ctx, world, 80, s -> RamBarrier.isUp(player(s)));
			log(ctx, world, "formed=" + formed);
			ctx.waitTicks(3);
			ctx.takeScreenshot("ram_barrier_formed_back");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.waitTicks(3);
			ctx.takeScreenshot("ram_barrier_formed_first_person");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));

			// The zombie is hit and thrown off its pillar.
			boolean hit = waitFor(ctx, world, 80, s -> player(s).getZ() > z + ZOMBIE_AT - 6);
			ctx.waitTicks(2);
			ctx.takeScreenshot("ram_barrier_hit");
			log(ctx, world, "reached zombie=" + hit);
			// The wall stops the glide and the barrier breaks along with the part of the wall it hit.
			boolean crashed = waitFor(ctx, world, 120, s -> !RamBarrier.isUp(player(s)) && player(s).getZ() > z + ZOMBIE_AT + 10);
			ctx.getInput().releaseKey(o -> o.keySprint);
			ctx.getInput().releaseKey(o -> o.keyUp);
			ctx.waitTicks(2);
			ctx.takeScreenshot("ram_barrier_wall_break");
			int broken = holeSize(world, x, y, z);
			log(ctx, world, "crashed=" + crashed + " wallHole=" + broken);
			ctx.waitTicks(30);
			ctx.takeScreenshot("ram_barrier_wall_hole");

			// The Ring Lab's big crater, further along the same wall.
			LabSettings.get().ramHole = LabSettings.RamHole.CRATER;
			world.getServer().runCommand("tp @p " + (x + CRATER_X + 0.5) + " " + (y + FLY) + " " + (z + ZOMBIE_AT + 0.5) + " 0 0");
			ctx.waitTicks(10);
			ctx.getInput().lookAt(0f, 0f);
			ctx.getInput().holdKey(o -> o.keyUp);
			ctx.getInput().holdKey(o -> o.keySprint);
			waitFor(ctx, world, 200, s -> player(s).getZ() > z + WALL_AT - 20 && !RamBarrier.isUp(player(s)) && player(s).getAbilities().flying
					&& s.overworld().getGameTime() > 0 && player(s).getZ() > z + WALL_AT - 6);
			ctx.getInput().releaseKey(o -> o.keySprint);
			ctx.getInput().releaseKey(o -> o.keyUp);
			ctx.waitTicks(30);
			int crater = holeSize(world, x + CRATER_X, y, z);
			log(ctx, world, "crater=" + crater);
			ctx.takeScreenshot("ram_barrier_crater");
			LabSettings.get().ramHole = LabSettings.RamHole.DENT;
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			RingTuning.RAM_BARRIER_FORM.set(RingTuning.RAM_BARRIER_FORM.defaultSeconds);
			if (!formed || broken == 0) throw new AssertionError("ram barrier: formed=" + formed + " wallHole=" + broken);
		}
	}

	/** Air blocks in the wall's front layer round the flight line at column x. */
	private static int holeSize(TestSingleplayerContext world, int x, int y, int z) {
		return world.getServer().computeOnServer(server -> {
			int n = 0;
			var level = server.overworld();
			for (int dx = -7; dx <= 7; dx++) {
				for (int dy = FLY - 7; dy <= FLY + 7; dy++) {
					if (level.getBlockState(new BlockPos(x + dx, y + dy, z + WALL_AT)).isAir()) n++;
				}
			}
			return n;
		});
	}

	private static boolean waitFor(ClientGameTestContext ctx, TestSingleplayerContext world, int ticks,
			java.util.function.Predicate<MinecraftServer> done) {
		for (int i = 0; i < ticks; i++) {
			if (world.getServer().computeOnServer(done::test)) return true;
			ctx.waitTicks(1);
		}
		return false;
	}

	private static void log(ClientGameTestContext ctx, TestSingleplayerContext world, String what) {
		String where = world.getServer().computeOnServer(s -> {
			ServerPlayer p = player(s);
			return String.format("z=%.1f y=%.1f flying=%s", p.getZ(), p.getY(), p.getAbilities().flying);
		});
		System.out.println("[ram barrier test] " + what + " " + where);
	}

	private static ServerPlayer player(MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
