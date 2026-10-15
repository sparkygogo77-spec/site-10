package com.sparky.lanternring.test;

import com.mojang.blaze3d.platform.InputConstants;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.UltimateDome;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.animal.cow.Cow;

/**
 * The Green Lantern's ultimate dome (pass 835 D1): look up and hold R with the green lantern out, a beam goes up,
 * the dome forms top-down and bottom-up, and once it's closed a cow can't walk through it.
 */
public class UltimateDomeTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 13000");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = player(server);
				p.setItemInHand(InteractionHand.MAIN_HAND, Corps.GREEN.ring());
				p.setItemInHand(InteractionHand.OFF_HAND, Corps.GREEN.lantern());
			});
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.runOnClient(mc -> mc.options.renderDistance().set(8));
			LanternSlotTest.crouchR(ctx);
			ctx.waitTicks(25);
			ctx.getInput().lookAt(0f, -70f);
			ctx.waitTicks(2);
			ctx.getInput().holdKey(InputConstants.KEY_R);
			ctx.waitTicks(14);
			ctx.getInput().releaseKey(InputConstants.KEY_R);
			boolean up = world.getServer().computeOnServer(server -> UltimateDome.standing(player(server)));
			if (!up) throw new AssertionError("Looking up and holding R with the green lantern should start the ultimate dome");
			ctx.waitTicks(22);
			ctx.takeScreenshot("ultimate_dome_beam");
			ctx.waitTicks(46);
			ctx.takeScreenshot("ultimate_dome_forming_up");
			ctx.getInput().lookAt(0f, -15f);
			ctx.waitTicks(60);
			ctx.takeScreenshot("ultimate_dome_forming");
			ctx.waitTicks(100);
			ctx.takeScreenshot("ultimate_dome_closed");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(0f, -35f);
			ctx.waitTicks(3);
			ctx.takeScreenshot("ultimate_dome_closed_third_person");

			// A cow stepping across the closed shell (from outside to inside) is put back outside.
			double[] placed = world.getServer().computeOnServer(server -> {
				ServerPlayer p = player(server);
				Cow z = EntityTypes.COW.create(p.level(), EntitySpawnReason.COMMAND);
				z.setNoAi(true);
				double a = Math.toRadians(40), r = UltimateDome.RADIUS + 1.5;
				z.setPos(p.getX() + Math.sin(a) * r, p.getY() + Math.cos(a) * r - z.getBbHeight() / 2, p.getZ());
				if (!p.level().addFreshEntity(z)) throw new AssertionError("Couldn't add the cow");
				return new double[] {z.getId()};
			});
			// Put it just outside the shell on its upper slope, let the dome see it there, then step it inside.
			world.getServer().runOnServer(server -> move(player(server), (int) placed[0], UltimateDome.RADIUS + 1.5));
			ctx.waitTicks(3);
			world.getServer().runOnServer(server -> move(player(server), (int) placed[0], UltimateDome.RADIUS - 2.5));
			ctx.waitTick();
			double dist = world.getServer().computeOnServer(server -> {
				ServerPlayer p = player(server);
				var z = p.level().getEntity((int) placed[0]);
				return z == null ? -1 : z.position().add(0, z.getBbHeight() / 2, 0).distanceTo(p.position());
			});
			System.out.println("[ultimate-dome] cow distance after crossing=" + dist);
			if (dist >= 0 && dist < UltimateDome.RADIUS) throw new AssertionError("The closed dome should keep the cow out, it is " + dist + " from the centre");
		}
	}

	private static void move(ServerPlayer p, int id, double r) {
		var z = p.level().getEntity(id);
		double a = Math.toRadians(40);
		z.setPos(p.getX() + Math.sin(a) * r, p.getY() + Math.cos(a) * r - z.getBbHeight() / 2, p.getZ());
	}

	private static ServerPlayer player(MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
