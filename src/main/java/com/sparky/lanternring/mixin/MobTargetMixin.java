package com.sparky.lanternring.mixin;

import com.sparky.lanternring.MindLinks;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** A mob under the Violet Lantern's Mind Link never targets its owner or the owner's other linked mobs. */
@Mixin(Mob.class)
public abstract class MobTargetMixin {
	@Inject(method = "setTarget", at = @At("HEAD"), cancellable = true)
	private void lanternring$spareMindLink(LivingEntity target, CallbackInfo ci) {
		if (MindLinks.spares((Mob) (Object) this, target)) ci.cancel();
	}
}
