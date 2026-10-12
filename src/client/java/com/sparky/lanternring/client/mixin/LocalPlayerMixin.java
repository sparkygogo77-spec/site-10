package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.FastFlight;
import net.minecraft.client.player.LocalPlayer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Keeps the ring glide going when it touches something, where vanilla would end it like an elytra. */
@Mixin(LocalPlayer.class)
public abstract class LocalPlayerMixin {
	/** Hitting a wall stops vanilla sprinting, which would drop the glide back to slow flight. */
	@Inject(method = "shouldStopRunSprinting", at = @At("HEAD"), cancellable = true)
	private void lanternring$keepSprintOnWalls(CallbackInfoReturnable<Boolean> cir) {
		if (FastFlight.isGliding((LocalPlayer) (Object) this)) cir.setReturnValue(false);
	}

	/** Vanilla lands a flying player as soon as they touch the ground; the glide skims over it instead. */
	@Inject(method = "aiStep", at = @At(value = "INVOKE", target = "Lnet/minecraft/client/player/AbstractClientPlayer;aiStep()V", shift = At.Shift.AFTER))
	private void lanternring$skimGround(CallbackInfo ci) {
		LocalPlayer self = (LocalPlayer) (Object) this;
		if (self.onGround() && FastFlight.isGliding(self)) self.setOnGround(false);
	}
}
