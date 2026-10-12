package com.sparky.lanternring.infinity;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.function.Consumer;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;

/**
 * The Infinity Gauntlet. Right-click it with a stone in the other hand to set the stone into its
 * socket (the Time Stone on the back of the hand, the Soul Stone on the thumb). Then crouch +
 * right-click cycles through the socketed stones' powers and right-click uses the chosen one.
 */
public class InfinityGauntletItem extends Item {
	public InfinityGauntletItem(Properties properties) {
		super(properties);
	}

	public static List<InfinityStone> stones(ItemStack glove) {
		return glove.getOrDefault(Infinity.STONES, List.of());
	}

	public static boolean has(ItemStack glove, InfinityStone stone) {
		return stones(glove).contains(stone);
	}

	public static List<InfinityPower> powers(ItemStack glove) {
		List<InfinityPower> out = new ArrayList<>();
		for (InfinityStone s : stones(glove)) out.addAll(s.powers());
		return out;
	}

	public static InfinityPower selected(ItemStack glove) {
		List<InfinityPower> powers = powers(glove);
		if (powers.isEmpty()) return null;
		return powers.get(Math.floorMod(glove.getOrDefault(Infinity.GAUNTLET_POWER, 0), powers.size()));
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		ItemStack glove = player.getItemInHand(hand);
		ItemStack other = player.getItemInHand(hand == InteractionHand.MAIN_HAND ? InteractionHand.OFF_HAND : InteractionHand.MAIN_HAND);

		if (other.getItem() instanceof InfinityStoneItem stoneItem) {
			InfinityStone stone = stoneItem.stone;
			if (has(glove, stone)) {
				player.sendOverlayMessage(Component.translatable("message.lanternring.gauntlet_has", stone.displayName()).withStyle(ChatFormatting.GOLD));
				return InteractionResult.FAIL;
			}
			if (!level.isClientSide()) {
				List<InfinityStone> stones = new ArrayList<>(stones(glove));
				stones.add(stone);
				stones.sort(Comparator.naturalOrder());
				glove.set(Infinity.STONES, List.copyOf(stones));
				glove.set(Infinity.GAUNTLET_POWER, powers(glove).indexOf(stone.powers().get(0)));
				other.consume(1, player);
				level.playSound(null, player.blockPosition(), SoundEvents.ANVIL_USE, SoundSource.PLAYERS, 0.6f, 1.6f);
				level.playSound(null, player.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 1f, 1.2f);
				player.sendOverlayMessage(Component.translatable("message.lanternring.gauntlet_socket", stone.displayName()).withStyle(ChatFormatting.GOLD));
			}
			return InteractionResult.SUCCESS;
		}

		List<InfinityPower> powers = powers(glove);
		if (powers.isEmpty()) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.gauntlet_empty").withStyle(ChatFormatting.GOLD));
			return InteractionResult.FAIL;
		}
		if (player.isShiftKeyDown()) {
			if (!level.isClientSide()) {
				int next = Math.floorMod(glove.getOrDefault(Infinity.GAUNTLET_POWER, 0) + 1, powers.size());
				glove.set(Infinity.GAUNTLET_POWER, next);
				player.sendOverlayMessage(Component.translatable("message.lanternring.gauntlet_power", powers.get(next).displayName()));
				level.playSound(null, player.blockPosition(), SoundEvents.UI_BUTTON_CLICK.value(), SoundSource.PLAYERS, 0.4f, 1.4f);
			}
			return InteractionResult.SUCCESS;
		}
		if (player.getCooldowns().isOnCooldown(glove)) return InteractionResult.FAIL;
		InfinityPower power = selected(glove);
		if (!(level instanceof ServerLevel server) || !(player instanceof ServerPlayer serverPlayer)) return InteractionResult.SUCCESS;
		if (!power.use(server, serverPlayer)) return InteractionResult.FAIL;
		player.getCooldowns().addCooldown(glove, power.cooldown());
		return InteractionResult.SUCCESS;
	}

	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> tooltip, TooltipFlag flag) {
		List<InfinityStone> stones = stones(stack);
		if (stones.isEmpty()) {
			tooltip.accept(Component.translatable("tooltip.lanternring.gauntlet_empty").withStyle(ChatFormatting.GRAY));
			return;
		}
		for (InfinityStone s : stones) tooltip.accept(Component.literal("◆ ").withStyle(s.chat).append(s.displayName()));
		InfinityPower power = selected(stack);
		tooltip.accept(Component.translatable("tooltip.lanternring.gauntlet_power", power.displayName()).withStyle(ChatFormatting.WHITE));
		tooltip.accept(power.description().copy().withStyle(ChatFormatting.DARK_GRAY));
		tooltip.accept(Component.translatable("tooltip.lanternring.gauntlet_help").withStyle(ChatFormatting.GRAY));
	}
}
