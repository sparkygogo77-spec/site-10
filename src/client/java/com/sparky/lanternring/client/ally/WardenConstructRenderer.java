package com.sparky.lanternring.client.ally;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ally.WardenConstruct;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.model.monster.warden.WardenModel;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.LivingEntityEmissiveLayer;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.state.WardenRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;

/** The Warden construct: the warden's own model and animations in hard light (see ConstructSkins). */
public class WardenConstructRenderer extends MobRenderer<WardenConstruct, WardenConstructRenderer.State, WardenModel> {
	private static final Identifier VANILLA = Identifier.withDefaultNamespace("textures/entity/warden/warden.png");

	public static class State extends WardenRenderState {
		float life;
		Corps corps = Corps.GREEN;
	}

	private static final Identifier BIOLUMINESCENT = Identifier.withDefaultNamespace("textures/entity/warden/warden_bioluminescent_layer.png");
	private static final Identifier SPOTS_1 = Identifier.withDefaultNamespace("textures/entity/warden/warden_pulsating_spots_1.png");
	private static final Identifier SPOTS_2 = Identifier.withDefaultNamespace("textures/entity/warden/warden_pulsating_spots_2.png");
	private static final Identifier HEART = Identifier.withDefaultNamespace("textures/entity/warden/warden_heart.png");

	@SuppressWarnings({"unchecked", "rawtypes"})
	public WardenConstructRenderer(EntityRendererProvider.Context context) {
		super(context, new WardenModel(context.bakeLayer(ModelLayers.WARDEN)), 0.6f);
		// The warden's glowing layers, as the real one has them, in bright mint: its markings,
		// the spots that pulse in turn, and the beating heart in its ribcage.
		WardenModel glowModel = new WardenModel(context.bakeLayer(ModelLayers.WARDEN_BIOLUMINESCENT));
		WardenModel spotsModel = new WardenModel(context.bakeLayer(ModelLayers.WARDEN_PULSATING_SPOTS));
		WardenModel heartModel = new WardenModel(context.bakeLayer(ModelLayers.WARDEN_HEART));
		RenderLayerParent parent = (RenderLayerParent) this;
		addLayer((RenderLayer) new LivingEntityEmissiveLayer<WardenRenderState, WardenModel>(parent,
				state -> ConstructSkins.glow("warden_markings", BIOLUMINESCENT, ((State) state).corps), (state, age) -> 1f, glowModel, RenderTypes::entityTranslucentEmissive, false));
		addLayer((RenderLayer) new LivingEntityEmissiveLayer<WardenRenderState, WardenModel>(parent,
				state -> ConstructSkins.glow("warden_spots_1", SPOTS_1, ((State) state).corps), (state, age) -> Math.max(0f, Mth.cos(age * 0.09f)), spotsModel,
				RenderTypes::entityTranslucentEmissive, false));
		addLayer((RenderLayer) new LivingEntityEmissiveLayer<WardenRenderState, WardenModel>(parent,
				state -> ConstructSkins.glow("warden_spots_2", SPOTS_2, ((State) state).corps), (state, age) -> Math.max(0f, Mth.cos(age * 0.09f + Mth.PI)), spotsModel,
				RenderTypes::entityTranslucentEmissive, false));
		addLayer((RenderLayer) new LivingEntityEmissiveLayer<WardenRenderState, WardenModel>(parent,
				state -> ConstructSkins.glow("warden_heart", HEART, ((State) state).corps), (state, age) -> state.heartAnimation, heartModel,
				RenderTypes::entityTranslucentEmissive, false));
	}

	@Override
	public Identifier getTextureLocation(State state) {
		return ConstructSkins.get("warden", model.root(), VANILLA, 4, state.corps);
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
		state.corps = entity.corps();
		state.attackAnimationState.copyFrom(entity.attackAnimationState);
		state.sonicBoomAnimationState.copyFrom(entity.sonicBoomAnimationState);
		state.life = entity.lifeFraction();
		// A steady heartbeat, quicker while it fights.
		float beat = state.ageInTicks * (entity.attackAnimationState.isStarted() ? 0.5f : 0.25f);
		state.heartAnimation = 0.4f + 0.6f * Math.max(0f, Mth.sin(beat));
		state.tendrilAnimation = 0.15f * Mth.sin(state.ageInTicks * 0.2f);
	}
}
