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
 * Item model property {@code lanternring:lantern_model}: the lantern picked in the Ring Lab, lower
 * case ("dark" or "keychain"), so items/power_battery.json shows that lantern everywhere the item
 * model is used.
 */
public record LanternModelProperty() implements SelectItemModelProperty<String> {
	public static final SelectItemModelProperty.Type<LanternModelProperty, String> TYPE =
			SelectItemModelProperty.Type.create(MapCodec.unit(new LanternModelProperty()), Codec.STRING);

	public static void register() {
		SelectItemModelProperties.ID_MAPPER.put(LanternRing.id("lantern_model"), TYPE);
	}

	@Override
	public String get(ItemStack stack, ClientLevel level, LivingEntity entity, int seed, ItemDisplayContext context) {
		return LabSettings.get().lanternModel.name().toLowerCase(Locale.ROOT);
	}

	@Override
	public Codec<String> valueCodec() {
		return Codec.STRING;
	}

	@Override
	public SelectItemModelProperty.Type<LanternModelProperty, String> type() {
		return TYPE;
	}
}
