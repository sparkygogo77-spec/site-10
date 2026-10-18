package com.sparky.lanternring.client.ally;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ally.WardenConstruct;
import com.sparky.lanternring.client.LabSettings;
import com.mojang.blaze3d.vertex.PoseStack;
import java.util.Map;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.SubmitNodeCollector;
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

/**
 * The Warden construct: the warden's own model and animations in hard light (see ConstructSkins), or with the Ring Lab's
 * "Construct warden" on R4b (Blender pass 838, J's KEEP) the real warden under W1 weave construct plate armour
 * (WardenArmourModel) that forms over it in 1 s, feet first, in the summoning ring's corps colour.
 */
public class WardenConstructRenderer extends MobRenderer<WardenConstruct, WardenConstructRenderer.State, WardenModel> {
	private static final Identifier VANILLA = Identifier.withDefaultNamespace("textures/entity/warden/warden.png");

	public static class State extends WardenRenderState {
		float life;
		Corps corps = Corps.GREEN;
		/** The R4b armour's strip, or null for the hard-light warden. */
		String armour;
	}

	/** Pixels per texel of the armour skin: one strip frame across a plate keeps its detail. */
	private static final int ARMOUR_SCALE = 4;
	/** The armour forms over 20 ticks, rising past the warden's full height (tendrils included). */
	private static final float FORM_TICKS = 20f, FORM_TOP = 62f;

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
				state -> ((State) state).armour != null ? BIOLUMINESCENT : ConstructSkins.glow("warden_markings", BIOLUMINESCENT, ((State) state).corps), (state, age) -> 1f, glowModel, RenderTypes::entityTranslucentEmissive, false));
		addLayer((RenderLayer) new LivingEntityEmissiveLayer<WardenRenderState, WardenModel>(parent,
				state -> ((State) state).armour != null ? SPOTS_1 : ConstructSkins.glow("warden_spots_1", SPOTS_1, ((State) state).corps), (state, age) -> Math.max(0f, Mth.cos(age * 0.09f)), spotsModel,
				RenderTypes::entityTranslucentEmissive, false));
		addLayer((RenderLayer) new LivingEntityEmissiveLayer<WardenRenderState, WardenModel>(parent,
				state -> ((State) state).armour != null ? SPOTS_2 : ConstructSkins.glow("warden_spots_2", SPOTS_2, ((State) state).corps), (state, age) -> Math.max(0f, Mth.cos(age * 0.09f + Mth.PI)), spotsModel,
				RenderTypes::entityTranslucentEmissive, false));
		addLayer((RenderLayer) new LivingEntityEmissiveLayer<WardenRenderState, WardenModel>(parent,
				state -> ((State) state).armour != null ? HEART : ConstructSkins.glow("warden_heart", HEART, ((State) state).corps), (state, age) -> state.heartAnimation, heartModel,
				RenderTypes::entityTranslucentEmissive, false));
		// 838 R4b: the plate armour, posed by the warden's own animation (same bones), forming feet first.
		ModelPart armourRoot = WardenArmourModel.create().bakeRoot();
		WardenModel armourModel = new WardenModel(armourRoot);
		Map<ModelPart, Float> pieces = WardenArmourModel.pieces(armourRoot);
		addLayer((RenderLayer) new LivingEntityEmissiveLayer<WardenRenderState, WardenModel>(parent,
				state -> ConstructSkins.stretched("warden_armour", armourRoot, WardenArmourModel.TEX_W, WardenArmourModel.TEX_H, ARMOUR_SCALE,
						((State) state).armour, ((State) state).corps),
				(state, age) -> 1f, armourModel, RenderTypes::entityTranslucentEmissive, false) {
			@Override
			public void submit(PoseStack pose, SubmitNodeCollector collector, int light, WardenRenderState state, float yRot, float xRot) {
				State st = (State) state;
				if (st.armour == null) return;
				WardenArmourModel.form(pieces, Math.min(1f, st.ageInTicks / FORM_TICKS) * FORM_TOP);
				super.submit(pose, collector, light, state, yRot, xRot);
			}
		});
	}

	@Override
	public Identifier getTextureLocation(State state) {
		if (state.armour != null) return VANILLA;
		return ConstructSkins.get("warden", model.root(), VANILLA, 4, state.corps);
	}

	@Override
	protected RenderType getRenderType(State state, boolean visible, boolean transparent, boolean glowing) {
		// R4b: the real warden, lit by the world, see-through only as it fades at the end of its life.
		if (state.armour != null) return RenderTypes.entityTranslucent(VANILLA);
		return RenderTypes.entityTranslucentEmissive(getTextureLocation(state));
	}

	@Override
	protected int getModelTint(State state) {
		return ConstructLook.tint(state.life, state.ageInTicks);
	}

	@Override
	protected int getBlockLightLevel(WardenConstruct entity, BlockPos pos) {
		return LabSettings.get().constructWarden.strip != null ? super.getBlockLightLevel(entity, pos) : 15;
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(WardenConstruct entity, State state, float partialTicks) {
		super.extractRenderState(entity, state, partialTicks);
		state.corps = entity.corps();
		state.armour = LabSettings.get().constructWarden.strip;
		state.attackAnimationState.copyFrom(entity.attackAnimationState);
		state.sonicBoomAnimationState.copyFrom(entity.sonicBoomAnimationState);
		state.life = entity.lifeFraction();
		// A steady heartbeat, quicker while it fights.
		float beat = state.ageInTicks * (entity.attackAnimationState.isStarted() ? 0.5f : 0.25f);
		state.heartAnimation = 0.4f + 0.6f * Math.max(0f, Mth.sin(beat));
		state.tendrilAnimation = 0.15f * Mth.sin(state.ageInTicks * 0.2f);
	}
}
