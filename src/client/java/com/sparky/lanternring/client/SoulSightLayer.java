package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;

/**
 * The Soul Stone's silhouette (see SoulSight): the body drawn again in additive orange in front of
 * walls, a faint fill with a bright line round each body part on players.
 */
public class SoulSightLayer<S extends LivingEntityRenderState, M extends EntityModel<? super S>> extends RenderLayer<S, M> {
	private static final int FULL_BRIGHT = 0xF000F0;

	public SoulSightLayer(RenderLayerParent<S, M> renderer) {
		super(renderer);
	}

	@Override
	public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, S state, float yRot, float xRot) {
		if (!((SoulSight.Holder) state).lanternring$soulSight()) return;
		float pulse = 0.8f + 0.2f * (float) Math.sin(state.ageInTicks * 0.15);
		collector.order(2).submitModel(getParentModel(), state, poseStack, SoulSight.FILL, FULL_BRIGHT, OverlayTexture.NO_OVERLAY,
				scale(SoulSight.ORANGE, 0.55f * pulse), null, 0);
		if (state instanceof AvatarRenderState) {
			collector.order(2).submitModel(getParentModel(), state, poseStack, SoulSight.EDGE, FULL_BRIGHT, OverlayTexture.NO_OVERLAY,
					0xFF000000 | SoulSight.ORANGE, null, 0);
		}
	}

	private static int scale(int rgb, float f) {
		int r = Math.round((rgb >> 16 & 0xFF) * f), g = Math.round((rgb >> 8 & 0xFF) * f), b = Math.round((rgb & 0xFF) * f);
		return 0xFF000000 | r << 16 | g << 8 | b;
	}
}
