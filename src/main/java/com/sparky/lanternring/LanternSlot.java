package com.sparky.lanternring;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.sparky.lanternring.net.LanternKeyPayload;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentSyncPredicate;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

/**
 * The lantern's own slot (J, 2026-10-13): a Power Battery kept apart from your hands, so it never
 * takes the off hand or left-click. The lantern key (R) puts a held lantern into the slot, then
 * summons it (it floats in a little below your view) and dismisses it again; crouch + R hands it
 * back. While it's summoned, holding right-click with the ring charges from it (see LanternCharge),
 * and holding R sets off its corps' own power ({@link #power}).
 */
public final class LanternSlot {
	/** The lantern in the slot (empty if none) and whether it's summoned right now. */
	public record State(ItemStack lantern, boolean out) {
		public static final State EMPTY = new State(ItemStack.EMPTY, false);
		public static final Codec<State> CODEC = RecordCodecBuilder.create(i -> i.group(
				ItemStack.OPTIONAL_CODEC.fieldOf("lantern").forGetter(State::lantern),
				Codec.BOOL.fieldOf("out").forGetter(State::out)
		).apply(i, State::new));
		public static final StreamCodec<RegistryFriendlyByteBuf, State> STREAM_CODEC = StreamCodec.composite(
				ItemStack.OPTIONAL_STREAM_CODEC, State::lantern,
				ByteBufCodecs.BOOL, State::out,
				State::new);
	}

	/** Kept through death; synced to its owner only (their client draws it). */
	public static final AttachmentType<State> SLOT = AttachmentRegistry.create(LanternRing.id("lantern_slot"),
			b -> b.persistent(State.CODEC).copyOnDeath().syncWith(State.STREAM_CODEC, AttachmentSyncPredicate.targetOnly()));

	private LanternSlot() {
	}

	static void register() {
		ServerPlayNetworking.registerGlobalReceiver(LanternKeyPayload.TYPE, (payload, context) -> {
			if (payload.power()) power(context.player());
			else press(context.player(), payload.crouch());
		});
	}

	public static State state(LivingEntity user) {
		State state = user.getAttached(SLOT);
		return state == null ? State.EMPTY : state;
	}

	/** The lantern in the slot, or empty. */
	public static ItemStack lantern(LivingEntity user) {
		return state(user).lantern();
	}

	/** True while a lantern is in the slot and summoned. */
	public static boolean out(LivingEntity user) {
		State state = state(user);
		return state.out() && state.lantern().is(ModRegistry.POWER_BATTERY_ITEM);
	}

	/** The lantern key (R) on the server: stow a held lantern, summon or dismiss it, or (crouching) take it back. */
	static void press(ServerPlayer player, boolean crouch) {
		State state = state(player);
		if (state.lantern().isEmpty()) {
			InteractionHand hand = player.getOffhandItem().is(ModRegistry.POWER_BATTERY_ITEM) ? InteractionHand.OFF_HAND
					: player.getMainHandItem().is(ModRegistry.POWER_BATTERY_ITEM) ? InteractionHand.MAIN_HAND : null;
			if (hand == null) {
				player.sendOverlayMessage(Component.translatable("message.lanternring.lantern_slot.none").withStyle(ChatFormatting.GRAY));
				return;
			}
			ItemStack held = player.getItemInHand(hand);
			ItemStack one = held.split(1);
			set(player, new State(one, true));
			sound(player, true);
			player.sendOverlayMessage(Component.translatable("message.lanternring.lantern_slot.stowed").withStyle(ChatFormatting.GREEN));
			return;
		}
		if (crouch) {
			// Back into your inventory (dropped at your feet when it's full).
			ItemStack lantern = state.lantern().copy();
			stopCharging(player);
			OrangeHorde.stop(player);
			set(player, State.EMPTY);
			player.getInventory().placeItemBackInInventory(lantern, net.minecraft.util.Prediction.SERVER_ONLY);
			sound(player, false);
			player.sendOverlayMessage(Component.translatable("message.lanternring.lantern_slot.taken").withStyle(ChatFormatting.GRAY));
			return;
		}
		boolean out = !state.out();
		if (!out) {
			stopCharging(player);
			OrangeHorde.stop(player);
		}
		set(player, new State(state.lantern(), out));
		sound(player, out);
	}

	/**
	 * Holding the lantern key with the lantern summoned: its corps' own power. The Orange Lantern's
	 * Horde crawls up out of the ground (see OrangeHorde); the Red Lantern self-destructs (see
	 * RedSelfDestruct).
	 */
	static void power(ServerPlayer player) {
		if (!out(player)) return;
		Corps corps = Corps.ofLantern(lantern(player));
		if (corps == Corps.ORANGE) {
			OrangeHorde.toggle(player);
		} else if (corps == Corps.RED) {
			RedSelfDestruct.start(player);
		} else {
			player.sendOverlayMessage(Component.translatable("message.lanternring.lantern_slot.no_power").withStyle(ChatFormatting.GRAY));
		}
	}

	private static void set(Player player, State state) {
		if (state.lantern().isEmpty()) player.removeAttached(SLOT);
		else player.setAttached(SLOT, state);
	}

	/** Dismissing the lantern mid-charge lets go of the charge. */
	private static void stopCharging(ServerPlayer player) {
		if (LanternCharge.isCharging(player)) player.stopUsingItem();
	}

	private static void sound(ServerPlayer player, boolean out) {
		if (out) {
			player.level().playSound(null, player.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, 0.5f, 1.6f);
		} else {
			player.level().playSound(null, player.blockPosition(), SoundEvents.AMETHYST_CLUSTER_BREAK, SoundSource.PLAYERS, 0.8f, 1.3f);
		}
	}
}
