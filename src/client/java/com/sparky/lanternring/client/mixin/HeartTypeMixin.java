package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModEffects;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.Identifier;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Dread (the Yellow Fear Nuke's slow death, see DreadEffect) turns your hearts yellow. */
@Mixin(targets = "net.minecraft.client.gui.Hud$HeartType")
public abstract class HeartTypeMixin {
	private static final Identifier FULL = LanternRing.id("hud/heart/dread_full");
	private static final Identifier FULL_BLINKING = LanternRing.id("hud/heart/dread_full_blinking");
	private static final Identifier HALF = LanternRing.id("hud/heart/dread_half");
	private static final Identifier HALF_BLINKING = LanternRing.id("hud/heart/dread_half_blinking");

	@Inject(method = "getSprite", at = @At("HEAD"), cancellable = true)
	private void lanternring$dread(boolean hardcore, boolean half, boolean blinking, CallbackInfoReturnable<Identifier> cir) {
		String type = ((Enum<?>) (Object) this).name();
		// The empty heart containers and absorption's golden hearts stay as they are.
		if (type.equals("CONTAINER") || type.equals("ABSORBING")) return;
		var player = Minecraft.getInstance().player;
		if (player == null || !player.hasEffect(ModEffects.DREAD)) return;
		cir.setReturnValue(half ? (blinking ? HALF_BLINKING : HALF) : (blinking ? FULL_BLINKING : FULL));
	}
}
