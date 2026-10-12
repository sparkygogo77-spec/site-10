package com.sparky.lanternring.item;

import com.sparky.lanternring.Anvils;
import com.sparky.lanternring.HeldConstructs;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.Lasso;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingFx;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingPowers;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.block.PowerBatteryBlock;
import com.sparky.lanternring.net.RingFxPayload;
import java.util.Objects;
import java.util.function.Consumer;
import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
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
import net.minecraft.world.item.component.UseEffects;
import net.minecraft.world.level.Level;

/**
 * The power ring. Right-click uses the current mode (see RingMode); sneak + right-click cycles
 * modes; the flight key (see RingFlight) toggles flight. Everything runs on charge, restored at
 * a power battery, or by holding right-click with a battery in the off hand (see LanternCharge).
 */
public class PowerRingItem extends Item {
	public static final int MAX_CHARGE = 1000;
	/** Holding the Dome or a Lasso catch doesn't slow you down: walk, sprint and fly at full speed. */
	private static final UseEffects FULL_SPEED = new UseEffects(true, false, 1.0f);

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
		if (mode == RingMode.ANVIL) {
			// The Anvil aims with left-click (see Anvils); right-click picks its size.
			if (user instanceof ServerPlayer player) Anvils.cycleSize(player, stack);
			return InteractionResult.SUCCESS;
		}

		if (!user.isCreative() && getCharge(stack) < mode.cost) {
			if (!level.isClientSide()) {
				user.sendOverlayMessage(Component.translatable("message.lanternring.no_charge").withStyle(ChatFormatting.RED));
				level.playSound(null, user.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.6f, 1.4f);
			}
			return InteractionResult.FAIL;
		}

		if (mode == RingMode.BEAM) {
			// A tap fires on release; holding for RingTuning.BEAM_CHARGE fires the charged beam.
			user.startUsingItem(hand);
			return InteractionResult.CONSUME;
		}

		if (isHeld(mode)) {
			// The Dome stays up and the Lasso keeps its catch for as long as right-click is held.
			if (!level.isClientSide() && !user.isCreative()) setCharge(stack, getCharge(stack) - mode.cost);
			// Holding the Dome or the Lasso doesn't slow you down: you can run, sprint and fly with it.
			// Crouching still slows you as usual (and widens the dome, see HeldConstructs).
			UseEffects effects = mode == RingMode.DOME || mode == RingMode.TETHER ? FULL_SPEED : null;
			if (!Objects.equals(stack.get(DataComponents.USE_EFFECTS), effects)) {
				if (effects != null) stack.set(DataComponents.USE_EFFECTS, effects);
				else stack.remove(DataComponents.USE_EFFECTS);
			}
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
		user.getCooldowns().addCooldown(stack, RingTuning.cooldownTicks(mode));
		user.sendOverlayMessage(chargeText(stack));
		return true;
	}

	@Override
	public int getUseDuration(ItemStack stack, LivingEntity user) {
		RingMode mode = getMode(stack);
		return isHeld(mode) || mode == RingMode.BEAM || LanternCharge.holdsBattery(user) ? 72000 : 0;
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
		if (!(user instanceof ServerPlayer player)) return;
		RingMode mode = getMode(stack);
		if (mode == RingMode.BEAM) {
			beamChargeTick((ServerLevel) level, player, stack, 72000 - remaining);
		} else if (mode == RingMode.TETHER) {
			Lasso.tick(player, stack);
		} else if (HeldConstructs.isHeldMode(mode)) {
			HeldConstructs.tick(player, mode, stack);
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
				if (held < LanternCharge.TAP && !isHeld(mode) && canPay
						&& !player.getCooldowns().isOnCooldown(stack)) {
					fire((ServerLevel) level, player, stack, mode);
				}
				return true;
			}
			if (getMode(stack) == RingMode.BEAM) {
				// Let go before the charged shot went off: a normal tap shot.
				if (!player.getCooldowns().isOnCooldown(stack)) fire((ServerLevel) level, player, stack, RingMode.BEAM);
				return true;
			}
			HeldConstructs.release(player);
			Lasso.release(player);
			player.getCooldowns().addCooldown(stack, RingTuning.cooldownTicks(getMode(stack)));
		}
		return true;
	}

	/** Modes that last while right-click is held. */
	public static boolean isHeld(RingMode mode) {
		return HeldConstructs.isHeldMode(mode) || mode == RingMode.TETHER;
	}

	/**
	 * Server side of holding right-click in Beam mode: a rising hum while it builds, then at
	 * RingTuning.BEAM_CHARGE the charged beam fires on its own and the hold ends. Without the
	 * charge for it, nothing fires until release, which then shoots a normal beam.
	 */
	private static void beamChargeTick(ServerLevel level, ServerPlayer player, ItemStack stack, int held) {
		int full = Math.max(1, RingTuning.BEAM_CHARGE.ticks());
		if (held > 0 && held < full && held % 4 == 0) {
			level.playSound(null, player.blockPosition(), SoundEvents.BEACON_AMBIENT, SoundSource.PLAYERS, 0.6f, 0.8f + 1.2f * held / full);
		}
		if (held != full) return;
		if (!player.isCreative() && getCharge(stack) < RingPowers.BEAM_CHARGED_COST) return;
		RingPowers.beam(level, player, true);
		if (!player.isCreative()) setCharge(stack, getCharge(stack) - RingPowers.BEAM_CHARGED_COST);
		player.getCooldowns().addCooldown(stack, RingTuning.cooldownTicks(RingMode.BEAM));
		player.sendOverlayMessage(chargeText(stack));
		player.stopUsingItem();
	}

	/** Server side of charging from the off-hand lantern, {@code held} ticks after right-click went down. */
	private static void chargeTick(ServerLevel level, ServerPlayer player, ItemStack stack, int held) {
		if (held == LanternCharge.hold()) {
			level.playSound(null, player.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 0.8f, 1.4f);
		} else if (held == LanternCharge.hold() + LanternCharge.REACH) {
			level.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1f, 0.8f);
		} else if (held == LanternCharge.done()) {
			// The light bursts a little way ahead so it doesn't fill the screen.
			PowerBatteryBlock.recharge(level, player, stack, player.getEyePosition().add(player.getLookAngle().scale(1.6)).add(0, -0.5, 0));
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
		if (mode == RingMode.ANVIL) tooltip.accept(Anvils.sizeText(Anvils.size(stack)).copy().withStyle(ChatFormatting.WHITE));
		if (isFlightOn(stack)) tooltip.accept(Component.translatable("tooltip.lanternring.flight_on").withStyle(ChatFormatting.AQUA));
		tooltip.accept(Component.translatable("tooltip.lanternring.use").withStyle(ChatFormatting.GRAY));
		tooltip.accept(Component.translatable("tooltip.lanternring.cycle").withStyle(ChatFormatting.GRAY));
		tooltip.accept(Component.translatable("tooltip.lanternring.flight").withStyle(ChatFormatting.GRAY));
		tooltip.accept(Component.translatable("tooltip.lanternring.recharge").withStyle(ChatFormatting.DARK_GREEN));
		tooltip.accept(Component.translatable("tooltip.lanternring.version", LanternRing.version()).withStyle(ChatFormatting.DARK_GRAY));
	}
}
