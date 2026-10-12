package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.FlightPoses;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** Third person: flight poses for the arms, legs and head. */
@Mixin(PlayerModel.class)
public abstract class PlayerModelMixin {
	@Inject(method = "setupAnim(Lnet/minecraft/client/renderer/entity/state/AvatarRenderState;)V", at = @At("TAIL"))
	private void lanternring$flightPose(AvatarRenderState state, CallbackInfo ci) {
		FlightPoses.pose((PlayerModel) (Object) this, state);
	}
}
