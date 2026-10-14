package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.PrimedSlams;
import com.sparky.lanternring.client.CombatInput;
import com.sparky.lanternring.client.FastFlight;
import com.sparky.lanternring.client.LabSettings;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;

/**
 * J's in-game report #2 and Blender pass 518: shift while flying forward is hyper speed; shift held in hyper speed
 * diving into the ground is the primed slam (P1: the whole 7x7 opens at once, lined, and left click rebuilds it rippling
 * out from where you look); crouch held on a super jump's way down is the primed 9x9 slam (P2), rebuilt as you sweep.
 */
public class PrimedSlamTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
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
			server.runCommand(String.format("forceload add %d %d %d %d", x - 60, z - 60, x + 60, z + 120));
			server.runCommand(String.format("fill %d %d %d %d %d %d dirt", x - 60, y - 4, z - 60, x + 60, y - 1, z + 120));
			server.runCommand(String.format("fill %d %d %d %d %d %d grass_block", x - 60, y - 1, z - 60, x + 60, y - 1, z + 120));
			server.runCommand(String.format("fill %d %d %d %d %d %d air", x - 60, y, z - 60, x + 60, y + 40, z + 120));
			server.runCommand("kill @e[type=!player]");
			ctx.runOnClient(mc -> LabSettings.get().superSprint = LabSettings.SuperSprint.FAST);

			String p1 = flight(ctx, world, x, y, z);
			String p2 = jump(ctx, world, o[0]);
			if (p1 != null || p2 != null) throw new AssertionError("primed slam: " + p1 + " " + p2);
		}
	}

	/** Hyper speed from 24 up, diving at 55 degrees with shift held: the primed P1 slam, then a click rebuilds it. */
	private static String flight(ClientGameTestContext ctx, TestSingleplayerContext world, int x, int y, int z) {
		var server = world.getServer();
		server.runCommand(String.format("tp @p %.1f %d %.1f 0 0", x + 0.5, y + 24, z - 30.5));
		ctx.waitTicks(5);
		ctx.runOnClient(mc -> {
			mc.player.getAbilities().flying = true;
			mc.player.onUpdateAbilities();
			mc.options.setCameraType(CameraType.THIRD_PERSON_BACK);
		});
		ctx.getInput().lookAt(0f, 0f);
		ctx.waitTicks(3);
		ctx.getInput().holdKey(o -> o.keyUp);
		ctx.getInput().holdKey(o -> o.keyShift);
		float top = 0;
		for (int t = 0; t < 14; t++) {
			ctx.waitTick();
			top = Math.max(top, ctx.computeOnClient(mc -> FastFlight.hyper() ? FastFlight.speed() : 0f));
		}
		ctx.takeScreenshot("primed_hyper_speed");
		ctx.getInput().lookAt(0f, 55f);
		boolean primed = false, fired = false;
		for (int t = 0; t < 60 && !fired; t++) {
			ctx.waitTick();
			primed |= ctx.computeOnClient(mc -> CombatInput.primed());
			fired = ctx.computeOnClient(mc -> CombatInput.locked());
			if (primed && t % 3 == 0 && t < 9) ctx.takeScreenshot("primed_p1_dive");
		}
		ctx.getInput().releaseKey(o -> o.keyUp);
		ctx.getInput().releaseKey(o -> o.keyShift);
		for (int t = 0; t < 8 && !ctx.computeOnClient(mc -> mc.player.onGround()); t++) ctx.waitTick();
		double[] feet = ctx.computeOnClient(mc -> new double[] {mc.player.getX(), mc.player.getY(), mc.player.getZ()});
		ctx.waitTicks(2);
		int open = holes(world, feet, y, 3);
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
		ctx.waitTicks(1);
		ctx.takeScreenshot("primed_p1_touchdown");
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
		ctx.getInput().lookAt(0f, 60f);
		ctx.waitTicks(8);
		ctx.takeScreenshot("primed_p1_crater_lined");
		boolean rebuildable = server.computeOnServer(s -> PrimedSlams.rebuildable(s.getPlayerList().getPlayers().get(0)));
		// At 2 s, left click on the crater 2 blocks ahead: it ripples back from there.
		ctx.waitTicks(20);
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
		ctx.getInput().lookAt(0f, 50f);
		ctx.waitTicks(1);
		ctx.getInput().holdKey(o -> o.keyAttack);
		ctx.waitTicks(4);
		ctx.takeScreenshot("primed_p1_rebuild_first_person");
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
		ctx.waitTicks(2);
		ctx.takeScreenshot("primed_p1_rebuild");
		ctx.getInput().releaseKey(o -> o.keyAttack);
		ctx.waitTicks(12);
		ctx.takeScreenshot("primed_p1_rebuilt");
		int left = holes(world, feet, y, 3);
		System.out.println(String.format("[primed slam] P1: hyper top %.2f, primed %s, fired %s, touchdown y %.2f, open %d of 48, rebuildable %s, left %d",
				top, primed, fired, feet[1] - y, open, rebuildable, left));
		if (top < 2 || !primed || !fired || open < 44 || !rebuildable || left > open - 30) {
			return "P1: top " + top + " primed " + primed + " fired " + fired + " open " + open + " left " + left;
		}
		return null;
	}

	/** A full super jump; crouch held on the way down primes P2, the 9x9; sweeping the crosshair over it rebuilds it. */
	private static String jump(ClientGameTestContext ctx, TestSingleplayerContext world, BlockPos o) {
		world.getServer().runOnServer(s -> s.getPlayerList().getPlayers().get(0).teleportTo(o.getX() + 30.5, o.getY(), o.getZ() - 30.5));
		ctx.getInput().lookAt(0f, 0f);
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
		ctx.waitTicks(10);
		ctx.getInput().holdKey(opt -> opt.keyUp);
		ctx.getInput().holdKey(opt -> opt.keySprint);
		ctx.waitTicks(95);
		ctx.getInput().holdKey(opt -> opt.keyJump);
		ctx.waitTicks(2);
		ctx.getInput().releaseKey(opt -> opt.keyJump);
		ctx.getInput().releaseKey(opt -> opt.keySprint);
		ctx.getInput().releaseKey(opt -> opt.keyUp);
		// Over the top, crouch.
		double last = -1e9;
		for (int t = 0; t < 120; t++) {
			ctx.waitTick();
			double yy = ctx.computeOnClient(mc -> mc.player.getY());
			if (yy < last - 0.05) break;
			last = yy;
		}
		ctx.getInput().holdKey(opt -> opt.keyShift);
		ctx.waitTicks(6);
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
		ctx.takeScreenshot("primed_p2_dive");
		for (int t = 0; t < 120 && !ctx.computeOnClient(mc -> mc.player.onGround()); t++) ctx.waitTick();
		double[] feet = ctx.computeOnClient(mc -> new double[] {mc.player.getX(), mc.player.getY(), mc.player.getZ()});
		ctx.waitTicks(3);
		ctx.getInput().releaseKey(opt -> opt.keyShift);
		ctx.takeScreenshot("primed_p2_touchdown");
		int open = holes(world, feet, o.getY(), 4);
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
		ctx.getInput().lookAt(0f, 65f);
		ctx.waitTicks(10);
		ctx.takeScreenshot("primed_p2_crater_lined");
		// Left click held, sweeping the crosshair across the crater.
		ctx.getInput().holdKey(opt -> opt.keyAttack);
		for (int i = 0; i < 24; i++) {
			ctx.getInput().lookAt(-60f + i * 5f, 55f);
			ctx.waitTick();
			if (i == 12) ctx.takeScreenshot("primed_p2_sweep");
		}
		ctx.getInput().releaseKey(opt -> opt.keyAttack);
		ctx.waitTicks(10);
		ctx.takeScreenshot("primed_p2_swept");
		int left = holes(world, feet, o.getY(), 4);
		System.out.println(String.format("[primed slam] P2: touchdown y %.2f, open %d of 80, left after the sweep %d", feet[1] - o.getY(), open, left));
		if (open < 70 || left >= open) return "P2: open " + open + " left " + left;
		return null;
	}

	/** Air blocks in the top layer of the (2r+1)^2 round the feet, the landing block aside. */
	private static int holes(TestSingleplayerContext world, double[] feet, int y, int r) {
		int[] n = {0};
		world.getServer().runOnServer(s -> {
			ServerLevel level = s.getPlayerList().getPlayers().get(0).level();
			BlockPos c = BlockPos.containing(feet[0], y - 1, feet[2]);
			for (BlockPos q : BlockPos.betweenClosed(c.offset(-r, 0, -r), c.offset(r, 0, r))) if (level.getBlockState(q).isAir()) n[0]++;
		});
		return n[0];
	}
}
