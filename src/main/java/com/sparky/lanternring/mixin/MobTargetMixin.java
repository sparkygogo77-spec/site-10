package com.sparky.lanternring.mixin;

import com.sparky.lanternring.MindLinks;
import com.sparky.lanternring.infinity.SoulStone;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** A mob under the Violet Lantern's Mind Link (or a Soul Stone soul) never targets its owner or the owner's other allies. */
@Mixin(Mob.class)
public abstract class MobTargetMixin {
	@Inject(method = "setTarget", at = @At("HEAD"), cancellable = true)
	private void lanternring$spareMindLink(LivingEntity target, CallbackInfo ci) {
		if (MindLinks.spares((Mob) (Object) this, target) || SoulStone.spares((Mob) (Object) this, target)) ci.cancel();
	}
}
