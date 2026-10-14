package com.sparky.lanternring;

import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentSyncPredicate;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.minecraft.resources.Identifier;
import net.minecraft.world.Container;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;

/**
 * The ring slot (J, 2026-10-14: "the ring should stay on when wearing it, make a ring slot in the
 * inventory for your right hand"). A ring put in the slot beside the off hand is worn on the right
 * hand and stays on whatever the hotbar holds: an empty hand works as the ring (PlayerEquipmentMixin
 * hands it out as the main-hand item, so every power reads it as held), the ring is drawn on the
 * hand while it holds something else, and flight, the charge meter and the corps colour keep going.
 */
public final class RingSlot {
	/** Kept through death; synced to everyone so other players see it on your hand. */
	public static final AttachmentType<ItemStack> WORN = AttachmentRegistry.create(LanternRing.id("worn_ring"),
			b -> b.persistent(ItemStack.CODEC).copyOnDeath().syncWith(ItemStack.OPTIONAL_STREAM_CODEC, AttachmentSyncPredicate.all()));

	/** The empty-slot ring outline (textures/gui/sprites/container/slot/ring.png). */
	public static final Identifier EMPTY_ICON = LanternRing.id("container/slot/ring");
	/** Where the slot sits in the survival inventory: just above the off hand slot. */
	public static final int X = 77, Y = 44;
	/** Where it sits on the creative inventory tab: left of the off hand slot. */
	public static final int CREATIVE_X = 16, CREATIVE_Y = 20;

	private RingSlot() {
	}

	static void register() {
		// Loads WORN at start-up so the attachment is registered before any player.
	}

	/** The ring worn in the slot, or empty. */
	public static ItemStack worn(LivingEntity entity) {
		if (!(entity instanceof Player player)) return ItemStack.EMPTY;
		ItemStack stack = player.getAttached(WORN);
		return stack == null ? ItemStack.EMPTY : stack;
	}

	/** The ring that powers this player: held in either hand first, then the worn one. */
	public static ItemStack ring(LivingEntity entity) {
		if (entity.getMainHandItem().getItem() instanceof PowerRingItem) return entity.getMainHandItem();
		if (entity.getOffhandItem().getItem() instanceof PowerRingItem) return entity.getOffhandItem();
		return worn(entity);
	}

	public static void setWorn(Player player, ItemStack stack) {
		if (stack.isEmpty()) player.removeAttached(WORN);
		else player.setAttached(WORN, stack);
	}

	/** The one-slot container behind the inventory's ring slot. */
	public static final class Worn implements Container {
		private final Player player;

		public Worn(Player player) {
			this.player = player;
		}

		@Override
		public int getContainerSize() {
			return 1;
		}

		@Override
		public boolean isEmpty() {
			return worn(player).isEmpty();
		}

		@Override
		public ItemStack getItem(int slot) {
			return worn(player);
		}

		@Override
		public ItemStack removeItem(int slot, int count) {
			ItemStack ring = worn(player);
			if (ring.isEmpty() || count <= 0) return ItemStack.EMPTY;
			setWorn(player, ItemStack.EMPTY);
			return ring;
		}

		@Override
		public ItemStack removeItemNoUpdate(int slot) {
			ItemStack ring = worn(player);
			setWorn(player, ItemStack.EMPTY);
			return ring;
		}

		@Override
		public void setItem(int slot, ItemStack stack) {
			setWorn(player, stack);
		}

		@Override
		public int getMaxStackSize() {
			return 1;
		}

		@Override
		public void setChanged() {
		}

		@Override
		public boolean stillValid(Player player) {
			return true;
		}

		@Override
		public void clearContent() {
			setWorn(player, ItemStack.EMPTY);
		}
	}

	/** The ring slot itself: takes one power ring and nothing else. */
	public static final class WornSlot extends Slot {
		public WornSlot(Player player, int x, int y) {
			super(new Worn(player), 0, x, y);
		}

		@Override
		public boolean mayPlace(ItemStack stack) {
			return stack.getItem() instanceof PowerRingItem;
		}

		@Override
		public int getMaxStackSize() {
			return 1;
		}

		@Override
		public int getMaxStackSize(ItemStack stack) {
			return 1;
		}

		@Override
		public Identifier getNoItemIcon() {
			return EMPTY_ICON;
		}
	}
}
