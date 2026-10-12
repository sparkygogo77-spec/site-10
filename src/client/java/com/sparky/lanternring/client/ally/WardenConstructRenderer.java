package com.sparky.lanternring.client.ally;

import com.sparky.lanternring.ally.WardenConstruct;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.model.monster.warden.WardenModel;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.state.WardenRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;

/** The Warden construct: the warden's own model and animations in hard light (see ConstructSkins). */
public class WardenConstructRenderer extends MobRenderer<WardenConstruct, WardenConstructRenderer.State, WardenModel> {
	private static final Identifier VANILLA = Identifier.withDefaultNamespace("textures/entity/warden/warden.png");

	public static class State extends WardenRenderState {
		float life;
	}

	public WardenConstructRenderer(EntityRendererProvider.Context context) {
		super(context, new WardenModel(context.bakeLayer(ModelLayers.WARDEN)), 0.6f);
	}

	@Override
	public Identifier getTextureLocation(State state) {
		return ConstructSkins.get("warden", model.root(), VANILLA, 4);
	}

	@Override
	protected RenderType getRenderType(State state, boolean visible, boolean transparent, boolean glowing) {
		return RenderTypes.entityTranslucentEmissive(getTextureLocation(state));
	}

	@Override
	protected int getModelTint(State state) {
		return ConstructLook.tint(state.life, state.ageInTicks);
	}

	@Override
	protected int getBlockLightLevel(WardenConstruct entity, BlockPos pos) {
		return 15;
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(WardenConstruct entity, State state, float partialTicks) {
		super.extractRenderState(entity, state, partialTicks);
		state.attackAnimationState.copyFrom(entity.attackAnimationState);
		state.sonicBoomAnimationState.copyFrom(entity.sonicBoomAnimationState);
		state.life = entity.lifeFraction();
	}
}
