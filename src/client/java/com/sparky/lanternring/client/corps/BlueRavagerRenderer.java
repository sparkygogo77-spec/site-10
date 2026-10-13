package com.sparky.lanternring.client.corps;

import com.mojang.blaze3d.vertex.PoseStack;
import com.sparky.lanternring.client.RiggedBb;
import com.sparky.lanternring.corps.BlueRavager;
import net.minecraft.client.model.geom.ModelLayers;
import net.minecraft.client.model.monster.ravager.RavagerModel;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import java.util.List;
import org.jspecify.annotations.Nullable;
import net.minecraft.client.renderer.entity.state.RavagerRenderState;
import net.minecraft.resources.Identifier;

/**
 * The Blue Lantern squad's ravager: the vanilla ravager tinted blue, inside J's R2 hard-light shell
 * from the lead Blender chat (bbmodel/blue_ravager_r2), whose plates move with its head, jaw and
 * legs (RiggedBb).
 */
public class BlueRavagerRenderer extends MobRenderer<BlueRavager, RavagerRenderState, RavagerModel> {
	private static final Identifier VANILLA = Identifier.withDefaultNamespace("textures/entity/illager/ravager.png");
	private static final int TINT = 0xFF8FB4FF;

	public BlueRavagerRenderer(EntityRendererProvider.Context context) {
		super(context, new RavagerModel(context.bakeLayer(ModelLayers.RAVAGER)), 1.1f);
		addLayer(new Shell(this));
	}

	private static class Shell extends RenderLayer<RavagerRenderState, RavagerModel> {
		private static final List<String> PARTS = List.of("body", "neck", "neck/head", "neck/head/mouth",
				"right_hind_leg", "left_hind_leg", "right_front_leg", "left_front_leg");
		private @Nullable RiggedBb rig;

		Shell(RenderLayerParent<RavagerRenderState, RavagerModel> parent) {
			super(parent);
		}

		@Override
		public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, RavagerRenderState state, float yRot, float xRot) {
			if (state.isInvisible) return;
			RavagerModel model = getParentModel();
			if (rig == null) rig = RiggedBb.load("blue_ravager_r2", model.root(), PARTS, null);
			rig.render(poseStack, collector, model.root(), light, -1);
		}
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
