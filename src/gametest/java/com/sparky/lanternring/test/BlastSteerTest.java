package com.sparky.lanternring.test;

import com.sparky.lanternring.BlastDrills;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.client.LabSettings;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

/**
 * The steerable Blast drill: it forms and waits while right-click is held, left-click sends it
 * straight on, and a double-click swings it right, left, up or down toward the aim in a gradual
 * curve (never more than RingTuning.BLAST_TURN allows in a tick). Double-click and hold keeps it
 * boring past its reach. Facing south (+Z), the player's right is west (-X).
 */
public class BlastSteerTest implements FabricClientGameTest {
	private static BlockPos feet;

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(60);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.getMainHandItem().set(ModComponents.MODE, RingMode.BLAST.ordinal());
				feet = p.blockPosition();
			});
			RingTuning.BLAST_CHARGE.set(0.25);
			looks(ctx, world);

			// Right (yaw +), left (yaw -), up (pitch -), down (pitch +).
			turn(ctx, world, "right", 40f, 0f, h -> -h.x);
			turn(ctx, world, "left", -40f, 0f, h -> h.x);
			turn(ctx, world, "up", 0f, -35f, h -> h.y);
			turn(ctx, world, "down", 0f, 35f, h -> h.y * -1);
			hold(ctx, world);
		}
	}

	private interface Side {
		double of(Vec3 heading);
	}

	/** Forms, launches straight south, then double-clicks looking off to one side and checks the swing. */
	private static void turn(ClientGameTestContext ctx, TestSingleplayerContext world, String name, float yaw, float pitch, Side side) {
		slab(world);
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
		ctx.getInput().lookAt(0f, 0f);
		ctx.waitTicks(10);
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(8);
		Vec3 formed = server(world, p -> BlastDrills.tip(p));
		ctx.takeScreenshot("steer_" + name + "_formed");
		if (name.equals("right")) {
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.waitTicks(2);
			ctx.takeScreenshot("steer_formed_3p");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
		}
		ctx.waitTicks(6);
		Vec3 still = server(world, p -> BlastDrills.tip(p));
		if (formed == null || still == null || formed.distanceTo(still) > 1.0e-6 || Boolean.TRUE.equals(server(world, BlastDrills::launched))) {
			throw new AssertionError(name + ": the drill should form and wait in place, " + formed + " then " + still);
		}
		ctx.getInput().pressKey(o -> o.keyAttack);
		ctx.waitTicks(3);
		Vec3 before = server(world, p -> BlastDrills.heading(p));
		if (before == null || before.z < 0.99) throw new AssertionError(name + ": launched straight on, heading " + before);
		ctx.getInput().lookAt(yaw, pitch);
		ctx.waitTicks(2);
		// The double-click.
		ctx.getInput().pressKey(o -> o.keyAttack);
		ctx.waitTicks(2);
		Object[] b0 = server(world, p -> new Object[] {BlastDrills.heading(p), p.level().getGameTime()});
		ctx.getInput().pressKey(o -> o.keyAttack);
		// Sampled with the server's clock: under software rendering the server can run ahead of the client.
		List<Vec3> headings = new ArrayList<>();
		List<Long> times = new ArrayList<>();
		long start = (Long) b0[1];
		for (int i = 0; i < 14; i++) {
			ctx.waitTicks(1);
			Object[] at = server(world, p -> new Object[] {BlastDrills.heading(p), p.level().getGameTime()});
			if (at[0] != null) {
				headings.add((Vec3) at[0]);
				times.add((Long) at[1]);
			}
			if (i == 4 || i == 9) ctx.takeScreenshot("steer_" + name + "_" + i);
		}
		double max = 0;
		int turning = 0;
		Vec3 last = b0[0] != null ? (Vec3) b0[0] : before;
		long lastTime = start;
		for (int i = 0; i < headings.size(); i++) {
			Vec3 h = headings.get(i);
			long dt = Math.max(1, times.get(i) - lastTime);
			double a = Math.toDegrees(Math.acos(Math.min(1, last.dot(h))));
			max = Math.max(max, a / dt);
			if (a > 0.5) turning += (int) dt;
			last = h;
			lastTime = times.get(i);
		}
		double limit = Math.toDegrees(BlastDrills.turnPerTick()) * 1.05 + 0.01;
		System.out.printf("[blast-steer] %s: %d ticks turning, at most %.1f deg a tick (limit %.1f), heading %s%n", name, turning, max, limit, last);
		if (max > limit) throw new AssertionError(name + ": turned " + max + " deg in a tick, a sharp turn (limit " + limit + ")");
		if (turning < 3) throw new AssertionError(name + ": should swing round over several ticks, turned in " + turning);
		if (side.of(last) < 0.25) throw new AssertionError(name + ": should have swung " + name + ", heading " + last);
		ctx.getInput().releaseKey(o -> o.keyUse);
		ctx.waitTicks(30);
		overhead(ctx, world, "steer_" + name + "_tunnel");
	}

	/** Each drill model formed and waiting, from behind and side on (no flat plate at its back). */
	private static void looks(ClientGameTestContext ctx, TestSingleplayerContext world) {
		for (LabSettings.DrillModel model : LabSettings.DrillModel.values()) {
			ctx.runOnClient(mc -> {
				LabSettings.get().drillModel = model;
				mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);
			});
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(5);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(10);
			ctx.takeScreenshot("look_" + model.name().toLowerCase() + "_back");
			ctx.getInput().lookAt(35f, 15f);
			ctx.waitTicks(3);
			ctx.takeScreenshot("look_" + model.name().toLowerCase() + "_side");
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.waitTicks(10);
		}
		ctx.runOnClient(mc -> {
			LabSettings.get().drillModel = LabSettings.DrillModel.CLASSIC;
			mc.options.setCameraType(CameraType.FIRST_PERSON);
		});
	}

	/** Double-click and hold, sweeping the aim round: it keeps turning and bores on past its 50 blocks. */
	private static void hold(ClientGameTestContext ctx, TestSingleplayerContext world) {
		slab(world);
		ctx.getInput().lookAt(0f, 0f);
		ctx.waitTicks(10);
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(8);
		ctx.getInput().pressKey(o -> o.keyAttack);
		ctx.waitTicks(2);
		ctx.getInput().holdKey(o -> o.keyAttack);
		for (int i = 0; i < 40; i++) {
			ctx.getInput().lookAt(i * 3f, 0f);
			ctx.waitTicks(1);
		}
		Vec3 h = server(world, p -> BlastDrills.heading(p));
		Vec3 tip = server(world, p -> BlastDrills.tip(p));
		double far = tip == null ? 0 : Math.sqrt(tip.distanceToSqr(Vec3.atCenterOf(feet)));
		System.out.println("[blast-steer] held: heading " + h + ", tip " + tip);
		if (h == null) throw new AssertionError("held: the drill should still be boring after 40 ticks (past its 50-block reach)");
		if (h.x > -0.3) throw new AssertionError("held: should have followed the aim round to the right, heading " + h);
		ctx.takeScreenshot("steer_hold_fp");
		ctx.getInput().releaseKey(o -> o.keyAttack);
		ctx.waitTicks(30);
		if (server(world, p -> BlastDrills.heading(p)) != null) throw new AssertionError("held: let go, it should run out and burst");
		ctx.getInput().releaseKey(o -> o.keyUse);
		ctx.waitTicks(10);
		System.out.println("[blast-steer] held: tip got " + Math.round(far) + " blocks out");
		overhead(ctx, world, "steer_hold_tunnel");
	}

	private interface Read<T> {
		T get(ServerPlayer player);
	}

	private static <T> T server(TestSingleplayerContext world, Read<T> read) {
		Object[] out = new Object[1];
		world.getServer().runOnServer(server -> out[0] = read.get(server.getPlayerList().getPlayers().get(0)));
		@SuppressWarnings("unchecked") T t = (T) out[0];
		return t;
	}

	/** A stone slab three blocks deep and 80 wide in front of the player, its top at head height: the tunnel shows as a trench from above. */
	private static void slab(TestSingleplayerContext world) {
		world.getServer().runOnServer(server -> {
			var level = server.getPlayerList().getPlayers().get(0).level();
			for (int x = -45; x <= 45; x++)
				for (int y = -1; y <= 1; y++)
					for (int z = 4; z <= 70; z++)
						level.setBlock(feet.offset(x, y, z), Blocks.STONE.defaultBlockState(), 2);
			for (int x = -45; x <= 45; x++)
				for (int y = 2; y <= 12; y++)
					for (int z = 4; z <= 70; z++)
						level.setBlock(feet.offset(x, y, z), Blocks.AIR.defaultBlockState(), 2);
		});
	}

	/** Looks down on the slab from high above it, then comes back. */
	private static void overhead(ClientGameTestContext ctx, TestSingleplayerContext world, String shot) {
		world.getServer().runCommand(String.format("tp @p %d %d %d 0 90", feet.getX(), feet.getY() + 45, feet.getZ() + 32));
		ctx.getInput().lookAt(0f, 90f);
		ctx.waitTicks(15);
		ctx.takeScreenshot(shot);
		world.getServer().runCommand(String.format("tp @p %d %d %d 0 0", feet.getX(), feet.getY(), feet.getZ()));
		ctx.waitTicks(10);
	}
}
