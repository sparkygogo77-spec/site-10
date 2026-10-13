package com.sparky.lanternring.test;

import com.mojang.blaze3d.platform.InputConstants;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.LanternSlot;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.client.LanternFirstPerson;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.server.level.ServerPlayer;

/**
 * The lantern's own slot: R stows the off-hand lantern and summons it (it floats in, low), right-click
 * alone charges from it, R dismisses it, crouch + R hands it back. Left-click is never needed.
 */
public class LanternSlotTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runCommand("item replace entity @a weapon.mainhand with lanternring:power_ring");
			world.getServer().runCommand("item replace entity @a weapon.offhand with lanternring:power_battery");
			ctx.waitTicks(60);
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 15f);

			// R: into the slot and summoned.
			ctx.getInput().pressKey(InputConstants.KEY_R);
			ctx.waitTicks(3);
			shot(ctx, "lantern_slot_floating_in");
			ctx.waitTicks(20);
			shot(ctx, "lantern_slot_resting");
			boolean stowed = world.getServer().computeOnServer(server -> LanternSlot.out(player(server))
					&& player(server).getOffhandItem().isEmpty());
			if (!stowed) throw new AssertionError("R should move the off-hand lantern into its slot and summon it");

			// Right-click alone charges from it.
			world.getServer().runOnServer(server -> PowerRingItem.setCharge(player(server).getMainHandItem(), 100));
			ctx.getInput().holdKey(o -> o.keyUse);
			ctx.waitTicks(LanternCharge.hold() + LanternCharge.reach() / 2);
			shot(ctx, "lantern_slot_drawn_in");
			ctx.waitTicks(LanternCharge.reach() / 2 + 6);
			shot(ctx, "lantern_slot_ring_in");
			ctx.waitTicks(LanternCharge.done() - LanternCharge.hold() - LanternCharge.reach() + 4);
			ctx.getInput().releaseKey(o -> o.keyUse);
			int charge = world.getServer().computeOnServer(server -> PowerRingItem.getCharge(player(server).getMainHandItem()));
			if (charge != PowerRingItem.MAX_CHARGE) {
				throw new AssertionError("Right-click with the lantern summoned should fill the ring, but it has " + charge);
			}
			ctx.waitTicks(LanternCharge.DEPLETE + 10);
			shot(ctx, "lantern_slot_after_charge");

			// R again: it breaks up into light.
			ctx.getInput().pressKey(InputConstants.KEY_R);
			ctx.waitTicks(4);
			shot(ctx, "lantern_slot_dismissing");
			ctx.waitTicks(20);
			shot(ctx, "lantern_slot_dismissed");
			boolean away = world.getServer().computeOnServer(server -> !LanternSlot.out(player(server))
					&& LanternSlot.lantern(player(server)).is(ModRegistry.POWER_BATTERY_ITEM));
			if (!away) throw new AssertionError("R should dismiss the lantern but keep it in its slot");

			// With it away, right-click is the ring's own power again.
			boolean wants = world.getServer().computeOnServer(server -> LanternCharge.wants(player(server)));
			if (wants) throw new AssertionError("Right-click shouldn't charge with the lantern dismissed");

			// Crouch + R: back into the inventory.
			ctx.getInput().holdKey(o -> o.keyShift);
			ctx.waitTicks(2);
			ctx.getInput().pressKey(InputConstants.KEY_R);
			ctx.waitTicks(4);
			ctx.getInput().releaseKey(o -> o.keyShift);
			boolean back = world.getServer().computeOnServer(server -> LanternSlot.lantern(player(server)).isEmpty()
					&& player(server).getInventory().contains(s -> s.is(ModRegistry.POWER_BATTERY_ITEM)));
			if (!back) throw new AssertionError("Crouch + R should give the lantern back");
		}
	}

	private static void shot(ClientGameTestContext ctx, String name) {
		ctx.takeScreenshot(name);
		System.out.println("[lantern-slot-test] " + name + ": " + LanternFirstPerson.debug);
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
