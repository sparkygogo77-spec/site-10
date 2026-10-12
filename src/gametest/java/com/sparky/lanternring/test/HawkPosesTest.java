package com.sparky.lanternring.test;

import com.sparky.lanternring.corps.DivingHawk;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;

/** The diving hawk's model close up in each pose (perch, glide, flap, stoop) from the side, front and above. */
public class HawkPosesTest implements FabricClientGameTest {
	private static final String[] NAMES = {"perch", "glide", "flap", "stoop"};
	private static final float[][] POSES = {{0, 0, 1, DivingHawk.PERCH_PITCH}, {0, 0, 0, 0}, {1, 0, 0, -10}, {0, 1, 0, 60}};

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			var server = world.getServer();
			server.runCommand("gamemode spectator @a");
			server.runCommand("gamerule doDaylightCycle false");
			server.runCommand("gamerule doMobSpawning false");
			server.runCommand("time set 6000");
			ctx.waitTicks(40);
			server.runCommand("execute at @p run fill ~-10 ~-1 ~-10 ~10 ~-1 ~10 white_concrete");
			server.runCommand("execute at @p run fill ~-10 ~ ~-10 ~10 ~10 ~10 air");
			server.runCommand("kill @e[type=!player]");
			server.runCommand("execute at @p run summon lanternring:diving_hawk ~ ~1 ~ {NoAI:1b,NoGravity:1b,Rotation:[0f,0f]}");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			for (int p = 0; p < POSES.length; p++) {
				float[] pose = POSES[p];
				ctx.runOnClient(mc -> mc.level.entitiesForRendering().forEach(e -> {
					if (e instanceof DivingHawk h) h.previewPose = pose;
				}));
				// Side (hawk faces south, camera to its east looking west), front, above-behind.
				view(ctx, server, "~4 ~1.5 ~", 90f, 8f);
				ctx.takeScreenshot("hawk_" + NAMES[p] + "_side");
				view(ctx, server, "~ ~1.8 ~4.5", 180f, 10f);
				ctx.takeScreenshot("hawk_" + NAMES[p] + "_front");
				view(ctx, server, "~-2.5 ~4.5 ~-3", -35f, 45f);
				ctx.takeScreenshot("hawk_" + NAMES[p] + "_above");
			}
		}
	}

	private static void view(ClientGameTestContext ctx, net.fabricmc.fabric.api.client.gametest.v1.context.TestServerContext server, String at, float yaw, float pitch) {
		server.runCommand("execute as @e[type=lanternring:diving_hawk,limit=1] at @s run tp @p " + at + " " + yaw + " " + pitch);
		ctx.waitTicks(12);
	}
}
