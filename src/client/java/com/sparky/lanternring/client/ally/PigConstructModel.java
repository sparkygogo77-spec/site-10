package com.sparky.lanternring.client.ally;

import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.util.Mth;

/**
 * The Pig construct's bones: the vanilla pig's boxes and texture layout (body 10x16x8, head 8x8x8 with a
 * 4x3x1 snout, legs 4x6x4 on a 64x64 sheet), so it keeps the pig's proportions as Blender pass 828 asks,
 * with the quadruped walk and the head following where it looks.
 */
public class PigConstructModel extends EntityModel<PigConstructRenderer.State> {
	static final int TEX_W = 64, TEX_H = 64;
	/** The eyes on the head's front face, as texels (x, y pairs): one glowing pixel each, as the Blender pigs have. */
	static final int[] EYES = {9, 10, 14, 10};

	private final ModelPart head, rightHindLeg, leftHindLeg, rightFrontLeg, leftFrontLeg;

	public PigConstructModel(ModelPart root) {
		super(root);
		head = root.getChild("head");
		rightHindLeg = root.getChild("right_hind_leg");
		leftHindLeg = root.getChild("left_hind_leg");
		rightFrontLeg = root.getChild("right_front_leg");
		leftFrontLeg = root.getChild("left_front_leg");
	}

	public static LayerDefinition create() {
		MeshDefinition mesh = new MeshDefinition();
		PartDefinition root = mesh.getRoot();
		PartDefinition head = root.addOrReplaceChild("head", CubeListBuilder.create().texOffs(0, 0).addBox(-4, -4, -8, 8, 8, 8), PartPose.offset(0, 12, -6));
		head.addOrReplaceChild("snout", CubeListBuilder.create().texOffs(16, 16).addBox(-2, 0, -9, 4, 3, 1), PartPose.ZERO);
		root.addOrReplaceChild("body", CubeListBuilder.create().texOffs(28, 8).addBox(-5, -10, -7, 10, 16, 8),
				PartPose.offsetAndRotation(0, 11, 2, Mth.PI / 2, 0, 0));
		CubeListBuilder leg = CubeListBuilder.create().texOffs(0, 16).addBox(-2, 0, -2, 4, 6, 4);
		root.addOrReplaceChild("right_hind_leg", leg, PartPose.offset(-3, 18, 7));
		root.addOrReplaceChild("left_hind_leg", leg, PartPose.offset(3, 18, 7));
		root.addOrReplaceChild("right_front_leg", leg, PartPose.offset(-3, 18, -5));
		root.addOrReplaceChild("left_front_leg", leg, PartPose.offset(3, 18, -5));
		return LayerDefinition.create(mesh, TEX_W, TEX_H);
	}

	@Override
	public void setupAnim(PigConstructRenderer.State s) {
		super.setupAnim(s);
		head.xRot += s.xRot * Mth.DEG_TO_RAD;
		head.yRot += s.yRot * Mth.DEG_TO_RAD;
		float swing = Mth.cos(s.walkAnimationPos * 0.6662f) * 1.4f * s.walkAnimationSpeed;
		rightHindLeg.xRot += swing;
		leftHindLeg.xRot -= swing;
		rightFrontLeg.xRot -= swing;
		leftFrontLeg.xRot += swing;
	}
}
