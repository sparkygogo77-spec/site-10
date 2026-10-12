package com.sparky.lanternring.client;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.sparky.lanternring.LanternRing;
import java.util.Locale;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties;
import net.minecraft.client.renderer.item.properties.select.SelectItemModelProperty;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;

/**
 * Item model property {@code lanternring:ring_model}: the ring picked in the Ring Lab, lower case
 * (e.g. "crest_gold"), so items/power_ring.json shows that ring's 3D model in the inventory, on
 * the ground and in item frames.
 */
public record RingModelProperty() implements SelectItemModelProperty<String> {
	public static final SelectItemModelProperty.Type<RingModelProperty, String> TYPE =
			SelectItemModelProperty.Type.create(MapCodec.unit(new RingModelProperty()), Codec.STRING);

	public static void register() {
		SelectItemModelProperties.ID_MAPPER.put(LanternRing.id("ring_model"), TYPE);
	}

	@Override
	public String get(ItemStack stack, ClientLevel level, LivingEntity entity, int seed, ItemDisplayContext context) {
		return LabSettings.get().ringModel.name().toLowerCase(Locale.ROOT);
	}

	@Override
	public Codec<String> valueCodec() {
		return Codec.STRING;
	}

	@Override
	public SelectItemModelProperty.Type<RingModelProperty, String> type() {
		return TYPE;
	}
}
