package com.sparky.lanternring.mixin;

import java.util.List;
import net.minecraft.world.level.levelgen.structure.StructurePiece;
import net.minecraft.world.level.levelgen.structure.pieces.StructurePiecesBuilder;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;

/** A structure's pieces while it's being laid out (the Warren entrance looks for mineshaft dead ends, warren/WarrenEntrance). */
@Mixin(StructurePiecesBuilder.class)
public interface StructurePiecesBuilderAccessor {
	@Accessor("pieces")
	List<StructurePiece> lanternring$pieces();
}
