package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.corps.HopeSanctuary;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

/** J's A6 Battery + cone: the Hope sanctuary forms above a rescue dome, its turbine turns, and a Blue ring charges under it. */
public class HopeSanctuaryTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode spectator @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			BlockPos[] dome = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				dome[0] = p.blockPosition().immutable();
				HopeSanctuary.request(p.level(), dome[0]);
				// Far enough out to see it whole, level with its middle.
				p.teleportTo(dome[0].getX() + 0.5, dome[0].getY() + 58, dome[0].getZ() - 80.5);
				ItemStack ring = Corps.BLUE.ring();
				PowerRingItem.setCharge(ring, 100);
				p.getInventory().setItem(0, ring);
			});
			ctx.getInput().lookAt(0f, -5f);
			for (int i = 0; i < 4; i++) {
				ctx.waitTicks(60);
				ctx.takeScreenshot("hope_sanctuary_forming_" + i);
			}
			ctx.waitTicks(80);
			ctx.takeScreenshot("hope_sanctuary_built");
			ctx.waitTicks(100);
			ctx.takeScreenshot("hope_sanctuary_turned");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				System.out.println("[HopeSanctuaryTest] turbines on the server " + p.level().getEntities(com.sparky.lanternring.ally.ModEntities.HOPE_TURBINE, e -> true).size());
			});
			// Close up on the turbine.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.teleportTo(dome[0].getX() + 0.5, dome[0].getY() + 34 + 28, dome[0].getZ() - 30.5);
			});
			ctx.getInput().lookAt(0f, 0f);
			ctx.waitTicks(40);
			ctx.takeScreenshot("hope_sanctuary_turbine");
			ctx.runOnClient(mc -> {
				int n = 0;
				for (net.minecraft.world.entity.Entity e : mc.level.entitiesForRendering()) if (e instanceof com.sparky.lanternring.corps.HopeTurbine) n++;
				System.out.println("[HopeSanctuaryTest] turbines on the client " + n);
			});
			// Under it, by the dome: the Blue ring charges.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.teleportTo(dome[0].getX() + 0.5, dome[0].getY() + 1, dome[0].getZ() + 18.5);
			});
			ctx.getInput().lookAt(180f, -60f);
			ctx.waitTicks(200);
			ctx.takeScreenshot("hope_sanctuary_from_below");
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				ItemStack ring = p.getInventory().getItem(0);
				System.out.println("[HopeSanctuaryTest] sites " + HopeSanctuary.sites(p.level()).size()
						+ " standing " + HopeSanctuary.sites(p.level()).get(0).standing()
						+ " ring charge " + PowerRingItem.getCharge(ring) + " (was 100)"
						+ " floor block " + p.level().getBlockState(HopeSanctuary.sites(p.level()).get(0).anchor()));
			});
		}
	}
}
