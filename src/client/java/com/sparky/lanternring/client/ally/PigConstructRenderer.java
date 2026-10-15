package com.sparky.lanternring.client.ally;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ally.PigConstruct;
import com.sparky.lanternring.client.LabSettings;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;

/**
 * The Pig construct (Blender pass 828): the vanilla pig's shape wearing only a construct texture, 88% opaque and
 * stretched over each face, with two glowing eyes. Which texture is the Ring Lab's "Construct pig" row: P2 H1 hex
 * (J's pick) or P3 W1 weave, in the summoning ring's corps colour.
 */
public class PigConstructRenderer extends MobRenderer<PigConstruct, PigConstructRenderer.State, PigConstructModel> {
	/** Pixels per texel of the made skin: one strip frame across a pig's body block keeps its full detail. */
	private static final int SCALE = 8;

	public static class State extends LivingEntityRenderState {
		float life;
		Corps corps = Corps.GREEN;
	}

	public PigConstructRenderer(EntityRendererProvider.Context context) {
		super(context, new PigConstructModel(PigConstructModel.create().bakeRoot()), 0.5f);
	}

	@Override
	public Identifier getTextureLocation(State state) {
		return ConstructSkins.stretched("pig", model.root(), PigConstructModel.TEX_W, PigConstructModel.TEX_H, SCALE,
				LabSettings.get().constructPig.strip, state.corps, PigConstructModel.EYES);
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
	protected int getBlockLightLevel(PigConstruct entity, BlockPos pos) {
		return 15;
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(PigConstruct entity, State state, float partialTicks) {
		super.extractRenderState(entity, state, partialTicks);
		state.corps = entity.corps();
		state.life = entity.lifeFraction();
	}
}
