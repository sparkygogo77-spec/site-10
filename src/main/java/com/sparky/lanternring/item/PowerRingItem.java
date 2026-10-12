package com.sparky.lanternring.item;

import com.sparky.lanternring.HeldConstructs;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingFx;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingPowers;
import com.sparky.lanternring.block.PowerBatteryBlock;
import com.sparky.lanternring.net.RingFxPayload;
import java.util.function.Consumer;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUseAnimation;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;

/**
 * The power ring. Right-click uses the current mode (see RingMode); sneak + right-click cycles
 * modes; the flight key (see RingFlight) toggles flight. Everything runs on charge, restored at
 * a power battery, or by holding right-click with a battery in the off hand (see LanternCharge).
 */
public class PowerRingItem extends Item {
	public static final int MAX_CHARGE = 1000;

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
				RingFx.send((ServerLevel) level, RingFxPayload.Kind.MODE_CHANGE, user.position());
			}
			return InteractionResult.SUCCESS;
		}

		if (hand == InteractionHand.MAIN_HAND && LanternCharge.holdsBattery(user)) {
			// Hold to charge from the lantern; a quick tap fires the power on release instead.
			user.startUsingItem(hand);
			return InteractionResult.CONSUME;
		}

		RingMode mode = getMode(stack);
		if (!user.isCreative() && getCharge(stack) < mode.cost) {
			if (!level.isClientSide()) {
				user.sendOverlayMessage(Component.translatable("message.lanternring.no_charge").withStyle(ChatFormatting.RED));
				level.playSound(null, user.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.6f, 1.4f);
			}
			return InteractionResult.FAIL;
		}

		if (HeldConstructs.isHeldMode(mode)) {
			// Wall and Dome stay up for as long as right-click is held.
			if (!level.isClientSide() && !user.isCreative()) setCharge(stack, getCharge(stack) - mode.cost);
			user.startUsingItem(hand);
			return InteractionResult.CONSUME;
		}

		if (level instanceof ServerLevel serverLevel && !fire(serverLevel, user, stack, mode)) return InteractionResult.FAIL;
		return InteractionResult.SUCCESS;
	}

	/** Uses an instant (not held) mode, paying its charge. */
	private static boolean fire(ServerLevel level, Player user, ItemStack stack, RingMode mode) {
		if (!RingPowers.activate(mode, level, user)) return false;
		if (!user.isCreative()) setCharge(stack, getCharge(stack) - mode.cost);
		user.getCooldowns().addCooldown(stack, mode.cooldown);
		user.sendOverlayMessage(chargeText(stack));
		return true;
	}

	@Override
	public int getUseDuration(ItemStack stack, LivingEntity user) {
		return HeldConstructs.isHeldMode(getMode(stack)) || LanternCharge.holdsBattery(user) ? 72000 : 0;
	}

	@Override
	public ItemUseAnimation getUseAnimation(ItemStack stack) {
		return ItemUseAnimation.NONE;
	}

	@Override
	public void onUseTick(Level level, LivingEntity user, ItemStack stack, int remaining) {
		if (LanternCharge.isCharging(user)) {
			if (user instanceof ServerPlayer player) chargeTick((ServerLevel) level, player, stack, 72000 - remaining);
			return;
		}
		if (user instanceof ServerPlayer player && HeldConstructs.isHeldMode(getMode(stack))) {
			HeldConstructs.tick(player, getMode(stack), stack);
		}
	}

	@Override
	public boolean releaseUsing(ItemStack stack, Level level, LivingEntity user, int remaining) {
		// Only the server owns constructs. (In singleplayer the client shares this JVM, and touching
		// the server's world from the render thread deadlocks the game.)
		if (!level.isClientSide() && user instanceof Player player) {
			if (LanternCharge.holdsBattery(player) && player.getMainHandItem() == stack) {
				int held = 72000 - remaining;
				RingMode mode = getMode(stack);
				boolean canPay = player.isCreative() || getCharge(stack) >= mode.cost;
				if (held < LanternCharge.TAP && !HeldConstructs.isHeldMode(mode) && canPay
						&& !player.getCooldowns().isOnCooldown(stack)) {
					fire((ServerLevel) level, player, stack, mode);
				}
				return true;
			}
			HeldConstructs.release(player);
			player.getCooldowns().addCooldown(stack, getMode(stack).cooldown);
		}
		return true;
	}

	/** Server side of charging from the off-hand lantern, {@code held} ticks after right-click went down. */
	private static void chargeTick(ServerLevel level, ServerPlayer player, ItemStack stack, int held) {
		if (held == LanternCharge.HOLD) {
			level.playSound(null, player.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 0.8f, 1.4f);
		} else if (held == LanternCharge.HOLD + LanternCharge.REACH) {
			level.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1f, 0.8f);
		} else if (held == LanternCharge.done()) {
			PowerBatteryBlock.recharge(level, player, stack, player.getEyePosition().add(player.getLookAngle().scale(0.6)));
			level.playSound(null, player.blockPosition(), SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 1f, 1.2f);
		}
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
