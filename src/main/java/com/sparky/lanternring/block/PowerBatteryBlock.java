package com.sparky.lanternring.block;

import com.sparky.lanternring.Corps;
import net.minecraft.world.level.block.state.StateDefinition;

import com.sparky.lanternring.ClientHooks;
import com.sparky.lanternring.RingFx;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.RingFxPayload;
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
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

/** The lantern that recharges a power ring: use the ring on it. */
public class PowerBatteryBlock extends Block {
	private static final int OATH_LINES = 4;
	/** The Blockbench lantern at 0.8 scale (tools/bbmodel_json.py): body, cap and handle. */
	private static final VoxelShape SHAPE = Shapes.or(
			Block.box(3.2, 0, 3.2, 12.8, 12, 12.8),
			Block.box(6.4, 12, 6.4, 9.6, 14.4, 9.6),
			Block.box(4, 11.2, 7.6, 12, 16, 8.4));

	public PowerBatteryBlock(Properties properties) {
		super(properties);
		registerDefaultState(stateDefinition.any().setValue(Corps.PROPERTY, Corps.GREEN).setValue(LanternStyle.PROPERTY, LanternStyle.STONE));
	}

	@Override
	protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
		builder.add(Corps.PROPERTY, LanternStyle.PROPERTY);
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}

	@Override
	protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
			Player player, InteractionHand hand, BlockHitResult hit) {
		if (!(stack.getItem() instanceof PowerRingItem)) return InteractionResult.TRY_WITH_EMPTY_HAND;
		// Each lantern charges only its own corps' rings.
		if (Corps.of(stack) != Corps.of(state)) {
			if (!level.isClientSide()) wrongLantern(player, Corps.of(state));
			return InteractionResult.FAIL;
		}

		if (level instanceof ServerLevel serverLevel) {
			recharge(serverLevel, player, stack, Vec3.atCenterOf(pos));
			level.playSound(null, pos, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 1f, 1.2f);
		}
		return InteractionResult.SUCCESS;
	}

	public static void wrongLantern(Player player, Corps lantern) {
		player.sendOverlayMessage(Component.translatable("message.lanternring.wrong_lantern",
				Component.translatable("corps.lanternring." + lantern.getSerializedName())).withStyle(lantern.chat));
		player.level().playSound(null, player.blockPosition(), SoundEvents.BEACON_DEACTIVATE, SoundSource.PLAYERS, 0.6f, 1.4f);
	}

	/** Fills the ring and announces it; {@code at} is where the light comes from. */
	public static void recharge(ServerLevel level, Player player, ItemStack stack, Vec3 at) {
		PowerRingItem.setCharge(stack, PowerRingItem.MAX_CHARGE);
		// Speak the oath on a full recharge, but don't spam it on a top-up.
		if (!player.getCooldowns().isOnCooldown(stack)) {
			Corps corps = Corps.of(stack);
			String oath = corps == Corps.GREEN ? "message.lanternring.oath." : "message.lanternring.oath." + corps.getSerializedName() + ".";
			for (int i = 1; i <= OATH_LINES; i++) {
				player.sendSystemMessage(Component.translatable(oath + i)
						.withStyle(corps.chat, ChatFormatting.ITALIC));
			}
		}
		player.getCooldowns().addCooldown(stack, 20);
		player.sendOverlayMessage(PowerRingItem.chargeText(stack));
		Corps before = Corps.enter(Corps.of(stack));
		try {
			RingFx.send(level, RingFxPayload.Kind.CHARGE, at, player.position(), 0f, 0, player);
		} finally {
			Corps.restore(before);
		}
	}

	@Override
	public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
		ClientHooks.batteryAmbient.animate(level, pos, random);
	}
}
