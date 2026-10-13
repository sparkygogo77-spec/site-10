package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.SunDim;
import net.minecraft.client.Camera;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.SkyRenderer;
import net.minecraft.client.renderer.state.level.SkyRenderState;
import org.joml.Vector3f;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** The sun dims round a charging ring (SunDim): a darker sky and a fainter sun, without a shader pack. */
@Mixin(SkyRenderer.class)
public abstract class SkyRendererMixin {
	@Inject(method = "extractRenderState", at = @At("TAIL"))
	private void lanternring$sunDim(ClientLevel level, float partialTick, Camera camera, SkyRenderState state, CallbackInfo ci) {
		float keep = SunDim.vanillaKeep(partialTick);
		if (keep >= 1f) return;
		if (state.skyColor != null) state.skyColor = new Vector3f(state.skyColor).mul(keep);
		state.rainBrightness *= keep;
	}
}
