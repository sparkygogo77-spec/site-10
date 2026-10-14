package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.SuperJumps;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Vanilla widens the view with movement speed, so super sprint's speed boost would push the FOV
 * to its 150% limit. Here super sprint only adds a touch over the normal sprint widening, at full
 * speed, and less in third person where the camera is already pulled back.
 */
@Mixin(AbstractClientPlayer.class)
public abstract class AbstractClientPlayerMixin {
	/** Vanilla's own sprint widening (sprint speed 0.13 over walk 0.1: (1.3 + 1) / 2). */
	private static final float SPRINT_FOV = 0.15f;
	/** What super sprint adds on top at full speed, first and third person. */
	private static final float EXTRA_FIRST = 0.05f, EXTRA_THIRD = 0.02f;
	/** The blur pick's full boost: the extra reaches its cap here. */
	private static final float FULL_BOOST = 1.2f;

	@Inject(method = "getFieldOfViewModifier", at = @At("RETURN"), cancellable = true)
	private void lanternring$capSuperSprint(boolean firstPerson, float effectScale, CallbackInfoReturnable<Float> cir) {
		AbstractClientPlayer self = (AbstractClientPlayer) (Object) this;
		AttributeInstance speed = self.getAttribute(Attributes.MOVEMENT_SPEED);
		AttributeModifier sprint = speed == null ? null : speed.getModifier(SuperJumps.SPRINT_ID);
		if (sprint == null) return;
		boolean third = !firstPerson || !Minecraft.getInstance().options.getCameraType().isFirstPerson();
		float extra = (third ? EXTRA_THIRD : EXTRA_FIRST) * Math.min(1f, (float) sprint.amount() / FULL_BOOST);
		float cap = 1f + effectScale * (SPRINT_FOV + extra);
		if (cir.getReturnValueF() > cap) cir.setReturnValue(cap);
	}
}
