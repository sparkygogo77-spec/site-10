package com.sparky.lanternring.hero;

import java.util.function.Consumer;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;

/**
 * Captain America's Shield. Hold right-click to block like a shield. Crouch + right-click throws
 * it: it ricochets between up to five mobs and comes back to your hand (see ShieldThrows).
 * Crouch + right-click while in the air, or while looking at your feet, slams it down into a
 * shockwave.
 */
public class CapShieldItem extends Item {
	public CapShieldItem(Properties properties) {
		super(properties);
	}

	@Override
	public InteractionResult use(Level level, Player player, InteractionHand hand) {
		if (!player.isShiftKeyDown()) return super.use(level, player, hand);
		if (level instanceof ServerLevel server && player instanceof ServerPlayer sp) {
			boolean slam = ShieldThrows.airborne(sp) || player.getXRot() > 60;
			if (slam) ShieldThrows.slam(server, sp, hand);
			else ShieldThrows.toss(server, sp, hand);
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> tooltip, TooltipFlag flag) {
		tooltip.accept(Component.translatable("item.lanternring.cap_shield.tip.block").withStyle(ChatFormatting.GRAY));
		tooltip.accept(Component.translatable("item.lanternring.cap_shield.tip.throw").withStyle(ChatFormatting.GRAY));
		tooltip.accept(Component.translatable("item.lanternring.cap_shield.tip.slam").withStyle(ChatFormatting.GRAY));
	}
}
