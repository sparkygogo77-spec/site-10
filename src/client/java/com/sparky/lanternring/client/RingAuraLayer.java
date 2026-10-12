package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
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
 * The ring wearer's aura: a soft glint in the corps' colour sliding over their body like an
 * enchantment glint, drawn additively like a charged creeper's shell (under a shader pack, where that
 * draws black, as faint see-through emissive glass instead). No outline and no hard edge. It is
 * drawn on your own arm in first person too ({@link #submitArm}).
 */
public class RingAuraLayer extends RenderLayer<AvatarRenderState, PlayerModel> {
	private static final Identifier SHEEN = LanternRing.id("textures/entity/ring_aura.png");
	/** How much bigger than the body the shell is (just enough not to flicker against the skin). */
	private static final float GROW = 1.02f;
	private static final int FULL_BRIGHT = 0xF000F0;

	public RingAuraLayer(RenderLayerParent<AvatarRenderState, PlayerModel> renderer) {
		super(renderer);
	}

	/** The glint's colour per corps: a deep red for the Red Lanterns, jade for green, and every other corps' own shade. */
	private static int color(Corps corps) {
		return corps == Corps.RED ? 0xC81A22 : CorpsTint.apply(corps, 0x2FC888);
	}

	/** The glint's render type and colour right now, or null when there is nothing to draw. */
	private static RenderType type(float age) {
		if (SoulSight.shaderPackOn()) return RenderTypes.entityTranslucentEmissive(SHEEN);
		return RenderTypes.energySwirl(SHEEN, age * 0.004f % 1f, age * 0.0025f % 1f);
	}

	private static int tint(Corps corps, float age, float strength) {
		// Breathes slowly, like the glint catching the light.
		float pulse = strength * (0.8f + 0.2f * (float) Math.sin(age * 0.1));
		// Under a shader pack the glass is not additive, so the colour's alpha keeps it faint.
		return SoulSight.shaderPackOn() ? withAlpha(color(corps), 0.55f * pulse) : scale(color(corps), pulse);
	}

	@Override
	public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, AvatarRenderState state, float yRot, float xRot) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null || !(mc.level.getEntity(state.id) instanceof Player player) || !RageGlow.glows(player)) return;
		Corps corps = Corps.held(player);
		float age = state.ageInTicks;
		poseStack.pushPose();
		// Grow it around the body's middle (the model's feet are 1.5 blocks below its origin).
		poseStack.translate(0, 0.75f * (1 - GROW), 0);
		poseStack.scale(GROW, GROW, GROW);
		collector.order(1).submitModel(getParentModel(), state, poseStack, type(age), FULL_BRIGHT, OverlayTexture.NO_OVERLAY,
				tint(corps, age, 1f), null, 0);
		poseStack.popPose();
	}

	/**
	 * The glint on your own arm in first person, with the pose stack where the game drew the arm
	 * (the arm part posed as it was drawn).
	 */
	public static void submitArm(PoseStack poseStack, SubmitNodeCollector collector, ModelPart arm, float partialTick) {
		Player player = Minecraft.getInstance().player;
		if (player == null || !RageGlow.glows(player)) return;
		float age = player.tickCount + partialTick;
		collector.order(1).submitModelPart(arm, poseStack, type(age), FULL_BRIGHT, OverlayTexture.NO_OVERLAY, null,
				// Softer than on the body: the arm fills much of the screen.
				tint(Corps.held(player), age, 0.7f));
	}

	private static int withAlpha(int rgb, float alpha) {
		return Math.clamp(Math.round(alpha * 255), 0, 255) << 24 | rgb & 0xFFFFFF;
	}

	private static int scale(int rgb, float f) {
		int r = Math.round((rgb >> 16 & 0xFF) * f), g = Math.round((rgb >> 8 & 0xFF) * f), b = Math.round((rgb & 0xFF) * f);
		return 0xFF000000 | r << 16 | g << 8 | b;
	}
}
