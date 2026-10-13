package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.corps.BlueRavager;
import com.sparky.lanternring.corps.BlueSquad;
import com.sparky.lanternring.corps.CorpsVillager;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;

/** Talking to the rescue squad: a flyer's trades and record, and a lift on the rider's beast. */
public class BlueTradeTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode creative @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("gamerule doMobSpawning false");
			world.getServer().runCommand("time set 6000");
			ctx.waitTicks(40);
			BlockPos[] lantern = new BlockPos[1];
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				BlockPos b = p.blockPosition().above(6);
				for (BlockPos pos : BlockPos.betweenClosed(b.offset(-30, -3, -30), b.offset(30, 25, 30))) {
					p.level().setBlock(pos, pos.getY() < b.getY() ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
				}
				lantern[0] = b.immutable();
				p.level().setBlock(b, ModRegistry.POWER_BATTERY.defaultBlockState().setValue(Corps.PROPERTY, Corps.BLUE), 3);
				p.teleportTo(b.getX() - 8.5, b.getY(), b.getZ() + 0.5);
				p.getAbilities().flying = true;
				p.onUpdateAbilities();
			});
			ctx.waitTicks(10);
			world.getServer().runOnServer(server -> BlueSquad.callOut(server.getPlayerList().getPlayers().get(0).level(), lantern[0]));
			ctx.waitTicks(200);
			// The flyer: its trades and its record.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				ServerLevel level = p.level();
				CorpsVillager f = level.getEntitiesOfClass(CorpsVillager.class, new AABB(lantern[0]).inflate(40), v -> v.squadRole() == BlueSquad.Role.FLYER).get(0);
				p.teleportTo(f.getX() + 2, f.getY(), f.getZ());
				var result = f.mobInteract(p, InteractionHand.MAIN_HAND);
				System.out.println("[BlueTradeTest] flyer " + result + ", offers " + f.getOffers().size());
			});
			ctx.waitTicks(20);
			ctx.takeScreenshot("blue_trade_flyer");
			ctx.getInput().pressKey(o -> o.keyInventory);
			ctx.waitTicks(10);
			// The rider: a lift on its beast.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				p.closeContainer();
				ServerLevel level = p.level();
				CorpsVillager r = level.getEntitiesOfClass(CorpsVillager.class, new AABB(lantern[0]).inflate(40), v -> v.squadRole() == BlueSquad.Role.RIDER).get(0);
				p.getAbilities().flying = false;
				p.onUpdateAbilities();
				p.teleportTo(r.getX() + 1.5, r.getY() - 2, r.getZ());
				var result = r.mobInteract(p, InteractionHand.MAIN_HAND);
				System.out.println("[BlueTradeTest] rider " + result + ", player riding " + p.getVehicle() + ", rider on " + r.getVehicle());
			});
			ctx.waitTicks(40);
			ctx.getInput().pressKey(o -> o.keyTogglePerspective);
			ctx.getInput().pressKey(o -> o.keyTogglePerspective);
			ctx.waitTicks(10);
			ctx.takeScreenshot("blue_trade_ride");
			// The beast falls with the player on it: sometimes the rider's ring chooses them.
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				if (p.getVehicle() instanceof BlueRavager mount) mount.kill(p.level());
			});
			ctx.waitTicks(20);
			world.getServer().runOnServer(server -> {
				ServerPlayer p = server.getPlayerList().getPlayers().get(0);
				System.out.println("[BlueTradeTest] after the beast fell, holding " + p.getMainHandItem() + " " + Corps.held(p));
			});
			ctx.takeScreenshot("blue_trade_after");
		}
	}
}
