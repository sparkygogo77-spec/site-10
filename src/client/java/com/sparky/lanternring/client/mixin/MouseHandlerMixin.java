package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.BuildInput;
import net.minecraft.client.Minecraft;
import net.minecraft.client.MouseHandler;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(MouseHandler.class)
public abstract class MouseHandlerMixin {
	/**
	 * While a build is being chosen the wheel scrolls designs, and while a Lasso catch is held it moves
	 * the bubble out or in, not the hotbar (see BuildInput, LassoFx).
	 */
	@Inject(method = "onScroll", at = @At("HEAD"), cancellable = true)
	private void lanternring$scrollBuilds(long window, double x, double y, CallbackInfo ci) {
		Minecraft mc = Minecraft.getInstance();
		if (window == mc.getWindow().handle() && (BuildInput.scroll(mc, y) || com.sparky.lanternring.client.LassoFx.scroll(mc, y))) ci.cancel();
	}
}
