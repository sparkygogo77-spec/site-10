package com.sparky.lanternring;

import com.sparky.lanternring.block.BlastGlowBlock;
import com.sparky.lanternring.block.ConstructBrickBlock;
import com.sparky.lanternring.block.GhostBlocks;
import com.sparky.lanternring.block.GhostMimicBlock;
import com.sparky.lanternring.block.GhostMimicBlockEntity;
import com.sparky.lanternring.block.LightConstructBlock;
import com.sparky.lanternring.block.PowerBatteryBlock;
import com.sparky.lanternring.block.PowerFontBlock;
import com.sparky.lanternring.block.RingForgeBlock;
import com.sparky.lanternring.block.RingForgeBlockEntity;
import java.util.Set;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.level.block.entity.BlockEntityType;
import com.sparky.lanternring.item.PowerBatteryItem;
import com.sparky.lanternring.item.PowerRingItem;
import java.util.function.Function;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.level.material.PushReaction;

public final class ModRegistry {
	public static final Block POWER_BATTERY = block("power_battery", PowerBatteryBlock::new, BlockBehaviour.Properties.of()
			.mapColor(MapColor.EMERALD)
			.strength(3.5f, 6f)
			.requiresCorrectToolForDrops()
			.lightLevel(state -> 13)
			.sound(SoundType.LANTERN)
			.noOcclusion());

	/** The Ring Forge: forges new power rings (see RingForgeBlock). */
	public static final Block RING_FORGE = block("ring_forge", RingForgeBlock::new, BlockBehaviour.Properties.of()
			.mapColor(MapColor.EMERALD)
			.strength(5f, 1200f)
			.requiresCorrectToolForDrops()
			.lightLevel(state -> 12)
			.sound(SoundType.NETHER_BRICKS)
			.noOcclusion());

	/** The big power sources (see PowerFontBlock): the green Great Power Battery and the red Lava Font. */
	public static final Block GREAT_BATTERY = block("great_battery", p -> new PowerFontBlock(Corps.GREEN, true, p), font(MapColor.EMERALD));
	public static final Block LAVA_FONT = block("lava_font", p -> new PowerFontBlock(Corps.RED, false, p), font(MapColor.COLOR_BLACK));

	private static BlockBehaviour.Properties font(MapColor color) {
		return BlockBehaviour.Properties.of()
				.mapColor(color)
				.strength(5f, 1200f)
				.requiresCorrectToolForDrops()
				.lightLevel(state -> state.getValue(PowerFontBlock.FILLED) ? 15 : 0)
				.sound(SoundType.NETHER_BRICKS)
				.noOcclusion();
	}

	public static final BlockEntityType<RingForgeBlockEntity> RING_FORGE_ENTITY = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE,
			LanternRing.id("ring_forge"), new BlockEntityType<>(RingForgeBlockEntity::new, Set.of(RING_FORGE)));

	public static final Block LIGHT_CONSTRUCT = block("light_construct", LightConstructBlock::new, BlockBehaviour.Properties.of()
			.mapColor(MapColor.EMERALD)
			.strength(-1f, 3600000f)
			.noLootTable()
			.lightLevel(state -> 10)
			.sound(SoundType.GLASS)
			.noOcclusion()
			.isValidSpawn(Blocks::never)
			.isRedstoneConductor(Blocks::never)
			.isSuffocating(Blocks::never)
			.isViewBlocking((state, level, pos, box) -> false)
			.pushReaction(PushReaction.IMMOVEABLE));

	// Green hard-light shapes for Build mode previews (see GhostBlocks and Builds.ghost).
	public static final Block GHOST_STAIRS = block("ghost_stairs", p -> new GhostBlocks.Stairs(LIGHT_CONSTRUCT.defaultBlockState(), p), ghost());
	public static final Block GHOST_SLAB = block("ghost_slab", GhostBlocks.Slab::new, ghost());
	public static final Block GHOST_FENCE = block("ghost_fence", GhostBlocks.Fence::new, ghost());
	public static final Block GHOST_PANE = block("ghost_pane", GhostBlocks.Pane::new, ghost());
	public static final Block GHOST_WALL = block("ghost_wall", GhostBlocks.Wall::new, ghost());
	public static final Block GHOST_DOOR = block("ghost_door", GhostBlocks.Door::new, ghost());
	public static final Block GHOST_TRAPDOOR = block("ghost_trapdoor", GhostBlocks.Trapdoor::new, ghost());
	public static final Block GHOST_GATE = block("ghost_gate", GhostBlocks.Gate::new, ghost());
	public static final Block GHOST_CARPET = block("ghost_carpet", GhostBlocks.Carpet::new, ghost());
	public static final Block GHOST_LADDER = block("ghost_ladder", GhostBlocks.Ladder::new, ghost());
	public static final Block GHOST_LANTERN = block("ghost_lantern", GhostBlocks.Lantern::new, ghost());
	public static final Block GHOST_LEAVES = block("ghost_leaves", GhostBlocks.Leaves::new, ghost());
	public static final Block GHOST_PLANT = block("ghost_plant", GhostBlocks.Plant::new, ghost().noCollision());
	/** A green copy of any block, drawn from the real block's own model (see GhostMimicBlock). */
	public static final Block GHOST_MIMIC = block("ghost_mimic", GhostMimicBlock::new, ghost().dynamicShape());
	public static final BlockEntityType<GhostMimicBlockEntity> GHOST_MIMIC_ENTITY = Registry.register(BuiltInRegistries.BLOCK_ENTITY_TYPE,
			LanternRing.id("ghost_mimic"), new BlockEntityType<>(GhostMimicBlockEntity::new, Set.of(GHOST_MIMIC)));

	private static BlockBehaviour.Properties ghost() {
		return BlockBehaviour.Properties.of()
				.mapColor(MapColor.EMERALD)
				.strength(-1f, 3600000f)
				.noLootTable()
				.lightLevel(state -> 10)
				.sound(SoundType.GLASS)
				.noOcclusion()
				.isValidSpawn(Blocks::never)
				.isRedstoneConductor(Blocks::never)
				.isSuffocating(Blocks::never)
				.isViewBlocking((state, level, pos, box) -> false)
				.pushReaction(PushReaction.IMMOVEABLE);
	}

	public static final Block CONSTRUCT_BRICK = block("construct_brick", ConstructBrickBlock::new, BlockBehaviour.Properties.of()
			.mapColor(MapColor.EMERALD)
			.strength(-1f, 3600000f)
			.noLootTable()
			.lightLevel(state -> 12)
			.sound(SoundType.NETHER_BRICKS)
			.noOcclusion()
			.isValidSpawn(Blocks::never)
			.pushReaction(PushReaction.IMMOVEABLE));

	/** Invisible, short-lived light left along a Blast tunnel. */
	public static final Block BLAST_GLOW = block("blast_glow", BlastGlowBlock::new, BlockBehaviour.Properties.of()
			.replaceable()
			.noCollision()
			.noLootTable()
			.lightLevel(state -> state.getValue(BlastGlowBlock.LEVEL)));

	/** The same invisible light, flashed for a moment along a Beam's path. */
	public static final Block BEAM_GLOW = block("beam_glow", props -> new BlastGlowBlock(props, () -> 0), BlockBehaviour.Properties.of()
			.replaceable()
			.noCollision()
			.noLootTable()
			.lightLevel(state -> state.getValue(BlastGlowBlock.LEVEL)));

	public static final Item POWER_RING = item("power_ring", PowerRingItem::new, new Item.Properties()
			.stacksTo(1)
			.rarity(Rarity.EPIC)
			.fireResistant()
			.component(ModComponents.CHARGE, PowerRingItem.MAX_CHARGE)
			.component(ModComponents.MODE, 0)
			.component(ModComponents.FLIGHT, false));

	public static final Item POWER_BATTERY_ITEM = item("power_battery",
			props -> new PowerBatteryItem(POWER_BATTERY, props),
			new Item.Properties().rarity(Rarity.RARE).useBlockDescriptionPrefix());

	public static final Item RING_FORGE_ITEM = item("ring_forge", props -> new BlockItem(RING_FORGE, props),
			new Item.Properties().rarity(Rarity.EPIC).useBlockDescriptionPrefix());

	public static final Item GREAT_BATTERY_ITEM = item("great_battery", props -> new BlockItem(GREAT_BATTERY, props),
			new Item.Properties().rarity(Rarity.EPIC).useBlockDescriptionPrefix());
	public static final Item LAVA_FONT_ITEM = item("lava_font", props -> new BlockItem(LAVA_FONT, props),
			new Item.Properties().rarity(Rarity.EPIC).useBlockDescriptionPrefix());

	/** The 1911 pistol (J, 2026-10-13): a 7-round magazine, right-click to fire, sneak + right-click or R to reload. */
	public static final Item PISTOL_1911 = item("pistol_1911", com.sparky.lanternring.item.Pistol1911Item::new, new Item.Properties()
			.stacksTo(1)
			.rarity(Rarity.UNCOMMON)
			.component(ModComponents.ROUNDS, com.sparky.lanternring.item.Pistol1911Item.MAGAZINE));

	/** The yellow construct weapons the Fear Nuke's gas hands frenzied mobs (see corps/FearFrenzy); they fade with the frenzy. */
	public static final Item CONSTRUCT_RIFLE = item("construct_rifle", com.sparky.lanternring.item.ConstructWeaponItem::new,
			new Item.Properties().stacksTo(1));
	public static final Item CONSTRUCT_CROSSBOW = item("construct_crossbow", com.sparky.lanternring.item.ConstructWeaponItem::new,
			new Item.Properties().stacksTo(1));
	public static final Item CONSTRUCT_BLADE = item("construct_blade", com.sparky.lanternring.item.ConstructWeaponItem::new,
			new Item.Properties().stacksTo(1));

	private static Block block(String name, Function<BlockBehaviour.Properties, Block> factory, BlockBehaviour.Properties props) {
		ResourceKey<Block> key = ResourceKey.create(Registries.BLOCK, LanternRing.id(name));
		return Registry.register(BuiltInRegistries.BLOCK, key, factory.apply(props.setId(key)));
	}

	private static Item item(String name, Function<Item.Properties, Item> factory, Item.Properties props) {
		ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, LanternRing.id(name));
		return Registry.register(BuiltInRegistries.ITEM, key, factory.apply(props.setId(key)));
	}

	static void init() {
		com.sparky.lanternring.item.ConstructTools.register();
	}

	private ModRegistry() {
	}
}
