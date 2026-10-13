package com.sparky.lanternring.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import com.sparky.lanternring.client.ConstructDisplays;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.DisplayRenderer;
import net.minecraft.client.renderer.entity.state.BlockDisplayEntityRenderState;
import net.minecraft.world.entity.Display;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Construct block displays (the falling Anvil) are drawn by ConstructDisplays instead. */
@Mixin(DisplayRenderer.BlockDisplayRenderer.class)
public abstract class BlockDisplayRendererMixin {
	@Inject(method = "extractRenderState(Lnet/minecraft/world/entity/Display$BlockDisplay;Lnet/minecraft/client/renderer/entity/state/BlockDisplayEntityRenderState;F)V",
			at = @At("TAIL"))
	private void lanternring$take(Display.BlockDisplay display, BlockDisplayEntityRenderState state, float partial, CallbackInfo ci) {
		((ConstructDisplays.Taken) state).lanternring$setTaken(ConstructDisplays.takes(display, partial));
	}

	@Inject(method = "submitInner(Lnet/minecraft/client/renderer/entity/state/BlockDisplayEntityRenderState;Lcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/SubmitNodeCollector;IF)V",
			at = @At("HEAD"), cancellable = true)
	private void lanternring$skip(BlockDisplayEntityRenderState state, PoseStack poseStack, SubmitNodeCollector collector, int light, float partial, CallbackInfo ci) {
		if (((ConstructDisplays.Taken) state).lanternring$taken()) ci.cancel();
	}
}
