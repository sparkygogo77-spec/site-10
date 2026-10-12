package com.sparky.lanternring.block;

import com.sparky.lanternring.ModRegistry;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/** The real block a GhostMimicBlock copies, sent to clients so they can draw it. */
public class GhostMimicBlockEntity extends BlockEntity {
	private BlockState real = Blocks.AIR.defaultBlockState();

	public GhostMimicBlockEntity(BlockPos pos, BlockState state) {
		super(ModRegistry.GHOST_MIMIC_ENTITY, pos, state);
	}

	public BlockState real() {
		return real;
	}

	public void setReal(BlockState real) {
		this.real = real;
		setChanged();
		if (level != null && !level.isClientSide()) level.sendBlockUpdated(worldPosition, getBlockState(), getBlockState(), 3);
	}

	@Override
	protected void loadAdditional(ValueInput input) {
		super.loadAdditional(input);
		real = input.read("real", BlockState.CODEC).orElse(Blocks.AIR.defaultBlockState());
	}

	@Override
	protected void saveAdditional(ValueOutput output) {
		super.saveAdditional(output);
		output.store("real", BlockState.CODEC, real);
	}

	@Override
	public Packet<ClientGamePacketListener> getUpdatePacket() {
		return ClientboundBlockEntityDataPacket.create(this);
	}

	@Override
	public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
		return saveCustomOnly(registries);
	}
}
