package com.sparky.lanternring.mixin;

import com.sparky.lanternring.corps.RedTower;
import net.minecraft.world.entity.Mob;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Monsters can't be leashed, except the enraged ones chained to posts in a Red tower's field. */
@Mixin(Mob.class)
public abstract class MobLeashMixin {
	@Inject(method = "canBeLeashed", at = @At("HEAD"), cancellable = true)
	private void lanternring$chained(CallbackInfoReturnable<Boolean> cir) {
		if (RedTower.chained((Mob) (Object) this)) cir.setReturnValue(true);
	}
}
