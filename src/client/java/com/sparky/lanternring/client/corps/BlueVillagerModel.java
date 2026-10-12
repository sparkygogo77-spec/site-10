package com.sparky.lanternring.client.corps;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.util.Mth;

/**
 * A Blue Lantern villager from J's reference sheet: the villager's tall head and nose on a suit
 * body with real arms and legs, so it can fly in the same poses as a ring-wearing player.
 * Texture: tools/blue_villager_skin.py (64x64 layout, painted at 4x).
 */
public class BlueVillagerModel extends HumanoidModel<BlueVillagerRenderer.State> {
	private static final float HALF_PI = Mth.PI / 2;

	public BlueVillagerModel(ModelPart root) {
		super(root);
	}

	public static LayerDefinition create(boolean baby) {
		MeshDefinition mesh = new MeshDefinition();
		PartDefinition root = mesh.getRoot();
		PartDefinition head = root.addOrReplaceChild("head", CubeListBuilder.create().texOffs(0, 0).addBox(-4, -10, -4, 8, 10, 8), PartPose.ZERO);
		head.addOrReplaceChild("nose", CubeListBuilder.create().texOffs(24, 0).addBox(-1, -1, -6, 2, 4, 2), PartPose.offset(0, -2, 0));
		head.addOrReplaceChild("hat", CubeListBuilder.create(), PartPose.ZERO);
		root.addOrReplaceChild("body", CubeListBuilder.create().texOffs(0, 20).addBox(-4, 0, -2, 8, 12, 4), PartPose.ZERO);
		root.addOrReplaceChild("right_arm", CubeListBuilder.create().texOffs(24, 20).addBox(-3, -2, -2, 4, 12, 4), PartPose.offset(-5, 2, 0));
		root.addOrReplaceChild("left_arm", CubeListBuilder.create().texOffs(40, 20).addBox(-1, -2, -2, 4, 12, 4), PartPose.offset(5, 2, 0));
		root.addOrReplaceChild("right_leg", CubeListBuilder.create().texOffs(0, 36).addBox(-2, 0, -2, 4, 12, 4), PartPose.offset(-1.9f, 12, 0));
		root.addOrReplaceChild("left_leg", CubeListBuilder.create().texOffs(16, 36).addBox(-2, 0, -2, 4, 12, 4), PartPose.offset(1.9f, 12, 0));
		LayerDefinition layer = LayerDefinition.create(mesh, 64, 64);
		return baby ? layer.apply(HumanoidModel.BABY_TRANSFORMER) : layer;
	}

	@Override
	public void setupAnim(BlueVillagerRenderer.State state) {
		super.setupAnim(state);
		float f = state.flying;
		if (f > 0) fly(state, f);
		if (state.building > 0) channel(state, state.building);
		if (state.aim > 0) point(state, state.aim);
	}

	/** Fighting: the ring arm points straight at what it's firing at (or the bubble it swings). */
	private void point(BlueVillagerRenderer.State state, float a) {
		set(rightArm, a, -HALF_PI + state.aimPitch, 0f);
		rightArm.yRot = Mth.lerp(a, rightArm.yRot, state.aimYaw);
	}

	/**
	 * Ring flight, as {@code FlightPoses} poses a flying player: legs trailing the way it came, one
	 * knee further back, arms relaxed a little forward, a slow sway; the body lean is in the renderer.
	 */
	private void fly(BlueVillagerRenderer.State state, float f) {
		float sway = Mth.sin(state.ageInTicks * 0.09f) * 0.06f;
		float trail = 0.2f + 0.55f * state.forward;
		float spread = -0.35f * state.side;
		set(rightLeg, f, trail + 0.18f + sway, 0.06f + spread);
		set(leftLeg, f, trail - 0.04f - sway, -0.06f + spread);
		rightLeg.yRot = Mth.lerp(f, rightLeg.yRot, 0);
		leftLeg.yRot = Mth.lerp(f, leftLeg.yRot, 0);
		// The head keeps looking where it looks: undo the lean.
		head.xRot += f * BlueVillagerRenderer.leanPitch(state.forward) * Mth.DEG_TO_RAD;
		set(rightArm, f, -0.25f + sway, 0.12f);
		set(leftArm, f, -0.25f - sway, -0.12f);
		rightArm.yRot = Mth.lerp(f, rightArm.yRot, 0);
		leftArm.yRot = Mth.lerp(f, leftArm.yRot, 0);
	}

	/** Building: both arms reach out at the construct, ring hand a little higher, pouring light into it. */
	private void channel(BlueVillagerRenderer.State state, float b) {
		float pulse = Mth.sin(state.ageInTicks * 0.25f) * 0.04f;
		float look = head.xRot;
		set(rightArm, b, look - HALF_PI - 0.12f + pulse, 0.0f);
		set(leftArm, b, look - HALF_PI + 0.1f - pulse, 0.0f);
		rightArm.yRot = Mth.lerp(b, rightArm.yRot, head.yRot - 0.22f);
		leftArm.yRot = Mth.lerp(b, leftArm.yRot, head.yRot + 0.22f);
	}

	private static void set(ModelPart part, float f, float xRot, float zRot) {
		part.xRot = Mth.lerp(f, part.xRot, xRot);
		part.zRot = Mth.lerp(f, part.zRot, zRot);
	}
}
