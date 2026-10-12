package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingTuning;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.creativetab.v1.CreativeModeTabEvents;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.ConversionParams;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.MobCategory;
import net.minecraft.world.entity.monster.illager.Pillager;
import net.minecraft.world.entity.npc.villager.Villager;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import org.jspecify.annotations.Nullable;

/**
 * The Lantern Corps' people: corps villagers, their golems and the Red sky raiders, with their
 * spawn eggs. Villagers become corps villagers by standing next to a placed lantern for a few
 * seconds (taking the oath), and now and then one is born to it; a pillager that stands by a
 * Red Lantern becomes a sky raider.
 */
public final class CorpsMobs {
	public static final EntityType<CorpsVillager> CORPS_VILLAGER = register("corps_villager",
			EntityType.Builder.<CorpsVillager>of(CorpsVillager::new, MobCategory.MISC).sized(0.6f, 1.95f).eyeHeight(1.62f).clientTrackingRange(10));
	public static final EntityType<CorpsGolem> CORPS_GOLEM = register("corps_golem",
			EntityType.Builder.<CorpsGolem>of(CorpsGolem::new, MobCategory.MISC).sized(1.4f, 2.7f).clientTrackingRange(10));
	public static final EntityType<SkyRaider> SKY_RAIDER = register("sky_raider",
			EntityType.Builder.<SkyRaider>of(SkyRaider::new, MobCategory.MISC).sized(0.6f, 1.95f).eyeHeight(1.62f).fireImmune().clientTrackingRange(10));

	/** The Red Lantern sanctuary's guardian warden and rage cats (see RedSanctuary). */
	public static final EntityType<RageWarden> RAGE_WARDEN = register("rage_warden",
			EntityType.Builder.<RageWarden>of(RageWarden::new, MobCategory.MONSTER).sized(0.9f, 2.9f).fireImmune().clientTrackingRange(16));
	public static final EntityType<RageCat> RAGE_CAT = register("rage_cat",
			EntityType.Builder.<RageCat>of(RageCat::new, MobCategory.MONSTER).sized(0.6f, 0.7f).fireImmune().clientTrackingRange(10));

	public static final Item CORPS_VILLAGER_EGG = egg("corps_villager_spawn_egg", CORPS_VILLAGER);
	public static final Item CORPS_GOLEM_EGG = egg("corps_golem_spawn_egg", CORPS_GOLEM);
	public static final Item SKY_RAIDER_EGG = egg("sky_raider_spawn_egg", SKY_RAIDER);

	/** One villager in this many becomes a (green) corps villager when it first loads. */
	private static final int BORN_CHANCE = 15;
	private static final String ROLLED = "lanternring.corps_rolled";

	private static <T extends Entity> EntityType<T> register(String name, EntityType.Builder<T> builder) {
		ResourceKey<EntityType<?>> key = ResourceKey.create(Registries.ENTITY_TYPE, LanternRing.id(name));
		return Registry.register(BuiltInRegistries.ENTITY_TYPE, key, builder.build(key));
	}

	private static Item egg(String name, EntityType<? extends Mob> type) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, LanternRing.id(name));
		return Registry.register(BuiltInRegistries.ITEM, key, new SpawnEggItem(new Item.Properties().spawnEgg(type).setId(key)));
	}

	/** How long each villager or pillager has stood by a lantern. */
	private static final Map<UUID, Integer> NEAR_LANTERN = new HashMap<>();
	/** Villagers born to the corps, converted on the next tick (not while they load). */
	private static final List<Villager> BORN = new ArrayList<>();

	public static void init() {
		FabricDefaultAttributeRegistry.register(CORPS_VILLAGER, CorpsVillager.createAttributes());
		FabricDefaultAttributeRegistry.register(CORPS_GOLEM, CorpsGolem.createAttributes());
		FabricDefaultAttributeRegistry.register(SKY_RAIDER, SkyRaider.createAttributes());
		FabricDefaultAttributeRegistry.register(RAGE_WARDEN, RageWarden.createAttributes());
		FabricDefaultAttributeRegistry.register(RAGE_CAT, RageCat.createAttributes());
		SkyBuilds.register();
		RedSanctuary.register();
		CreativeModeTabEvents.modifyOutputEvent(CreativeModeTabs.SPAWN_EGGS).register(output -> {
			output.accept(CORPS_VILLAGER_EGG);
			output.accept(CORPS_GOLEM_EGG);
			output.accept(SKY_RAIDER_EGG);
		});
		ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
			if (entity.getType() != EntityTypes.VILLAGER || entity.entityTags().contains(ROLLED)) return;
			entity.addTag(ROLLED);
			// The Villager Spark's builders belong to the Blue Lantern: never roll them into a Green Lantern.
			if (entity.getAttached(com.sparky.lanternring.Hope.MARK) != null) return;
			Villager v = (Villager) entity;
			if (!v.isBaby() && level.getRandom().nextInt(BORN_CHANCE) == 0) BORN.add(v);
		});
		ServerTickEvents.END_SERVER_TICK.register(CorpsMobs::tick);
	}

	private static void tick(MinecraftServer server) {
		if (!BORN.isEmpty()) {
			for (Villager v : List.copyOf(BORN)) {
				if (v.isAlive() && v.level() instanceof ServerLevel level) oath(level, v, Corps.GREEN, false);
			}
			BORN.clear();
		}
		if (server.getTickCount() % 20 != 0) return;
		Set<UUID> seen = new HashSet<>();
		for (ServerLevel level : server.getAllLevels()) {
			for (ServerPlayer player : level.players()) {
				AABB box = player.getBoundingBox().inflate(48);
				for (Mob mob : level.getEntitiesOfClass(Mob.class, box, m -> m.isAlive()
						&& (m.getType() == EntityTypes.VILLAGER || m.getType() == EntityTypes.PILLAGER))) {
					if (!seen.add(mob.getUUID())) continue;
					boolean pillager = mob instanceof Pillager;
					Corps corps = lanternNear(level, mob.blockPosition(), pillager);
					if (corps == null) {
						NEAR_LANTERN.remove(mob.getUUID());
						continue;
					}
					int secs = NEAR_LANTERN.merge(mob.getUUID(), 1, Integer::sum);
					if (secs < RingTuning.LANTERN_OATH.seconds()) continue;
					NEAR_LANTERN.remove(mob.getUUID());
					if (mob instanceof Villager v) oath(level, v, corps, true);
					else if (pillager) raider(level, (Pillager) mob);
				}
			}
		}
		NEAR_LANTERN.keySet().retainAll(seen);
	}

	/** The corps of a placed lantern within 3 blocks: red only for pillagers, any other for villagers. */
	@Nullable
	private static Corps lanternNear(ServerLevel level, BlockPos at, boolean pillager) {
		for (BlockPos p : BlockPos.betweenClosed(at.offset(-3, -2, -3), at.offset(3, 2, 3))) {
			BlockState s = level.getBlockState(p);
			if (!s.is(ModRegistry.POWER_BATTERY)) continue;
			Corps corps = Corps.of(s);
			if (pillager == (corps == Corps.RED)) return corps;
		}
		return null;
	}

	/** Turns a villager into a corps villager, keeping its job, trades and experience. */
	static void oath(ServerLevel level, Villager v, Corps corps, boolean say) {
		CorpsVillager cv = v.convertTo(CORPS_VILLAGER, ConversionParams.single(v, false, false), c -> {
			c.setVillagerData(v.getVillagerData());
			c.setOffers(v.getOffers().copy());
			c.setVillagerXp(v.getVillagerXp());
			c.setCorps(corps);
		});
		if (cv == null) return;
		CorpsShots.summon(level, cv.position(), cv.getBbHeight(), 1f, corps);
		if (!say) return;
		for (ServerPlayer p : level.players()) {
			if (p.distanceToSqr(cv) < 48 * 48) {
				p.sendSystemMessage(Component.translatable("message.lanternring.corps_oath", corps.ring().getHoverName())
						.withStyle(corps.chat, ChatFormatting.ITALIC));
			}
		}
	}

	private static void raider(ServerLevel level, Pillager pillager) {
		SkyRaider raider = pillager.convertTo(SKY_RAIDER, ConversionParams.single(pillager, false, false),
				r -> r.setItemSlot(EquipmentSlot.MAINHAND, Corps.RED.ring()));
		if (raider == null) return;
		CorpsShots.summon(level, raider.position(), raider.getBbHeight(), 1f, Corps.RED);
		for (ServerPlayer p : level.players()) {
			if (p.distanceToSqr(raider) < 48 * 48) {
				p.sendSystemMessage(Component.translatable("message.lanternring.red_oath").withStyle(ChatFormatting.RED, ChatFormatting.ITALIC));
			}
		}
	}

	private CorpsMobs() {
	}
}
