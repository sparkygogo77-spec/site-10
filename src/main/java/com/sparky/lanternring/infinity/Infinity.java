package com.sparky.lanternring.infinity;

import com.sparky.lanternring.LanternRing;
import java.util.List;
import java.util.function.Function;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.minecraft.core.Registry;
import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.ExtraCodecs;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;

/**
 * The Infinity Stones and the Infinity Gauntlet. The Soul Stone drops from the Wither and the Time
 * Stone from Elder Guardians (both are in the creative Tools tab too); the Gauntlet is crafted.
 */
public final class Infinity {
	/** The stones set into a Gauntlet, in InfinityStone order. */
	public static final DataComponentType<List<InfinityStone>> STONES = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("infinity_stones"),
			DataComponentType.<List<InfinityStone>>builder().persistent(InfinityStone.CODEC.listOf())
					.networkSynchronized(InfinityStone.STREAM_CODEC.apply(ByteBufCodecs.list())).build());
	/** Which of the Gauntlet's powers right-click uses (an index into InfinityGauntletItem.powers). */
	public static final DataComponentType<Integer> GAUNTLET_POWER = Registry.register(BuiltInRegistries.DATA_COMPONENT_TYPE,
			LanternRing.id("gauntlet_power"),
			DataComponentType.<Integer>builder().persistent(ExtraCodecs.NON_NEGATIVE_INT).networkSynchronized(ByteBufCodecs.VAR_INT).build());

	public static final Item SOUL_STONE = item("soul_stone", p -> new InfinityStoneItem(InfinityStone.SOUL, p), stone());
	public static final Item TIME_STONE = item("time_stone", p -> new InfinityStoneItem(InfinityStone.TIME, p), stone());
	public static final Item GAUNTLET = item("infinity_gauntlet", InfinityGauntletItem::new,
			new Item.Properties().stacksTo(1).rarity(Rarity.EPIC).fireResistant());

	private static Item.Properties stone() {
		return new Item.Properties().stacksTo(1).rarity(Rarity.EPIC).fireResistant();
	}

	private static Item item(String name, Function<Item.Properties, Item> factory, Item.Properties props) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, LanternRing.id(name));
		return Registry.register(BuiltInRegistries.ITEM, key, factory.apply(props.setId(key)));
	}

	public static void register() {
		SoulStone.register();
		TimeStone.register();
		CreativeModeTabEvents.modifyOutputEvent(CreativeModeTabs.TOOLS_AND_UTILITIES).register(output -> {
			output.accept(GAUNTLET);
			output.accept(SOUL_STONE);
			output.accept(TIME_STONE);
		});
		// Boss drops.
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (!(entity.level() instanceof ServerLevel level)) return;
			Item drop = entity.getType() == EntityTypes.WITHER ? SOUL_STONE
					: entity.getType() == EntityTypes.ELDER_GUARDIAN ? TIME_STONE : null;
			if (drop == null) return;
			ItemEntity item = new ItemEntity(level, entity.getX(), entity.getY() + 0.5, entity.getZ(), new ItemStack(drop));
			item.setUnlimitedLifetime();
			item.setGlowingTag(true);
			level.addFreshEntity(item);
		});
	}

	private Infinity() {
	}
}
