package com.sparky.lanternring.client.ally;

import java.util.function.Function;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;

/**
 * The Rage Bull's bones (from assets/lanternring/bbmodel/rage_bull.bbmodel, see BbRig) and its
 * heavy trot: the legs swing in diagonal pairs, the body rocks and dips with each stride, the low
 * head tosses its horns and the tail swings. Standing still once its run is over.
 */
public class RageBullModel extends EntityModel<RageBullRenderer.State> {
	private final Function<String, ModelPart> parts;
	private final ModelPart body, head, tail, frontLeft, frontRight, backLeft, backRight;

	public RageBullModel(ModelPart root) {
		super(root);
		parts = root.createPartLookup();
		body = part("body");
		head = part("head");
		tail = part("tail");
		frontLeft = part("leg_front_left");
		frontRight = part("leg_front_right");
		backLeft = part("leg_back_left");
		backRight = part("leg_back_right");
	}

	/** A bone by name; a dummy if the model was edited and lost it, so the rest still animates. */
	private ModelPart part(String name) {
		ModelPart p = parts.apply(name);
		return p != null ? p : new ModelPart(java.util.List.of(), java.util.Map.of());
	}

	@Override
	public void setupAnim(RageBullRenderer.State s) {
		super.setupAnim(s);
		float ph = s.walkAnimationPos * 0.6662f;
		float amp = s.walkAnimationSpeed;
		float swing = Mth.cos(ph) * 1.1f * amp;
		// A trot: each front leg moves with the opposite back leg.
		frontLeft.xRot += swing;
		backRight.xRot += swing;
		frontRight.xRot -= swing;
		backLeft.xRot -= swing;
		// The body dips at each footfall (twice a stride) and rolls a little from side to side.
		float bob = Math.abs(Mth.sin(ph)) * amp;
		body.y += bob * 0.9f;
		body.zRot += Mth.sin(ph) * 0.03f * amp;
		// Head low and tossing the horns; the tail swings against the stride.
		head.xRot += 0.08f * amp + Mth.sin(ph * 2f + 0.6f) * 0.07f * amp + Mth.sin(s.ageInTicks * 0.05f) * 0.03f;
		head.yRot += Mth.sin(ph) * 0.05f * amp;
		tail.zRot += Mth.sin(ph + 1.2f) * 0.15f * amp + Mth.sin(s.ageInTicks * 0.09f) * 0.08f;
		tail.xRot += 0.2f * amp;
	}
}
