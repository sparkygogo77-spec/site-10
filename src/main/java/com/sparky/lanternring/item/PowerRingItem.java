package com.sparky.lanternring.item;

import com.sparky.lanternring.Anvils;
import com.sparky.lanternring.BlackHoles;
import com.sparky.lanternring.BlastDrills;
import com.sparky.lanternring.Builds;
import com.sparky.lanternring.ClientHooks;
import com.sparky.lanternring.Deluges;
import com.sparky.lanternring.ConstructArmy;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.HeldConstructs;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.Lasso;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.PortalGun;
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
 * a power battery, or by holding left-click and right-click together with a battery in the off
 * hand (see LanternCharge).
 */
public class PowerRingItem extends Item {
	public static final int MAX_CHARGE = 1000;
	/** Holding the Dome, the Shield or a Lasso catch doesn't slow you down: walk, sprint and fly at full speed. */
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
		return Corps.of(stack).allowed(RingMode.byIndex(stack.getOrDefault(ModComponents.MODE, 0)));
	}

	/** Red Power Ring and so on; the green ring keeps its plain name. */
	@Override
	public Component getName(ItemStack stack) {
		Corps corps = Corps.of(stack);
		if (corps == Corps.GREEN) return super.getName(stack);
		return Component.translatable("item.lanternring.power_ring." + corps.getSerializedName());
	}

	// Everything the ring does runs with its corps current, so constructs and effects take its colour.

	@Override
	public InteractionResult use(Level level, Player user, InteractionHand hand) {
		Corps before = Corps.enter(Corps.of(user.getItemInHand(hand)));
		try {
			return useRing(level, user, hand);
		} finally {
			Corps.restore(before);
		}
	}

	@Override
	public void onUseTick(Level level, LivingEntity user, ItemStack stack, int remaining) {
		Corps before = Corps.enter(Corps.of(stack));
		try {
			useTick(level, user, stack, remaining);
		} finally {
			Corps.restore(before);
		}
	}

	@Override
	public boolean releaseUsing(ItemStack stack, Level level, LivingEntity user, int remaining) {
		Corps before = Corps.enter(Corps.of(stack));
		try {
			return release(stack, level, user, remaining);
		} finally {
			Corps.restore(before);
		}
	}

	private InteractionResult useRing(Level level, Player user, InteractionHand hand) {
		ItemStack stack = user.getItemInHand(hand);

		// Right-click with left-click held talks to the lantern; everything else is the ring's own power.
		boolean lanternCharge = hand == InteractionHand.MAIN_HAND && LanternCharge.wants(user);
		LanternCharge.begin(user, lanternCharge);
		if (lanternCharge) {
			// Hold both to charge from the lantern (the client calls it off if left-click lets go early).
			user.startUsingItem(hand);
			return InteractionResult.CONSUME;
		}

		RingMode mode = getMode(stack);
		if (mode == RingMode.BUILD) {
			// Hold to size an area, let go to clear it; then right-click builds the design showing (see Builds).
			if (level.isClientSide()) {
				// Crouching cycles modes (or calls off a build); while one is being chosen the click builds it.
				if (user.isShiftKeyDown() || ClientHooks.buildBusy.getAsBoolean()) return InteractionResult.SUCCESS;
				user.startUsingItem(hand);
				return InteractionResult.CONSUME;
			}
			if (user instanceof ServerPlayer player) {
				if (Builds.press(player, stack, user.isShiftKeyDown())) return InteractionResult.SUCCESS;
				if (user.isShiftKeyDown()) {
					cycleMode(player.level(), user, stack);
					return InteractionResult.SUCCESS;
				}
			}
			user.startUsingItem(hand);
			return InteractionResult.CONSUME;
		}

		if (user.isShiftKeyDown()) {
			if (level instanceof ServerLevel serverLevel) cycleMode(serverLevel, user, stack);
			return InteractionResult.SUCCESS;
		}

		if (mode == RingMode.ANVIL || mode == RingMode.DELUGE || mode == RingMode.BLACK_HOLE) {
			// Hold right-click to aim the marker, let go to drop (see Anvils); left-click while
			// aiming picks the size. The charge and cooldown are checked as it aims.
			user.startUsingItem(hand);
			return InteractionResult.CONSUME;
		}

		if (mode == RingMode.ARMY) {
			// Hold right-click to aim, left-click to pick the construct, let go to summon it (see
			// ConstructArmy). Any charge at all will do: the last of it makes a shorter-lived ally.
			if (!user.isCreative() && getCharge(stack) <= 0) {
				if (!level.isClientSide()) {
					user.sendOverlayMessage(Component.translatable("message.lanternring.no_charge").withStyle(ChatFormatting.RED));
					level.playSound(null, user.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.6f, 1.4f);
				}
				return InteractionResult.FAIL;
			}
			user.startUsingItem(hand);
			return InteractionResult.CONSUME;
		}

		if (mode == RingMode.PORTAL) {
			// A tap opens a portal to the exit, holding sets the exit (see PortalGun; it checks the charge).
			user.startUsingItem(hand);
			return InteractionResult.CONSUME;
		}

		if (mode == RingMode.BLAST) {
			// Hold to charge the drill's reach; it goes on release (see BlastDrills).
			if (!user.isCreative() && getCharge(stack) < BlastDrills.cost(BlastDrills.level(stack), 0f)) {
				if (!level.isClientSide()) {
					user.sendOverlayMessage(Component.translatable("message.lanternring.no_charge").withStyle(ChatFormatting.RED));
					level.playSound(null, user.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.6f, 1.4f);
				}
				return InteractionResult.FAIL;
			}
			if (user instanceof ServerPlayer player) BlastDrills.beginCharge(player);
			user.startUsingItem(hand);
			return InteractionResult.CONSUME;
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
			UseEffects effects = mode == RingMode.DOME || mode == RingMode.SHIELD || mode == RingMode.TETHER ? FULL_SPEED : null;
			if (!Objects.equals(stack.get(DataComponents.USE_EFFECTS), effects)) {
				if (effects != null) stack.set(DataComponents.USE_EFFECTS, effects);
				else stack.remove(DataComponents.USE_EFFECTS);
			}
			if (mode == RingMode.TETHER && user instanceof ServerPlayer player) Lasso.pressed(player);
			user.startUsingItem(hand);
			return InteractionResult.CONSUME;
		}

		if (level instanceof ServerLevel serverLevel && !fire(serverLevel, user, stack, mode)) return InteractionResult.FAIL;
		return InteractionResult.SUCCESS;
	}

	private static void cycleMode(ServerLevel level, Player user, ItemStack stack) {
		Corps corps = Corps.of(stack);
		RingMode next = corps.next(getMode(stack));
		stack.set(ModComponents.MODE, next.ordinal());
		user.sendOverlayMessage(Component.translatable("message.lanternring.mode", corps.modeName(next))
				.withStyle(corps.chat));
		level.playSound(null, user.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1f, 1.6f);
		RingFx.send(level, RingFxPayload.Kind.MODE_CHANGE, user.position(), user.position(), 0f, 0, user);
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
		return isHeld(mode) || mode == RingMode.BEAM || mode == RingMode.BLAST || mode == RingMode.ANVIL || mode == RingMode.DELUGE
				|| mode == RingMode.PORTAL || mode == RingMode.BLACK_HOLE || mode == RingMode.BUILD || mode == RingMode.ARMY || LanternCharge.started(user) ? 72000 : 0;
	}

	@Override
	public ItemUseAnimation getUseAnimation(ItemStack stack) {
		return ItemUseAnimation.NONE;
	}

	private static void useTick(Level level, LivingEntity user, ItemStack stack, int remaining) {
		if (LanternCharge.isCharging(user)) {
			if (user instanceof ServerPlayer player) chargeTick((ServerLevel) level, player, stack, 72000 - remaining);
			return;
		}
		if (!(user instanceof ServerPlayer player)) return;
		RingMode mode = getMode(stack);
		if (mode == RingMode.BLAST) {
			BlastDrills.chargeTick(player);
		} else if (mode == RingMode.BEAM) {
			beamChargeTick((ServerLevel) level, player, stack, 72000 - remaining);
		} else if (mode == RingMode.ANVIL) {
			Anvils.aimTick(player, stack);
		} else if (mode == RingMode.BUILD) {
			Builds.selectTick(player, stack);
		} else if (mode == RingMode.DELUGE) {
			Deluges.aimTick(player, stack);
		} else if (mode == RingMode.PORTAL) {
			PortalGun.holdTick((ServerLevel) level, player, stack, 72000 - remaining);
		} else if (mode == RingMode.BLACK_HOLE) {
			BlackHoles.aimTick(player, stack);
		} else if (mode == RingMode.ARMY) {
			ConstructArmy.aimTick(player, stack, 72000 - remaining);
		} else if (mode == RingMode.TETHER) {
			Lasso.tick(player, stack);
		} else if (HeldConstructs.isHeldMode(mode)) {
			HeldConstructs.tick(player, mode, stack);
		}
	}

	private static boolean release(ItemStack stack, Level level, LivingEntity user, int remaining) {
		// Only the server owns constructs. (In singleplayer the client shares this JVM, and touching
		// the server's world from the render thread deadlocks the game.)
		if (!level.isClientSide() && user instanceof Player player) {
			if (LanternCharge.started(player)) {
				LanternCharge.begin(player, false);
				return true;
			}
			if (LanternCharge.wants(player)) {
				// Left-click went down mid-power: the client let go to start a lantern charge.
				// Drop whatever was up quietly: no beam shot, no anvil, no cooldown to block the charge.
				HeldConstructs.release(player);
				Lasso.release(player);
				Anvils.cancel(player);
				Deluges.cancel(player);
				BlackHoles.cancel(player);
				if (player instanceof ServerPlayer serverPlayer) BlastDrills.cancel(serverPlayer);
				if (getMode(stack) == RingMode.BUILD) Builds.cancel(player, false);
				return true;
			}
			if (getMode(stack) == RingMode.BEAM) {
				// Let go before the charged shot went off: a normal tap shot.
				if (!player.getCooldowns().isOnCooldown(stack)) fire((ServerLevel) level, player, stack, RingMode.BEAM);
				return true;
			}
			if (getMode(stack) == RingMode.BLAST) {
				if (player instanceof ServerPlayer serverPlayer) BlastDrills.release((ServerLevel) level, serverPlayer, stack);
				return true;
			}
			if (getMode(stack) == RingMode.ARMY) {
				if (player instanceof ServerPlayer serverPlayer && !player.getCooldowns().isOnCooldown(stack)) ConstructArmy.release(serverPlayer, stack);
				return true;
			}
			// Letting go in Build mode chooses the area and clears it.
			if (getMode(stack) == RingMode.BUILD) {
				if (player instanceof ServerPlayer serverPlayer) Builds.release(serverPlayer, stack);
				return true;
			}
			if (getMode(stack) == RingMode.PORTAL) {
				// Let go before the exit was set: a tap, which opens a portal.
				if (player instanceof ServerPlayer serverPlayer && !player.getCooldowns().isOnCooldown(stack)) {
					PortalGun.tap((ServerLevel) level, serverPlayer, stack);
				}
				return true;
			}
			// Letting go in Anvil mode drops the anvil where the marker is (Anvils sets the cooldown).
			if (getMode(stack) == RingMode.ANVIL) {
				if (player instanceof ServerPlayer serverPlayer) Anvils.release(serverPlayer, stack);
				return true;
			}
			if (getMode(stack) == RingMode.DELUGE) {
				if (player instanceof ServerPlayer serverPlayer) Deluges.release(serverPlayer, stack);
				return true;
			}
			if (getMode(stack) == RingMode.BLACK_HOLE) {
				if (player instanceof ServerPlayer serverPlayer) BlackHoles.release(serverPlayer, stack);
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
		} else if (held > LanternCharge.hold() + LanternCharge.REACH && held < LanternCharge.done()) {
			// A hum that climbs in pitch and speeds up as the light builds toward the burst.
			float x = (held - LanternCharge.hold() - LanternCharge.REACH) / (float) (LanternCharge.done() - LanternCharge.hold() - LanternCharge.REACH);
			int every = x < 0.5f ? 6 : x < 0.8f ? 4 : 2;
			if (held % every == 0) {
				level.playSound(null, player.blockPosition(), SoundEvents.BEACON_AMBIENT, SoundSource.PLAYERS, 0.5f + 0.5f * x, 0.6f + 1.4f * x);
			}
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
		return Corps.of(stack).rgb;
	}

	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display,
			Consumer<Component> tooltip, TooltipFlag flag) {
		RingMode mode = getMode(stack);
		Corps corps = Corps.of(stack);
		if (corps != Corps.GREEN) tooltip.accept(Component.translatable("tooltip.lanternring.corps",
				Component.translatable("corps.lanternring." + corps.getSerializedName()), corps.emotion()).withStyle(corps.chat));
		tooltip.accept(chargeText(stack));
		tooltip.accept(Component.translatable("tooltip.lanternring.mode", corps.modeName(mode)).withStyle(ChatFormatting.WHITE));
		tooltip.accept(corps.modeDescription(mode).copy().withStyle(ChatFormatting.DARK_GRAY));
		if (mode == RingMode.BLAST) tooltip.accept(BlastDrills.levelText(BlastDrills.level(stack)).copy().withStyle(ChatFormatting.WHITE));
		if (mode == RingMode.BUILD) tooltip.accept(Component.translatable("tooltip.lanternring.build_shape", Builds.shapeText(Builds.shape(stack))).withStyle(ChatFormatting.WHITE));
		if (mode == RingMode.ARMY) tooltip.accept(ConstructArmy.typeText(ConstructArmy.type(stack)).copy().withStyle(ChatFormatting.WHITE));
		if (mode == RingMode.ANVIL) tooltip.accept(Anvils.sizeText(Anvils.size(stack)).copy().withStyle(ChatFormatting.WHITE));
		if (mode == RingMode.DELUGE) tooltip.accept(Deluges.levelText(Deluges.level(stack)).copy().withStyle(ChatFormatting.WHITE));
		if (mode == RingMode.PORTAL || mode == RingMode.GOLEM) {
			var exit = PortalGun.exit(stack);
			tooltip.accept((exit == null ? Component.translatable("tooltip.lanternring.portal_no_exit")
					: Component.translatable("tooltip.lanternring.portal_exit", exit.pos().pos().getX(), exit.pos().pos().getY(),
							exit.pos().pos().getZ(), exit.pos().dimension().identifier().getPath())).withStyle(ChatFormatting.WHITE));
		}
		if (mode == RingMode.BLACK_HOLE) tooltip.accept(BlackHoles.sizeText(BlackHoles.size(stack)).copy().withStyle(ChatFormatting.WHITE));
		if (isFlightOn(stack)) tooltip.accept(Component.translatable("tooltip.lanternring.flight_on").withStyle(ChatFormatting.AQUA));
		tooltip.accept(Component.translatable("tooltip.lanternring.use").withStyle(ChatFormatting.GRAY));
		tooltip.accept(Component.translatable("tooltip.lanternring.cycle").withStyle(ChatFormatting.GRAY));
		tooltip.accept(Component.translatable("tooltip.lanternring.flight").withStyle(ChatFormatting.GRAY));
		tooltip.accept((corps == Corps.GREEN ? Component.translatable("tooltip.lanternring.recharge")
				: Component.translatable("tooltip.lanternring.recharge." + corps.getSerializedName())).withStyle(ChatFormatting.DARK_GRAY));
		tooltip.accept(Component.translatable("tooltip.lanternring.version", LanternRing.version()).withStyle(ChatFormatting.DARK_GRAY));
	}
}
