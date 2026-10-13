package com.sparky.lanternring.corps;

import com.sparky.lanternring.Anvils;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.RingFx;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.RingPowers;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The Aerial Drop mode: each corps' big drop from the sky, after the Red Lantern's level 4 Deluge
 * sanctuary (J, 2026-10-12, "generate aerial drops for the rest of the corps"). Hold right-click to
 * aim the marker, let go to drop. The Yellow ring forms the Fear Nuke in the sky over the raised hand and sends it
 * out to airburst over the marker ({@link FearNuke}), the Blue
 * ring a Hope Drop ({@link HopeDrop}), the Orange ring Larfleeze's Hoard Rain ({@link HoardRain}).
 */
public final class AerialDrops {
	private static final class Aim {
		ServerLevel level;
		@Nullable BlockPos mark;
		@Nullable LivingEntity target;
	}

	private static final Map<UUID, Aim> AIMS = new HashMap<>();
	private static final Map<UUID, Long> NOTE = new HashMap<>();

	private AerialDrops() {
	}

	/** What a drop costs this ring now (the Fear Nuke's price falls as fear builds). */
	public static int cost(ItemStack ring) {
		return switch (Corps.of(ring)) {
			case YELLOW -> FearNuke.cost(ring);
			case ORANGE -> HoardRain.COST;
			default -> HopeDrop.COST;
		};
	}

	/** Every tick right-click is held in Aerial mode: moves the marker. */
	public static void aimTick(ServerPlayer player, ItemStack ring) {
		ServerLevel level = player.level();
		if (!AIMS.containsKey(player.getUUID())) {
			if (player.getCooldowns().isOnCooldown(ring)) return;
			if (!player.isCreative() && PowerRingItem.getCharge(ring) < cost(ring)) {
				long now = level.getGameTime();
				if (now - NOTE.getOrDefault(player.getUUID(), Long.MIN_VALUE / 2) > 20) {
					NOTE.put(player.getUUID(), now);
					player.sendOverlayMessage(Component.translatable("message.lanternring.aerial_charge",
							String.valueOf(cost(ring) / 10)).withStyle(ChatFormatting.RED));
					level.playSound(null, player.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.6f, 1.4f);
				}
				return;
			}
			if (Corps.of(ring) == Corps.YELLOW && FearNuke.busy(player)) return;
		}
		// The Fear Nuke forms in the sky, tethered to the raised ring, while right-click is held.
		if (Corps.of(ring) == Corps.YELLOW) FearNuke.buildTick(player, ring);
		Aim aim = AIMS.computeIfAbsent(player.getUUID(), id -> new Aim());
		aim.level = level;
		aim.mark = Corps.of(ring) == Corps.YELLOW ? FearNuke.findMark(level, player) : Anvils.findMark(level, player);
		aim.target = null;
		if (Corps.of(ring) == Corps.BLUE) {
			// Aimed at a mob: a container comes down round it instead of a dome.
			var hit = RingPowers.trace(level, player, 48);
			if (hit.entity() instanceof LivingEntity living && living.isAlive() && living.onGround()) {
				aim.target = living;
				aim.mark = living.blockPosition();
			}
		}
		if (aim.mark != null && level.getGameTime() % 2 == 0) {
			Vec3 at = new Vec3(aim.mark.getX() + 0.5, aim.mark.getY(), aim.mark.getZ() + 0.5);
			double r = Corps.of(ring) == Corps.YELLOW ? FearNuke.crater(FearNuke.fear(ring)) : Corps.of(ring) == Corps.ORANGE ? HoardRain.RADIUS : aim.target != null ? HopeDrop.CAGE : HopeDrop.DOME;
			RingFx.send(level, Kind.DELUGE_MARK, at, at.add(r, 0, 0), 0f, 0, player);
		}
		if (Corps.of(ring) == Corps.YELLOW && level.getGameTime() % 10 == 0 && FearNuke.strayed(player) < 0 && !FearNuke.broken(player)) {
			player.sendOverlayMessage(FearNuke.status(ring).copy().withStyle(ChatFormatting.YELLOW));
		}
	}

	/** Right-click let go: drops it over the marker, and pays for it. */
	public static void release(ServerPlayer player, ItemStack ring) {
		Aim aim = AIMS.remove(player.getUUID());
		boolean yellow = Corps.of(ring) == Corps.YELLOW;
		if (aim == null || aim.mark == null || aim.level != player.level()) {
			if (yellow) FearNuke.cancelBuild(player);
			return;
		}
		int cost = cost(ring);
		if (!player.isCreative() && PowerRingItem.getCharge(ring) < cost) {
			if (yellow) FearNuke.cancelBuild(player);
			return;
		}
		if (yellow && !FearNuke.built(player)) {
			// Let go before it was built: it comes apart, nothing is spent.
			boolean broken = FearNuke.broken(player);
			FearNuke.cancelBuild(player);
			if (!broken) player.sendOverlayMessage(Component.translatable("message.lanternring.fear_nuke_unbuilt").withStyle(ChatFormatting.GOLD));
			return;
		}
		boolean dropped = switch (Corps.of(ring)) {
			case YELLOW -> FearNuke.launch(aim.level, player, ring, aim.mark);
			case BLUE -> HopeDrop.drop(aim.level, player, aim.mark, aim.target != null);
			case ORANGE -> HoardRain.drop(aim.level, player, aim.mark);
			default -> false;
		};
		if (!dropped) return;
		if (!player.isCreative()) PowerRingItem.setCharge(ring, PowerRingItem.getCharge(ring) - cost);
		player.getCooldowns().addCooldown(ring, RingTuning.cooldownTicks(RingMode.AERIAL));
	}

	public static void cancel(Player player) {
		AIMS.remove(player.getUUID());
		FearNuke.cancelBuild(player);
	}
}
