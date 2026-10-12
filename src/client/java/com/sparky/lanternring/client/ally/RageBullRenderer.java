package com.sparky.lanternring.client.ally;

import com.mojang.blaze3d.vertex.PoseStack;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ally.RageBull;
import net.minecraft.client.model.animal.cow.CowModel;
import net.minecraft.client.model.animal.cow.WarmCowModel;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;

/**
 * The Red Lantern's Rage Bull: for now the warm cow's own model (the one with the long horns) in
 * red hard light, {@link RageBull#SCALE} times its size, trotting with the cow's walk. It fades in
 * as it appears and out once its run is over. A proper bull model replaces it once J approves one.
 */
public class RageBullRenderer extends MobRenderer<RageBull, RageBullRenderer.State, CowModel> {
	private static final Identifier VANILLA = Identifier.withDefaultNamespace("textures/entity/cow/cow_warm.png");
	private static final float FADE_IN = 10f;

	public static class State extends LivingEntityRenderState {
		float alpha = 1f;
	}

	public RageBullRenderer(EntityRendererProvider.Context context) {
		super(context, new WarmCowModel(context.bakeLayer(ModelLayers.WARM_COW)), 0.6f * RageBull.SCALE);
	}

	@Override
	public Identifier getTextureLocation(State state) {
		return ConstructSkins.get("cow_warm", model.root(), VANILLA, 4, Corps.RED);
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
		state.walkAnimationSpeed = stopped < 0 ? Math.min(state.walkAnimationSpeed, 0.5f) : 0f;
	}
}
