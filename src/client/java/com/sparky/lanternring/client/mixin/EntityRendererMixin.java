package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.RageGlow;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(EntityRenderer.class)
public abstract class EntityRendererMixin {
	/** A ring's wearer is outlined in its corps' colour (see RageGlow). */
	@Inject(method = "extractRenderState", at = @At("TAIL"))
	private void lanternring$rageGlow(Entity entity, EntityRenderState state, float partialTick, CallbackInfo ci) {
		if (RageGlow.glows(entity)) state.outlineColor = RageGlow.color(entity);
	}
}
