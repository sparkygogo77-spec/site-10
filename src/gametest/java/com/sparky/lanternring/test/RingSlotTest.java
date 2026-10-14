package com.sparky.lanternring.test;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.RingFlight;
import com.sparky.lanternring.RingSlot;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;
import net.minecraft.client.CameraType;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.Items;

/**
 * The ring slot: a worn ring stays on the hand whatever it holds. An empty hand works as the ring,
 * a sword in hand keeps flight and the corps colour going, F never copies the ring into the off hand,
 * and shift-click moves it in and out of the slot.
 */
public class RingSlotTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		try (TestSingleplayerContext world = ctx.worldBuilder().create()) {
			world.getServer().runCommand("gamemode survival @a");
			world.getServer().runCommand("gamerule doDaylightCycle false");
			world.getServer().runCommand("time set 6000");
			world.getServer().runOnServer(server -> RingSlot.setWorn(player(server), Corps.RED.ring()));
			ctx.waitTicks(40);

			// An empty hand is the ring.
			boolean bare = world.getServer().computeOnServer(server -> player(server).getMainHandItem().getItem() instanceof PowerRingItem
					&& player(server).getInventory().getSelectedItem().isEmpty());
			boolean bareClient = ctx.computeOnClient(mc -> mc.player.getMainHandItem().getItem() instanceof PowerRingItem);
			if (!bare || !bareClient) throw new AssertionError("An empty hand should work as the worn ring (server " + bare + ", client " + bareClient + ")");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));
			ctx.getInput().lookAt(0f, 10f);
			ctx.waitTicks(10);
			ctx.takeScreenshot("ring_slot_bare_hand_fp");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			ctx.waitTicks(10);
			ctx.takeScreenshot("ring_slot_bare_hand_3p");

			// F with an empty hand doesn't copy the ring into the off hand.
			ctx.getInput().pressKey(o -> o.keySwapOffhand);
			ctx.waitTicks(10);
			int rings = world.getServer().computeOnServer(server -> {
				ServerPlayer p = player(server);
				int n = RingSlot.worn(p).isEmpty() ? 0 : 1;
				for (int i = 0; i < p.getInventory().getContainerSize(); i++) if (p.getInventory().getItem(i).getItem() instanceof PowerRingItem) n++;
				return n;
			});
			if (rings != 1) throw new AssertionError("Swapping hands shouldn't copy the worn ring, found " + rings);

			// A sword in hand: the ring stays on, flight and the corps colour still read it.
			world.getServer().runCommand("item replace entity @a weapon.mainhand with diamond_sword");
			ctx.waitTicks(10);
			boolean kept = world.getServer().computeOnServer(server -> {
				ServerPlayer p = player(server);
				return p.getMainHandItem().is(Items.DIAMOND_SWORD) && Corps.held(p) == Corps.RED && !RingFlight.findRing(p).isEmpty();
			});
			if (!kept) throw new AssertionError("With a sword in hand the worn ring should keep its powers");
			ctx.takeScreenshot("ring_slot_sword_3p");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));

			// The slot in the inventory, above the off hand.
			ctx.runOnClient(mc -> mc.setScreenAndShow(new InventoryScreen(mc.player)));
			ctx.waitTicks(10);
			ctx.takeScreenshot("ring_slot_inventory");
			boolean slot = ctx.computeOnClient(mc -> {
				for (Slot s : mc.player.inventoryMenu.slots) if (s instanceof RingSlot.WornSlot && s.getItem().getItem() instanceof PowerRingItem) return true;
				return false;
			});
			if (!slot) throw new AssertionError("The inventory should show the worn ring in its slot");
			ctx.runOnClient(mc -> mc.setScreenAndShow(null));

			// Creative: on the inventory tab the slot sits left of the off hand, not over the hotbar.
			world.getServer().runCommand("gamemode creative @a");
			ctx.waitTicks(5);
			ctx.runOnClient(mc -> {
				var screen = new net.minecraft.client.gui.screens.inventory.CreativeModeInventoryScreen(mc.player, mc.player.connection.enabledFeatures(), false);
				mc.setScreenAndShow(screen);
				try {
					var select = screen.getClass().getDeclaredMethod("selectTab", net.minecraft.world.item.CreativeModeTab.class);
					select.setAccessible(true);
					select.invoke(screen, net.minecraft.core.registries.BuiltInRegistries.CREATIVE_MODE_TAB.getValueOrThrow(net.minecraft.world.item.CreativeModeTabs.INVENTORY));
				} catch (ReflectiveOperationException e) {
					throw new AssertionError(e);
				}
				boolean placed = false;
				for (Slot s : screen.getMenu().slots) {
					if (s.container instanceof RingSlot.Worn) placed = s.x == RingSlot.CREATIVE_X && s.y == RingSlot.CREATIVE_Y;
				}
				if (!placed) throw new AssertionError("The creative inventory tab should place the ring slot left of the off hand");
			});
			ctx.waitTicks(10);
			ctx.takeScreenshot("ring_slot_creative");
			ctx.runOnClient(mc -> mc.setScreenAndShow(null));
			world.getServer().runCommand("gamemode survival @a");
			ctx.waitTicks(5);

			// Shift-click it out and back in.
			boolean moved = world.getServer().computeOnServer(server -> {
				ServerPlayer p = player(server);
				int index = -1;
				for (Slot s : p.inventoryMenu.slots) if (s instanceof RingSlot.WornSlot) index = s.index;
				p.inventoryMenu.quickMoveStack(p, index);
				boolean out = RingSlot.worn(p).isEmpty() && p.getInventory().contains(st -> st.getItem() instanceof PowerRingItem);
				int at = -1;
				for (Slot s : p.inventoryMenu.slots) if (s.container == p.getInventory() && s.getItem().getItem() instanceof PowerRingItem) at = s.index;
				p.inventoryMenu.quickMoveStack(p, at);
				return out && !RingSlot.worn(p).isEmpty() && !p.getInventory().contains(st -> st.getItem() instanceof PowerRingItem);
			});
			if (!moved) throw new AssertionError("Shift-click should move the ring out of its slot and back");
		}
	}

	private static ServerPlayer player(net.minecraft.server.MinecraftServer server) {
		return server.getPlayerList().getPlayers().get(0);
	}
}
