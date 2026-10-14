package com.sparky.lanternring.test;

import com.sparky.lanternring.ChargeLight;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.LightLayer;

/**
 * The bearer becomes a sun while charging (J, 2026-10-14): photographs a dark night before, during
 * and after a lantern charge, and checks the ground round the bearer is lit to full block light out
 * to many blocks, and that the light is pulled back in once the charge ends.
 */
public class ChargeLightTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("weather clear");
			world.getServer().runCommand("time set 18000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			world.getServer().runCommand("item replace entity @a weapon.offhand with lanternring:power_battery");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			ctx.getInput().lookAt(30f, 25f);
			ctx.waitTicks(60);
			world.getServer().runOnServer(server -> PowerRingItem.setCharge(player(server).getMainHandItem(), 10));
			int farBefore = world.getServer().computeOnServer(server -> blockLight(player(server), 12));
			ctx.takeScreenshot("charge_light_before");

			ctx.getInput().holdKey(o -> o.keyAttack);
			ctx.waitTicks(1);
			ctx.getInput().holdKey(o -> o.keyUse);
			int contact = LanternCharge.hold() + LanternCharge.reach();
			ctx.waitTicks(contact + (LanternCharge.done() - contact) / 3);
			ctx.takeScreenshot("charge_light_building");
			ctx.waitTicks(LanternCharge.done() - (contact + (LanternCharge.done() - contact) / 3) - 2);
			ctx.takeScreenshot("charge_light_full");
			int lit = world.getServer().computeOnServer(server -> ChargeLight.lit(player(server).getUUID()));
			int near = world.getServer().computeOnServer(server -> blockLight(player(server), 0));
			int far = world.getServer().computeOnServer(server -> blockLight(player(server), 12));
			ctx.waitTicks(4);
			ctx.takeScreenshot("charge_light_burst");
			ctx.getInput().releaseKey(o -> o.keyUse);
			ctx.getInput().releaseKey(o -> o.keyAttack);
			ctx.waitTicks(80);
			int after = world.getServer().computeOnServer(server -> ChargeLight.lit(player(server).getUUID()));
			int nearAfter = world.getServer().computeOnServer(server -> blockLight(player(server), 0));
			ctx.takeScreenshot("charge_light_after");
			System.out.println("[charge-light-test] lights " + lit + " near " + near + " far " + far + " (before " + farBefore + ") after " + after + " nearAfter " + nearAfter);
			if (lit < 8) throw new AssertionError("The charge should light the ground round the bearer, but placed " + lit + " lights");
			if (near < 13) throw new AssertionError("The ground at the bearer should be bright while charging, block light " + near);
			if (far < 8 || far <= farBefore) throw new AssertionError("The ground 12 blocks out should be lit while charging, block light " + far);
			if (after != 0 || nearAfter > 2) throw new AssertionError("The light should be pulled back after the charge, still " + after + " lights, block light " + nearAfter);
		}
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}

	/** Block light on the ground {@code out} blocks east of the player. */
	private static int blockLight(ServerPlayer p, int out) {
		BlockPos at = p.blockPosition().offset(out, 0, 0);
		return p.level().getBrightness(LightLayer.BLOCK, at);
	}
}
