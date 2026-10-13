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

			// A plain R does nothing: the lantern needs crouch + R.
			ctx.getInput().pressKey(InputConstants.KEY_R);
			ctx.waitTicks(4);
			boolean early = world.getServer().computeOnServer(server -> !LanternSlot.lantern(player(server)).isEmpty());
			if (early) throw new AssertionError("A plain R shouldn't summon the lantern");

			// Crouch + R: into the slot and summoned.
			crouchR(ctx);
			ctx.waitTicks(3);
			shot(ctx, "lantern_slot_floating_in");
			ctx.waitTicks(20);
			shot(ctx, "lantern_slot_resting");
			boolean stowed = world.getServer().computeOnServer(server -> LanternSlot.out(player(server))
					&& player(server).getOffhandItem().isEmpty());
			if (!stowed) throw new AssertionError("Crouch + R should move the off-hand lantern into its slot and summon it");

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

			// Tapping and holding plain R never lets it go.
			ctx.getInput().pressKey(InputConstants.KEY_R);
			ctx.getInput().holdKey(InputConstants.KEY_R);
			ctx.waitTicks(20);
			ctx.getInput().releaseKey(InputConstants.KEY_R);
			ctx.waitTicks(4);
			boolean still = world.getServer().computeOnServer(server -> LanternSlot.out(player(server)));
			if (!still) throw new AssertionError("A plain R (tapped or held) shouldn't dismiss the lantern");

			// Crouch + R again: it breaks up into light.
			crouchR(ctx);
			ctx.waitTicks(4);
			shot(ctx, "lantern_slot_dismissing");
			ctx.waitTicks(20);
			shot(ctx, "lantern_slot_dismissed");
			boolean away = world.getServer().computeOnServer(server -> !LanternSlot.out(player(server))
					&& LanternSlot.lantern(player(server)).is(ModRegistry.POWER_BATTERY_ITEM));
			if (!away) throw new AssertionError("Crouch + R should dismiss the lantern but keep it in its slot");

			// With it away, right-click is the ring's own power again.
			boolean wants = world.getServer().computeOnServer(server -> LanternCharge.wants(player(server)));
			if (wants) throw new AssertionError("Right-click shouldn't charge with the lantern dismissed");

			// Crouch + R with another lantern in hand: it swaps in, the old one goes to the inventory,
			// and only one is ever out.
			world.getServer().runOnServer(server -> player(server).setItemInHand(net.minecraft.world.InteractionHand.OFF_HAND,
					com.sparky.lanternring.Corps.RED.lantern()));
			ctx.waitTicks(5);
			crouchR(ctx);
			ctx.waitTicks(20);
			shot(ctx, "lantern_slot_swapped");
			boolean swapped = world.getServer().computeOnServer(server -> {
				ServerPlayer p = player(server);
				return LanternSlot.out(p) && com.sparky.lanternring.Corps.ofLantern(LanternSlot.lantern(p)) == com.sparky.lanternring.Corps.RED
						&& p.getOffhandItem().isEmpty() && p.getInventory().contains(st -> st.is(ModRegistry.POWER_BATTERY_ITEM));
			});
			if (!swapped) throw new AssertionError("Crouch + R with a lantern in hand should swap it into the slot");
		}
	}

	static void crouchR(ClientGameTestContext ctx) {
		ctx.getInput().holdKey(o -> o.keyShift);
		ctx.waitTicks(2);
		ctx.getInput().pressKey(InputConstants.KEY_R);
		ctx.waitTicks(2);
		ctx.getInput().releaseKey(o -> o.keyShift);
	}

	private static void shot(ClientGameTestContext ctx, String name) {
		ctx.takeScreenshot(name);
		System.out.println("[lantern-slot-test] " + name + ": " + LanternFirstPerson.debug);
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
