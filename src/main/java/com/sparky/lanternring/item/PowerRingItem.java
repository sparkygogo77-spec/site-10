package com.sparky.lanternring.item;

import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingPowers;
import java.util.function.Consumer;
import net.minecraft.ChatFormatting;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;

/**
 * The power ring. Right-click uses the current mode (see RingMode); sneak + right-click cycles
 * modes; the flight key (see RingFlight) toggles flight. Everything runs on charge, restored at
 * a power battery.
 */
public class PowerRingItem extends Item {
	public static final int MAX_CHARGE = 1000;
	public static final DustParticleOptions GREEN_LIGHT = new DustParticleOptions(0x4DFF66, 1.2f);

	public PowerRingItem(Properties properties) {
		super(properties);
	}

	public static int getCharge(ItemStack stack) {
		return stack.getOrDefault(ModComponents.CHARGE, 0);
	}

	public static void setCharge(ItemStack stack, int charge) {
		stack.set(ModComponents.CHARGE, Mth.clamp(charge, 0, MAX_CHARGE));
	}

	public static boolean isFlightOn(ItemStack stack) {
		return stack.getOrDefault(ModComponents.FLIGHT, false);
	}

	public static RingMode getMode(ItemStack stack) {
		return RingMode.byIndex(stack.getOrDefault(ModComponents.MODE, 0));
	}

	@Override
	public InteractionResult use(Level level, Player user, InteractionHand hand) {
		ItemStack stack = user.getItemInHand(hand);

		if (user.isShiftKeyDown()) {
			if (!level.isClientSide()) {
				RingMode next = getMode(stack).next();
				stack.set(ModComponents.MODE, next.ordinal());
				user.sendOverlayMessage(Component.translatable("message.lanternring.mode", next.displayName())
						.withStyle(ChatFormatting.GREEN));
				level.playSound(null, user.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1f, 1.6f);
			}
			return InteractionResult.SUCCESS;
		}

		RingMode mode = getMode(stack);
		if (!user.isCreative() && getCharge(stack) < mode.cost) {
			if (!level.isClientSide()) {
				user.sendOverlayMessage(Component.translatable("message.lanternring.no_charge").withStyle(ChatFormatting.RED));
				level.playSound(null, user.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.6f, 1.4f);
			}
			return InteractionResult.FAIL;
		}

		if (level instanceof ServerLevel serverLevel) {
			if (!RingPowers.activate(mode, serverLevel, user)) return InteractionResult.FAIL;
			if (!user.isCreative()) setCharge(stack, getCharge(stack) - mode.cost);
			user.getCooldowns().addCooldown(stack, mode.cooldown);
			user.sendOverlayMessage(chargeText(stack));
		}
		return InteractionResult.SUCCESS;
	}

	public static Component chargeText(ItemStack stack) {
		int percent = Math.round(100f * getCharge(stack) / MAX_CHARGE);
		ChatFormatting color = percent > 25 ? ChatFormatting.GREEN : percent > 10 ? ChatFormatting.YELLOW : ChatFormatting.RED;
		return Component.translatable("message.lanternring.charge", percent).withStyle(color);
	}

	@Override
	public boolean isBarVisible(ItemStack stack) {
		return true;
	}

	@Override
	public int getBarWidth(ItemStack stack) {
		return Math.round(13f * getCharge(stack) / MAX_CHARGE);
	}

	@Override
	public int getBarColor(ItemStack stack) {
		return 0x3CFF5A;
	}

	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display,
			Consumer<Component> tooltip, TooltipFlag flag) {
		RingMode mode = getMode(stack);
		tooltip.accept(chargeText(stack));
		tooltip.accept(Component.translatable("tooltip.lanternring.mode", mode.displayName()).withStyle(ChatFormatting.WHITE));
		tooltip.accept(mode.description().copy().withStyle(ChatFormatting.DARK_GRAY));
		if (isFlightOn(stack)) tooltip.accept(Component.translatable("tooltip.lanternring.flight_on").withStyle(ChatFormatting.AQUA));
		tooltip.accept(Component.translatable("tooltip.lanternring.use").withStyle(ChatFormatting.GRAY));
		tooltip.accept(Component.translatable("tooltip.lanternring.cycle").withStyle(ChatFormatting.GRAY));
		tooltip.accept(Component.translatable("tooltip.lanternring.flight").withStyle(ChatFormatting.GRAY));
		tooltip.accept(Component.translatable("tooltip.lanternring.recharge").withStyle(ChatFormatting.DARK_GREEN));
	}
}
