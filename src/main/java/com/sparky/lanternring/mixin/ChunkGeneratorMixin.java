package com.sparky.lanternring.mixin;

import com.sparky.lanternring.warren.WarrenLair;
import com.sparky.lanternring.warren.WarrenSites;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.StructureManager;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.chunk.ChunkAccess;
import net.minecraft.world.level.chunk.ChunkGenerator;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** After a chunk's features, a Dread Warren lair carves its part of the chunk if one is near (warren/WarrenLair). */
@Mixin(ChunkGenerator.class)
public abstract class ChunkGeneratorMixin {
	@Inject(method = "applyBiomeDecoration", at = @At("TAIL"))
	private void lanternring$warrenLair(WorldGenLevel level, ChunkAccess chunk, StructureManager structures, CallbackInfo ci) {
		ServerLevel server = level.getLevel();
		if (server.dimension() != Level.OVERWORLD) return;
		ChunkPos pos = chunk.getPos();
		int x = pos.getMiddleBlockX(), z = pos.getMiddleBlockZ();
		int[] site = WarrenSites.siteAt(level.getSeed(), x, z, (ChunkGenerator) (Object) this,
				server.getChunkSource().randomState(), level);
		if (site == null) return;
		WarrenLair.get(level.getSeed(), site).carve(level, pos);
	}
}
