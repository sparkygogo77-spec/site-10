package com.sparky.lanternring.item;

import com.sparky.lanternring.Anvils;
import com.sparky.lanternring.corps.AerialDrops;
import com.sparky.lanternring.corps.FearNuke;
import com.sparky.lanternring.BlackHoles;
import com.sparky.lanternring.BlastDrills;
import com.sparky.lanternring.Builds;
import com.sparky.lanternring.Bridges;
import com.sparky.lanternring.Saws;
import com.sparky.lanternring.ClientHooks;
import com.sparky.lanternring.Deluges;
import com.sparky.lanternring.ConstructArmy;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.HeldConstructs;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.LanternFlash;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.Lasso;
import com.sparky.lanternring.ModComponents;
import com.sparky.lanternring.PortalGun;
import com.sparky.lanternring.RingFx;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingPowers;
import com.sparky.lanternring.RingSounds;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.Shockwaves;
import com.sparky.lanternring.block.PowerBatteryBlock;
import com.sparky.lanternring.net.RingFxPayload;
import java.util.Objects;
import java.util.function.Consumer;
import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.core.BlockPos;
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

	/**
	 * How much light a held ring gives off under a shader pack (Iris asks every item through
	 * {@link #getLightEmission}). The client sets it: on only with the Lantern Ring copy of a pack,
	 * which colours the light by the ring's corps (other packs would light it white).
	 */
	public static java.util.function.IntSupplier shaderHeldLight = () -> 0;
	/**
	 * How dimmed the sunlight round a charging ring is (0..1) for the Lantern Ring copy of a shader
	 * pack, or -1 without one. The client sets it (SunDim); it rides in {@link #getLightColor}.
	 */
	public static java.util.function.DoubleSupplier shaderSunDim = () -> -1;

	public PowerRingItem(Properties properties) {
		super(properties);
	}

	public static int getCharge(ItemStack stack) {
		return stack.getOrDefault(ModComponents.CHARGE, 0);
	}

	/**
	 * Sets the ring's charge. A ring with a Hope boost (see {@link #hopeReserve}) pays for what it
	 * spends out of the boost first, so the boost works as charge past full.
	 */
	public static void setCharge(ItemStack stack, int charge) {
		int now = getCharge(stack);
		int over = overcharge(stack);
		if (over > 0 && charge < now) {
			int fromOver = Math.min(over, now - charge);
			charge += fromOver;
			setOvercharge(stack, over - fromOver);
		}
		int reserve = hopeReserve(stack);
		if (reserve > 0 && charge < now) {
			int fromReserve = Math.min(reserve, now - charge);
			charge += fromReserve;
			setHopeReserve(stack, reserve - fromReserve);
		}
		stack.set(ModComponents.CHARGE, Mth.clamp(charge, 0, MAX_CHARGE));
	}

	/** Extra charge past full from an overcharge at the lantern (see LanternCharge). */
	public static int overcharge(ItemStack stack) {
		return stack.getOrDefault(ModComponents.OVERCHARGE, 0);
	}

	public static void setOvercharge(ItemStack stack, int over) {
		if (over <= 0) stack.remove(ModComponents.OVERCHARGE);
		else stack.set(ModComponents.OVERCHARGE, Math.min(over, LanternCharge.OVERCHARGE_MAX));
	}

	/** The Hope boost's extra charge (a Blue city's crown lantern gives a Green ring up to a full ring more). */
	public static int hopeReserve(ItemStack stack) {
		return stack.getOrDefault(ModComponents.HOPE_RESERVE, 0);
	}

	public static void setHopeReserve(ItemStack stack, int reserve) {
		if (reserve <= 0) stack.remove(ModComponents.HOPE_RESERVE);
		else stack.set(ModComponents.HOPE_RESERVE, Math.min(reserve, MAX_CHARGE));
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

	/** Crouch and use the ring on a Blue lantern: its rescue squad flies out (J, 2026-10-13; see corps.BlueSquad). */
	@Override
	public InteractionResult useOn(net.minecraft.world.item.context.UseOnContext context) {
		Player user = context.getPlayer();
		BlockPos pos = context.getClickedPos();
		var state = context.getLevel().getBlockState(pos);
		if (user == null || !user.isShiftKeyDown() || !state.is(com.sparky.lanternring.ModRegistry.POWER_BATTERY) || Corps.of(state) != Corps.BLUE) {
			return InteractionResult.PASS;
		}
		if (context.getLevel() instanceof ServerLevel level && user instanceof ServerPlayer player) {
			com.sparky.lanternring.corps.BlueSquad.summon(level, pos, player);
		}
		return InteractionResult.SUCCESS;
	}

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

		if (mode == RingMode.ANVIL || mode == RingMode.DELUGE || mode == RingMode.BLACK_HOLE || mode == RingMode.AERIAL || mode == RingMode.HAMMER) {
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

		if (mode == RingMode.BRIDGE) {
			// Hold to pick the starting block and lock its level; left-click held builds (see Bridges).
			if (!user.isCreative() && getCharge(stack) < Bridges.STEP_COST) {
				if (!level.isClientSide()) user.sendOverlayMessage(Component.translatable("message.lanternring.no_charge").withStyle(ChatFormatting.RED));
				return InteractionResult.FAIL;
			}
			if (user instanceof ServerPlayer player) Bridges.begin(player);
			user.startUsingItem(hand);
			return InteractionResult.CONSUME;
		}

		if (mode == RingMode.SAW) {
			// Hold to pick a block, drag to form the saw, left-click held spins it forward (see Saws).
			if (!user.isCreative() && getCharge(stack) < RingMode.SAW.cost) {
				if (!level.isClientSide()) user.sendOverlayMessage(Component.translatable("message.lanternring.no_charge").withStyle(ChatFormatting.RED));
				return InteractionResult.FAIL;
			}
			if (user instanceof ServerPlayer player) Saws.begin(player);
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

		if (mode == RingMode.WALL) {
			// Hold to draw the wall: it's pinned where you aim and grows as you drag (see
			// HeldConstructs.beginWall); it goes up on release, paid for by its size.
			if (user instanceof ServerPlayer player) HeldConstructs.beginWall(player);
			user.startUsingItem(hand);
			return InteractionResult.CONSUME;
		}

		if (mode == RingMode.BEAM || mode == RingMode.PUSH) {
			// A tap fires on release; holding for RingTuning.BEAM_CHARGE fires the charged beam.
			// The Shockwave goes on release too, bigger the longer it was held (RingTuning.SHOCKWAVE_CHARGE).
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
			if (level instanceof ServerLevel serverLevel) {
				if (mode == RingMode.DOME) RingSounds.domeUp(serverLevel, user);
				else if (mode == RingMode.SHIELD) RingSounds.shieldUp(serverLevel, user);
			}
			user.startUsingItem(hand);
			return InteractionResult.CONSUME;
		}

		if (level instanceof ServerLevel serverLevel && !fire(serverLevel, user, stack, mode)) return InteractionResult.FAIL;
		return InteractionResult.SUCCESS;
	}

	private static void cycleMode(ServerLevel level, Player user, ItemStack stack) {
		selectMode(level, user, stack, Corps.of(stack).next(getMode(stack)));
	}

	/** Switches the ring to a mode its corps has (the mode wheel picks one directly). */
	public static void selectMode(ServerLevel level, Player user, ItemStack stack, RingMode next) {
		Corps corps = Corps.of(stack);
		if (!corps.has(next)) return;
		stack.set(ModComponents.MODE, next.ordinal());
		// The charge meter shows the new mode's name, so the action bar stays clear.
		level.playSound(null, user.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1f, 1.6f);
		RingFx.send(level, RingFxPayload.Kind.MODE_CHANGE, user.position(), user.position(), 0f, 0, user);
	}

	/** Uses an instant (not held) mode, paying its charge. */
	private static boolean fire(ServerLevel level, Player user, ItemStack stack, RingMode mode) {
		if (!RingPowers.activate(mode, level, user)) return false;
		if (!user.isCreative()) setCharge(stack, getCharge(stack) - mode.cost);
		user.getCooldowns().addCooldown(stack, RingTuning.cooldownTicks(mode));
		return true;
	}

	@Override
	public int getUseDuration(ItemStack stack, LivingEntity user) {
		RingMode mode = getMode(stack);
		return isHeld(mode) || mode == RingMode.BEAM || mode == RingMode.PUSH || mode == RingMode.WALL || mode == RingMode.BRIDGE || mode == RingMode.SAW || mode == RingMode.BLAST || mode == RingMode.ANVIL || mode == RingMode.DELUGE
				|| mode == RingMode.AERIAL || mode == RingMode.HAMMER || mode == RingMode.PORTAL || mode == RingMode.BLACK_HOLE || mode == RingMode.BUILD || mode == RingMode.ARMY || LanternCharge.started(user) ? 72000 : 0;
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
		} else if (mode == RingMode.PUSH) {
			shockwaveChargeTick((ServerLevel) level, player, stack, 72000 - remaining);
		} else if (mode == RingMode.WALL) {
			HeldConstructs.wallTick(player, stack);
		} else if (mode == RingMode.BRIDGE) {
			Bridges.tick(player);
		} else if (mode == RingMode.SAW) {
			Saws.tick(player, stack);
		} else if (mode == RingMode.ANVIL) {
			Anvils.aimTick(player, stack);
		} else if (mode == RingMode.BUILD) {
			Builds.selectTick(player, stack);
		} else if (mode == RingMode.DELUGE) {
			Deluges.aimTick(player, stack);
		} else if (mode == RingMode.AERIAL) {
			AerialDrops.aimTick(player, stack);
		} else if (mode == RingMode.HAMMER) {
			com.sparky.lanternring.HammerSlams.aimTick(player, stack);
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
			if (LanternCharge.switching(player)) {
				// Left-click went down mid-power: the client let go to start a lantern charge.
				// Drop whatever was up quietly: no beam shot, no anvil, no cooldown to block the charge.
				HeldConstructs.release(player);
				HeldConstructs.cancelWall(player);
				Bridges.cancel(player);
				Saws.cancel(player);
				Lasso.release(player);
				Anvils.cancel(player);
				Deluges.cancel(player);
				AerialDrops.cancel(player);
				com.sparky.lanternring.HammerSlams.cancel(player);
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
			if (getMode(stack) == RingMode.PUSH) {
				if (!player.getCooldowns().isOnCooldown(stack)) releaseShockwave((ServerLevel) level, player, stack, 72000 - remaining);
				return true;
			}
			if (getMode(stack) == RingMode.BRIDGE) {
				Bridges.release(player);
				player.getCooldowns().addCooldown(stack, RingTuning.cooldownTicks(RingMode.BRIDGE));
				player.sendOverlayMessage(chargeText(stack));
				return true;
			}
			if (getMode(stack) == RingMode.SAW) {
				Saws.release(player);
				player.getCooldowns().addCooldown(stack, RingTuning.cooldownTicks(RingMode.SAW));
				player.sendOverlayMessage(chargeText(stack));
				return true;
			}
			if (getMode(stack) == RingMode.WALL) {
				if (player instanceof ServerPlayer serverPlayer && HeldConstructs.finishWall(serverPlayer, stack)) {
					player.getCooldowns().addCooldown(stack, RingTuning.cooldownTicks(RingMode.WALL));
					player.sendOverlayMessage(chargeText(stack));
				}
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
			if (getMode(stack) == RingMode.AERIAL) {
				if (player instanceof ServerPlayer serverPlayer) AerialDrops.release(serverPlayer, stack);
				return true;
			}
			if (getMode(stack) == RingMode.HAMMER) {
				if (player instanceof ServerPlayer serverPlayer) {
					// A tap swings the construct hammer at what's in front of you (pass 503 R2); a hold aims the leap.
					int held = 72000 - remaining;
					if (held <= RingTuning.HAMMER_TAP.ticks() && !com.sparky.lanternring.HammerSlams.leaping(player)) {
						com.sparky.lanternring.HammerSlams.cancel(player);
						com.sparky.lanternring.ConstructHammers.start(serverPlayer, held);
					} else {
						com.sparky.lanternring.HammerSlams.release(serverPlayer, stack);
					}
				}
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
		player.stopUsingItem();
	}

	/** How far a Shockwave held this many ticks has charged, 0 to 1. */
	private static float shockwaveCharge(int held) {
		return Mth.clamp(held / (float) Math.max(1, RingTuning.SHOCKWAVE_CHARGE.ticks()), 0f, 1f);
	}

	/** Holding right-click in Shockwave mode: a rising hum while it builds, and a chime when it's full. */
	private static void shockwaveChargeTick(ServerLevel level, ServerPlayer player, ItemStack stack, int held) {
		int full = Math.max(1, RingTuning.SHOCKWAVE_CHARGE.ticks());
		if (held > 2 && held < full && held % 4 == 0) {
			level.playSound(null, player.blockPosition(), SoundEvents.BEACON_AMBIENT, SoundSource.PLAYERS, 0.6f, 0.6f + 1.0f * held / full);
		} else if (held == full) {
			level.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1f, 1.8f);
		}
	}

	/** Right-click let go in Shockwave mode: the wave goes, as big as it was charged, paying for its size. */
	private static void releaseShockwave(ServerLevel level, Player player, ItemStack stack, int held) {
		float charge = shockwaveCharge(held);
		int cost = Shockwaves.cost(charge);
		if (!player.isCreative() && getCharge(stack) < cost) {
			// Not enough for the charged wave: a tap's worth still goes if the ring has that.
			charge = 0f;
			cost = Shockwaves.cost(0f);
			if (getCharge(stack) < cost) return;
		}
		Shockwaves.start(level, player, charge);
		if (!player.isCreative()) setCharge(stack, getCharge(stack) - cost);
		player.getCooldowns().addCooldown(stack, RingTuning.cooldownTicks(RingMode.PUSH));
		player.sendOverlayMessage(chargeText(stack));
	}

	/** Server side of charging from the off-hand lantern, {@code held} ticks after right-click went down. */
	private static void chargeTick(ServerLevel level, ServerPlayer player, ItemStack stack, int held) {
		// The light pouring out is a flashbang for anyone looking (see LanternFlash).
		LanternFlash.tick(level, player, held);
		if (held == LanternCharge.hold()) {
			LanternCharge.overcharging(player, false);
			level.playSound(null, player.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 0.8f, 1.4f);
		} else if (held == LanternCharge.hold() + LanternCharge.reach()) {
		com.sparky.lanternring.WhatsNew.done(player, "lantern.charge");
			level.playSound(null, player.blockPosition(), SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.PLAYERS, 1f, 0.8f);
		}
		// J: the ring fills over the charge (shown on the meter), so letting go early keeps what it got.
		if (held > LanternCharge.hold() && held < LanternCharge.done()) {
			int target = Math.round(MAX_CHARGE * LanternCharge.progress(held));
			if (target > getCharge(stack)) stack.set(ModComponents.CHARGE, target);
		}
		if (held > LanternCharge.hold() + LanternCharge.reach() && held < LanternCharge.done()) {
			// A hum that climbs in pitch and speeds up as the light builds toward the burst.
			float x = (held - LanternCharge.hold() - LanternCharge.reach()) / (float) (LanternCharge.done() - LanternCharge.hold() - LanternCharge.reach());
			int every = x < 0.5f ? 6 : x < 0.8f ? 4 : 2;
			if (held % every == 0) {
				level.playSound(null, player.blockPosition(), SoundEvents.BEACON_AMBIENT, SoundSource.PLAYERS, 0.5f + 0.5f * x, 0.6f + 1.4f * x);
			}
		} else if (held == LanternCharge.done()) {
			// The light bursts a little way ahead so it doesn't fill the screen.
			PowerBatteryBlock.recharge(level, player, stack, player.getEyePosition().add(player.getLookAngle().scale(1.6)).add(0, -0.5, 0));
			level.playSound(null, player.blockPosition(), SoundEvents.BEACON_ACTIVATE, SoundSource.PLAYERS, 1f, 1.2f);
		} else if (held > LanternCharge.done()) {
			overchargeTick(level, player, stack, held);
		}
	}

	/**
	 * Holding on past full overcharges the ring up to +25%. Once the short grace after full is over,
	 * it burns {@link LanternCharge#OVERCHARGE_BURN} of the battery's {@link LanternCharge#BATTERY_CHARGES} charges.
	 */
	private static void overchargeTick(ServerLevel level, ServerPlayer player, ItemStack stack, int held) {
		ItemStack battery = player.getOffhandItem();
		if (held == LanternCharge.overStart()) {
			if (!LanternCharge.canOvercharge(battery)) {
				player.sendOverlayMessage(Component.translatable("message.lanternring.battery_burnt_out").withStyle(ChatFormatting.RED));
				return;
			}
			if (!player.isCreative()) LanternCharge.burn(battery);
			LanternCharge.overcharging(player, true);
			level.playSound(null, player.blockPosition(), SoundEvents.RESPAWN_ANCHOR_CHARGE, SoundSource.PLAYERS, 1f, 1.3f);
		}
		if (!LanternCharge.overcharging(player)) return;
		float x = LanternCharge.overProgress(held);
		int target = Math.round(LanternCharge.OVERCHARGE_MAX * x);
		if (target > overcharge(stack)) setOvercharge(stack, target);
		if (held < LanternCharge.overDone()) {
			if (held % 2 == 0) level.playSound(null, player.blockPosition(), SoundEvents.BEACON_AMBIENT, SoundSource.PLAYERS, 1f, 1.6f + 0.4f * x);
		} else if (held == LanternCharge.overDone()) {
			level.playSound(null, player.blockPosition(), SoundEvents.TOTEM_USE, SoundSource.PLAYERS, 0.7f, 1.4f);
			player.sendOverlayMessage(Component.translatable("message.lanternring.overcharged",
					LanternCharge.chargesLeft(battery), LanternCharge.BATTERY_CHARGES).withStyle(ChatFormatting.GOLD));
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
		// Boosted by hope: the bar shows Blue Lantern blue until the boost is spent.
		return hopeReserve(stack) > 0 ? Corps.BLUE.rgb : Corps.of(stack).rgb;
	}

	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display,
			Consumer<Component> tooltip, TooltipFlag flag) {
		RingMode mode = getMode(stack);
		Corps corps = Corps.of(stack);
		if (corps != Corps.GREEN) tooltip.accept(Component.translatable("tooltip.lanternring.corps",
				Component.translatable("corps.lanternring." + corps.getSerializedName()), corps.emotion()).withStyle(corps.chat));
		tooltip.accept(chargeText(stack));
		if (overcharge(stack) > 0) tooltip.accept(Component.translatable("tooltip.lanternring.overcharge",
				Math.round(100f * overcharge(stack) / MAX_CHARGE)).withStyle(ChatFormatting.GOLD));
		if (hopeReserve(stack) > 0) {
			tooltip.accept(Component.translatable("tooltip.lanternring.hope_boost", Math.round(100f * hopeReserve(stack) / MAX_CHARGE))
					.withStyle(ChatFormatting.AQUA));
		}
		tooltip.accept(Component.translatable("tooltip.lanternring.mode", corps.modeName(mode)).withStyle(ChatFormatting.WHITE));
		tooltip.accept(corps.modeDescription(mode).copy().withStyle(ChatFormatting.DARK_GRAY));
		if (mode == RingMode.BLAST) tooltip.accept(BlastDrills.levelText(BlastDrills.level(stack), stack).copy().withStyle(ChatFormatting.WHITE));
		if (mode == RingMode.BUILD) tooltip.accept(Component.translatable("tooltip.lanternring.build_shape", Builds.shapeText(Builds.shape(stack))).withStyle(ChatFormatting.WHITE));
		if (mode == RingMode.ARMY) tooltip.accept(ConstructArmy.typeText(ConstructArmy.type(stack)).copy().withStyle(ChatFormatting.WHITE));
		if (mode == RingMode.ANVIL) tooltip.accept(Anvils.sizeText(Anvils.size(stack)).copy().withStyle(ChatFormatting.WHITE));
		if (mode == RingMode.DELUGE) tooltip.accept(Deluges.levelText(Deluges.level(stack)).copy().withStyle(ChatFormatting.WHITE));
		if (mode == RingMode.AERIAL && corps == Corps.YELLOW) tooltip.accept(FearNuke.status(stack).copy().withStyle(ChatFormatting.YELLOW));
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

	/**
	 * Iris's held item light (it mixes IrisItemLightProvider into every Item, so this overrides it
	 * when Iris is installed and is never called otherwise): a held ring lights what's around you.
	 */
	public int getLightEmission(Player player, ItemStack stack) {
		return shaderHeldLight.getAsInt();
	}

	/** The held light's colour for Iris: the ring's corps. The patched pack also tints bloom and fog with it. */
	public org.joml.Vector3f getLightColor(Player player, ItemStack stack) {
		Corps corps = Corps.of(stack);
		org.joml.Vector3f color = new org.joml.Vector3f(corps.red(), corps.green(), corps.blue());
		double dim = shaderSunDim.getAsDouble();
		if (dim < 0) return color;
		// The patched pack reads the colour's direction as the corps and its length as the sun
		// dimming: 10 = none, 12 = full (no item's light colour is ever that long by itself).
		if (color.lengthSquared() < 1.0e-6f) color.set(1f);
		return color.normalize((float) (10 + 2 * Math.min(1, dim)));
	}
}
