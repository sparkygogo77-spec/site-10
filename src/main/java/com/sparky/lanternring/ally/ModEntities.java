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
	/** Blender pass 828: a hard-light pig in the vanilla pig's size. */
	public static final EntityType<PigConstruct> PIG = register("pig_construct",
			EntityType.Builder.of(PigConstruct::new, MobCategory.MISC).sized(0.9f, 0.9f).eyeHeight(0.7f)
					.fireImmune().noLootTable().clientTrackingRange(10));

	/** The Yellow Lantern's Brood (see Terror): a giant hard-light spider and its spiderlings. */
	public static final EntityType<BroodSpider> BROOD_SPIDER = register("brood_spider",
			EntityType.Builder.<BroodSpider>of(BroodSpider::new, MobCategory.MISC).sized(3.1f, 2.0f).eyeHeight(1.45f)
					.fireImmune().noLootTable().clientTrackingRange(10));
	public static final EntityType<BroodSpider> SPIDERLING = register("spiderling",
			EntityType.Builder.<BroodSpider>of(BroodSpider::new, MobCategory.MISC).sized(0.6f, 0.4f).eyeHeight(0.3f)
					.fireImmune().noLootTable().clientTrackingRange(10));

	/** The Red Lantern's biggest Blast (level 4): a giant hard-light bull that bulldozes a round tunnel. */
	public static final EntityType<RageBull> RAGE_BULL = register("rage_bull",
			EntityType.Builder.<RageBull>of(RageBull::new, MobCategory.MISC).sized(10f, 17f).eyeHeight(14f)
					.fireImmune().noLootTable().clientTrackingRange(16).updateInterval(1));

	/** The Yellow Lantern's biggest Blast (level 4): a gaunt fear construct that sprints at what you aim at. */
	public static final EntityType<DreadRunner> DREAD_RUNNER = register("dread_runner",
			EntityType.Builder.<DreadRunner>of(DreadRunner::new, MobCategory.MISC).sized(1.6f, 4f).eyeHeight(3.4f)
					.fireImmune().noLootTable().clientTrackingRange(16).updateInterval(1));

	/** The Hope sanctuary's spinning turbine (drawn by the client from the sanctuary's block plan). */
	public static final EntityType<com.sparky.lanternring.corps.HopeTurbine> HOPE_TURBINE = register("hope_turbine",
			EntityType.Builder.<com.sparky.lanternring.corps.HopeTurbine>of(com.sparky.lanternring.corps.HopeTurbine::new, MobCategory.MISC)
					.sized(1f, 1f).fireImmune().noLootTable().noSummon().clientTrackingRange(16).updateInterval(200));

	private static <T extends Entity> EntityType<T> register(String name, EntityType.Builder<T> builder) {
		ResourceKey<EntityType<?>> key = ResourceKey.create(Registries.ENTITY_TYPE, LanternRing.id(name));
		return Registry.register(BuiltInRegistries.ENTITY_TYPE, key, builder.build(key));
	}

	public static void init() {
		FabricDefaultAttributeRegistry.register(WARDEN, WardenConstruct.createAttributes());
		FabricDefaultAttributeRegistry.register(DRAGON, DragonConstruct.createAttributes());
		FabricDefaultAttributeRegistry.register(SENTRY, SentryConstruct.createAttributes());
		FabricDefaultAttributeRegistry.register(PIG, PigConstruct.createAttributes());
		FabricDefaultAttributeRegistry.register(BROOD_SPIDER, BroodSpider.createAttributes(true));
		FabricDefaultAttributeRegistry.register(SPIDERLING, BroodSpider.createAttributes(false));
		FabricDefaultAttributeRegistry.register(RAGE_BULL, RageBull.createAttributes());
		FabricDefaultAttributeRegistry.register(DREAD_RUNNER, DreadRunner.createAttributes());
	}

	private ModEntities() {
	}
}
