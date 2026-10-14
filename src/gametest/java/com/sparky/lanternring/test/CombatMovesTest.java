package com.sparky.lanternring.test;

import com.sparky.lanternring.AbsorbBlasts;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.client.CombatInput;
import com.sparky.lanternring.client.LabSettings;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.animal.pig.Pig;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.AABB;

/**
 * J's combat picks (Blender passes 503, 509, 510): the big flight slam fired from a steep, fast dive at H5 (its 7x7
 * crater lit, mobs round it thrown up the tick after touchdown), the flying flurry's string from a melee hit in
 * flight (the target launched by the backfist), and the absorb catching an arrow while left click is held.
 * Set COMBAT_ONLY=slam, flurry or absorb to run one part.
 */
public class CombatMovesTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		String only = System.getenv("COMBAT_ONLY");
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			var server = world.getServer();
			server.runCommand("gamemode survival @a");
			server.runCommand("difficulty peaceful");
			server.runCommand("gamerule doDaylightCycle false");
			server.runCommand("gamerule doMobSpawning false");
			server.runCommand("time set 6000");
			ctx.waitTicks(60);
			BlockPos[] o = new BlockPos[1];
			server.runOnServer(s -> {
				ServerPlayer p = s.getPlayerList().getPlayers().get(0);
				o[0] = p.blockPosition();
				ItemStack ring = Corps.GREEN.ring();
				ring.set(ModComponents.CHARGE, PowerRingItem.MAX_CHARGE);
				ring.set(ModComponents.FLIGHT, true);
				p.setItemInHand(InteractionHand.MAIN_HAND, ring);
			});
			int x = o[0].getX(), y = o[0].getY(), z = o[0].getZ();
			server.runCommand(String.format("forceload add %d %d %d %d", x - 40, z - 40, x + 40, z + 80));
			server.runCommand(String.format("fill %d %d %d %d %d %d dirt", x - 40, y - 4, z - 40, x + 40, y - 1, z + 80));
			server.runCommand(String.format("fill %d %d %d %d %d %d grass_block", x - 40, y - 1, z - 40, x + 40, y - 1, z + 80));
			server.runCommand(String.format("fill %d %d %d %d %d %d air", x - 40, y, z - 40, x + 40, y + 40, z + 80));
			server.runCommand("kill @e[type=!player]");
			ctx.waitTicks(10);

			if (only == null || only.equals("slam")) slam(ctx, world, x, y, z);
			if (only == null || only.equals("flurry")) flurry(ctx, world, x, y, z);
			if (only == null || only.equals("absorb")) absorb(ctx, world, x, y, z);
		}
	}

	/** Dives at 70 degrees from 24 blocks up; the slam fires at H5 and lands in its 7x7 crater among four pigs. */
	private static void slam(ClientGameTestContext ctx, TestSingleplayerContext world, int x, int y, int z) {
		var server = world.getServer();
		ctx.runOnClient(mc -> LabSettings.get().flightSlam = LabSettings.FlightSlam.H5);
		server.runCommand(String.format("tp @p %.1f %d %.1f 0 70", x + 0.5, y + 24, z + 0.5));
		ctx.waitTicks(5);
		ctx.runOnClient(mc -> {
			mc.player.getAbilities().flying = true;
			mc.player.onUpdateAbilities();
			mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);
		});
		ctx.waitTicks(5);
		ctx.getInput().lookAt(0f, 70f);
		ctx.getInput().holdKey(opt -> opt.keyUp);
		ctx.getInput().holdKey(opt -> opt.keySprint);
		boolean fired = false;
		for (int t = 0; t < 80 && !fired; t++) {
			ctx.waitTick();
			fired = ctx.computeOnClient(mc -> CombatInput.locked());
		}
		ctx.getInput().releaseKey(opt -> opt.keyUp);
		ctx.getInput().releaseKey(opt -> opt.keySprint);
		if (!fired) throw new AssertionError("the flight slam never fired");
		// Pigs round where it's coming down, to be thrown up the tick after touchdown.
		double[] at = ctx.computeOnClient(mc -> new double[] {mc.player.getX(), mc.player.getY(), mc.player.getZ(), mc.player.getDeltaMovement().x,
				mc.player.getDeltaMovement().z});
		double lx = at[0] + at[3] * 3, lz = at[2] + at[4] * 3;
		for (int i = 0; i < 4; i++) {
			double a = i * Math.PI / 2;
			server.runCommand(String.format("summon pig %.2f %d %.2f {NoAI:1b}", lx + Math.cos(a) * 3.5, y, lz + Math.sin(a) * 3.5));
		}
		boolean landed = false;
		for (int t = 0; t < 10 && !landed; t++) {
			ctx.waitTick();
			landed = ctx.computeOnClient(mc -> mc.player.onGround());
		}
		double[] feet = ctx.computeOnClient(mc -> new double[] {mc.player.getX(), mc.player.getY(), mc.player.getZ()});
		ctx.waitTicks(2);
		double[] rising = {0};
		server.runOnServer(s -> {
			var level = s.getPlayerList().getPlayers().get(0).level();
			for (Pig pig : level.getEntitiesOfClass(Pig.class, new AABB(feet[0], feet[1], feet[2], feet[0], feet[1], feet[2]).inflate(8))) {
				rising[0] = Math.max(rising[0], pig.getY() - y);
			}
		});
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
		ctx.waitTicks(2);
		ctx.takeScreenshot("combat_slam_h5_touchdown");
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
		ctx.getInput().lookAt(0f, 50f);
		ctx.waitTicks(4);
		ctx.takeScreenshot("combat_slam_h5_crater");
		ctx.waitTicks(10);
		ctx.takeScreenshot("combat_slam_h5_crater_late");
		ctx.waitTicks(20);
		int[] holes = {0};
		server.runOnServer(s -> {
			var level = s.getPlayerList().getPlayers().get(0).level();
			BlockPos c = BlockPos.containing(feet[0], y - 1, feet[2]);
			for (BlockPos q : BlockPos.betweenClosed(c.offset(-3, 0, -3), c.offset(3, 0, 3))) if (level.getBlockState(q).isAir()) holes[0]++;
		});
		System.out.println(String.format("[combat] slam: touchdown (%.2f, %.2f, %.2f), pigs rose %.2f, crater holes %d", feet[0] - x, feet[1] - y,
				feet[2] - z, rising[0], holes[0]));
		server.runCommand("kill @e[type=pig]");
		if (holes[0] < 36 || rising[0] < 0.3) throw new AssertionError("flight slam: holes=" + holes[0] + " pigs rose=" + rising[0]);
	}

	/** Hovering 10 up, a melee hit on a pig in front starts the string; the backfist launches it. */
	private static void flurry(ClientGameTestContext ctx, TestSingleplayerContext world, int x, int y, int z) {
		var server = world.getServer();
		server.runCommand(String.format("tp @p %.1f %d %.1f 0 0", x + 0.5, y + 10, z + 20.5));
		ctx.waitTicks(3);
		ctx.runOnClient(mc -> {
			mc.player.getAbilities().flying = true;
			mc.player.onUpdateAbilities();
			mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT);
		});
		ctx.getInput().lookAt(0f, 10f);
		server.runCommand(String.format("summon pig %.1f %d %.1f {NoAI:1b,NoGravity:1b}", x + 0.5, y + 10, z + 22.5));
		ctx.waitTicks(5);
		int pigId = world.getServer().computeOnServer(s -> {
			var level = s.getPlayerList().getPlayers().get(0).level();
			return level.getEntitiesOfClass(Pig.class, new AABB(x - 4, y, z + 16, x + 4, y + 20, z + 28)).getFirst().getId();
		});
		double startZ = world.getServer().computeOnServer(s -> s.getPlayerList().getPlayers().get(0).level().getEntity(pigId).getZ());
		ctx.runOnClient(mc -> {
			Entity pig = mc.level.getEntity(pigId);
			if (pig != null) mc.gameMode.attack(mc.player, pig);
		});
		ctx.waitTicks(6);
		ctx.takeScreenshot("combat_flurry_cross");
		ctx.waitTicks(7);
		ctx.takeScreenshot("combat_flurry_backfist");
		ctx.waitTicks(4);
		ctx.takeScreenshot("combat_flurry_launched");
		ctx.waitTicks(20);
		double[] pig = world.getServer().computeOnServer(s -> {
			Entity e = s.getPlayerList().getPlayers().get(0).level().getEntity(pigId);
			return e == null ? new double[] {Double.NaN, 0} : new double[] {e.getZ(), e.getY()};
		});
		System.out.println(String.format("[combat] flurry: pig moved %.1f blocks along z, now %.1f up", pig[0] - startZ, pig[1] - y));
		server.runCommand("kill @e[type=pig]");
		ctx.runOnClient(mc -> {
			mc.player.getAbilities().flying = false;
			mc.player.onUpdateAbilities();
		});
		if (!Double.isNaN(pig[0]) && pig[0] - startZ < 8) throw new AssertionError("flying flurry: the pig wasn't launched (" + (pig[0] - startZ) + ")");
	}

	/** Left click held looking up: an arrow shot at you is caught at the ring, and let go it's sent back as the blast. */
	private static void absorb(ClientGameTestContext ctx, TestSingleplayerContext world, int x, int y, int z) {
		var server = world.getServer();
		server.runCommand(String.format("tp @p %.1f %d %.1f 0 0", x + 0.5, y, z + 0.5));
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
		ctx.getInput().lookAt(0f, -30f);
		ctx.waitTicks(5);
		ctx.getInput().holdKey(opt -> opt.keyAttack);
		ctx.waitTicks(3);
		server.runCommand(String.format("summon arrow %.1f %d %.1f {Motion:[0.0,0.05,-1.2d]}", x + 0.5, y + 1, z + 9.5));
		boolean caught = false;
		for (int t = 0; t < 20 && !caught; t++) {
			ctx.waitTick();
			caught = server.computeOnServer(s -> AbsorbBlasts.holds(s.getPlayerList().getPlayers().get(0)));
		}
		ctx.waitTicks(10);
		ctx.takeScreenshot("combat_absorb_r4b_held");
		ctx.waitTicks(30);
		ctx.takeScreenshot("combat_absorb_r4b_charged");
		ctx.getInput().releaseKey(opt -> opt.keyAttack);
		ctx.waitTicks(3);
		ctx.takeScreenshot("combat_absorb_release");
		boolean still = server.computeOnServer(s -> AbsorbBlasts.holds(s.getPlayerList().getPlayers().get(0)));
		System.out.println("[combat] absorb: caught " + caught + ", still held after release " + still);
		if (!caught || still) throw new AssertionError("absorb: caught=" + caught + " still held=" + still);
	}
}
