package com.sparky.lanternring.test;

import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.client.FlightPoses;
import com.sparky.lanternring.client.LabFx;
import com.sparky.lanternring.client.LabSettings;
import com.sparky.lanternring.client.RingFirstPerson;
import com.sparky.lanternring.client.RingTuningScreen;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

/** Boots the real client, puts the ring on, and photographs each Ring Lab version and power. */
public class RingClientTest implements FabricClientGameTest {
	private static final int RIGHT_MOUSE = 1;

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			ctx.waitTicks(60);
			LabSettings lab = LabSettings.get();
			RingFirstPerson.recordDebug = true;
			lab.handPose = LabSettings.HandPose.RING_FORWARD;
			lab.ringGlow = LabSettings.RingGlow.AURA;
			ctx.getInput().lookAt(0f, 10f);
			// RING_TEST_ONLY=lasso runs just the lasso part, for quick local iterations.
			if ("lasso".equals(System.getenv("RING_TEST_ONLY"))) {
				lasso(ctx, world);
				return;
			}

			// The Durations editor, with one value changed so the green highlight shows.
			RingTuning.CONSTRUCT_LIFETIME.set(30);
			ctx.setScreen(() -> new RingTuningScreen(null));
			ctx.waitTicks(4);
			ctx.takeScreenshot("durations_menu");
			ctx.setScreen(() -> null);
			RingTuning.resetAll();

			world.getServer().runCommand("time set 18000");
			lab.ringModel = LabSettings.RingModel.SIGNET;
			camera(ctx, CameraType.FIRST_PERSON);

			// Twin helix beam: grows out of the ring, holds on the target, then unravels.
			beam(ctx, world, LabSettings.UseFx.HELIX, CameraType.FIRST_PERSON, "beam_fp");
			beamSideOn(ctx, LabSettings.UseFx.HELIX, "beam_side");
			beamSideOn(ctx, LabSettings.UseFx.HELIX_RECALL, "beam_recall_side");
			// Held for a second: the fat charged beam and its Shockwave-sized dome at the wall.
			chargedBeam(ctx, world);
			ctx.runOnClient(mc -> LabFx.chargedBeam(mc.player.getEyePosition().add(-7, -0.5, 9), mc.player.getEyePosition().add(7, -0.5, 9)));
			for (int i = 1; i <= 6; i++) {
				ctx.waitTicks(2);
				ctx.takeScreenshot("beam_charged_side_" + i);
			}
			ctx.waitTicks(20);
			camera(ctx, CameraType.FIRST_PERSON);


			// 9x9 wall from one click, at night so the glow shows. It outlasts the click.
			mode(world, RingMode.WALL);
			ctx.getInput().lookAt(0f, 0f);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(10);
			ctx.takeScreenshot("wall_night");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			ctx.takeScreenshot("wall_day_still_standing");
			ctx.waitTicks(RingTuning.WALL_LIFETIME.ticks());
			ctx.takeScreenshot("wall_expired");

			// Dome into a stone hill.
			hill(world);
			ctx.waitTicks(10);
			mode(world, RingMode.DOME);
			ctx.getInput().lookAt(0f, 0f);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(10);
			ctx.takeScreenshot("dome_fp");
			camera(ctx, CameraType.THIRD_PERSON_BACK);
			ctx.waitTicks(4);
			ctx.takeScreenshot("dome_tp_back");
			ctx.getInput().holdKey(o -> o.keyShift);
			ctx.waitTicks(15);
			ctx.takeScreenshot("dome_tp_crouch_wide");
			ctx.getInput().releaseKey(o -> o.keyShift);
			ctx.waitTicks(15);
			ctx.getInput().lookAt(0f, 80f);
			ctx.waitTicks(10);
			ctx.takeScreenshot("dome_tp_looking_down");
			ctx.getInput().releaseKey(o -> o.keyUse);
			camera(ctx, CameraType.FIRST_PERSON);
			ctx.waitTicks(10);
			ctx.takeScreenshot("dome_released");

			// Blast into a fresh hill.
			hill(world);
			ctx.waitTicks(10);
			mode(world, RingMode.BLAST);
			ctx.getInput().lookAt(0f, 0f);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(3);
			ctx.takeScreenshot("blast_fire");
			ctx.waitTicks(25);
			ctx.takeScreenshot("blast_after");

			// Shockwave: a dome grows out, mows the grass and throws a ring of pigs back as it reaches them.
			world.getServer().runCommand("time set 18000");
			world.getServer().runCommand("execute at @p run fill ~-12 ~ ~-12 ~12 ~6 ~12 air");
			// A meadow of grass the dome should mow flat as it passes.
			world.getServer().runCommand("execute at @p run fill ~-10 ~ ~-10 ~10 ~ ~10 minecraft:short_grass");
			for (int[] at : new int[][] {{4, 3}, {-4, 4}, {0, 6}, {5, -2}, {-3, -5}}) {
				world.getServer().runCommand("execute at @p run summon minecraft:pig ~" + at[0] + " ~ ~" + at[1]);
			}
			mode(world, RingMode.PUSH);
			camera(ctx, CameraType.THIRD_PERSON_BACK);
			ctx.getInput().lookAt(0f, 30f);
			ctx.waitTicks(10);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(4);
			ctx.takeScreenshot("shockwave_growing");
			ctx.waitTicks(5);
			ctx.takeScreenshot("shockwave_full");
			ctx.waitTicks(10);
			ctx.takeScreenshot("shockwave_after");

			// From outside: a dome drawn 14 blocks ahead, so the whole glass shell is in view.
			ctx.getInput().lookAt(0f, 12f);
			ctx.waitTicks(2);
			ctx.runOnClient(mc -> LabFx.shockwave(mc.player.position().add(0, 0, 14)));
			ctx.waitTicks(5);
			ctx.takeScreenshot("shockwave_outside_growing");
			ctx.waitTicks(5);
			ctx.takeScreenshot("shockwave_outside_full");

			// Again in first person, into a hill: the dome should be clear glass with a bright seam
			// where it cuts into the stone and the ground.
			hill(world);
			camera(ctx, CameraType.FIRST_PERSON);
			ctx.getInput().lookAt(0f, 10f);
			ctx.waitTicks(40);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(7);
			ctx.takeScreenshot("shockwave_fp_hill");
			camera(ctx, CameraType.FIRST_PERSON);

			anvil(ctx, world);
			lasso(ctx, world);
			flight(ctx, world);
		}
	}

	/**
	 * Anvil: aim the glowing marker on a stone plateau at night, let go, watch the anvil build bright,
	 * cool to jade, fall and smash its crater.
	 */
	private static void anvil(ClientGameTestContext ctx, TestSingleplayerContext world) {
		world.getServer().runCommand("time set 18000");
		world.getServer().runCommand("kill @e[type=minecraft:pig]");
		world.getServer().runCommand("execute at @p run fill ~-16 ~ ~-6 ~16 ~16 ~34 air");
		world.getServer().runCommand("execute at @p run fill ~-16 ~ ~-6 ~16 ~7 ~34 stone");
		world.getServer().runCommand("execute at @p run fill ~-16 ~7 ~-6 ~16 ~7 ~34 grass_block");
		for (int[] at : new int[][] {{3, 12}, {-2, 14}, {1, 9}}) {
			world.getServer().runCommand("execute at @p run summon minecraft:pig ~" + at[0] + " ~8 ~" + at[1]);
		}
		world.getServer().runCommand("execute at @p run tp @p ~ ~8 ~");
		mode(world, RingMode.ANVIL);
		camera(ctx, CameraType.THIRD_PERSON_BACK);
		ctx.getInput().lookAt(0f, 8f);
		ctx.waitTicks(20);
		// Left-click aims the Anvil.
		ctx.getInput().holdKey(o -> o.keyAttack);
		ctx.waitTicks(10);
		ctx.takeScreenshot("anvil_marker");
		ctx.getInput().lookAt(15f, 10f);
		ctx.waitTicks(6);
		ctx.takeScreenshot("anvil_marker_moved");
		ctx.getInput().lookAt(0f, 8f);
		ctx.waitTicks(4);
		ctx.getInput().releaseKey(o -> o.keyAttack);
		ctx.getInput().lookAt(0f, -10f);
		ctx.waitTicks(Math.max(1, RingTuning.ANVIL_BUILD.ticks() / 2));
		ctx.takeScreenshot("anvil_building");
		ctx.waitTicks(Math.max(1, RingTuning.ANVIL_BUILD.ticks() / 2) + 2);
		ctx.takeScreenshot("anvil_built_bright");
		for (int i = 0; i < 8; i++) {
			ctx.waitTicks(4);
			ctx.takeScreenshot("anvil_drop_" + i);
		}
		ctx.getInput().lookAt(0f, 25f);
		ctx.waitTicks(30);
		ctx.takeScreenshot("anvil_crater");
		world.getServer().runCommand("time set 6000");
		ctx.waitTicks(10);
		ctx.takeScreenshot("anvil_crater_day");
		camera(ctx, CameraType.FIRST_PERSON);
		ctx.getInput().lookAt(0f, 40f);
		ctx.waitTicks(10);
		ctx.takeScreenshot("anvil_crater_fp");

		// Right-click twice: 5x. Drop one further out and watch it from above.
		world.getServer().runCommand("time set 18000");
		camera(ctx, CameraType.THIRD_PERSON_BACK);
		for (int i = 0; i < 2; i++) {
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(5);
		}
		ctx.takeScreenshot("anvil5_size_message");
		world.getServer().runCommand("execute at @p run tp @p ~ ~20 ~-20");
		ctx.getInput().lookAt(0f, 30f);
		ctx.waitTicks(20);
		ctx.getInput().holdKey(o -> o.keyAttack);
		ctx.waitTicks(10);
		ctx.takeScreenshot("anvil5_marker");
		ctx.getInput().releaseKey(o -> o.keyAttack);
		ctx.waitTicks(RingTuning.ANVIL_BUILD.ticks() * 3 + 2);
		ctx.takeScreenshot("anvil5_built");
		for (int i = 0; i < 6; i++) {
			ctx.waitTicks(6);
			ctx.takeScreenshot("anvil5_drop_" + i);
		}
		ctx.waitTicks(80);
		world.getServer().runCommand("time set 6000");
		ctx.waitTicks(10);
		ctx.takeScreenshot("anvil5_crater_day");
	}

	/**
	 * Lasso: catch a pig 10 blocks away and reel it in, swing it and throw it. Then catch another,
	 * push it out with left-click (it should stay out there), and smash it into the ground. Then push
	 * one far out past the old 64-block limit, bowl a row of pigs over, fly with a catch, and gather a
	 * group with a double-click.
	 */
	private static void lasso(ClientGameTestContext ctx, TestSingleplayerContext world) {
		world.getServer().runCommand("time set 18000");
		world.getServer().runCommand("execute at @p run fill ~-20 ~ ~-20 ~20 ~12 ~20 air");
		world.getServer().runCommand("kill @e[type=minecraft:pig]");
		world.getServer().runCommand("execute at @p run summon minecraft:pig ~ ~ ~10 {NoAI:1b}");
		mode(world, RingMode.TETHER);
		camera(ctx, CameraType.THIRD_PERSON_BACK);
		ctx.getInput().lookAt(0f, 6f);
		ctx.waitTicks(10);
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(3);
		ctx.takeScreenshot("lasso_caught");
		ctx.waitTicks(25);
		ctx.takeScreenshot("lasso_reeled_in");
		ctx.getInput().lookAt(70f, -10f);
		ctx.waitTicks(2);
		ctx.takeScreenshot("lasso_swinging");
		ctx.waitTicks(10);
		// A fast swing back, then let go mid-swing: the bubble flies off and pops where it lands.
		ctx.getInput().lookAt(0f, -25f);
		ctx.waitTicks(2);
		ctx.getInput().releaseKey(o -> o.keyUse);
		ctx.waitTicks(4);
		ctx.takeScreenshot("lasso_thrown");
		ctx.waitTicks(12);
		ctx.takeScreenshot("lasso_thrown_later");
		ctx.waitTicks(40);

		world.getServer().runCommand("kill @e[type=minecraft:pig]");
		world.getServer().runCommand("execute at @p run summon minecraft:pig ~ ~ ~6 {NoAI:1b}");
		ctx.getInput().lookAt(0f, 10f);
		ctx.waitTicks(10);
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(15);
		// Holding left-click pushes it out, faster and faster; let go and it stays out there.
		ctx.getInput().holdKey(o -> o.keyAttack);
		ctx.waitTicks(20);
		ctx.getInput().releaseKey(o -> o.keyAttack);
		ctx.waitTicks(3);
		ctx.takeScreenshot("lasso_pushed_out");
		ctx.waitTicks(20);
		ctx.takeScreenshot("lasso_stays_out");
		ctx.getInput().lookAt(0f, 75f);
		ctx.waitTicks(15);
		ctx.takeScreenshot("lasso_smashed_down");
		ctx.getInput().releaseKey(o -> o.keyUse);
		ctx.waitTicks(20);

		// No more 64-block limit: hold left-click for three seconds and it goes way out.
		world.getServer().runCommand("kill @e[type=minecraft:pig]");
		world.getServer().runCommand("execute at @p run fill ~-6 ~ ~ ~6 ~12 ~120 air");
		world.getServer().runCommand("execute at @p run summon minecraft:pig ~ ~ ~6 {NoAI:1b}");
		ctx.getInput().lookAt(0f, 10f);
		ctx.waitTicks(10);
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(15);
		ctx.getInput().holdKey(o -> o.keyAttack);
		ctx.waitTicks(60);
		ctx.getInput().releaseKey(o -> o.keyAttack);
		ctx.getInput().lookAt(0f, -5f);
		ctx.waitTicks(5);
		ctx.takeScreenshot("lasso_far_out");
		ctx.getInput().releaseKey(o -> o.keyUse);
		ctx.waitTicks(20);

		// Bowling: swing a caught pig into a row of pigs and throw it through them.
		world.getServer().runCommand("kill @e[type=minecraft:pig]");
		world.getServer().runCommand("execute at @p run summon minecraft:pig ~ ~ ~5 {NoAI:1b}");
		for (double yaw : new double[] {25, 40, 55}) {
			double rad = Math.toRadians(yaw);
			world.getServer().runCommand(String.format(java.util.Locale.ROOT, "execute at @p run summon minecraft:pig ~%.2f ~ ~%.2f {NoAI:1b}",
					-4.2 * Math.sin(rad), 4.2 * Math.cos(rad)));
		}
		camera(ctx, CameraType.FIRST_PERSON);
		ctx.getInput().lookAt(0f, 15f);
		ctx.waitTicks(10);
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(15);
		ctx.takeScreenshot("lasso_bubble_close");
		ctx.getInput().lookAt(-40f, 15f);
		ctx.waitTicks(10);
		ctx.getInput().lookAt(70f, 15f);
		ctx.waitTicks(2);
		ctx.getInput().releaseKey(o -> o.keyUse);
		ctx.waitTicks(3);
		ctx.takeScreenshot("lasso_bowling");
		ctx.waitTicks(10);
		ctx.takeScreenshot("lasso_bowling_after");
		ctx.waitTicks(30);

		// Flying with a catch: space rises (it doesn't toggle the reel), and sprint-flying is full speed.
		world.getServer().runCommand("kill @e[type=minecraft:pig]");
		world.getServer().runCommand("execute at @p run summon minecraft:pig ~ ~ ~5 {NoAI:1b}");
		ctx.getInput().lookAt(0f, 15f);
		ctx.waitTicks(10);
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(10);
		double startY = ctx.computeOnClient(mc -> mc.player.getY());
		ctx.runOnClient(mc -> {
			mc.player.getAbilities().flying = true;
			mc.player.onUpdateAbilities();
		});
		camera(ctx, CameraType.THIRD_PERSON_BACK);
		ctx.getInput().holdKey(o -> o.keyJump);
		ctx.waitTicks(25);
		ctx.getInput().releaseKey(o -> o.keyJump);
		ctx.getInput().lookAt(0f, 0f);
		ctx.getInput().holdKey(o -> o.keyUp);
		ctx.getInput().holdKey(o -> o.keySprint);
		ctx.waitTicks(15);
		ctx.takeScreenshot("lasso_flying");
		ctx.getInput().releaseKey(o -> o.keySprint);
		ctx.getInput().releaseKey(o -> o.keyUp);
		double risen = ctx.computeOnClient(mc -> mc.player.getY()) - startY;
		boolean stillCaught = ctx.computeOnClient(mc -> mc.player.isUsingItem());
		System.out.println("[lasso test] rose " + risen + " blocks while holding a catch, still holding: " + stillCaught);
		if (risen < 3) throw new AssertionError("Couldn't fly up while holding a lasso catch (rose " + risen + ")");
		ctx.getInput().releaseKey(o -> o.keyUse);
		ctx.runOnClient(mc -> {
			mc.player.getAbilities().flying = false;
			mc.player.onUpdateAbilities();
		});
		ctx.waitTicks(40);

		// Double-click and hold: every pig around the aimed spot goes into one big bubble.
		world.getServer().runCommand("kill @e[type=minecraft:pig]");
		world.getServer().runCommand("execute at @p run fill ~-8 ~-1 ~-8 ~8 ~-1 ~16 grass_block");
		world.getServer().runCommand("execute at @p run fill ~-8 ~ ~-8 ~8 ~12 ~16 air");
		for (int[] at : new int[][] {{0, 9}, {2, 10}, {-2, 8}, {1, 7}, {-1, 11}}) {
			world.getServer().runCommand("execute at @p run summon minecraft:pig ~" + at[0] + " ~ ~" + at[1] + " {NoAI:1b}");
		}
		world.getServer().runCommand("execute at @p run summon minecraft:pig ~6 ~ ~14 {NoAI:1b}");
		camera(ctx, CameraType.THIRD_PERSON_BACK);
		ctx.getInput().lookAt(0f, 12f);
		ctx.waitTicks(10);
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(2);
		ctx.getInput().releaseKey(o -> o.keyUse);
		ctx.waitTicks(2);
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(30);
		ctx.getInput().lookAt(0f, -10f);
		ctx.waitTicks(10);
		ctx.takeScreenshot("lasso_group");
		ctx.getInput().lookAt(40f, -10f);
		ctx.waitTicks(10);
		ctx.takeScreenshot("lasso_group_swing");
		ctx.getInput().releaseKey(o -> o.keyUse);
		ctx.waitTicks(4);
		ctx.takeScreenshot("lasso_group_thrown");
		ctx.waitTicks(40);
		camera(ctx, CameraType.FIRST_PERSON);
	}

	/** Ring flight poses from the front: hovering, a slow lean with trailing legs, and the sprint glide. */
	private static void flight(ClientGameTestContext ctx, TestSingleplayerContext world) {
		world.getServer().runCommand("time set 6000");
		world.getServer().runCommand("execute at @p run tp @p ~ ~20 ~");
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			p.getAbilities().flying = true;
			p.onUpdateAbilities();
		});
		ctx.runOnClient(mc -> mc.player.getAbilities().flying = true);
		ctx.getInput().lookAt(0f, 10f);
		camera(ctx, CameraType.THIRD_PERSON_FRONT);
		ctx.waitTicks(20);
		ctx.takeScreenshot("fly_hover");

		ctx.getInput().holdKey(o -> o.keyUp);
		ctx.waitTicks(15);
		ctx.takeScreenshot("fly_slow_forward");
		ctx.getInput().holdKey(o -> o.keyRight);
		ctx.waitTicks(10);
		ctx.takeScreenshot("fly_slow_strafe");
		ctx.getInput().releaseKey(o -> o.keyRight);

		ctx.getInput().holdKey(o -> o.keySprint);
		ctx.waitTicks(15);
		ctx.takeScreenshot("fly_fast_front");
		camera(ctx, CameraType.THIRD_PERSON_BACK);
		ctx.waitTicks(5);
		ctx.takeScreenshot("fly_fast_back");
		// The glide goes where you look: down in a dive, up in a climb.
		double before = playerY(ctx);
		ctx.getInput().lookAt(0f, 50f);
		ctx.waitTicks(10);
		ctx.takeScreenshot("fly_fast_dive");
		double dived = playerY(ctx);
		ctx.getInput().lookAt(0f, -45f);
		ctx.waitTicks(15);
		ctx.takeScreenshot("fly_fast_climb");
		System.out.println("[lanternring test] glide y: start " + before + ", after dive " + dived + ", after climb " + playerY(ctx));
		// Diving into the ground skims along it instead of landing like an elytra.
		ctx.getInput().lookAt(0f, 70f);
		ctx.waitTicks(60);
		camera(ctx, CameraType.THIRD_PERSON_BACK);
		ctx.waitTicks(5);
		ctx.takeScreenshot("fly_fast_skim");
		boolean stillFlying = ctx.computeOnClient(mc -> mc.player.getAbilities().flying);
		System.out.println("[lanternring test] glide into ground: y " + playerY(ctx) + ", still flying " + stillFlying);
		ctx.getInput().lookAt(0f, -45f);
		ctx.waitTicks(15);
		ctx.getInput().releaseKey(o -> o.keySprint);
		ctx.getInput().releaseKey(o -> o.keyUp);

		ctx.getInput().lookAt(0f, 10f);
		ctx.waitTicks(25);
		ctx.takeScreenshot("fly_stopped_back");

		// Firing snaps the ring arm to where you look, in the air and on the ground.
		mode(world, RingMode.BLAST);
		camera(ctx, CameraType.THIRD_PERSON_FRONT);
		ctx.getInput().lookAt(0f, -20f);
		ctx.waitTicks(10);
		ctx.getInput().pressKey(o -> o.keyUse);
		ctx.waitTicks(3);
		ctx.takeScreenshot("aim_flying");
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			p.getAbilities().flying = false;
			p.onUpdateAbilities();
		});
		ctx.runOnClient(mc -> mc.player.getAbilities().flying = false);
		ctx.waitTicks(80);
		ctx.getInput().lookAt(0f, 15f);
		ctx.waitTicks(25);
		ctx.getInput().pressKey(o -> o.keyUse);
		ctx.waitTicks(3);
		ctx.takeScreenshot("aim_ground");
		camera(ctx, CameraType.FIRST_PERSON);
		// The first-person ring arm points at the crosshair too (after Blast's cooldown).
		ctx.waitTicks(80);
		ctx.getInput().pressKey(o -> o.keyUse);
		ctx.waitTicks(3);
		System.out.println("[lanternring test] first-person point " + ctx.computeOnClient(mc -> FlightPoses.localPoint(0f)));
		System.out.println("[lanternring test] aim: " + RingFirstPerson.debug);
		ctx.takeScreenshot("aim_first_person");
		ctx.waitTicks(25);
		System.out.println("[lanternring test] after aim: " + RingFirstPerson.debug);
		ctx.takeScreenshot("aim_first_person_after");
		// Flying forward in first person, the ring leads the way.
		world.getServer().runCommand("execute at @p run tp @p ~ ~4 ~");
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			p.getAbilities().flying = true;
			p.onUpdateAbilities();
		});
		ctx.runOnClient(mc -> mc.player.getAbilities().flying = true);
		ctx.getInput().lookAt(0f, 0f);
		ctx.getInput().holdKey(o -> o.keyUp);
		ctx.waitTicks(20);
		System.out.println("[lanternring test] first-person flying point " + ctx.computeOnClient(mc -> FlightPoses.localPoint(0f)));
		ctx.takeScreenshot("fly_first_person");
		ctx.getInput().releaseKey(o -> o.keyUp);
		ctx.runOnClient(mc -> mc.player.getAbilities().flying = false);
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			p.getAbilities().flying = false;
			p.onUpdateAbilities();
		});
		ctx.waitTicks(60);
	}

	private static double playerY(ClientGameTestContext ctx) {
		return ctx.computeOnClient(mc -> mc.player.getY());
	}

	/** Fires one beam at a wall and photographs every tick of its life. */
	private static void beam(ClientGameTestContext ctx, TestSingleplayerContext world, LabSettings.UseFx fx, CameraType cam, String name) {
		targetWall(world);
		LabSettings.get().useFx = fx;
		mode(world, RingMode.BEAM);
		camera(ctx, cam);
		ctx.getInput().lookAt(0f, 0f);
		ctx.waitTicks(10);
		ctx.getInput().pressKey(o -> o.keyUse);
		for (int i = 1; i <= 9; i++) {
			ctx.waitTick();
			ctx.takeScreenshot(name + "_" + i);
		}
		ctx.waitTicks(20);
	}

	/** Holds right-click in Beam mode until the charged shot fires, photographing it hit the wall. */
	private static void chargedBeam(ClientGameTestContext ctx, TestSingleplayerContext world) {
		targetWall(world);
		LabSettings.get().useFx = LabSettings.UseFx.HELIX;
		mode(world, RingMode.BEAM);
		camera(ctx, CameraType.FIRST_PERSON);
		ctx.getInput().lookAt(0f, 0f);
		ctx.waitTicks(10);
		ctx.getInput().holdKey(o -> o.keyUse);
		ctx.waitTicks(RingTuning.BEAM_CHARGE.ticks() - 4);
		ctx.takeScreenshot("beam_charging");
		for (int i = 1; i <= 8; i++) {
			ctx.waitTicks(2);
			ctx.takeScreenshot("beam_charged_fp_" + i);
		}
		ctx.getInput().releaseKey(o -> o.keyUse);
		ctx.waitTicks(30);
	}

	/**
	 * Draws a beam across the view from left to right, so the way it grows and unravels is seen
	 * side-on (a real shot runs along the view and hides its length).
	 */
	private static void beamSideOn(ClientGameTestContext ctx, LabSettings.UseFx fx, String name) {
		LabSettings.get().useFx = fx;
		camera(ctx, CameraType.FIRST_PERSON);
		ctx.getInput().lookAt(0f, 0f);
		ctx.waitTicks(10);
		ctx.runOnClient(mc -> {
			Vec3 eye = mc.player.getEyePosition();
			LabFx.useLine(eye.add(-7, -0.5, 9), eye.add(7, -0.5, 9), true);
		});
		for (int i = 1; i <= 9; i++) {
			ctx.waitTick();
			ctx.takeScreenshot(name + "_" + i);
		}
		ctx.waitTicks(20);
	}

	private static void camera(ClientGameTestContext ctx, CameraType type) {
		ctx.runOnClient(mc -> mc.options.setCameraType(type));
	}

	private static void mode(TestSingleplayerContext world, RingMode mode) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			p.getMainHandItem().set(ModComponents.MODE, mode.ordinal());
		});
	}

	/** A stone wall 22 blocks in front of the player, far enough to watch the beam travel. */
	private static void targetWall(TestSingleplayerContext world) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			BlockPos feet = p.blockPosition();
			for (int x = -4; x <= 4; x++)
				for (int y = -1; y < 7; y++)
					p.level().setBlockAndUpdate(feet.offset(x, y, 22), Blocks.STONE.defaultBlockState());
		});
	}

	/** A 13x8x12 stone hill (with a bedrock pillar) a few blocks in front of the player (+Z). */
	private static void hill(TestSingleplayerContext world) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			BlockPos feet = p.blockPosition();
			var level = p.level();
			for (int x = -6; x <= 6; x++)
				for (int y = 0; y < 8; y++)
					for (int z = 4; z < 16; z++)
						level.setBlockAndUpdate(feet.offset(x, y, z), (x == 0 && z == 6) ? Blocks.BEDROCK.defaultBlockState()
								: (y + z) % 5 == 0 ? Blocks.DIRT.defaultBlockState() : Blocks.STONE.defaultBlockState());
		});
	}
}
