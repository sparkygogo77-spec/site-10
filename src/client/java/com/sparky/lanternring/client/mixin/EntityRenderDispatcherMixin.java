package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.corps.BlueVillagerRenderer;
import net.minecraft.client.renderer.entity.EntityRenderDispatcher;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** The Blue Lantern's villagers are drawn in their suit (BlueVillagerRenderer), other villagers as usual. */
@Mixin(EntityRenderDispatcher.class)
public abstract class EntityRenderDispatcherMixin {
	@Inject(method = "getRenderer(Lnet/minecraft/world/entity/Entity;)Lnet/minecraft/client/renderer/entity/EntityRenderer;",
			at = @At("HEAD"), cancellable = true)
	private void lanternring$blueVillager(Entity entity, CallbackInfoReturnable<EntityRenderer<?, ?>> cir) {
		BlueVillagerRenderer r = BlueVillagerRenderer.forEntity(entity);
		if (r != null) cir.setReturnValue(r);
	}

	@Inject(method = "getRenderer(Lnet/minecraft/client/renderer/entity/state/EntityRenderState;)Lnet/minecraft/client/renderer/entity/EntityRenderer;",
			at = @At("HEAD"), cancellable = true)
	private void lanternring$blueVillagerState(EntityRenderState state, CallbackInfoReturnable<EntityRenderer<?, ?>> cir) {
		BlueVillagerRenderer r = BlueVillagerRenderer.forState(state);
		if (r != null) cir.setReturnValue(r);
	}
}
