package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ally.ConstructAlly;
import com.sparky.lanternring.ally.FlyingConstruct;
import com.sparky.lanternring.ally.ModEntities;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

/** Yellow Lantern army constructs in their own formations: Wardens as your shadow, Dragons as vultures, Sentries as watchers all round you. */
public class YellowArmyTest implements FabricClientGameTest {
	private static void summon(TestSingleplayerContext world, EntityType<? extends ConstructAlly> type, int count, double up) {
		world.getServer().runOnServer(server -> {
			ServerPlayer p = server.getPlayerList().getPlayers().get(0);
			Corps before = Corps.enter(Corps.YELLOW);
			for (int i = 0; i < count; i++) {
				ConstructAlly ally = type.create(p.level(), EntitySpawnReason.MOB_SUMMONED);
				Vec3 at = p.position().add(2 + i, up, 2);
				ally.snapTo(at.x, at.y, at.z, 0f, 0f);
				ally.setup(p, 20 * 120);
				if (ally instanceof FlyingConstruct f) f.setHome(p.position().add(0, up, 0));
				p.level().addFreshEntity(ally);
			}
			Corps.restore(before);
		});
	}

	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(60);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.YELLOW.ring());
				BlockPos o = p.blockPosition().above(10);
				for (BlockPos pos : BlockPos.betweenClosed(o.offset(-30, -3, -30), o.offset(30, 20, 30))) {
					p.level().setBlock(pos, pos.getY() < o.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				p.teleportTo(o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
			});
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));

			summon(world, ModEntities.WARDEN, 3, 0);
			ctx.getInput().lookAt(180f, 30f);
			ctx.waitTicks(100);
			ctx.takeScreenshot("yellow_wardens_shadow");
			// Walking: single file at your heels.
			ctx.getInput().lookAt(0f, 30f);
			ctx.getInput().holdKey(o -> o.keyUp);
			ctx.waitTicks(60);
			ctx.getInput().lookAt(180f, 25f);
			ctx.waitTicks(4);
			ctx.takeScreenshot("yellow_wardens_walking");
			ctx.getInput().releaseKey(o -> o.keyUp);
			world.getServer().runCommand("kill @e[type=lanternring:warden_construct]");

			summon(world, ModEntities.SENTRY, 3, 2);
			ctx.getInput().lookAt(0f, 35f);
			ctx.waitTicks(100);
			ctx.takeScreenshot("yellow_sentries_watchers");
			world.getServer().runCommand("kill @e[type=lanternring:sentry_construct]");

			summon(world, ModEntities.DRAGON, 2, 5);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, -60f);
			ctx.waitTicks(100);
			ctx.takeScreenshot("yellow_dragons_vultures");
		}
	}
}
