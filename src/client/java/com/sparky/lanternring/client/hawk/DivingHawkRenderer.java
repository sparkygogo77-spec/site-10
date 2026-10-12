package com.sparky.lanternring.client.hawk;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.client.BbRig;
import com.sparky.lanternring.corps.DivingHawk;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.LivingEntityEmissiveLayer;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;

/**
 * The armored diving hawk: the rigged Blockbench model (BbRig) posed by DivingHawkModel, pitched
 * nose-down along its flight path and banked into turns, with its armour trim, lance tip and helm
 * emblem drawn again full-bright on top so they glow Blue Lantern blue in the dark.
 */
public class DivingHawkRenderer extends MobRenderer<DivingHawk, DivingHawkRenderer.State, DivingHawkModel> {
	private static final Identifier TEXTURE = LanternRing.id("textures/entity/bb/diving_hawk.png");
	private static BbRig.Layers layers;

	public static class State extends LivingEntityRenderState {
		public float flapPhase, flap, stoop, perch, pitch, bank;
	}

	private static BbRig.Layers layers() {
		if (layers == null) layers = BbRig.load("diving_hawk");
		return layers;
	}

	public DivingHawkRenderer(EntityRendererProvider.Context context) {
		super(context, new DivingHawkModel(layers().solid().bakeRoot()), 0.7f);
		DivingHawkModel glow = new DivingHawkModel(layers().glow().bakeRoot());
		addLayer(new LivingEntityEmissiveLayer<>((RenderLayerParent<State, DivingHawkModel>) this, state -> TEXTURE,
				(state, age) -> 1f, glow, RenderTypes::eyes, false));
	}

	@Override
	public Identifier getTextureLocation(State state) {
		return TEXTURE;
	}

	@Override
	protected void setupRotations(State state, PoseStack poseStack, float bodyRot, float scale) {
		super.setupRotations(state, poseStack, bodyRot, scale);
		// Pitch and bank about the middle of the body, not the feet.
		poseStack.translate(0f, 1f, 0f);
		poseStack.rotateDegrees(Axis.XP, -state.pitch);
		poseStack.rotateDegrees(Axis.ZP, -state.bank);
		poseStack.translate(0f, -1f, 0f);
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(DivingHawk hawk, State state, float partialTicks) {
		super.extractRenderState(hawk, state, partialTicks);
		state.flapPhase = Mth.lerp(partialTicks, hawk.oFlapPhase, hawk.flapPhase);
		state.flap = Mth.lerp(partialTicks, hawk.oFlap, hawk.flap);
		state.stoop = Mth.lerp(partialTicks, hawk.oStoop, hawk.stoop);
		state.perch = Mth.lerp(partialTicks, hawk.oPerch, hawk.perch);
		state.pitch = Mth.lerp(partialTicks, hawk.oPitch, hawk.pitch);
		state.bank = Mth.lerp(partialTicks, hawk.oBank, hawk.bank);
	}
}
