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
 * Item model property {@code lanternring:red_lantern}: the Red lantern picked in the Ring Lab ("new" or
 * "classic"), so a red Power Battery item shows that lantern.
 */
public record RedLanternProperty() implements SelectItemModelProperty<String> {
	public static final SelectItemModelProperty.Type<RedLanternProperty, String> TYPE =
			SelectItemModelProperty.Type.create(MapCodec.unit(new RedLanternProperty()), Codec.STRING);

	public static void register() {
		SelectItemModelProperties.ID_MAPPER.put(LanternRing.id("red_lantern"), TYPE);
	}

	@Override
	public String get(ItemStack stack, ClientLevel level, LivingEntity entity, int seed, ItemDisplayContext context) {
		return LabSettings.get().redLantern.name().toLowerCase(Locale.ROOT);
	}

	@Override
	public Codec<String> valueCodec() {
		return Codec.STRING;
	}

	@Override
	public SelectItemModelProperty.Type<RedLanternProperty, String> type() {
		return TYPE;
	}
}
