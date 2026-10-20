package com.sparky.lanternring.mixin;

import com.sparky.lanternring.warren.WarrenEntrance;
import net.minecraft.world.level.levelgen.structure.Structure;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePiecesBuilder;
import net.minecraft.world.level.levelgen.structure.structures.MineshaftStructure;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Once a mineshaft is laid out at its final height, some dead ends near a Dread Warren carry on as ours. */
@Mixin(MineshaftStructure.class)
public abstract class MineshaftStructureMixin {
	@Inject(method = "generatePiecesAndAdjust", at = @At("RETURN"))
	private void lanternring$warrenEntrance(StructurePiecesBuilder builder, Structure.GenerationContext ctx,
			CallbackInfoReturnable<Integer> cir) {
		WarrenEntrance.attach(builder, ctx.seed(), ctx.heightAccessor(), ctx.chunkGenerator(), ctx.randomState());
	}
}
