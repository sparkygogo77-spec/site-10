package com.sparky.lanternring.item;

import com.sparky.lanternring.Corps;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

/**
 * One of the hard-light tools a Green or Blue ring puts in your inventory in Tools mode (see
 * ConstructTools): a netherite-grade sword, pickaxe, axe, shovel, hoe or hammer that never wears
 * out. Each block mined or hit landed takes a little charge from your ring, and the tool dissolves
 * as soon as you have no charged ring of its colour, or if it leaves your inventory.
 */
public class ConstructToolItem extends Item {
	public final ConstructTools.Tool tool;
	public final Corps corps;

	public ConstructToolItem(ConstructTools.Tool tool, Corps corps, Properties properties) {
		super(properties);
		this.tool = tool;
		this.corps = corps;
	}

	@Override
	public void inventoryTick(ItemStack stack, ServerLevel level, Entity owner, EquipmentSlot slot) {
		if (!(owner instanceof Player p) || ConstructTools.ring(p, corps).isEmpty()) stack.setCount(0);
	}

	@Override
	public boolean mineBlock(ItemStack stack, Level level, BlockState state, BlockPos pos, LivingEntity miner) {
		if (state.getDestroySpeed(level, pos) > 0 && miner instanceof Player p) ConstructTools.spend(p, corps);
		com.sparky.lanternring.WhatsNew.done(miner, "mode.tools.use");
		return true;
	}

	@Override
	public void hurtEnemy(ItemStack stack, LivingEntity target, LivingEntity attacker) {
		if (attacker instanceof Player p) {
			ConstructTools.spend(p, corps);
			// Pass 844 S3b: the sword's sweep pair, the backswing striking again.
			if (tool == ConstructTools.Tool.SWORD) SwordSweeps.hit(p, corps);
		}
		com.sparky.lanternring.WhatsNew.done(attacker, "mode.tools.use");
	}
}
