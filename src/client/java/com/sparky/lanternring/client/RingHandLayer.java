package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.mojang.blaze3d.vertex.PoseStack;
import com.sparky.lanternring.item.PowerRingItem;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.player.PlayerModelType;
import net.minecraft.world.item.ItemStack;

/** Third person: draws the ring on whichever hand holds it, and the ring Shield on its arm. */
public class RingHandLayer extends RenderLayer<AvatarRenderState, PlayerModel> {
	public RingHandLayer(RenderLayerParent<AvatarRenderState, PlayerModel> renderer) {
		super(renderer);
	}

	@Override
	public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, AvatarRenderState state, float yRot, float xRot) {
		boolean slim = state.skin != null && state.skin.model() == PlayerModelType.SLIM;
		LabSettings.RingModel model = LabSettings.get().ringModel;
		// Charging the Beam: the glow goes on the hand doing it.
		Minecraft mc = Minecraft.getInstance();
		Player charging = mc.level != null && mc.level.getEntity(state.id) instanceof Player p ? p : null;
		HumanoidArm glowArm = charging == null ? null : BeamChargeGlow.chargingArm(charging);
		float partial = mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
		if (charging != null) {
			RiotShields.submitOnArm(poseStack, collector, getParentModel().rightArm, true, charging, partial);
			RiotShields.submitOnArm(poseStack, collector, getParentModel().leftArm, false, charging, partial);
		}
		if (isRing(state.rightHandItemStack)) {
			Corps before = CorpsTint.enter(Corps.of(state.rightHandItemStack));
			poseStack.pushPose();
			getParentModel().rightArm.translateAndRotate(poseStack);
			RingModels.glintBoost = charging != null && RingEmit.ringArm(charging) == HumanoidArm.RIGHT ? LanternFlash.sun(charging, partial) : 0f;
			RingModels.render(poseStack, collector, light, model, false, slim);
			RingModels.glintBoost = 0f;
			if (glowArm == HumanoidArm.RIGHT) glow(poseStack, collector, charging, partial, model, false, slim);
			flare(poseStack, collector, charging, HumanoidArm.RIGHT, partial, model, false, slim);
			poseStack.popPose();
			CorpsTint.restore(before);
		}
		if (isRing(state.leftHandItemStack)) {
			Corps before = CorpsTint.enter(Corps.of(state.leftHandItemStack));
			poseStack.pushPose();
			getParentModel().leftArm.translateAndRotate(poseStack);
			RingModels.glintBoost = charging != null && RingEmit.ringArm(charging) == HumanoidArm.LEFT ? LanternFlash.sun(charging, partial) : 0f;
			RingModels.render(poseStack, collector, light, model, true, slim);
			RingModels.glintBoost = 0f;
			if (glowArm == HumanoidArm.LEFT) glow(poseStack, collector, charging, partial, model, true, slim);
			flare(poseStack, collector, charging, HumanoidArm.LEFT, partial, model, true, slim);
			poseStack.popPose();
			CorpsTint.restore(before);
		}
	}

	private static void glow(PoseStack poseStack, SubmitNodeCollector collector, Player player, float partial,
			LabSettings.RingModel model, boolean leftArm, boolean slim) {
		BeamChargeGlow.render(poseStack, collector, BeamChargeGlow.progress(player, partial), player.tickCount + partial, model, leftArm, slim);
	}

	/** The flare on the ring face as a power leaves it. */
	private static void flare(PoseStack poseStack, SubmitNodeCollector collector, Player player, HumanoidArm arm, float partial,
			LabSettings.RingModel model, boolean leftArm, boolean slim) {
		if (player == null || RingEmit.ringArm(player) != arm) return;
		BeamChargeGlow.renderFlash(poseStack, collector, RingEmit.flare(player, partial), player.tickCount + partial, model, leftArm, slim, false);
		BeamChargeGlow.renderHold(poseStack, collector, RingEmit.held(player, partial), player.tickCount + partial, model, leftArm, slim, false);
		BeamChargeGlow.renderSun(poseStack, collector, LanternFlash.sun(player, partial), player.tickCount + partial, model, leftArm, slim, false);
	}

	private static boolean isRing(ItemStack stack) {
		return stack != null && stack.getItem() instanceof PowerRingItem;
	}
}
