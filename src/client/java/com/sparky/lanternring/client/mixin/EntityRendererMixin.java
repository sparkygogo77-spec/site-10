package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.SoulSight;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(EntityRenderer.class)
public abstract class EntityRendererMixin {
	/** The Soul Stone outlines what it sees in orange (SoulSight). Ring wearers have no outline, only a soft glint (RingAuraLayer). */
	@Inject(method = "extractRenderState", at = @At("TAIL"))
	private void lanternring$rageGlow(Entity entity, EntityRenderState state, float partialTick, CallbackInfo ci) {
		boolean soul = SoulSight.sees(entity);
		((SoulSight.Holder) state).lanternring$setSoulSight(soul);
		if (soul) state.outlineColor = 0xFF000000 | SoulSight.ORANGE;
	}
}
