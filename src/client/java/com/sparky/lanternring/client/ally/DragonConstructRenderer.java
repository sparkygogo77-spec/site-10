package com.sparky.lanternring.client.ally;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.ally.DragonConstruct;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.model.monster.dragon.EnderDragonModel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.EnderDragonRenderState;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;

/**
 * The Dragon construct: the ender dragon's model at DRAGON_SCALE, in hard light. It is drawn the
 * way EnderDragonRenderer draws the real one, from the recent heights and headings the entity
 * keeps (see DragonConstruct.flightHistory), so its neck and tail trail behind as it turns.
 */
public class DragonConstructRenderer extends EntityRenderer<DragonConstruct, DragonConstructRenderer.State> {
	/** About a third of the real dragon: some 5 blocks nose to tail. */
	public static final float DRAGON_SCALE = 0.32f;
	private static final Identifier VANILLA = Identifier.withDefaultNamespace("textures/entity/enderdragon/dragon.png");
	private final EnderDragonModel model;

	public static class State extends EnderDragonRenderState {
		float life;
	}

	public DragonConstructRenderer(EntityRendererProvider.Context context) {
		super(context);
		shadowRadius = 0.6f;
		model = new EnderDragonModel(context.bakeLayer(ModelLayers.ENDER_DRAGON));
	}

	@Override
	public void submit(State state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
		Identifier texture = ConstructSkins.get("dragon", model.root(), VANILLA, 2);
		poseStack.pushPose();
		poseStack.scale(DRAGON_SCALE, DRAGON_SCALE, DRAGON_SCALE);
		float yr = state.getHistoricalPos(7).yRot();
		float tilt = (float) (state.getHistoricalPos(5).y() - state.getHistoricalPos(10).y());
		poseStack.rotateDegrees(Axis.YP, -yr);
		// Heights are in blocks, so a small dragon tilts as much as a big one would for the same climb.
		poseStack.rotateDegrees(Axis.XP, tilt * 10f / DRAGON_SCALE * 0.4f);
		poseStack.translate(0f, 0f, 1f);
		poseStack.scale(-1f, -1f, 1f);
		poseStack.translate(0f, -1.501f, 0f);
		collector.submitModel(model, state, poseStack, RenderTypes.entityTranslucentEmissive(texture), ConstructLook.FULL_BRIGHT,
				OverlayTexture.NO_OVERLAY, ConstructLook.tint(state.life, state.ageInTicks), null, state.outlineColor);
		poseStack.popPose();
		super.submit(state, poseStack, collector, camera);
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(DragonConstruct entity, State state, float partialTicks) {
		super.extractRenderState(entity, state, partialTicks);
		state.flapTime = Mth.lerp(partialTicks, entity.oFlapTime, entity.flapTime);
		state.deathTime = 0f;
		state.hasRedOverlay = false;
		state.beamOffset = null;
		state.isLandingOrTakingOff = false;
		state.isSitting = false;
		state.distanceToEgg = 10000;
		state.partialTicks = partialTicks;
		state.flightHistory.copyFrom(entity.flightHistory);
		state.life = entity.lifeFraction();
	}
}
