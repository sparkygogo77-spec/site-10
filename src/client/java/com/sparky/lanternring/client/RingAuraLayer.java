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
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.player.Player;

/**
 * The ring wearer's aura, two shells a touch bigger than their body, both drawn additively like a
 * charged creeper's shell (under a shader pack, where that draws black, as see-through emissive glass
 * instead; either way it shows where packs like Complementary drop the game's Glowing outline):
 * - a faint sheen, dark to pale, sliding over them like an enchantment glint;
 * - a bright line round the edge of every body part, so the outer line is always the brightest.
 * Red is a very dark red with a hot red edge; green is jade with a pale jade edge.
 */
public class RingAuraLayer extends RenderLayer<AvatarRenderState, PlayerModel> {
	private static final Identifier SHEEN = LanternRing.id("textures/entity/ring_aura.png");
	private static final Identifier EDGE = LanternRing.id("textures/entity/ring_aura_edge.png");
	/** How much bigger than the body each shell is. */
	private static final float SHEEN_GROW = 1.03f, EDGE_GROW = 1.06f;
	private static final int FULL_BRIGHT = 0xF000F0;

	public RingAuraLayer(RenderLayerParent<AvatarRenderState, PlayerModel> renderer) {
		super(renderer);
	}

	/** The sheen's colour (dark) and the edge's (bright), per corps. */
	private static int sheenColor(Corps corps) {
		return corps == Corps.RED ? 0x8A0C14 : 0x1E9A66;
	}

	private static int edgeColor(Corps corps) {
		return corps == Corps.RED ? 0xFF3030 : 0x7CFFC8;
	}

	@Override
	public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, AvatarRenderState state, float yRot, float xRot) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null || !(mc.level.getEntity(state.id) instanceof Player player) || !RageGlow.glows(player)) return;
		Corps corps = Corps.held(player);
		float age = state.ageInTicks;
		// The sheen breathes slowly; the edge stays steady and bright.
		float pulse = 0.75f + 0.25f * (float) Math.sin(age * 0.12);
		if (SoulSight.shaderPackOn()) {
			// Under a shader pack (Iris) the energy swirl draws as a solid black shell, so there both
			// are see-through emissive glass instead (as the ring flare does); dark texels are clear.
			shell(poseStack, collector, state, SHEEN_GROW, RenderTypes.entityTranslucentEmissive(SHEEN), withAlpha(sheenColor(corps), 0.7f * pulse));
			shell(poseStack, collector, state, EDGE_GROW, RenderTypes.entityTranslucentEmissive(EDGE), withAlpha(edgeColor(corps), 1f));
			return;
		}
		shell(poseStack, collector, state, SHEEN_GROW, RenderTypes.energySwirl(SHEEN, age * 0.006f % 1f, age * 0.004f % 1f), scale(sheenColor(corps), pulse));
		shell(poseStack, collector, state, EDGE_GROW, RenderTypes.energySwirl(EDGE, 0f, 0f), 0xFF000000 | edgeColor(corps));
	}

	private void shell(PoseStack poseStack, SubmitNodeCollector collector, AvatarRenderState state, float grow, RenderType type, int color) {
		poseStack.pushPose();
		// Grow it around the body's middle (the model's feet are 1.5 blocks below its origin).
		poseStack.translate(0, 0.75f * (1 - grow), 0);
		poseStack.scale(grow, grow, grow);
		collector.order(1).submitModel(getParentModel(), state, poseStack, type, FULL_BRIGHT, OverlayTexture.NO_OVERLAY, color, null, state.outlineColor);
		poseStack.popPose();
	}

	private static int withAlpha(int rgb, float alpha) {
		return Math.clamp(Math.round(alpha * 255), 0, 255) << 24 | rgb & 0xFFFFFF;
	}

	private static int scale(int rgb, float f) {
		int r = Math.round((rgb >> 16 & 0xFF) * f), g = Math.round((rgb >> 8 & 0xFF) * f), b = Math.round((rgb & 0xFF) * f);
		return 0xFF000000 | r << 16 | g << 8 | b;
	}
}
