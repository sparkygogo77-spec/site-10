package com.sparky.lanternring.item;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.block.LanternStyle;
import com.sparky.lanternring.net.LanternChargePayload;
import com.sparky.lanternring.net.PlaceLanternPayload;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * The Power Battery as an item: a lantern carried in the off hand. It never goes in the main hand
 * (it swaps itself over), and a plain right-click never places it, so it can't get in the way of
 * the ring. To set it down, double-click right-click on a block and hold the second click (the
 * client spots that, see LanternPlaceInput, and sends {@link PlaceLanternPayload}).
 */
public class PowerBatteryItem extends BlockItem {
	public PowerBatteryItem(Block block, Properties properties) {
		super(block, properties);
	}

	public static void register() {
		ServerPlayNetworking.registerGlobalReceiver(PlaceLanternPayload.TYPE, (payload, context) -> place(context.player(), LanternStyle.byName(payload.style())));
		ServerPlayNetworking.registerGlobalReceiver(LanternChargePayload.TYPE, (payload, context) -> LanternCharge.want(context.player(), payload.charge()));
	}

	/** Red Lantern and so on; the green one keeps its plain name. */
	@Override
	public Component getName(ItemStack stack) {
		Corps corps = Corps.ofLantern(stack);
		if (corps == Corps.GREEN) return super.getName(stack);
		return Component.translatable("block.lanternring.power_battery." + corps.getSerializedName());
	}

	/** Overcharging burns out the battery's charges (see LanternCharge): a bar shows what is left once any are gone. */
	@Override
	public boolean isBarVisible(ItemStack stack) {
		return LanternCharge.burnt(stack) > 0;
	}

	@Override
	public int getBarWidth(ItemStack stack) {
		return Math.round(13f * LanternCharge.chargesLeft(stack) / LanternCharge.BATTERY_CHARGES);
	}

	@Override
	public int getBarColor(ItemStack stack) {
		return LanternCharge.canOvercharge(stack) ? 0xFFC040 : 0xFF4040;
	}

	@Override
	public void appendHoverText(ItemStack stack, TooltipContext context, net.minecraft.world.item.component.TooltipDisplay display,
			java.util.function.Consumer<Component> tooltip, net.minecraft.world.item.TooltipFlag flag) {
		super.appendHoverText(stack, context, display, tooltip, flag);
		tooltip.accept(Component.translatable("tooltip.lanternring.battery_charges", LanternCharge.chargesLeft(stack), LanternCharge.BATTERY_CHARGES)
				.withStyle(LanternCharge.canOvercharge(stack) ? net.minecraft.ChatFormatting.GOLD : net.minecraft.ChatFormatting.RED));
	}

	@Override
	public InteractionResult useOn(UseOnContext context) {
		return InteractionResult.PASS;
	}

	@Override
	public void inventoryTick(ItemStack stack, ServerLevel level, Entity entity, EquipmentSlot slot) {
		// Only the off hand holds the lantern: picking it in the hotbar moves it there, like pressing F.
		if (slot != EquipmentSlot.MAINHAND || !(entity instanceof Player player) || player.isSpectator()) return;
		ItemStack off = player.getOffhandItem();
		if (off.getItem() instanceof PowerBatteryItem) return;
		player.setItemInHand(InteractionHand.OFF_HAND, stack);
		player.setItemInHand(InteractionHand.MAIN_HAND, off);
	}

	/** Sets the off-hand lantern down on the block the player is looking at, as {@code style}. */
	private static void place(ServerPlayer player, LanternStyle style) {
		ItemStack stack = player.getOffhandItem();
		if (!(stack.getItem() instanceof PowerBatteryItem item) || player.isSpectator()) return;
		Vec3 eye = player.getEyePosition();
		Vec3 end = eye.add(player.getLookAngle().scale(player.blockInteractionRange()));
		BlockHitResult hit = player.level().clip(new ClipContext(eye, end, ClipContext.Block.OUTLINE, ClipContext.Fluid.NONE, player));
		if (hit.getType() != HitResult.Type.BLOCK || !player.mayInteract(player.level(), hit.getBlockPos())) return;
		BlockPlaceContext context = new BlockPlaceContext(player, InteractionHand.OFF_HAND, stack, hit);
		BlockPos pos = context.getClickedPos();
		if (!item.place(context).consumesAction()) return;
		BlockState state = player.level().getBlockState(pos);
		if (state.hasProperty(LanternStyle.PROPERTY)) player.level().setBlockAndUpdate(pos, state.setValue(LanternStyle.PROPERTY, style));
	}
}
