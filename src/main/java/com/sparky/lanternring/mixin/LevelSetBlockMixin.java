package com.sparky.lanternring.mixin;

import com.sparky.lanternring.infinity.TimeStone;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Logs each block change for the Time Stone's Rewind, only while someone online carries the stone. */
@Mixin(Level.class)
public abstract class LevelSetBlockMixin {
	@Inject(method = "setBlock(Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;II)Z", at = @At("HEAD"))
	private void lanternring$logForTimeStone(BlockPos pos, BlockState state, int flags, int recursionLeft, CallbackInfoReturnable<Boolean> cir) {
		if (TimeStone.recording) TimeStone.beforeSet((Level) (Object) this, pos, state);
	}
}
