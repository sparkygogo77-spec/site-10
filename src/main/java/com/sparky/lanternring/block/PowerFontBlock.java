package com.sparky.lanternring.block;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.item.PowerRingItem;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ItemUtils;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * A big power source: a table with a pool of light in its basin that recharges its corps' rings,
 * any number of times. The Great Power Battery (green) is always full and also powers a Ring
 * Forge nearby; the Lava Font (red) starts dry and is filled by pouring a lava bucket into it.
 */
public class PowerFontBlock extends Block {
	public static final BooleanProperty FILLED = BooleanProperty.create("filled");
	private static final VoxelShape SHAPE = Block.box(0, 0, 0, 16, 15, 16);
	private final Corps corps;

	public PowerFontBlock(Corps corps, boolean startsFull, Properties properties) {
		super(properties);
		this.corps = corps;
		registerDefaultState(stateDefinition.any().setValue(FILLED, startsFull));
	}

	public Corps corps() {
		return corps;
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(FILLED);
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}

	@Override
	protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
			Player player, InteractionHand hand, BlockHitResult hit) {
		if (stack.is(Items.LAVA_BUCKET) && corps == Corps.RED && !state.getValue(FILLED)) {
			if (!level.isClientSide()) {
				level.setBlockAndUpdate(pos, state.setValue(FILLED, true));
				player.setItemInHand(hand, ItemUtils.createFilledResult(stack, player, new ItemStack(Items.BUCKET)));
				level.playSound(null, pos, SoundEvents.BUCKET_EMPTY_LAVA, SoundSource.BLOCKS, 1f, 0.8f);
			}
			return InteractionResult.SUCCESS;
		}
		if (!(stack.getItem() instanceof PowerRingItem)) return InteractionResult.TRY_WITH_EMPTY_HAND;
		if (Corps.of(stack) != corps) {
			if (!level.isClientSide()) PowerBatteryBlock.wrongLantern(player, corps);
			return InteractionResult.FAIL;
		}
		if (!state.getValue(FILLED)) return InteractionResult.FAIL;
		if (level instanceof ServerLevel server) {
			PowerBatteryBlock.recharge(server, player, stack, Vec3.atCenterOf(pos).add(0, 0.4, 0));
			level.playSound(null, pos, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 1f, 0.9f);
		}
		return InteractionResult.SUCCESS;
	}
}
