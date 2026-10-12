package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.LanternPlaceInput;
import net.minecraft.client.Minecraft;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(Minecraft.class)
public abstract class MinecraftMixin {
	/** The double-click that sets the lantern down shouldn't also fire the ring. */
	@Inject(method = "startUseItem", at = @At("HEAD"), cancellable = true)
	private void lanternring$placeLantern(CallbackInfo ci) {
		if (LanternPlaceInput.consumesUse((Minecraft) (Object) this)) ci.cancel();
	}
}
