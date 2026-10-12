package com.sparky.lanternring.item;

import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.net.LanternChargePayload;
import com.sparky.lanternring.net.PlaceLanternPayload;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
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
		ServerPlayNetworking.registerGlobalReceiver(PlaceLanternPayload.TYPE, (payload, context) -> place(context.player()));
		ServerPlayNetworking.registerGlobalReceiver(LanternChargePayload.TYPE, (payload, context) -> LanternCharge.want(context.player(), payload.charge()));
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

	/** Sets the off-hand lantern down on the block the player is looking at. */
	private static void place(ServerPlayer player) {
		ItemStack stack = player.getOffhandItem();
		if (!(stack.getItem() instanceof PowerBatteryItem item) || player.isSpectator()) return;
		Vec3 eye = player.getEyePosition();
		Vec3 end = eye.add(player.getLookAngle().scale(player.blockInteractionRange()));
		BlockHitResult hit = player.level().clip(new ClipContext(eye, end, ClipContext.Block.OUTLINE, ClipContext.Fluid.NONE, player));
		if (hit.getType() != HitResult.Type.BLOCK || !player.mayInteract(player.level(), hit.getBlockPos())) return;
		item.place(new BlockPlaceContext(player, InteractionHand.OFF_HAND, stack, hit));
	}
}
