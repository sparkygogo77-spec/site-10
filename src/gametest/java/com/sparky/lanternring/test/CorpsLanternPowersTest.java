package com.sparky.lanternring.test;

import com.mojang.blaze3d.platform.InputConstants;
import com.sparky.lanternring.BlueBeacon;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.GreenFortress;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.VioletCharm;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.monster.zombie.Zombie;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CropBlock;

/**
 * The Green, Blue and Violet lanterns' own powers (hold R with the lantern summoned): the Green
 * fortress dome rises while R is held and comes down when it's let go, the Blue hope beacon grows
 * wheat around you, and the Violet love charm makes a zombie forget you.
 */
public class CorpsLanternPowersTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = player(server);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.GREEN.ring());
				p.setItemInHand(InteractionHand.OFF_HAND, Corps.GREEN.lantern());
			});
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, -10f);

			// Green: hold R and the fortress rises; let go and it comes down.
			LanternSlotTest.crouchR(ctx);
			ctx.waitTicks(25);
			ctx.getInput().holdKey(InputConstants.KEY_R);
			ctx.waitTicks(14);
			ctx.takeScreenshot("green_fortress_rising");
			ctx.waitTicks(40);
			ctx.takeScreenshot("green_fortress_up");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(0f, 30f);
			ctx.waitTicks(2);
			ctx.takeScreenshot("green_fortress_third_person");
			int blocks = world.getServer().computeOnServer(server -> count(player(server)));
			boolean standing = world.getServer().computeOnServer(server -> GreenFortress.standing(player(server)));
			System.out.println("[corps-lantern-powers] fortress blocks=" + blocks);
			if (!standing || blocks < 150) throw new AssertionError("Holding R should raise the fortress, found " + blocks + " blocks");
			ctx.getInput().releaseKey(InputConstants.KEY_R);
			ctx.waitTicks(40);
			int after = world.getServer().computeOnServer(server -> count(player(server)));
			System.out.println("[corps-lantern-powers] after release=" + after);
			if (after > 0) throw new AssertionError("Letting go of R should take the fortress down, " + after + " left");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 30f);

			// Blue: wheat seedlings around you grow under the beacon.
			LanternSlotTest.crouchR(ctx);
			ctx.waitTicks(25);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = player(server);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.BLUE.ring());
				p.setItemInHand(InteractionHand.OFF_HAND, Corps.BLUE.lantern());
				ServerLevel level = p.level();
				BlockPos feet = p.blockPosition();
				for (int dx = -4; dx <= 4; dx++) {
					for (int dz = 2; dz <= 6; dz++) {
						BlockPos crop = feet.offset(dx, 0, dz);
						level.setBlockAndUpdate(crop.below(), Blocks.FARMLAND.defaultBlockState());
						level.setBlockAndUpdate(crop, Blocks.WHEAT.defaultBlockState());
					}
				}
			});
			LanternSlotTest.crouchR(ctx);
			ctx.waitTicks(25);
			ctx.getInput().holdKey(InputConstants.KEY_R);
			ctx.waitTicks(14);
			ctx.getInput().releaseKey(InputConstants.KEY_R);
			ctx.waitTicks(200);
			ctx.takeScreenshot("blue_hope_beacon");
			int grown = world.getServer().computeOnServer(server -> {
				ServerPlayer p = player(server);
				int n = 0;
				BlockPos feet = p.blockPosition();
				for (int dx = -4; dx <= 4; dx++) {
					for (int dz = 2; dz <= 6; dz++) {
						var s = p.level().getBlockState(feet.offset(dx, 0, dz));
						if (s.is(Blocks.WHEAT) && s.getValue(CropBlock.AGE) > 1) n++;
					}
				}
				return n;
			});
			boolean lit = world.getServer().computeOnServer(server -> BlueBeacon.lit(player(server)));
			System.out.println("[corps-lantern-powers] wheat grown=" + grown + " lit=" + lit);
			if (!lit || grown < 5) throw new AssertionError("The hope beacon should grow the wheat, " + grown + " grew");

			// Violet: a zombie that was after you forgets you.
			LanternSlotTest.crouchR(ctx);
			ctx.waitTicks(25);
			int zombie = world.getServer().computeOnServer(server -> {
				ServerPlayer p = player(server);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.VIOLET.ring());
				p.setItemInHand(InteractionHand.OFF_HAND, Corps.VIOLET.lantern());
				Zombie z = EntityTypes.ZOMBIE.create(p.level(), EntitySpawnReason.COMMAND);
				z.setPos(p.getX() + 5, p.getY(), p.getZ() + 5);
				p.level().addFreshEntity(z);
				z.setTarget(p);
				return z.getId();
			});
			LanternSlotTest.crouchR(ctx);
			ctx.waitTicks(25);
			ctx.getInput().holdKey(InputConstants.KEY_R);
			ctx.waitTicks(14);
			ctx.getInput().releaseKey(InputConstants.KEY_R);
			ctx.waitTicks(30);
			ctx.takeScreenshot("violet_love_charm");
			boolean calm = world.getServer().computeOnServer(server -> {
				var z = (Zombie) player(server).level().getEntity(zombie);
				return z != null && VioletCharm.charmed(z) && z.getTarget() == null;
			});
			if (!calm) throw new AssertionError("The love charm should calm the zombie");
		}
	}

	private static int count(ServerPlayer p) {
		int n = 0;
		BlockPos c = p.blockPosition();
		for (BlockPos pos : BlockPos.betweenClosed(c.offset(-10, -2, -10), c.offset(10, 11, 10))) {
			if (p.level().getBlockState(pos).is(ModRegistry.LIGHT_CONSTRUCT)) n++;
		}
		return n;
	}

	private static ServerPlayer player(MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
