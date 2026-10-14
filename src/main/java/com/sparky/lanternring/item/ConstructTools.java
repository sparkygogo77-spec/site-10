package com.sparky.lanternring.item;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import net.minecraft.core.BlockPos;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.EmptyBlockGetter;
import net.minecraft.world.level.block.state.BlockState;
import org.jspecify.annotations.Nullable;

/**
 * Construct tools (J, 2026-10-14, 29a): a Green or Blue ring held in the hand forms the matching
 * hard-light tool as you mine, dig or fight (J's T3 Green and U3 Blue designs from the lead Blender
 * chat). The ring then works as that tool: pickaxe on stone and ores, the hammer on the hardest of
 * those (obsidian, metal blocks, ancient debris), axe on wood, shovel on dirt and sand, hoe on leaves
 * and crops, and a sword when it hits a mob. Each block or hit takes a little charge; an empty ring
 * forms nothing. The client draws the tool (ConstructToolHold) from the same rules.
 */
public final class ConstructTools {
	public enum Tool {
		SWORD, PICKAXE, AXE, SHOVEL, HOE, HAMMER;

		/** Its model: bbmodel/construct_{tool}_{green|blue}. */
		public String model(Corps corps) {
			return "construct_" + name().toLowerCase(java.util.Locale.ROOT) + "_" + (corps == Corps.BLUE ? "blue" : "green");
		}
	}

	/** Mining speed with a formed tool: netherite is 9, the hammer smashes through faster. */
	private static final float SPEED = 9f, HAMMER_SPEED = 40f;
	/** Pickaxe blocks at least this hard take the hammer (iron block 5, obsidian 50). */
	private static final float HAMMER_HARDNESS = 5f;
	/** Added to a bare-hand hit: 8 in all, a netherite sword's. */
	public static final float SWORD_DAMAGE = 7f;
	/** Charge each block mined or hit landed takes (a full ring is 1000). */
	private static final int COST = 1;

	private ConstructTools() {
	}

	/** Whether this ring forms construct tools: a Green or Blue ring with charge left. */
	public static boolean forms(ItemStack ring) {
		if (!ring.is(ModRegistry.POWER_RING) || PowerRingItem.getCharge(ring) <= 0) return false;
		Corps c = Corps.of(ring);
		return c == Corps.GREEN || c == Corps.BLUE;
	}

	/** The tool for mining {@code state}, or null if no tool helps (bare hand speed). */
	public static @Nullable Tool forBlock(BlockState state) {
		if (state.is(BlockTags.MINEABLE_WITH_PICKAXE)) {
			return state.getDestroySpeed(EmptyBlockGetter.INSTANCE, BlockPos.ZERO) >= HAMMER_HARDNESS ? Tool.HAMMER : Tool.PICKAXE;
		}
		if (state.is(BlockTags.MINEABLE_WITH_AXE)) return Tool.AXE;
		if (state.is(BlockTags.MINEABLE_WITH_SHOVEL)) return Tool.SHOVEL;
		if (state.is(BlockTags.MINEABLE_WITH_HOE)) return Tool.HOE;
		if (state.is(BlockTags.SWORD_EFFICIENT)) return Tool.SWORD;
		return null;
	}

	static float destroySpeed(ItemStack ring, BlockState state) {
		if (!forms(ring)) return 1f;
		Tool tool = forBlock(state);
		if (tool == null) return 1f;
		if (tool == Tool.SWORD) return 1.5f;
		return tool == Tool.HAMMER ? HAMMER_SPEED : SPEED;
	}

	static boolean correctForDrops(ItemStack ring, BlockState state) {
		if (!forms(ring)) return false;
		Tool tool = forBlock(state);
		return tool != null && tool != Tool.SWORD && !state.is(BlockTags.INCORRECT_FOR_NETHERITE_TOOL);
	}

	/** A block broken with the formed tool: it costs a little charge. */
	static void mined(ItemStack ring, BlockState state, LivingEntity miner) {
		if (miner instanceof Player p && p.isCreative()) return;
		if (forms(ring) && forBlock(state) != null && state.getDestroySpeed(EmptyBlockGetter.INSTANCE, BlockPos.ZERO) > 0) spend(ring);
	}

	/** A hit with the formed sword: it costs a little charge too. */
	static void hit(ItemStack ring, LivingEntity attacker) {
		if (attacker instanceof Player p && p.isCreative()) return;
		if (forms(ring)) spend(ring);
	}

	private static void spend(ItemStack ring) {
		PowerRingItem.setCharge(ring, Math.max(0, PowerRingItem.getCharge(ring) - COST));
	}
}
