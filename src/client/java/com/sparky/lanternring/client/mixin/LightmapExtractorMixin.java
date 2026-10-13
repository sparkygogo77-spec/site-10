package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.SunDim;
import net.minecraft.client.renderer.LightmapRenderStateExtractor;
import net.minecraft.client.renderer.state.LightmapRenderState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** The sun dims round a charging ring (SunDim): less sky light on everything, without a shader pack. */
@Mixin(LightmapRenderStateExtractor.class)
public abstract class LightmapExtractorMixin {
	@Inject(method = "extract", at = @At("TAIL"))
	private void lanternring$sunDim(LightmapRenderState state, float partialTick, CallbackInfo ci) {
		if (state.needsUpdate) state.skyFactor *= SunDim.vanillaKeep(partialTick);
	}
}
