package com.sparky.lanternring.block;

import com.sparky.lanternring.item.PowerRingItem;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** The lantern that recharges a power ring: use the ring on it. */
public class PowerBatteryBlock extends Block {
	private static final int OATH_LINES = 4;
	private static final VoxelShape SHAPE = Shapes.or(
			Block.box(3, 0, 3, 13, 2, 13),
			Block.box(4, 2, 4, 12, 12, 12),
			Block.box(3, 12, 3, 13, 14, 13),
			Block.box(6, 14, 6, 10, 16, 10));

	public PowerBatteryBlock(Properties properties) {
		super(properties);
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}

	@Override
	protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
			Player player, InteractionHand hand, BlockHitResult hit) {
		if (!(stack.getItem() instanceof PowerRingItem)) return InteractionResult.TRY_WITH_EMPTY_HAND;

		if (level instanceof ServerLevel serverLevel) {
			PowerRingItem.setCharge(stack, PowerRingItem.MAX_CHARGE);
			// Speak the oath on a full recharge, but don't spam it on a top-up.
			if (!player.getCooldowns().isOnCooldown(stack)) {
				for (int i = 1; i <= OATH_LINES; i++) {
					player.sendSystemMessage(Component.translatable("message.lanternring.oath." + i)
							.withStyle(ChatFormatting.GREEN, ChatFormatting.ITALIC));
				}
			}
			player.getCooldowns().addCooldown(stack, 20);
			player.sendOverlayMessage(PowerRingItem.chargeText(stack));
			serverLevel.sendParticles(PowerRingItem.GREEN_LIGHT, pos.getX() + 0.5, pos.getY() + 0.6, pos.getZ() + 0.5,
					40, 0.4, 0.5, 0.4, 0);
			level.playSound(null, pos, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 1f, 1.2f);
		}
		return InteractionResult.SUCCESS;
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		if (random.nextInt(3) != 0) return;
		level.addParticle(PowerRingItem.GREEN_LIGHT,
				pos.getX() + 0.3 + random.nextDouble() * 0.4,
				pos.getY() + 0.2 + random.nextDouble() * 0.6,
				pos.getZ() + 0.3 + random.nextDouble() * 0.4,
				0, 0.02, 0);
	}
}
