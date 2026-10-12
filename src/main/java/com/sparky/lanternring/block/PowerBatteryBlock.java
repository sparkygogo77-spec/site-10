package com.sparky.lanternring.block;

import com.mojang.serialization.MapCodec;
import com.sparky.lanternring.item.PowerRingItem;
import net.minecraft.block.Block;
import net.minecraft.block.BlockState;
import net.minecraft.block.ShapeContext;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.Hand;
import net.minecraft.util.ItemActionResult;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.random.Random;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.util.shape.VoxelShapes;
import net.minecraft.world.BlockView;
import net.minecraft.world.World;

/** The lantern that recharges a power ring: use the ring on it. */
public class PowerBatteryBlock extends Block {
	public static final MapCodec<PowerBatteryBlock> CODEC = createCodec(PowerBatteryBlock::new);
	private static final int OATH_LINES = 4;
	private static final VoxelShape SHAPE = VoxelShapes.union(
			Block.createCuboidShape(3, 0, 3, 13, 2, 13),
			Block.createCuboidShape(4, 2, 4, 12, 12, 12),
			Block.createCuboidShape(3, 12, 3, 13, 14, 13),
			Block.createCuboidShape(6, 14, 6, 10, 16, 10));

	public PowerBatteryBlock(Settings settings) {
		super(settings);
	}

	@Override
	protected MapCodec<? extends Block> getCodec() {
		return CODEC;
	}

	@Override
	protected VoxelShape getOutlineShape(BlockState state, BlockView world, BlockPos pos, ShapeContext context) {
		return SHAPE;
	}

	@Override
	protected ItemActionResult onUseWithItem(ItemStack stack, BlockState state, World world, BlockPos pos,
			PlayerEntity player, Hand hand, BlockHitResult hit) {
		if (!(stack.getItem() instanceof PowerRingItem)) return ItemActionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;

		if (world instanceof ServerWorld serverWorld) {
			PowerRingItem.setCharge(stack, PowerRingItem.MAX_CHARGE);
			// Speak the oath on a full recharge, but don't spam it on a top-up.
			if (!player.getItemCooldownManager().isCoolingDown(stack.getItem())) {
				for (int i = 1; i <= OATH_LINES; i++) {
					player.sendMessage(Text.translatable("message.lanternring.oath." + i)
							.formatted(Formatting.GREEN, Formatting.ITALIC), false);
				}
			}
			player.getItemCooldownManager().set(stack.getItem(), 20);
			player.sendMessage(PowerRingItem.chargeText(stack), true);
			serverWorld.spawnParticles(PowerRingItem.GREEN_LIGHT, pos.getX() + 0.5, pos.getY() + 0.6, pos.getZ() + 0.5,
					40, 0.4, 0.5, 0.4, 0);
			world.playSound(null, pos, SoundEvents.BLOCK_BEACON_ACTIVATE, SoundCategory.BLOCKS, 1f, 1.2f);
		}
		return ItemActionResult.success(world.isClient);
	}

	@Override
	public void randomDisplayTick(BlockState state, World world, BlockPos pos, Random random) {
		if (random.nextInt(3) != 0) return;
		world.addParticle(PowerRingItem.GREEN_LIGHT,
				pos.getX() + 0.3 + random.nextDouble() * 0.4,
				pos.getY() + 0.2 + random.nextDouble() * 0.6,
				pos.getZ() + 0.3 + random.nextDouble() * 0.4,
				0, 0.02, 0);
	}
}
