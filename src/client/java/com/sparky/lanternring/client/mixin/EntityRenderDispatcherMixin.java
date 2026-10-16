package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.DroppedRingRenderer;
import com.sparky.lanternring.client.corps.BlueVillagerRenderer;
import com.sparky.lanternring.client.corps.HopeGolemRenderer;
import net.minecraft.client.renderer.entity.EntityRenderDispatcher;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * The Blue Lantern's villagers are drawn in their suit (BlueVillagerRenderer) and its golems as hard
 * light (HopeGolemRenderer); other villagers and golems as usual. Dropped rings are the real
 * glowing ring (DroppedRingRenderer).
 */
@Mixin(EntityRenderDispatcher.class)
public abstract class EntityRenderDispatcherMixin {
	@Inject(method = "getRenderer(Lnet/minecraft/world/entity/Entity;)Lnet/minecraft/client/renderer/entity/EntityRenderer;",
			at = @At("HEAD"), cancellable = true)
	private void lanternring$blueVillager(Entity entity, CallbackInfoReturnable<EntityRenderer<?, ?>> cir) {
		BlueVillagerRenderer r = BlueVillagerRenderer.forEntity(entity);
		if (r != null) cir.setReturnValue(r);
		HopeGolemRenderer g = HopeGolemRenderer.forEntity(entity);
		if (g != null) cir.setReturnValue(g);
		DroppedRingRenderer d = DroppedRingRenderer.forEntity(entity);
		if (d != null) cir.setReturnValue(d);
	}

	@Inject(method = "getRenderer(Lnet/minecraft/client/renderer/entity/state/EntityRenderState;)Lnet/minecraft/client/renderer/entity/EntityRenderer;",
			at = @At("HEAD"), cancellable = true)
	private void lanternring$blueVillagerState(EntityRenderState state, CallbackInfoReturnable<EntityRenderer<?, ?>> cir) {
		BlueVillagerRenderer r = BlueVillagerRenderer.forState(state);
		if (r != null) cir.setReturnValue(r);
		HopeGolemRenderer g = HopeGolemRenderer.forState(state);
		if (g != null) cir.setReturnValue(g);
		DroppedRingRenderer d = DroppedRingRenderer.forState(state);
		if (d != null) cir.setReturnValue(d);
	}
}
