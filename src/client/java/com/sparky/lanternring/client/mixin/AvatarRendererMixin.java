package com.sparky.lanternring.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import com.sparky.lanternring.client.FlightPoses;
import net.minecraft.client.renderer.entity.player.AvatarRenderer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.world.entity.Avatar;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Third person: tilts the whole body for ring flight. */
@Mixin(AvatarRenderer.class)
public abstract class AvatarRendererMixin {
	@Inject(method = "extractRenderState(Lnet/minecraft/world/entity/Avatar;Lnet/minecraft/client/renderer/entity/state/AvatarRenderState;F)V",
			at = @At("TAIL"))
	private void lanternring$extractFlightPose(Avatar avatar, AvatarRenderState state, float partialTick, CallbackInfo ci) {
		FlightPoses.extract(avatar, state, partialTick);
	}

	@Inject(method = "setupRotations(Lnet/minecraft/client/renderer/entity/state/AvatarRenderState;Lcom/mojang/blaze3d/vertex/PoseStack;FF)V",
			at = @At("TAIL"))
	private void lanternring$tiltForFlight(AvatarRenderState state, PoseStack poseStack, float bodyRot, float scale, CallbackInfo ci) {
		FlightPoses.rotate(state, poseStack);
	}
}
