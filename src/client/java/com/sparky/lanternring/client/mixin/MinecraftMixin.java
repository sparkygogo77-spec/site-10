package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.AnvilInput;
import com.sparky.lanternring.client.LanternChargeInput;
import com.sparky.lanternring.client.LanternPlaceInput;
import com.sparky.lanternring.client.LassoFx;
import com.sparky.lanternring.client.SoulSight;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(Minecraft.class)
public abstract class MinecraftMixin {
	/**
	 * The double-click that sets the lantern down shouldn't also fire the ring, and with left-click
	 * held right-click charges from the lantern instead (see LanternChargeInput).
	 */
	@Inject(method = "startUseItem", at = @At("HEAD"), cancellable = true)
	private void lanternring$placeLantern(CallbackInfo ci) {
		Minecraft mc = (Minecraft) (Object) this;
		if (LanternPlaceInput.consumesUse(mc) || LanternChargeInput.beforeUse(mc)) ci.cancel();
	}

	/** Left-click picks the Anvil's size, charges from the lantern or picks Lasso mobs, instead of hitting or mining. */
	@Inject(method = "startAttack", at = @At("HEAD"), cancellable = true)
	private void lanternring$anvilNoAttack(CallbackInfoReturnable<Boolean> cir) {
		Minecraft mc = (Minecraft) (Object) this;
		if (AnvilInput.ownsLeftClick(mc) || LanternChargeInput.ownsLeftClick(mc) || LassoFx.picking(mc)) cir.setReturnValue(false);
	}

	/** The Soul Stone outlines what it sees (ring wearers get the soft aura instead, RingAuraLayer). */
	@Inject(method = "shouldEntityAppearGlowing", at = @At("HEAD"), cancellable = true)
	private void lanternring$soulSightGlow(Entity entity, CallbackInfoReturnable<Boolean> cir) {
		if (SoulSight.sees(entity)) cir.setReturnValue(true);
	}

	@Inject(method = "continueAttack", at = @At("HEAD"), cancellable = true)
	private void lanternring$anvilNoMining(boolean down, CallbackInfo ci) {
		Minecraft mc = (Minecraft) (Object) this;
		if (AnvilInput.ownsLeftClick(mc) || LanternChargeInput.ownsLeftClick(mc) || LassoFx.picking(mc)) {
			if (mc.gameMode != null && mc.gameMode.isDestroying()) mc.gameMode.stopDestroyBlock();
			ci.cancel();
		}
	}
}
