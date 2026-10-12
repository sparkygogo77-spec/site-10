package com.sparky.lanternring.client.ally;

import com.sparky.lanternring.ally.SentryConstruct;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.model.monster.guardian.GuardianModel;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.state.GuardianRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;

/**
 * The Sentry construct: a guardian's spiked eye in hard light. Its spikes stand out while it has a
 * target and its eye follows what it shoots (the beam itself is a ring effect, see LabFx).
 */
public class SentryConstructRenderer extends MobRenderer<SentryConstruct, SentryConstructRenderer.State, GuardianModel> {
	private static final Identifier VANILLA = Identifier.withDefaultNamespace("textures/entity/guardian/guardian.png");

	public static class State extends GuardianRenderState {
		float life;
	}

	public SentryConstructRenderer(EntityRendererProvider.Context context) {
		super(context, new GuardianModel(context.bakeLayer(ModelLayers.GUARDIAN)), 0.4f);
	}

	@Override
	public Identifier getTextureLocation(State state) {
		return ConstructSkins.get("sentry", model.root(), VANILLA, 4);
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
	protected int getBlockLightLevel(SentryConstruct entity, BlockPos pos) {
		return 15;
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(SentryConstruct entity, State state, float partialTicks) {
		super.extractRenderState(entity, state, partialTicks);
		state.spikesAnimation = Mth.lerp(partialTicks, entity.oSpikes, entity.spikes);
		state.tailAnimation = Mth.lerp(partialTicks, entity.oTail, entity.tail);
		state.eyePosition = entity.getEyePosition(partialTicks);
		Entity look = entity.aimed();
		if (look == null) look = Minecraft.getInstance().getCameraEntity();
		if (look != null) {
			state.lookDirection = entity.getViewVector(partialTicks);
			state.lookAtPosition = look.getEyePosition(partialTicks);
		} else {
			state.lookDirection = null;
			state.lookAtPosition = null;
		}
		state.attackTargetPosition = null;
		state.life = entity.lifeFraction();
	}
}
