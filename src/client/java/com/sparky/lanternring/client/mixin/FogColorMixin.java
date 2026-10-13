package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.SunDim;
import net.minecraft.client.Camera;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.fog.FogRenderer;
import org.joml.Vector4f;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** The sun dims round a charging ring (SunDim): the horizon haze darkens with the sky, without a shader pack. */
@Mixin(FogRenderer.class)
public abstract class FogColorMixin {
	@Inject(method = "computeFogColor", at = @At("TAIL"))
	private void lanternring$sunDim(Camera camera, float partialTick, ClientLevel level, int renderDistance, float darkenWorld,
			Vector4f color, CallbackInfo ci) {
		float keep = SunDim.vanillaKeep(partialTick);
		if (keep < 1f) color.set(color.x * keep, color.y * keep, color.z * keep, color.w);
	}
}
