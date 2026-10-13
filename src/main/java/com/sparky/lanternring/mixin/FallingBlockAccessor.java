package com.sparky.lanternring.mixin;

import net.minecraft.world.entity.item.FallingBlockEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;

/** A moving block that never stood in the world (the Blue squad's lifting platforms, corps/BlueClearing). */
@Mixin(FallingBlockEntity.class)
public interface FallingBlockAccessor {
	@Invoker("<init>")
	static FallingBlockEntity lanternring$create(Level level, double x, double y, double z, BlockState state) {
		throw new AssertionError();
	}
}
