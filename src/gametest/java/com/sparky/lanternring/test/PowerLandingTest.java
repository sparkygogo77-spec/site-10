package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.client.LabSettings;
import com.sparky.lanternring.client.PowerSlide;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/**
 * J's power landing (Blender pass 400): a full super jump lands in the A3 dissolve slide (about 5
 * blocks, a 3-wide trench, stopping on solid ground), a half one with the plough picked in B2, and
 * a half one with dissolve picked stops dead (D0, the 8 blocks round the feet gone).
 */
public class PowerLandingTest implements FabricClientGameTest {
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
				p.setItemInHand(InteractionHand.MAIN_HAND, ring);
			});
			int x = o[0].getX(), y = o[0].getY(), z = o[0].getZ();
			server.runCommand(String.format("forceload add %d %d %d %d", x - 40, z - 40, x + 40, z + 110));
			server.runCommand(String.format("fill %d %d %d %d %d %d dirt", x - 40, y - 4, z - 40, x + 40, y - 1, z + 110));
			server.runCommand(String.format("fill %d %d %d %d %d %d grass_block", x - 40, y - 1, z - 40, x + 40, y - 1, z + 110));
			server.runCommand(String.format("fill %d %d %d %d %d %d air", x - 40, y, z - 40, x + 40, y + 40, z + 110));
			server.runCommand("kill @e[type=!player]");

			float dissolve = jump(ctx, world, o[0], 0, 95, "dissolve");
			ctx.runOnClient(mc -> LabSettings.get().landingSlide = LabSettings.LandingSlide.PLOUGH);
			float plough = jump(ctx, world, o[0], -20, 55, "plough");
			ctx.runOnClient(mc -> LabSettings.get().landingSlide = LabSettings.LandingSlide.DISSOLVE);
			float stop = jump(ctx, world, o[0], 20, 55, "stop");
			ctx.runOnClient(mc -> {
				LabSettings.get().landingSlide = LabSettings.LandingSlide.DISSOLVE;
				LabSettings.get().labTab = LabSettings.Group.LANDING;
				mc.setScreenAndShow(new com.sparky.lanternring.client.RingLabScreen(null));
			});
			ctx.waitTicks(5);
			ctx.takeScreenshot("power_ring_lab_landing_tab");
			ctx.runOnClient(mc -> {
				LabSettings.get().labTab = null;
				mc.setScreenAndShow(new com.sparky.lanternring.client.RingLabScreen(null));
			});
			ctx.waitTicks(3);
			ctx.takeScreenshot("power_ring_lab_all");
			ctx.runOnClient(mc -> mc.setScreenAndShow(null));
			System.out.println(String.format("[power landing] slides: dissolve %.2f plough %.2f stop %.2f", dissolve, plough, stop));
			if (dissolve < 3.5 || dissolve > 5.6 || plough < 1.5 || plough > 4.5 || stop > 0.6) {
				throw new AssertionError("power landing slides: dissolve=" + dissolve + " plough=" + plough + " stop=" + stop);
			}
		}
	}

	/** Sprints for sprint ticks from dx along x, super jumps north to south, and lands; returns how far it slid after touchdown. */
	private static float jump(ClientGameTestContext ctx, TestSingleplayerContext world, BlockPos o, int dx, int sprint, String name) {
		world.getServer().runOnServer(s -> s.getPlayerList().getPlayers().get(0).teleportTo(o.getX() + dx + 0.5, o.getY(), o.getZ() - 30.5));
		ctx.getInput().lookAt(0f, 0f);
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
		ctx.waitTicks(10);
		ctx.getInput().holdKey(opt -> opt.keyUp);
		ctx.getInput().holdKey(opt -> opt.keySprint);
		ctx.waitTicks(sprint);
		ctx.getInput().holdKey(opt -> opt.keyJump);
		ctx.waitTicks(2);
		ctx.getInput().releaseKey(opt -> opt.keyJump);
		ctx.getInput().releaseKey(opt -> opt.keySprint);
		// Hold forward through the air, as a player would.
		boolean landed = false;
		for (int t = 0; t < 240 && !landed; t++) {
			ctx.waitTick();
			landed = ctx.computeOnClient(mc -> PowerSlide.locked());
			if (t % 10 == 0) {
				final int at = t;
				ctx.runOnClient(mc -> System.out.println(String.format("[power landing] %s t=%d y=%.2f z=%.2f v=%.2f", name, at, mc.player.getY() - o.getY(),
						mc.player.getZ() - o.getZ(), mc.player.getDeltaMovement().horizontalDistance())));
			}
		}
		// Let go of forward at touchdown, so what follows is the landing's own movement.
		ctx.getInput().releaseKey(opt -> opt.keyUp);
		Vec3 touch = ctx.computeOnClient(mc -> mc.player.position());
		double[] speed = {0};
		ctx.runOnClient(mc -> speed[0] = mc.player.getDeltaMovement().horizontalDistance());
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
		ctx.waitTicks(2);
		ctx.takeScreenshot("power_" + name + "_impact");
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
		ctx.getInput().lookAt(0f, 35f);
		ctx.waitTicks(2);
		ctx.takeScreenshot("power_" + name + "_skid");
		ctx.waitTicks(4);
		ctx.takeScreenshot("power_" + name + "_halt");
		ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
		ctx.waitTicks(4);
		ctx.takeScreenshot("power_" + name + "_halt_front");
		ctx.waitTicks(12);
		ctx.takeScreenshot("power_" + name + "_after");
		Vec3 end = ctx.computeOnClient(mc -> mc.player.position());
		ctx.waitTicks(4);
		float slid = (float) Math.sqrt(Math.pow(end.x - touch.x, 2) + Math.pow(end.z - touch.z, 2));
		// The trench: air in the top layer under the slide's path.
		int[] holes = {0};
		world.getServer().runOnServer(s -> {
			var level = s.getPlayerList().getPlayers().get(0).level();
			BlockPos c = BlockPos.containing(touch.x, o.getY() - 1, touch.z);
			for (BlockPos q : BlockPos.betweenClosed(c.offset(-2, 0, -2), c.offset(2, 0, 7))) if (level.getBlockState(q).isAir()) holes[0]++;
		});
		boolean onGround = ctx.computeOnClient(mc -> mc.player.onGround());
		System.out.println(String.format("[power landing] %s: touchdown (%.2f, %.2f, %.2f) speed %.2f, slid %.2f, holes %d, on ground %s, end y %.2f", name,
				touch.x - o.getX(), touch.y - o.getY(), touch.z - o.getZ(), speed[0], slid, holes[0], onGround, end.y - o.getY()));
		return slid;
	}
}
