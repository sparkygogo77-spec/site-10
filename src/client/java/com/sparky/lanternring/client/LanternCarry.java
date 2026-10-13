package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternCharge;
import com.sparky.lanternring.ModRegistry;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Avatar;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import org.joml.Quaternionf;

/**
 * Third person: the Power Battery isn't held at your side like an item. The off arm carries it out
 * in front of you, the lantern hanging upright from the fist by its handle and swinging as you
 * walk; with a floating charge style it floats in front of your chest instead, no hand needed.
 * Either way it swings back on its handle when the ring hits the port (see {@link ChargeMotion#swing}).
 */
public class LanternCarry extends RenderLayer<AvatarRenderState, PlayerModel> {
	/** The carrying arm: pitch (negative raises it forward) and inward turn, in radians for the right arm. */
	public static float carryX = -1.2f, carryY = 0.3f;
	/** Floating: where the lantern's handle top hovers, in model pixels (x toward the off hand, y down, -z ahead). */
	public static float floatX = 2f, floatY = -1f, floatZ = -10f;

	public LanternCarry(RenderLayerParent<AvatarRenderState, PlayerModel> renderer) {
		super(renderer);
	}

	/** The arm holding the lantern, or null when no lantern is carried this way. */
	private static HumanoidArm lanternArm(AvatarRenderState state) {
		HumanoidArm off = state.mainArm.getOpposite();
		ItemStack stack = off == HumanoidArm.RIGHT ? state.rightHandItemStack : state.leftHandItemStack;
		return stack != null && stack.is(ModRegistry.POWER_BATTERY_ITEM) ? off : null;
	}

	/** True when the lantern floats instead of being held (the floating charge styles, on your own player). */
	private static boolean floating(AvatarRenderState state) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.player == null || state.id != mc.player.getId()) return false;
		LabSettings.ChargeStyle style = LabSettings.get().chargeStyle;
		return style == LabSettings.ChargeStyle.FLOAT || style == LabSettings.ChargeStyle.SUMMON;
	}

	/** Called after the render state is filled: the item isn't drawn in the hand, this layer draws it. */
	public static void extract(Avatar avatar, AvatarRenderState state) {
		HumanoidArm arm = lanternArm(state);
		if (arm == null) return;
		(arm == HumanoidArm.RIGHT ? state.rightHandItemState : state.leftHandItemState).clear();
	}

	/** Raises the carrying arm out in front (before the charge pose, which takes it from here). */
	public static void pose(PlayerModel model, AvatarRenderState state) {
		HumanoidArm arm = lanternArm(state);
		if (arm == null || floating(state)) return;
		ModelPart part = arm == HumanoidArm.RIGHT ? model.rightArm : model.leftArm;
		float f = arm == HumanoidArm.RIGHT ? 1f : -1f;
		// A little bob with each step, so it isn't held rigid.
		float step = Mth.cos(state.walkAnimationPos * 0.6662f) * state.walkAnimationSpeed;
		part.xRot = carryX + 0.08f * step;
		part.yRot = -f * carryY;
		part.zRot = 0f;
	}

	@Override
	public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, AvatarRenderState state, float yRot, float xRot) {
		HumanoidArm arm = lanternArm(state);
		if (arm == null) return;
		Minecraft mc = Minecraft.getInstance();
		ItemStack stack = arm == HumanoidArm.RIGHT ? state.rightHandItemStack : state.leftHandItemStack;
		Corps corps = Corps.ofLantern(stack);
		boolean self = mc.player != null && state.id == mc.player.getId();
		// Set down as a shrine, it's drawn in the world instead.
		if (self && LabSettings.get().chargeStyle.grounded() && LanternShrine.active()) return;
		float partial = mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
		float t = -1f;
		if (mc.level != null && mc.level.getEntity(state.id) instanceof Player player && LanternCharge.isCharging(player)) {
			t = player.getTicksUsingItem() + partial;
		}
		float raise = self ? ChargeMotion.local(partial).raise() : ChargeMotion.at(t).raise();
		float f = arm == HumanoidArm.RIGHT ? 1f : -1f;

		poseStack.pushPose();
		if (floating(state)) {
			// Floating in front of the chest, bobbing gently.
			poseStack.translate(-f * floatX / 16f, (floatY + 0.6f * Mth.sin(state.ageInTicks * 0.08f)) / 16f, floatZ / 16f);
		} else {
			// From the fist, then undo the arm's turn so the lantern hangs straight down.
			ModelPart part = arm == HumanoidArm.RIGHT ? getParentModel().rightArm : getParentModel().leftArm;
			part.translateAndRotate(poseStack);
			poseStack.translate(f / 16f, 10.5f / 16f, 0f);
			poseStack.rotate(new Quaternionf().rotationZYX(part.zRot, part.yRot, part.xRot).conjugate());
		}
		// Model space is upside down: turn it so the lantern stands up.
		poseStack.rotateDegrees(Axis.ZP, 180f);
		// Swaying with each step, and swinging back on its handle when the ring hits the port.
		float step = Mth.sin(state.walkAnimationPos * 0.6662f) * state.walkAnimationSpeed;
		poseStack.rotateDegrees(Axis.ZP, 12f * step * (1f - raise));
		poseStack.rotateDegrees(Axis.XP, 6f * Mth.cos(state.walkAnimationPos * 0.6662f) * state.walkAnimationSpeed * (1f - raise) + ChargeMotion.swing(t));
		// Its port looks ahead while carried, and the wrist turns it back toward the ring to charge.
		poseStack.rotateDegrees(Axis.YP, 180f * raise);
		LanternFirstPerson.Look look = LanternFirstPerson.look(corps);
		float s = LanternFirstPerson.scale * look.size();
		poseStack.scale(s, s, s);
		poseStack.translate(0f, -look.handleTop() / 16f, 0f);
		float glow = self ? LanternFirstPerson.glow(partial) : LanternGlare.IDLE;
		Corps before = CorpsTint.enter(corps);
		try {
			LanternFirstPerson.othersLantern = !self;
			LanternFirstPerson.drawLantern(poseStack, collector, light, look, corps, glow);
		} finally {
			LanternFirstPerson.othersLantern = false;
			CorpsTint.restore(before);
		}
		poseStack.popPose();
	}
}
