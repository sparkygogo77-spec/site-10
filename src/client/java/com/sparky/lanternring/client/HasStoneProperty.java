package com.sparky.lanternring.client;

import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.infinity.InfinityGauntletItem;
import com.sparky.lanternring.infinity.InfinityStone;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties;
import net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperty;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;

/**
 * Item model condition {@code lanternring:has_stone} with a {@code stone} field ("soul", "time"):
 * whether that stone is set into the Infinity Gauntlet, so items/infinity_gauntlet.json can show it.
 */
public record HasStoneProperty(InfinityStone stone) implements ConditionalItemModelProperty {
	public static final MapCodec<HasStoneProperty> MAP_CODEC = RecordCodecBuilder.mapCodec(i -> i.group(
			InfinityStone.CODEC.fieldOf("stone").forGetter(HasStoneProperty::stone)).apply(i, HasStoneProperty::new));

	public static void register() {
		ConditionalItemModelProperties.ID_MAPPER.put(LanternRing.id("has_stone"), MAP_CODEC);
	}

	@Override
	public boolean get(ItemStack stack, ClientLevel level, LivingEntity entity, int seed, ItemDisplayContext context) {
		return InfinityGauntletItem.has(stack, stone);
	}

	@Override
	public MapCodec<HasStoneProperty> type() {
		return MAP_CODEC;
	}
}
