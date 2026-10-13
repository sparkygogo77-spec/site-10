package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.ConstructDisplays;
import net.minecraft.client.renderer.entity.state.BlockDisplayEntityRenderState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;

/** Remembers whether ConstructDisplays draws this block display this frame. */
@Mixin(BlockDisplayEntityRenderState.class)
public abstract class BlockDisplayRenderStateMixin implements ConstructDisplays.Taken {
	@Unique
	private boolean lanternring$taken;

	@Override
	public boolean lanternring$taken() {
		return lanternring$taken;
	}

	@Override
	public void lanternring$setTaken(boolean taken) {
		lanternring$taken = taken;
	}
}
