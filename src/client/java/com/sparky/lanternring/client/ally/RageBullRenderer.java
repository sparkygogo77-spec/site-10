package com.sparky.lanternring.client.ally;

import com.mojang.blaze3d.vertex.PoseStack;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ally.RageBull;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.client.BbRig;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.LivingEntityEmissiveLayer;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;

/**
 * The Red Lantern's Rage Bull: the rigged Blockbench bull (tools/rage_bull.py, posed by
 * RageBullModel) in red hard light, {@link RageBull#SCALE} times its size, with its eyes and
 * nostrils burning full-bright on top. It fades in as it appears and out once its run is over.
 */
public class RageBullRenderer extends MobRenderer<RageBull, RageBullRenderer.State, RageBullModel> {
	private static final Identifier TEXTURE = LanternRing.id("textures/entity/bb/rage_bull.png");
	private static BbRig.Layers layers;
	private static final float FADE_IN = 10f;

	public static class State extends LivingEntityRenderState {
		float alpha = 1f;
	}

	private static BbRig.Layers layers() {
		if (layers == null) layers = BbRig.load("rage_bull");
		return layers;
	}

	public RageBullRenderer(EntityRendererProvider.Context context) {
		super(context, new RageBullModel(layers().solid().bakeRoot()), 0.45f * RageBull.SCALE);
		RageBullModel glow = new RageBullModel(layers().glow().bakeRoot());
		addLayer(new LivingEntityEmissiveLayer<>((RenderLayerParent<State, RageBullModel>) this,
				state -> ConstructSkins.glow("rage_bull", TEXTURE, Corps.RED),
				(state, age) -> state.alpha * (0.85f + 0.15f * Mth.sin(age * 0.4f)), glow, RenderTypes::entityTranslucentEmissive, false));
	}

	@Override
	public Identifier getTextureLocation(State state) {
		return ConstructSkins.get("rage_bull", model.root(), TEXTURE, 2, Corps.RED);
	}

	@Override
	protected RenderType getRenderType(State state, boolean visible, boolean transparent, boolean glowing) {
		return RenderTypes.entityTranslucentEmissive(getTextureLocation(state));
	}

	@Override
	protected int getModelTint(State state) {
		return Math.round(state.alpha * 255) << 24 | 0xFFFFFF;
	}

	@Override
	protected void scale(State state, PoseStack poseStack) {
		poseStack.scale(RageBull.SCALE, RageBull.SCALE, RageBull.SCALE);
	}

	@Override
	protected int getBlockLightLevel(RageBull entity, BlockPos pos) {
		return 15;
	}

	@Override
	protected boolean shouldShowName(RageBull entity, double distance) {
		return false;
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(RageBull entity, State state, float partialTicks) {
		super.extractRenderState(entity, state, partialTicks);
		float in = Mth.clamp((entity.tickCount + partialTicks) / FADE_IN, 0.05f, 1f);
		int stopped = entity.stopped();
		float out = stopped < 0 ? 1f : Mth.clamp(1f - (stopped + partialTicks) / RageBull.FADE, 0f, 1f);
		state.alpha = in * out;
		// The walk is worked out from how far it moved, which for something this big is a frantic
		// gallop: slow it to a heavy trot with a steady swing, and stand still once it stops.
		state.walkAnimationPos *= 0.6f;
		state.walkAnimationSpeed = stopped < 0 ? Math.min(state.walkAnimationSpeed, 0.6f) : 0f;
	}
}
