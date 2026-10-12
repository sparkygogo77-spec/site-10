package com.sparky.lanternring.hero;

import com.sparky.lanternring.LanternRing;
import java.util.List;
import java.util.Optional;
import java.util.function.Function;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.DamageTypeTags;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.component.BlocksAttacks;

/** Superhero gear from outside the Lantern Corps: Captain America's Shield (see CapShieldItem). */
public final class HeroItems {
	/**
	 * Vibranium: it blocks the instant you raise it, an axe can't knock it out of your hands, and it
	 * never wears out (no durability, so the vanilla shield's item damage does nothing).
	 */
	public static final Item CAP_SHIELD = item("cap_shield", CapShieldItem::new, new Item.Properties()
			.stacksTo(1)
			.rarity(Rarity.EPIC)
			.fireResistant()
			.delayedComponent(DataComponents.BLOCKS_ATTACKS, registries -> new BlocksAttacks(0f, 0f,
					List.of(new BlocksAttacks.DamageReduction(90f, Optional.empty(), 0f, 1f)),
					new BlocksAttacks.ItemDamageFunction(3f, 1f, 1f),
					Optional.of(registries.getOrThrow(DamageTypeTags.BYPASSES_SHIELD)),
					Optional.of(SoundEvents.SHIELD_BLOCK), Optional.of(SoundEvents.SHIELD_BREAK))));

	private static Item item(String name, Function<Item.Properties, Item> factory, Item.Properties props) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, LanternRing.id(name));
		return Registry.register(BuiltInRegistries.ITEM, key, factory.apply(props.setId(key)));
	}

	public static void register() {
		ShieldThrows.register();
		CreativeModeTabEvents.modifyOutputEvent(CreativeModeTabs.COMBAT).register(output -> output.accept(CAP_SHIELD));
	}

	private HeroItems() {
	}
}
