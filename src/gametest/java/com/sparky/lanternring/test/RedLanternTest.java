package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.ModFluids;
import com.sparky.lanternring.RingMode;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.animal.pig.Pig;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;

/** The Red Lantern ring: the ring and lantern in hand, a red Wall and Dome, then a Lava Deluge that burns and sinks. */
public class RedLanternTest implements FabricClientGameTest {
	private static void report(TestSingleplayerContext world, BlockPos o, String when) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			var level = p.level();
			int lava = 0, magma = 0, burning = 0, below = 0;
			for (BlockPos pos : BlockPos.betweenClosed(o.offset(-30, -8, -10), o.offset(30, 16, 50))) {
				var fluid = level.getFluidState(pos);
				if (fluid.getType() == ModFluids.EMBER_SOURCE || fluid.getType() == ModFluids.EMBER_FLOWING) {
					lava++;
					if (pos.getY() < o.getY()) below++;
				}
				if (level.getBlockState(pos).is(Blocks.NETHER_WART_BLOCK)) magma++;
			}
			for (Pig pig : level.getEntitiesOfClass(Pig.class, new AABB(o).inflate(40))) {
				if (pig.isOnFire()) burning++;
			}
			System.out.println("[red] " + when + ": ember=" + lava + " sunkBelowGround=" + below + " magma=" + magma + " burningPigs=" + burning);
		});
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));

			BlockPos[] origin = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.RED.ring());
				p.setItemInHand(InteractionHand.OFF_HAND, Corps.RED.lantern());
				BlockPos o = p.blockPosition().above(10);
				origin[0] = o;
				var level = p.level();
				for (int x = -30; x <= 30; x++)
					for (int y = -6; y <= 24; y++)
						for (int z = -10; z <= 50; z++) {
							level.setBlock(o.offset(x, y, z), y < -3 ? Blocks.STONE.defaultBlockState()
									: y < -1 ? Blocks.DIRT.defaultBlockState()
									: y == -1 ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
						}
				p.teleportTo(o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
			});
			ctx.getInput().lookAt(0f, 10f);
			ctx.waitTicks(30);
			ctx.takeScreenshot("red_ring_and_lantern");
			// The wearer's red rage outline, seen from the front, by day and by night.
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.waitTicks(10);
			ctx.takeScreenshot("red_rage_glow");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("red_rage_glow_night");
			// The green ring's wearer glows green.
			world.getServer().runOnServer(server -> server.getPlayerList().getPlayers().get(0).setItemInHand(InteractionHand.MAIN_HAND, Corps.GREEN.ring()));
			ctx.waitTicks(10);
			ctx.takeScreenshot("green_ring_glow_night");
			world.getServer().runOnServer(server -> server.getPlayerList().getPlayers().get(0).setItemInHand(InteractionHand.MAIN_HAND, Corps.RED.ring()));
			world.getServer().runCommand("time set 6000");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));

			// A red Wall.
			world.getServer().runOnServer(server -> server.getPlayerList().getPlayers().get(0).getMainHandItem()
					.set(ModComponents.MODE, RingMode.WALL.ordinal()));
			ctx.waitTicks(5);
			ctx.getInput().pressKey(o -> o.keyUse);
			ctx.waitTicks(20);
			ctx.takeScreenshot("red_wall");
			world.getServer().runCommand("kill @e[type=!player]");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos o = origin[0];
				for (BlockPos pos : BlockPos.betweenClosed(o.offset(-12, 0, -12), o.offset(12, 12, 12))) {
					if (!p.level().getBlockState(pos).isAir()) p.level().setBlock(pos, Blocks.AIR.defaultBlockState(), 2);
				}
				p.getMainHandItem().set(ModComponents.MODE, RingMode.DOME.ordinal());
				p.teleportTo(o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
			});
			ctx.waitTicks(10);

			// A red Dome, seen from inside.
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(25);
			ctx.takeScreenshot("red_dome_inside");
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.waitTicks(10);

			// The Lava Deluge, level 2, onto pigs in a field.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos o = origin[0];
				p.teleportTo(o.getX() + 0.5, o.getY() + 5, o.getZ() - 6.5);
				p.getAbilities().flying = true;
				p.onUpdateAbilities();
				p.getMainHandItem().set(ModComponents.MODE, RingMode.DELUGE.ordinal());
				p.getMainHandItem().set(ModComponents.DELUGE_LEVEL, 1);
			});
			for (int[] at : new int[][] {{4, 16}, {-6, 20}, {8, 24}, {-10, 14}, {0, 26}}) {
				world.getServer().runCommand("summon minecraft:pig " + (origin[0].getX() + at[0]) + " " + origin[0].getY() + " " + (origin[0].getZ() + at[1]));
			}
			ctx.getInput().lookAt(0f, 16f);
			ctx.waitTicks(20);
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(12);
			ctx.takeScreenshot("red_deluge_marker");
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.getInput().lookAt(0f, -5f);
			ctx.waitTicks(14);
			ctx.takeScreenshot("red_deluge_globe");
			ctx.getInput().lookAt(0f, 16f);
			for (int i = 0; i < 6; i++) {
				ctx.waitTicks(4);
				ctx.takeScreenshot("red_deluge_burst_" + i);
			}
			ctx.waitTicks(30);
			report(world, origin[0], "flooded");
			ctx.takeScreenshot("red_deluge_flood");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("red_deluge_flood_night");
			world.getServer().runCommand("time set 6000");

			// Level 2 lasts 20 s from the burst; it sinks as it drains at the end.
			ctx.waitTicks(20 * 12);
			report(world, origin[0], "16s");
			ctx.takeScreenshot("red_deluge_16s");
			ctx.waitTicks(20 * 3);
			report(world, origin[0], "19s");
			ctx.takeScreenshot("red_deluge_sinking");
			ctx.waitTicks(20 * 4);
			report(world, origin[0], "23s");
			ctx.takeScreenshot("red_deluge_scorched_pit");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(0f, 40f);
			ctx.waitTicks(10);
			ctx.takeScreenshot("red_deluge_pit_above");

			// The Flame Ring: on fresh grass, a ring of mobs around the bearer melt down into the fire.
			world.getServer().runCommand("kill @e[type=!player]");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos o = origin[0].offset(0, 0, 40);
				var level = p.level();
				for (BlockPos pos : BlockPos.betweenClosed(o.offset(-18, -2, -18), o.offset(18, 8, 18))) {
					level.setBlock(pos, pos.getY() < o.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				p.getAbilities().flying = false;
				p.onUpdateAbilities();
				p.teleportTo(o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
				p.getMainHandItem().set(ModComponents.MODE, RingMode.INFERNO.ordinal());
			});
			BlockPos ring = origin[0].offset(0, 0, 40);
			String[] mobs = {"zombie", "pig", "skeleton", "cow", "creeper", "sheep", "zombie", "pig"};
			for (int i = 0; i < 16; i++) {
				double a = i * Math.PI / 8;
				double d = 4 + (i % 4) * 2.5;
				world.getServer().runCommand("summon minecraft:" + mobs[i % mobs.length] + " " + (ring.getX() + 0.5 + Math.cos(a) * d) + " " + ring.getY()
						+ " " + (ring.getZ() + 0.5 + Math.sin(a) * d) + " {NoAI:1b}");
			}
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(0f, 35f);
			ctx.waitTicks(20);
			ctx.takeScreenshot("red_flame_ring_before");
			ctx.getInput().pressKey(o -> o.keyUse);
			for (int i = 0; i < 6; i++) {
				ctx.waitTicks(6);
				ctx.takeScreenshot("red_flame_ring_" + i);
			}
			ctx.waitTicks(40);
			world.getServer().runOnServer(server -> {
				var level = server.getPlayerList().getPlayers().get(0).level();
				int left = level.getEntitiesOfClass(net.minecraft.world.entity.Mob.class, new AABB(ring).inflate(20)).size();
				System.out.println("[red] flame ring: mobs left=" + left);
			});
			ctx.takeScreenshot("red_flame_ring_after");
		}
	}
}
