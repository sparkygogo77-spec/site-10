package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.AnvilInput;
import net.minecraft.client.Minecraft;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** With the ring in Anvil mode, left-click aims the anvil (see AnvilInput) instead of hitting or mining. */
@Mixin(Minecraft.class)
public abstract class MinecraftMixin {
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
