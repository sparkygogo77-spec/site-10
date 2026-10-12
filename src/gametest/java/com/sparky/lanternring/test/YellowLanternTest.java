package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.ModEffects;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.ally.BroodSpider;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;

/** The Yellow Lantern ring: the ring and lantern, a yellow Wall, Fear on a husk and pigs, the Brood, then Fear on yourself. */
public class YellowLanternTest implements FabricClientGameTest {
	private static void report(TestSingleplayerContext world, BlockPos o, String when) {
		world.getServer().runOnServer(server -> {
			var level = server.getPlayerList().getPlayers().get(0).level();
			AABB box = new AABB(o).inflate(40);
			int giants = 0, little = 0, feared = 0;
			for (BroodSpider s : level.getEntitiesOfClass(BroodSpider.class, box)) {
				if (s.isGiant()) giants++;
				else little++;
			}
			for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, box)) {
				if (e.hasEffect(ModEffects.FEAR)) feared++;
			}
			var husks = level.getEntitiesOfClass(Husk.class, box);
			System.out.println("[yellow] " + when + ": giant=" + giants + " spiderlings=" + little + " feared=" + feared
					+ " husks=" + husks.size() + (husks.isEmpty() ? "" : " huskHealth=" + husks.getFirst().getHealth()));
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
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.YELLOW.ring());
				p.setItemInHand(InteractionHand.OFF_HAND, Corps.YELLOW.lantern());
				BlockPos o = p.blockPosition().above(10);
				origin[0] = o;
				var level = p.level();
				for (int x = -30; x <= 30; x++)
					for (int y = -4; y <= 16; y++)
						for (int z = -10; z <= 40; z++) {
							level.setBlock(o.offset(x, y, z), y < -1 ? Blocks.DIRT.defaultBlockState()
									: y == -1 ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
						}
				p.teleportTo(o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
			});
			BlockPos o = origin[0];
			ctx.getInput().lookAt(0f, 10f);
			ctx.waitTicks(30);
			ctx.takeScreenshot("yellow_ring_and_lantern");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.waitTicks(10);
			ctx.takeScreenshot("yellow_wearer");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));

			// A yellow Wall.
			world.getServer().runOnServer(server -> server.getPlayerList().getPlayers().get(0).getMainHandItem()
					.set(ModComponents.MODE, RingMode.WALL.ordinal()));
			ctx.waitTicks(5);
			ctx.getInput().pressKey(o2 -> o2.keyUse);
			ctx.waitTicks(20);
			ctx.takeScreenshot("yellow_wall");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				for (BlockPos pos : BlockPos.betweenClosed(o.offset(-12, 0, -2), o.offset(12, 12, 12))) {
					if (!p.level().getBlockState(pos).isAir()) p.level().setBlock(pos, Blocks.AIR.defaultBlockState(), 2);
				}
				p.getMainHandItem().set(ModComponents.MODE, RingMode.FEAR.ordinal());
			});

			// Fear on a husk with pigs round it.
			world.getServer().runCommand("summon minecraft:husk " + (o.getX() + 0.5) + " " + o.getY() + " " + (o.getZ() + 12.5) + " {PersistenceRequired:1b}");
			for (int[] at : new int[][] {{3, 14}, {-3, 13}, {2, 10}}) {
				world.getServer().runCommand("summon minecraft:pig " + (o.getX() + at[0] + 0.5) + " " + o.getY() + " " + (o.getZ() + at[1] + 0.5));
			}
			ctx.getInput().lookAt(0f, 3f);
			ctx.waitTicks(20);
			ctx.takeScreenshot("fear_before");
			ctx.getInput().pressKey(o2 -> o2.keyUse);
			ctx.waitTicks(10);
			ctx.takeScreenshot("fear_closing");
			ctx.waitTicks(30);
			ctx.takeScreenshot("fear_dark");
			report(world, o, "feared");

			// Again on the husk: the Brood.
			float[] aim = new float[2];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				var husk = p.level().getEntitiesOfClass(Husk.class, new AABB(o).inflate(40)).getFirst();
				// Hold it still so the shot can't miss.
				husk.teleportTo(o.getX() + 0.5, o.getY(), o.getZ() + 12.5);
				husk.getNavigation().stop();
				double dx = husk.getX() - p.getX(), dz = husk.getZ() - p.getZ(), dy = husk.getY() + 1 - p.getEyeY();
				aim[0] = (float) Math.toDegrees(Math.atan2(-dx, dz));
				aim[1] = (float) -Math.toDegrees(Math.atan2(dy, Math.sqrt(dx * dx + dz * dz)));
			});
			ctx.getInput().lookAt(aim[0], aim[1]);
			ctx.waitTicks(1);
			ctx.getInput().pressKey(o2 -> o2.keyUse);
			ctx.waitTicks(3);
			report(world, o, "brood called");
			ctx.takeScreenshot("brood_0");
			for (int i = 1; i <= 4; i++) {
				ctx.waitTicks(10);
				ctx.takeScreenshot("brood_" + i);
			}
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(0f, 30f);
			ctx.waitTicks(5);
			ctx.takeScreenshot("brood_above");
			world.getServer().runCommand("time set 18000");
			ctx.waitTicks(10);
			ctx.takeScreenshot("brood_night");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			report(world, o, "3s later");
			ctx.takeScreenshot("brood_later");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));

			// Fear on yourself: the view closes in.
			world.getServer().runCommand("kill @e[type=!player]");
			world.getServer().runCommand("summon minecraft:pig " + (o.getX() + 0.5) + " " + o.getY() + " " + (o.getZ() + 8.5));
			ctx.getInput().lookAt(0f, 8f);
			ctx.waitTicks(10);
			world.getServer().runCommand("effect give @a lanternring:fear 20");
			ctx.waitTicks(10);
			ctx.takeScreenshot("self_fear_closing");
			ctx.waitTicks(35);
			ctx.takeScreenshot("self_fear_dark");
			ctx.waitTicks(9);
			ctx.takeScreenshot("self_fear_eyes");
		}
	}
}
