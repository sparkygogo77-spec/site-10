package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.sparky.lanternring.item.PowerRingItem;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.world.entity.player.PlayerModelType;
import net.minecraft.world.item.ItemStack;

/** Third person: draws the ring on whichever hand holds it. */
public class RingHandLayer extends RenderLayer<AvatarRenderState, PlayerModel> {
	public RingHandLayer(RenderLayerParent<AvatarRenderState, PlayerModel> renderer) {
		super(renderer);
	}

	@Override
	public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, AvatarRenderState state, float yRot, float xRot) {
		boolean slim = state.skin != null && state.skin.model() == PlayerModelType.SLIM;
		LabSettings.RingModel model = LabSettings.get().ringModel;
		if (isRing(state.rightHandItemStack)) {
			poseStack.pushPose();
			getParentModel().rightArm.translateAndRotate(poseStack);
			RingModels.render(poseStack, collector, light, model, false, slim);
			poseStack.popPose();
		}
		if (isRing(state.leftHandItemStack)) {
			poseStack.pushPose();
			getParentModel().leftArm.translateAndRotate(poseStack);
			RingModels.render(poseStack, collector, light, model, true, slim);
			poseStack.popPose();
		}
	}

	private static boolean isRing(ItemStack stack) {
		return stack != null && stack.getItem() instanceof PowerRingItem;
	}
}
