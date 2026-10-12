package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.AnvilInput;
import com.sparky.lanternring.client.LanternPlaceInput;
import net.minecraft.client.Minecraft;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(Minecraft.class)
public abstract class MinecraftMixin {
	/** The double-click that sets the lantern down shouldn't also fire the ring. */
	@Inject(method = "startUseItem", at = @At("HEAD"), cancellable = true)
	private void lanternring$placeLantern(CallbackInfo ci) {
		if (LanternPlaceInput.consumesUse((Minecraft) (Object) this)) ci.cancel();
	}

	/** With the ring in Anvil mode, left-click aims the anvil (see AnvilInput) instead of hitting or mining. */
	@Inject(method = "startAttack", at = @At("HEAD"), cancellable = true)
	private void lanternring$anvilNoAttack(CallbackInfoReturnable<Boolean> cir) {
		if (AnvilInput.ownsLeftClick((Minecraft) (Object) this)) cir.setReturnValue(false);
	}

	@Inject(method = "continueAttack", at = @At("HEAD"), cancellable = true)
	private void lanternring$anvilNoMining(boolean down, CallbackInfo ci) {
		Minecraft mc = (Minecraft) (Object) this;
		if (AnvilInput.ownsLeftClick(mc)) {
			if (mc.gameMode != null && mc.gameMode.isDestroying()) mc.gameMode.stopDestroyBlock();
			ci.cancel();
		}
	}
}
