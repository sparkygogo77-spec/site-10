package com.sparky.lanternring.client.ally;

import com.mojang.blaze3d.vertex.PoseStack;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ally.BroodSpider;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.model.monster.spider.SpiderModel;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.LivingEntityEmissiveLayer;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;

/**
 * The Yellow Lantern's Brood: the spider's own model and walk in golden hard light, scaled up to
 * the giant or down to a spiderling, with burning eyes. They fade in out of the dark as they come.
 */
public class BroodSpiderRenderer extends MobRenderer<BroodSpider, BroodSpiderRenderer.State, SpiderModel> {
	private static final Identifier VANILLA = Identifier.withDefaultNamespace("textures/entity/spider/spider.png");
	private static final Identifier EYES = Identifier.withDefaultNamespace("textures/entity/spider/spider_eyes.png");
	/** Ticks it takes to come all the way out of the dark. */
	private static final float FADE_IN = 16f;

	public static class State extends LivingEntityRenderState {
		float life;
		float fadeIn;
	}

	private final float size;

	@SuppressWarnings({"unchecked", "rawtypes"})
	public BroodSpiderRenderer(EntityRendererProvider.Context context, float size) {
		super(context, new SpiderModel(context.bakeLayer(ModelLayers.SPIDER)), 0.8f * size);
		this.size = size;
		SpiderModel eyesModel = new SpiderModel(context.bakeLayer(ModelLayers.SPIDER));
		addLayer((RenderLayer) new LivingEntityEmissiveLayer<LivingEntityRenderState, SpiderModel>((RenderLayerParent) this,
				state -> ConstructSkins.glow("spider_eyes", EYES, Corps.YELLOW),
				(state, age) -> 0.75f + 0.25f * Mth.sin(age * 0.3f), eyesModel, RenderTypes::entityTranslucentEmissive, false));
	}

	@Override
	public Identifier getTextureLocation(State state) {
		return ConstructSkins.get("spider", model.root(), VANILLA, 4, Corps.YELLOW);
	}

	@Override
	protected RenderType getRenderType(State state, boolean visible, boolean transparent, boolean glowing) {
		return RenderTypes.entityTranslucentEmissive(getTextureLocation(state));
	}

	@Override
	protected int getModelTint(State state) {
		int tint = ConstructLook.tint(state.life, state.ageInTicks);
		int alpha = Math.round((tint >>> 24) * state.fadeIn);
		return alpha << 24 | (tint & 0xFFFFFF);
	}

	@Override
	protected float getFlipDegrees() {
		return 180f;
	}

	@Override
	protected void scale(State state, PoseStack poseStack) {
		poseStack.scale(size, size, size);
	}

	@Override
	protected int getBlockLightLevel(BroodSpider entity, BlockPos pos) {
		return 15;
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(BroodSpider entity, State state, float partialTicks) {
		super.extractRenderState(entity, state, partialTicks);
		state.life = entity.lifeFraction();
		state.fadeIn = Mth.clamp((entity.tickCount + partialTicks) / FADE_IN, 0.05f, 1f);
	}
}
