package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.HopeTint;
import com.sparky.lanternring.client.OmegaFx;
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
		((FabricRenderState) state).setData(OmegaFx.EMBER_KEY, OmegaFx.ember(entity));
		((FabricRenderState) state).setData(com.sparky.lanternring.client.CombatFx.TUMBLE_KEY, com.sparky.lanternring.client.CombatFx.tumble(entity, partialTick));
		((FabricRenderState) state).setData(com.sparky.lanternring.client.HitFx.KEY, com.sparky.lanternring.client.HitFx.hit(entity, partialTick));
	}

	/** A mob launched by the flying flurry's backfist tumbles head over heels (CombatFx). */
	@Inject(method = "setupRotations(Lnet/minecraft/client/renderer/entity/state/LivingEntityRenderState;Lcom/mojang/blaze3d/vertex/PoseStack;FF)V", at = @At("TAIL"))
	private void lanternring$tumble(LivingEntityRenderState state, com.mojang.blaze3d.vertex.PoseStack poseStack, float bodyRot, float scale, CallbackInfo ci) {
		com.sparky.lanternring.client.CombatFx.rotate(state, poseStack);
		com.sparky.lanternring.client.HitFx.rotate(state, poseStack);
	}

	@Inject(method = "getModelTint", at = @At("RETURN"), cancellable = true)
	private void lanternring$hopeTint(LivingEntityRenderState state, CallbackInfoReturnable<Integer> cir) {
		float t = ((FabricRenderState) state).getDataOrDefault(HopeTint.KEY, 0f);
		if (t > 0f) cir.setReturnValue(HopeTint.apply(cir.getReturnValue(), t));
		// Burnt by the omega beams: ember orange, charring at the end (OmegaFx).
		float ember = ((FabricRenderState) state).getDataOrDefault(OmegaFx.EMBER_KEY, 0f);
		if (ember > 0f) cir.setReturnValue(OmegaFx.emberTint(cir.getReturnValue(), ember));
	}
}
