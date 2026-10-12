package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.HopeTint;
import net.fabricmc.fabric.api.client.rendering.v1.FabricRenderState;
import net.minecraft.client.renderer.entity.LivingEntityRenderer;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.world.entity.LivingEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(LivingEntityRenderer.class)
public abstract class LivingEntityRendererMixin {
	/** The Blue Lantern's villagers and golems are drawn blue (see HopeTint). */
	@Inject(method = "extractRenderState(Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/client/renderer/entity/state/LivingEntityRenderState;F)V",
			at = @At("TAIL"))
	private void lanternring$hope(LivingEntity entity, LivingEntityRenderState state, float partialTick, CallbackInfo ci) {
		((FabricRenderState) state).setData(HopeTint.KEY, HopeTint.strength(entity));
	}

	@Inject(method = "getModelTint", at = @At("RETURN"), cancellable = true)
	private void lanternring$hopeTint(LivingEntityRenderState state, CallbackInfoReturnable<Integer> cir) {
		float t = ((FabricRenderState) state).getDataOrDefault(HopeTint.KEY, 0f);
		if (t > 0f) cir.setReturnValue(HopeTint.apply(cir.getReturnValue(), t));
	}
}
