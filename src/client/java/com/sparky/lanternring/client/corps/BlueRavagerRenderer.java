package com.sparky.lanternring.client.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.client.ally.ConstructSkins;
import com.sparky.lanternring.corps.BlueRavager;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.model.monster.ravager.RavagerModel;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.layers.LivingEntityEmissiveLayer;
import net.minecraft.client.renderer.entity.state.RavagerRenderState;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;

/**
 * The Blue Lantern squad's ravager, a placeholder look until its Blender skin is ready: the vanilla
 * ravager tinted blue with a faint layer of blue hard light over it (ConstructSkins.glow). Swap
 * {@link #getTextureLocation} (and drop the tint) for the finished skin.
 */
public class BlueRavagerRenderer extends MobRenderer<BlueRavager, RavagerRenderState, RavagerModel> {
	private static final Identifier VANILLA = Identifier.withDefaultNamespace("textures/entity/illager/ravager.png");
	private static final int TINT = 0xFF8FB4FF;

	public BlueRavagerRenderer(EntityRendererProvider.Context context) {
		super(context, new RavagerModel(context.bakeLayer(ModelLayers.RAVAGER)), 1.1f);
		addLayer(new LivingEntityEmissiveLayer<>(this, state -> ConstructSkins.glow("blue_ravager", VANILLA, Corps.BLUE),
				(state, age) -> 0.3f, new RavagerModel(context.bakeLayer(ModelLayers.RAVAGER)), RenderTypes::entityTranslucentEmissive, false));
	}

	@Override
	public Identifier getTextureLocation(RavagerRenderState state) {
		return VANILLA;
	}

	@Override
	protected int getModelTint(RavagerRenderState state) {
		return TINT;
	}

	@Override
	public RavagerRenderState createRenderState() {
		return new RavagerRenderState();
	}

	@Override
	public void extractRenderState(BlueRavager entity, RavagerRenderState state, float partialTick) {
		super.extractRenderState(entity, state, partialTick);
		state.stunnedTicksRemaining = 0;
		state.roarAnimation = 0;
		state.attackTicksRemaining = entity.attackTick() > 0 ? entity.attackTick() - partialTick : 0;
	}
}
