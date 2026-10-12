package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModFluids;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.ally.ModEntities;
import com.sparky.lanternring.block.PowerFontBlock;
import com.sparky.lanternring.city.CityBlocks;
import it.unimi.dsi.fastutil.objects.Object2IntFunction;
import it.unimi.dsi.fastutil.objects.Object2IntMap;
import it.unimi.dsi.fastutil.objects.Object2IntOpenHashMap;
import java.lang.reflect.Constructor;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.client.Minecraft;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Files the mod's blocks, items and entities under a shader pack's own material IDs, so packs like
 * Complementary Reimagined light and glow them properly. Those packs give each block, item and
 * entity an ID from their block/item/entity.properties and pick light colour, glow and effects by
 * ID; ours aren't listed, so they would get the pack's default warm light and no glow.
 *
 * <p>When Iris loads a pack, each glowing block state is given the ID of the vanilla light whose
 * colour matches its corps (see {@link #lightFor}), read from the pack itself so it follows the pack's
 * version. The Deluge's hard-light liquid takes the pack's water ID (waves, reflections, its green
 * tint) and the Red Deluge's ember liquid red light. Held lanterns and batteries light the hand like
 * a held froglight, and the Warden, Dragon and Sentry constructs glow all over like a glow squid.
 * ShaderPackPatcher makes a copy of Complementary with exact corps colours instead.
 *
 * <p>Iris has no public API for this, so it is done by reflection and does nothing if Iris is
 * missing or its internals change. Without colored lighting turned on in the pack, block light is
 * one colour for everything and there is nothing a mod can tint.
 */
final class ShaderPackIds {
	private static final String SETTINGS = "net.irisshaders.iris.shaderpack.materialmap.WorldRenderingSettings";
	private static final String NAMESPACED_ID = "net.irisshaders.iris.shaderpack.materialmap.NamespacedId";
	private static final boolean IRIS = FabricLoader.getInstance().isModLoaded("iris");
	private static Object patchedBlocks, patchedItems, patchedEntities;
	/** The pack's own item IDs, the NamespacedId constructor, and the held lantern's corps last applied. */
	private static Object2IntMap<Object> packItems;
	private static Constructor<?> namespacedId;
	private static Corps heldCorps, ringCorps;
	private static boolean failed;
	private static int tick;

	private ShaderPackIds() {
	}

	/**
	 * The vanilla light whose colour each corps borrows. Under Complementary: verdant froglight is
	 * green, redstone block red, crying obsidian purple, shroomlight orange, soul lantern blue-cyan
	 * and ochre froglight yellow.
	 */
	static Block lightFor(Corps corps) {
		return switch (corps.getSerializedName()) {
			case "red" -> Blocks.REDSTONE_BLOCK;
			case "violet" -> Blocks.CRYING_OBSIDIAN;
			case "orange" -> Blocks.SHROOMLIGHT;
			case "blue" -> Blocks.SOUL_LANTERN;
			case "yellow" -> Blocks.OCHRE_FROGLIGHT;
			default -> Blocks.VERDANT_FROGLIGHT;
		};
	}

	static void tick(Minecraft mc) {
		if (IRIS && !failed && mc.level != null && tick % 4 == 0) heldLight(mc);
		if (!IRIS || failed || mc.level == null || ++tick % 20 != 0) return;
		try {
			Class<?> settings = Class.forName(SETTINGS);
			Object instance = settings.getField("INSTANCE").get(null);
			Object blocks = settings.getMethod("getBlockStateIds").invoke(instance);
			if (blocks != null && blocks != patchedBlocks) {
				patchedBlocks = blocks;
				@SuppressWarnings("unchecked")
				Object2IntMap<BlockState> map = (Object2IntMap<BlockState>) blocks;
				patchBlocks(map);
				// Chunks already built carry the old IDs; new ones (like a fresh Blast tunnel) are fine.
				try {
					mc.levelRenderer.getClass().getMethod("allChanged").invoke(mc.levelRenderer);
				} catch (ReflectiveOperationException ignored) {
					// Older chunks pick the IDs up next time they rebuild.
				}
			}
			// Iris keeps the item and entity IDs read-only, so ours go into a copy that replaces them.
			Constructor<?> id = Class.forName(NAMESPACED_ID).getConstructor(String.class, String.class);
			Object items = settings.getMethod("getItemIds").invoke(instance);
			if (items != null && items != patchedItems) {
				@SuppressWarnings("unchecked")
				Object2IntMap<Object> pack = (Object2IntMap<Object>) items;
				packItems = pack;
				namespacedId = id;
				heldCorps = null;
				ringCorps = null;
				patchedItems = withExtras((Object2IntFunction<?>) items, id, itemExtras());
				settings.getMethod("setItemIds", Object2IntFunction.class).invoke(instance, patchedItems);
			}
			Object entities = settings.getMethod("getEntityIds").invoke(instance);
			if (entities != null && entities != patchedEntities) {
				patchedEntities = withExtras((Object2IntFunction<?>) entities, id, entityExtras());
				settings.getMethod("setEntityIds", Object2IntFunction.class).invoke(instance, patchedEntities);
			}
		} catch (ReflectiveOperationException | RuntimeException e) {
			failed = true;
			LanternRing.LOGGER.info("Couldn't give the ring's blocks shader pack IDs ({}); they use the pack's defaults", e.toString());
		}
	}

	private static void patchBlocks(Object2IntMap<BlockState> map) {
		lookLike(map);
		if (map.containsKey(ModRegistry.LIGHT_CONSTRUCT.defaultBlockState())) {
			// A pack that lists our blocks itself (like the Lantern Ring copy ShaderPackPatcher makes) knows best.
			LanternRing.LOGGER.info("Shader pack lists the ring's blocks itself; leaving its IDs alone");
			return;
		}
		BlockState water = Blocks.WATER.defaultBlockState();
		if (map.containsKey(water)) {
			// The Deluge's liquid is water to the pack: its waves, reflections and refraction,
			// coloured by the liquid's green tint (see ModFluids).
			int waterId = map.getInt(water);
			for (BlockState state : ModFluids.BLOCK.getStateDefinition().getPossibleStates()) map.put(state, waterId);
		}
		int count = 0;
		for (Block block : BuiltInRegistries.BLOCK) {
			if (!LanternRing.MOD_ID.equals(BuiltInRegistries.BLOCK.getKey(block).getNamespace()) || block == ModFluids.BLOCK) continue;
			for (BlockState state : block.getStateDefinition().getPossibleStates()) {
				// Only states that give light: an empty font or a spent glow keeps the pack's default.
				if (state.getLightEmission() <= 0) continue;
				BlockState light = lightFor(corpsOf(state)).defaultBlockState();
				if (!map.containsKey(light)) continue;
				map.put(state, map.getInt(light));
				count++;
			}
		}
		LanternRing.LOGGER.info("Shader pack: {} glowing ring block states given their corps' light colour", count);
	}

	/**
	 * The sky city's Skystone is the End city's purpur in sky colours, so it takes the pack's purpur
	 * IDs (its polish and reflections), state by state so stairs and slabs match. Hope Quartz takes
	 * the quartz blocks' IDs the same way. Done for every
	 * pack, the Lantern Ring copy too, unless the pack lists Skystone itself.
	 */
	private static void lookLike(Object2IntMap<BlockState> map) {
		Map<Block, Block> like = Map.of(CityBlocks.SKYSTONE_BRICKS, Blocks.PURPUR_BLOCK, CityBlocks.SKYSTONE_TILES, Blocks.PURPUR_BLOCK,
				CityBlocks.SKYSTONE_PILLAR, Blocks.PURPUR_PILLAR, CityBlocks.SKYSTONE_STAIRS, Blocks.PURPUR_STAIRS,
				CityBlocks.SKYSTONE_SLAB, Blocks.PURPUR_SLAB, CityBlocks.HOPE_QUARTZ, Blocks.QUARTZ_BLOCK,
				CityBlocks.HOPE_QUARTZ_BRICKS, Blocks.QUARTZ_BRICKS, CityBlocks.HOPE_QUARTZ_PILLAR, Blocks.QUARTZ_PILLAR,
				CityBlocks.HOPE_QUARTZ_STAIRS, Blocks.QUARTZ_STAIRS, CityBlocks.HOPE_QUARTZ_SLAB, Blocks.QUARTZ_SLAB);
		for (Map.Entry<Block, Block> e : like.entrySet()) {
			if (map.containsKey(e.getKey().defaultBlockState())) continue;
			for (BlockState state : e.getKey().getStateDefinition().getPossibleStates()) {
				BlockState vanilla = e.getValue().withPropertiesOf(state);
				if (map.containsKey(vanilla)) map.put(state, map.getInt(vanilla));
				else if (map.containsKey(e.getValue().defaultBlockState())) map.put(state, map.getInt(e.getValue().defaultBlockState()));
			}
		}
	}

	private static Corps corpsOf(BlockState state) {
		if (state.hasProperty(Corps.PROPERTY)) return state.getValue(Corps.PROPERTY);
		if (CityBlocks.isCity(state)) return Corps.BLUE;
		if (state.getBlock() instanceof PowerFontBlock font) return font.corps();
		if (state.is(ModFluids.EMBER_BLOCK)) return Corps.RED;
		return Corps.GREEN;
	}

	/**
	 * One item covers every corps' lantern, and the pack picks a held item's light by item alone, so
	 * the lantern's entry follows the corps of the lantern you're holding: a Red Lantern lights your
	 * hands and the ground red. (Other players holding a lantern take your lantern's colour.) The
	 * ring works the same way: a held ring lights your hand in its corps' colour.
	 */
	private static void heldLight(Minecraft mc) {
		if (!(patchedItems instanceof Object2IntOpenHashMap<?> copy) || packItems == null || mc.player == null) return;
		Corps lantern = null, ring = null;
		for (var stack : List.of(mc.player.getMainHandItem(), mc.player.getOffhandItem())) {
			if (lantern == null && stack.is(ModRegistry.POWER_BATTERY_ITEM)) lantern = Corps.ofLantern(stack);
			if (ring == null && stack.is(ModRegistry.POWER_RING)) ring = Corps.of(stack);
		}
		@SuppressWarnings("unchecked")
		Object2IntOpenHashMap<Object> map = (Object2IntOpenHashMap<Object>) copy;
		try {
			if (lantern != null && lantern != heldCorps && light(map, ModRegistry.POWER_BATTERY_ITEM, lantern)) heldCorps = lantern;
			if (ring != null && ring != ringCorps && light(map, ModRegistry.POWER_RING, ring)) ringCorps = ring;
		} catch (ReflectiveOperationException e) {
			if (lantern != null) heldCorps = lantern;
			if (ring != null) ringCorps = ring;
		}
	}

	/** Gives {@code item} the held light of {@code corps}; false if the pack has no such light. */
	private static boolean light(Object2IntOpenHashMap<Object> map, Item item, Corps corps) throws ReflectiveOperationException {
		// The Red Lantern borrows the Lava Font's red where the patched pack lists it, else redstone.
		Identifier like = corps == Corps.RED && packItems.containsKey(nsid(key(ModRegistry.LAVA_FONT_ITEM)))
				? key(ModRegistry.LAVA_FONT_ITEM) : BuiltInRegistries.ITEM.getKey(lightFor(corps).asItem());
		if (corps == Corps.GREEN && packItems.containsKey(nsid(key(ModRegistry.POWER_BATTERY_ITEM)))) like = key(ModRegistry.POWER_BATTERY_ITEM);
		else if (corps == Corps.GREEN) like = Identifier.withDefaultNamespace("verdant_froglight");
		Object source = nsid(like);
		if (!packItems.containsKey(source)) return false;
		map.put(nsid(key(item)), packItems.getInt(source));
		return true;
	}

	private static Object nsid(Identifier id) throws ReflectiveOperationException {
		return namespacedId.newInstance(id.getNamespace(), id.getPath());
	}

	/** Held lanterns, batteries and rings light the hand (the lantern's colour then follows the held lantern's corps, see heldLight). */
	private static Map<Identifier, Identifier> itemExtras() {
		Identifier froglight = Identifier.withDefaultNamespace("verdant_froglight");
		return Map.of(
				key(ModRegistry.POWER_BATTERY_ITEM), froglight,
				key(ModRegistry.GREAT_BATTERY_ITEM), froglight,
				key(ModRegistry.RING_FORGE_ITEM), froglight,
				key(ModRegistry.POWER_RING), froglight,
				key(ModRegistry.LAVA_FONT_ITEM), Identifier.withDefaultNamespace("redstone_block"));
	}

	/** The army constructs glow all over, like a glow squid. */
	private static Map<Identifier, Identifier> entityExtras() {
		Identifier squid = Identifier.withDefaultNamespace("glow_squid");
		Map<Identifier, Identifier> extras = new HashMap<>();
		for (EntityType<?> type : List.of(ModEntities.WARDEN, ModEntities.DRAGON, ModEntities.SENTRY)) {
			extras.put(BuiltInRegistries.ENTITY_TYPE.getKey(type), squid);
		}
		return extras;
	}

	private static Identifier key(Item item) {
		return BuiltInRegistries.ITEM.getKey(item);
	}

	/** A copy of the pack's map with each of ours under the ID of the vanilla thing it copies, if the pack lists that. */
	private static Object2IntOpenHashMap<Object> withExtras(Object2IntFunction<?> pack, Constructor<?> id,
			Map<Identifier, Identifier> extras) throws ReflectiveOperationException {
		@SuppressWarnings("unchecked")
		Object2IntMap<Object> source = (Object2IntMap<Object>) pack;
		Object2IntOpenHashMap<Object> copy = new Object2IntOpenHashMap<>(source);
		copy.defaultReturnValue(source.defaultReturnValue());
		for (Map.Entry<Identifier, Identifier> e : extras.entrySet()) {
			Object like = id.newInstance(e.getValue().getNamespace(), e.getValue().getPath());
			Object ours = id.newInstance(e.getKey().getNamespace(), e.getKey().getPath());
			if (source.containsKey(like) && !source.containsKey(ours)) copy.put(ours, source.getInt(like));
		}
		return copy;
	}
}
