package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.player.Player;

/**
 * The ring wearer's aura: a slightly bigger copy of their body in glowing flame streaks of their
 * corps' colour, drawn like a charged creeper's shell. Shader packs (Complementary under Iris) hide
 * the game's Glowing outline but keep this, and treat it as emissive, so it glows there too.
 */
public class RingAuraLayer extends RenderLayer<AvatarRenderState, PlayerModel> {
	private static final Identifier TEXTURE = LanternRing.id("textures/entity/ring_aura.png");
	/** How much bigger than the body the aura is. */
	private static final float GROW = 1.12f;
	private static final int FULL_BRIGHT = 0xF000F0;

	public RingAuraLayer(RenderLayerParent<AvatarRenderState, PlayerModel> renderer) {
		super(renderer);
	}

	@Override
	public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, AvatarRenderState state, float yRot, float xRot) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null || !(mc.level.getEntity(state.id) instanceof Player player) || !RageGlow.glows(player)) return;
		Corps corps = Corps.held(player);
		float age = state.ageInTicks;
		// A slow pulse, so it breathes like the lantern.
		float pulse = 0.7f + 0.2f * (float) Math.sin(age * 0.15);
		int r = Math.round((corps.rgb >> 16 & 0xFF) * pulse), g = Math.round((corps.rgb >> 8 & 0xFF) * pulse), b = Math.round((corps.rgb & 0xFF) * pulse);
		int color = 0xFF000000 | r << 16 | g << 8 | b;
		poseStack.pushPose();
		// Grow it around the body's middle (the model's feet are 1.5 blocks below its origin).
		poseStack.translate(0, 0.75f * (1 - GROW), 0);
		poseStack.scale(GROW, GROW, GROW);
		collector.order(1).submitModel(getParentModel(), state, poseStack,
				RenderTypes.energySwirl(TEXTURE, 0f, -age * 0.02f % 1f), FULL_BRIGHT, OverlayTexture.NO_OVERLAY, color, null, state.outlineColor);
		poseStack.popPose();
	}
}
