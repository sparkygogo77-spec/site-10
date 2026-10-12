package com.sparky.lanternring.client.mixin;

import com.mojang.blaze3d.vertex.PoseStack;
import com.sparky.lanternring.client.LanternFirstPerson;
import com.sparky.lanternring.client.RingFirstPerson;
import net.minecraft.client.renderer.FirstPersonHandsAndItemsRenderer;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.state.level.FirstPersonHandsAndItemsRenderState;
import net.minecraft.client.renderer.state.level.PlayerRenderState;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(FirstPersonHandsAndItemsRenderer.class)
public abstract class FirstPersonHandsMixin {
	@Inject(method = "submitArmWithItem", at = @At("HEAD"), cancellable = true)
	private void lanternring$ringAndLantern(PlayerRenderState playerState, FirstPersonHandsAndItemsRenderState handsState,
			float partialTick, float xRot, InteractionHand hand, float swing, ItemStack stack, float equip,
			PoseStack poseStack, SubmitNodeCollector collector, int light, CallbackInfo ci) {
		if (RingFirstPerson.render(playerState, hand, swing, equip, stack, poseStack, collector, light, partialTick)
				|| LanternFirstPerson.render(playerState, hand, swing, equip, stack, poseStack, collector, light, partialTick)) {
			ci.cancel();
		}
	}
}
