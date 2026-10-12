package com.sparky.lanternring.block;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingFx;
import com.sparky.lanternring.net.RingFxPayload;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.BaseEntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.VoxelShape;

/**
 * The Ring Forge: where new Green Lantern rings are made. Use an emerald block on it while a Power
 * Battery (or a Great Power Battery) stands within {@link #BATTERY_RANGE} blocks and it forges a new power ring, which rises
 * out of its top. Its floating core, ports and emblem are drawn by RingForgeRenderer.
 */
public class RingForgeBlock extends BaseEntityBlock {
	public static final int BATTERY_RANGE = 5;
	private static final VoxelShape SHAPE = net.minecraft.world.level.block.Block.box(0, 0, 0, 16, 12, 16);

	public RingForgeBlock(Properties properties) {
		super(properties);
	}

	@Override
	public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
		return new RingForgeBlockEntity(pos, state);
	}

	@Override
	protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
		return SHAPE;
	}

	@Override
	protected InteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
			Player player, InteractionHand hand, BlockHitResult hit) {
		if (!stack.is(Items.EMERALD_BLOCK)) return InteractionResult.TRY_WITH_EMPTY_HAND;
		if (!(level instanceof ServerLevel server)) return InteractionResult.SUCCESS;
		if (!batteryNear(level, pos)) {
			player.sendOverlayMessage(Component.translatable("message.lanternring.forge_needs_battery").withStyle(Corps.GREEN.chat));
			level.playSound(null, pos, SoundEvents.BEACON_DEACTIVATE, SoundSource.BLOCKS, 0.6f, 1.4f);
			return InteractionResult.FAIL;
		}
		stack.consume(1, player);
		Vec3 top = Vec3.atBottomCenterOf(pos).add(0, 1.0, 0);
		ItemEntity ring = new ItemEntity(level, top.x, top.y, top.z, new ItemStack(ModRegistry.POWER_RING));
		ring.setDeltaMovement(0, 0.12, 0);
		ring.setDefaultPickUpDelay();
		level.addFreshEntity(ring);
		level.playSound(null, pos, SoundEvents.BEACON_POWER_SELECT, SoundSource.BLOCKS, 1f, 1.3f);
		level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1f, 0.7f);
		Corps before = Corps.enter(Corps.GREEN);
		try {
			RingFx.send(server, RingFxPayload.Kind.CHARGE, top, player.position());
		} finally {
			Corps.restore(before);
		}
		player.sendOverlayMessage(Component.translatable("message.lanternring.forged").withStyle(Corps.GREEN.chat));
		return InteractionResult.SUCCESS;
	}

	/** Whether a green Power Battery stands near enough to power the forge. */
	private static boolean batteryNear(Level level, BlockPos pos) {
		for (BlockPos p : BlockPos.betweenClosed(pos.offset(-BATTERY_RANGE, -2, -BATTERY_RANGE), pos.offset(BATTERY_RANGE, 2, BATTERY_RANGE))) {
			BlockState s = level.getBlockState(p);
			if (s.is(ModRegistry.POWER_BATTERY) && Corps.of(s) == Corps.GREEN || s.is(ModRegistry.GREAT_BATTERY)) return true;
		}
		return false;
	}
}
