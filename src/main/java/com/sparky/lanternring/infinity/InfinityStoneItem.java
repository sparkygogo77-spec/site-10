package com.sparky.lanternring.infinity;

import java.util.function.Consumer;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;

/** A loose Infinity Stone: right-click uses its first power, crouch + right-click its second (if it has one). */
public class InfinityStoneItem extends Item {
	public final InfinityStone stone;

	public InfinityStoneItem(InfinityStone stone, Properties properties) {
		super(properties);
		this.stone = stone;
	}

	public InfinityPower power(boolean crouching) {
		var powers = stone.powers();
		return crouching && powers.size() > 1 ? powers.get(1) : powers.get(0);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack stack = player.getItemInHand(hand);
		// Held with the Gauntlet in the other hand, a right-click on the Gauntlet sockets it instead.
		if (player.getItemInHand(hand == InteractionHand.MAIN_HAND ? InteractionHand.OFF_HAND : InteractionHand.MAIN_HAND)
				.getItem() instanceof InfinityGauntletItem) {
			return InteractionResult.PASS;
		}
		if (player.getCooldowns().isOnCooldown(stack)) return InteractionResult.FAIL;
		InfinityPower power = power(player.isShiftKeyDown());
		if (!(level instanceof ServerLevel server) || !(player instanceof ServerPlayer serverPlayer)) return InteractionResult.SUCCESS;
		if (!power.use(server, serverPlayer)) return InteractionResult.FAIL;
		player.getCooldowns().addCooldown(stack, power.cooldown());
		return InteractionResult.SUCCESS;
	}

	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> tooltip, TooltipFlag flag) {
		var powers = stone.powers();
		for (int i = 0; i < powers.size(); i++) {
			InfinityPower p = powers.get(i);
			tooltip.accept(Component.translatable(i == 0 ? "tooltip.lanternring.stone_use" : "tooltip.lanternring.stone_crouch_use",
					p.displayName()).withStyle(ChatFormatting.WHITE));
			tooltip.accept(p.description().copy().withStyle(ChatFormatting.DARK_GRAY));
		}
		if (stone == InfinityStone.SOUL) tooltip.accept(Component.translatable("tooltip.lanternring.soul_sight").withStyle(ChatFormatting.GOLD));
		tooltip.accept(Component.translatable("tooltip.lanternring.stone_socket").withStyle(ChatFormatting.GRAY));
	}
}
