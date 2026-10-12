package com.sparky.lanternring.item;

import com.sparky.lanternring.corps.HawkBonds;
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
import net.minecraft.world.level.Level;

/**
 * A Blue Lantern hawk whistle, sold in the sky cities: blow it and the hawk you tamed comes to you
 * from wherever it is in the world, and follows you again.
 */
public class HawkWhistleItem extends Item {
	public HawkWhistleItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		level.playSound(null, player.blockPosition(), SoundEvents.NOTE_BLOCK_FLUTE.value(), SoundSource.PLAYERS, 1.2f, 1.6f);
		if (level instanceof ServerLevel server && player instanceof ServerPlayer sp) {
			Component result = HawkBonds.whistle(server, sp);
			sp.sendOverlayMessage(result.copy().withStyle(ChatFormatting.AQUA));
			player.getCooldowns().addCooldown(player.getItemInHand(hand), 40);
		}
		return InteractionResult.SUCCESS;
	}
}
