package com.sparky.lanternring.item;

import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingPowers;
import java.util.List;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.item.tooltip.TooltipType;
import net.minecraft.particle.DustParticleEffect;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.Hand;
import net.minecraft.util.TypedActionResult;
import net.minecraft.util.math.MathHelper;
import net.minecraft.world.World;
import org.joml.Vector3f;

/**
 * The power ring. Right-click uses the current mode (see RingMode); sneak + right-click cycles
 * modes; the flight key (see RingFlight) toggles flight. Everything runs on charge, restored at
 * a power battery.
 */
public class PowerRingItem extends Item {
	public static final int MAX_CHARGE = 1000;
	public static final DustParticleEffect GREEN_LIGHT = new DustParticleEffect(new Vector3f(0.3f, 1f, 0.4f), 1.2f);

	public PowerRingItem(Settings settings) {
		super(settings);
	}

	public static int getCharge(ItemStack stack) {
		return stack.getOrDefault(ModComponents.CHARGE, 0);
	}

	public static void setCharge(ItemStack stack, int charge) {
		stack.set(ModComponents.CHARGE, MathHelper.clamp(charge, 0, MAX_CHARGE));
	}

	public static boolean isFlightOn(ItemStack stack) {
		return stack.getOrDefault(ModComponents.FLIGHT, false);
	}

	public static RingMode getMode(ItemStack stack) {
		return RingMode.byIndex(stack.getOrDefault(ModComponents.MODE, 0));
	}

	@Override
	public TypedActionResult<ItemStack> use(World world, PlayerEntity user, Hand hand) {
		ItemStack stack = user.getStackInHand(hand);

		if (user.isSneaking()) {
			if (!world.isClient) {
				RingMode next = getMode(stack).next();
				stack.set(ModComponents.MODE, next.ordinal());
				user.sendMessage(Text.translatable("message.lanternring.mode", next.displayName())
						.formatted(Formatting.GREEN), true);
				world.playSound(null, user.getBlockPos(), SoundEvents.BLOCK_AMETHYST_BLOCK_CHIME,
						SoundCategory.PLAYERS, 1f, 1.6f);
			}
			return TypedActionResult.success(stack, world.isClient);
		}

		RingMode mode = getMode(stack);
		if (!user.isCreative() && getCharge(stack) < mode.cost) {
			if (!world.isClient) {
				user.sendMessage(Text.translatable("message.lanternring.no_charge").formatted(Formatting.RED), true);
				world.playSound(null, user.getBlockPos(), SoundEvents.BLOCK_BEACON_DEACTIVATE, SoundCategory.PLAYERS, 0.6f, 1.4f);
			}
			return TypedActionResult.fail(stack);
		}

		if (world instanceof ServerWorld serverWorld) {
			if (!RingPowers.activate(mode, serverWorld, user)) return TypedActionResult.fail(stack);
			if (!user.isCreative()) setCharge(stack, getCharge(stack) - mode.cost);
			user.getItemCooldownManager().set(this, mode.cooldown);
			user.sendMessage(chargeText(stack), true);
		}
		return TypedActionResult.success(stack, world.isClient);
	}

	public static Text chargeText(ItemStack stack) {
		int percent = Math.round(100f * getCharge(stack) / MAX_CHARGE);
		Formatting color = percent > 25 ? Formatting.GREEN : percent > 10 ? Formatting.YELLOW : Formatting.RED;
		return Text.translatable("message.lanternring.charge", percent).formatted(color);
	}

	@Override
	public boolean isItemBarVisible(ItemStack stack) {
		return true;
	}

	@Override
	public int getItemBarStep(ItemStack stack) {
		return Math.round(13f * getCharge(stack) / MAX_CHARGE);
	}

	@Override
	public int getItemBarColor(ItemStack stack) {
		return 0x3CFF5A;
	}

	@Override
	public void appendTooltip(ItemStack stack, TooltipContext context, List<Text> tooltip, TooltipType type) {
		RingMode mode = getMode(stack);
		tooltip.add(chargeText(stack));
		tooltip.add(Text.translatable("tooltip.lanternring.mode", mode.displayName()).formatted(Formatting.WHITE));
		tooltip.add(mode.description().copy().formatted(Formatting.DARK_GRAY));
		if (isFlightOn(stack)) tooltip.add(Text.translatable("tooltip.lanternring.flight_on").formatted(Formatting.AQUA));
		tooltip.add(Text.translatable("tooltip.lanternring.use").formatted(Formatting.GRAY));
		tooltip.add(Text.translatable("tooltip.lanternring.cycle").formatted(Formatting.GRAY));
		tooltip.add(Text.translatable("tooltip.lanternring.flight").formatted(Formatting.GRAY));
		tooltip.add(Text.translatable("tooltip.lanternring.recharge").formatted(Formatting.DARK_GREEN));
	}
}
