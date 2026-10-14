package com.sparky.lanternring.item;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModRegistry;
import java.util.EnumMap;
import java.util.Locale;
import java.util.Map;
import net.minecraft.ChatFormatting;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.ItemTags;
import net.minecraft.util.Unit;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.ToolMaterial;

/**
 * Construct tools (J, 2026-10-14): in Tools mode a Green or Blue ring's right-click puts six
 * hard-light tools in your hotbar (then the rest of your inventory) as real items you pick and use:
 * sword, pickaxe, axe, shovel, hoe and the hammer (J's T3 Green and U3 Blue designs). Right-click
 * again takes them back. They mine and hit like netherite (the hammer smashes stone much faster),
 * never wear out, and each block or hit takes a little charge from your ring; they dissolve when
 * no charged ring of their colour is left on you, or when they leave your inventory.
 * (Before this the ring formed a tool by itself on every swing; J wanted to pick them instead.)
 */
public final class ConstructTools {
	public enum Tool {
		SWORD, PICKAXE, AXE, SHOVEL, HOE, HAMMER;

		/** Its model and item name: construct_{tool}_{green|blue}. */
		public String model(Corps corps) {
			return "construct_" + name().toLowerCase(Locale.ROOT) + "_" + (corps == Corps.BLUE ? "blue" : "green");
		}
	}

	/** The two corps with tools. */
	public static final Corps[] CORPS = {Corps.GREEN, Corps.BLUE};
	/** Netherite, but the hammer smashes through stone and metal blocks at 40 (netherite is 9). */
	private static final ToolMaterial HAMMER_MATERIAL = new ToolMaterial(BlockTags.INCORRECT_FOR_NETHERITE_TOOL, 2031, 40f, 4f, 15,
			ItemTags.NETHERITE_TOOL_MATERIALS);
	/** Charge each block mined or hit landed takes (a full ring is 1000). */
	private static final int COST = 1;

	private static final Map<Corps, Map<Tool, Item>> ITEMS = new EnumMap<>(Corps.class);

	private ConstructTools() {
	}

	/** Registers the twelve tool items (ModRegistry.init). */
	public static void register() {
		for (Corps corps : CORPS) {
			Map<Tool, Item> byTool = new EnumMap<>(Tool.class);
			for (Tool tool : Tool.values()) {
				ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, LanternRing.id(tool.model(corps)));
				Item.Properties props = properties(tool).setId(key).stacksTo(1).rarity(Rarity.EPIC).fireResistant()
						.component(DataComponents.UNBREAKABLE, Unit.INSTANCE);
				byTool.put(tool, Registry.register(BuiltInRegistries.ITEM, key, new ConstructToolItem(tool, corps, props)));
			}
			ITEMS.put(corps, byTool);
		}
		net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity instanceof ItemEntity item && dissolves(item)) entity.discard();
		});
	}

	private static Item.Properties properties(Tool tool) {
		Item.Properties p = new Item.Properties();
		ToolMaterial m = ToolMaterial.NETHERITE;
		return switch (tool) {
			case SWORD -> p.sword(m, 3f, -2.4f);
			case PICKAXE -> p.pickaxe(m, 1f, -2.8f);
			case AXE -> p.axe(m, 5f, -3f);
			case SHOVEL -> p.shovel(m, 1.5f, -3f);
			case HOE -> p.hoe(m, -4f, 0f);
			case HAMMER -> p.tool(HAMMER_MATERIAL, BlockTags.MINEABLE_WITH_PICKAXE, 6f, -3.2f, 0f);
		};
	}

	public static Item item(Corps corps, Tool tool) {
		return ITEMS.get(corps).get(tool);
	}

	/** A charged ring of {@code corps} on {@code player} (held or in the inventory), or EMPTY. */
	public static ItemStack ring(Player player, Corps corps) {
		Inventory inv = player.getInventory();
		for (int i = 0; i < inv.getContainerSize(); i++) {
			ItemStack s = inv.getItem(i);
			if (s.is(ModRegistry.POWER_RING) && Corps.of(s) == corps && (player.isCreative() || PowerRingItem.getCharge(s) > 0)) return s;
		}
		return ItemStack.EMPTY;
	}

	/** A block mined or a hit landed with a tool: it costs a little of the ring's charge. */
	static void spend(Player player, Corps corps) {
		if (player.isCreative()) return;
		ItemStack ring = ring(player, corps);
		if (!ring.isEmpty()) PowerRingItem.setCharge(ring, Math.max(0, PowerRingItem.getCharge(ring) - COST));
	}

	private static boolean isTool(ItemStack s) {
		return s.getItem() instanceof ConstructToolItem;
	}

	/**
	 * Tools mode's right-click: takes the tools back if you have any, otherwise puts the six tools
	 * of the ring's colour in your free hotbar slots, then the rest of your inventory.
	 */
	public static boolean toggle(ServerPlayer player, ItemStack ring) {
		Inventory inv = player.getInventory();
		boolean had = false;
		for (int i = 0; i < inv.getContainerSize(); i++) {
			if (isTool(inv.getItem(i))) {
				inv.setItem(i, ItemStack.EMPTY);
				had = true;
			}
		}
		if (had) {
			player.level().playSound(null, player.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.5f, 1.8f);
			player.sendOverlayMessage(Component.translatable("message.lanternring.tools_recalled"));
			return true;
		}
		Corps corps = Corps.of(ring);
		if (!ITEMS.containsKey(corps)) return false;
		int placed = 0;
		for (Tool tool : Tool.values()) {
			int slot = -1;
			for (int i = 0; i < Inventory.INVENTORY_SIZE && slot < 0; i++) if (inv.getItem(i).isEmpty()) slot = i;
			if (slot < 0) break;
			inv.setItem(slot, new ItemStack(item(corps, tool)));
			placed++;
		}
		if (placed == 0) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.tools_no_room").withStyle(ChatFormatting.RED));
			return false;
		}
		player.level().playSound(null, player.blockPosition(), SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 0.5f, 1.8f);
		player.sendOverlayMessage(Component.translatable(placed < Tool.values().length ? "message.lanternring.tools_some" : "message.lanternring.tools_formed"));
		return true;
	}

	/** A tool dropped, thrown or spilled on death dissolves instead of lying in the world (LanternRing's entity-load hook). */
	public static boolean dissolves(ItemEntity entity) {
		return isTool(entity.getItem());
	}
}
