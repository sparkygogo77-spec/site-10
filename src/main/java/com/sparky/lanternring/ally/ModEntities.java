package com.sparky.lanternring.ally;

import com.sparky.lanternring.LanternRing;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;

/** The Army mode's construct allies. */
public final class ModEntities {
	public static final EntityType<WardenConstruct> WARDEN = register("warden_construct",
			EntityType.Builder.of(WardenConstruct::new, MobCategory.MISC).sized(0.9f, 2.9f).eyeHeight(2.4f)
					.fireImmune().noLootTable().clientTrackingRange(10));
	public static final EntityType<DragonConstruct> DRAGON = register("dragon_construct",
			EntityType.Builder.of(DragonConstruct::new, MobCategory.MISC).sized(2.4f, 1.2f).eyeHeight(0.8f)
					.fireImmune().noLootTable().clientTrackingRange(10));
	public static final EntityType<SentryConstruct> SENTRY = register("sentry_construct",
			EntityType.Builder.of(SentryConstruct::new, MobCategory.MISC).sized(0.85f, 0.85f).eyeHeight(0.425f)
					.fireImmune().noLootTable().clientTrackingRange(10));

	private static <T extends Entity> EntityType<T> register(String name, EntityType.Builder<T> builder) {
		ResourceKey<EntityType<?>> key = ResourceKey.create(Registries.ENTITY_TYPE, LanternRing.id(name));
		return Registry.register(BuiltInRegistries.ENTITY_TYPE, key, builder.build(key));
	}

	public static void init() {
		FabricDefaultAttributeRegistry.register(WARDEN, WardenConstruct.createAttributes());
		FabricDefaultAttributeRegistry.register(DRAGON, DragonConstruct.createAttributes());
		FabricDefaultAttributeRegistry.register(SENTRY, SentryConstruct.createAttributes());
	}

	private ModEntities() {
	}
}
