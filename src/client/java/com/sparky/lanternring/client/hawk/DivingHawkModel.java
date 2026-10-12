package com.sparky.lanternring.client.hawk;

import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.util.Mth;
import java.util.function.Function;

/**
 * The diving hawk's bones (from assets/lanternring/bbmodel/diving_hawk.bbmodel, see BbRig) and how
 * they move. Four poses are blended by how much the hawk is doing each:
 * <ul>
 * <li><b>flap</b>: a heavy raptor's wingbeat, the arm leading and the forearm and hand following a
 * little later, so the wing whips; primaries spread on the downstroke, the body bobs against it;</li>
 * <li><b>glide</b>: wings out and slightly raised (a shallow V), tail fanned, a gentle sway;</li>
 * <li><b>stoop</b>: wings folded back into a teardrop, primaries and tail closed, head and lance
 * straight ahead, legs tucked;</li>
 * <li><b>perch</b>: wings folded along the back, tail down, legs standing, head looking about.</li>
 * </ul>
 * Rotations are in entity-model space (Blockbench's turned about Z): for the +X ("left") wing,
 * +zRot raises it and +yRot sweeps it back; the other wing mirrors both.
 */
public class DivingHawkModel extends EntityModel<DivingHawkRenderer.State> {
	private final Function<String, ModelPart> parts;
	private final ModelPart body, neck, head, tail;
	private final ModelPart[] arm = new ModelPart[2], mid = new ModelPart[2], tip = new ModelPart[2], leg = new ModelPart[2];
	private final ModelPart[][] primaries = new ModelPart[2][5];
	private final ModelPart[] tails = new ModelPart[5];

	public DivingHawkModel(ModelPart root) {
		super(root);
		parts = root.createPartLookup();
		body = part("body");
		neck = part("neck");
		head = part("head");
		tail = part("tail");
		String[] sides = {"left", "right"};
		for (int s = 0; s < 2; s++) {
			arm[s] = part("wing_" + sides[s]);
			mid[s] = part("wing_" + sides[s] + "_mid");
			tip[s] = part("wing_" + sides[s] + "_tip");
			leg[s] = part("leg_" + sides[s]);
			for (int i = 0; i < 5; i++) primaries[s][i] = part("primary_" + sides[s] + "_" + i);
		}
		for (int i = 0; i < 5; i++) tails[i] = part("tail_" + i);
	}

	/** A bone by name; a dummy if the model was edited and lost it, so the rest still animates. */
	private ModelPart part(String name) {
		ModelPart p = parts.apply(name);
		return p != null ? p : new ModelPart(java.util.List.of(), java.util.Map.of());
	}

	@Override
	public void setupAnim(DivingHawkRenderer.State s) {
		super.setupAnim(s);
		float perch = s.perch;
		float stoop = s.stoop * (1 - perch);
		float air = 1 - perch - stoop;
		float flap = s.flap * air;
		float glide = air - flap;
		float ph = s.flapPhase;
		float beat = Mth.sin(ph);
		float t = s.ageInTicks;

		// Wings. Flight poses move each segment; the stoop and perch fold the whole wing back along
		// the body, roll its feathers down against the flank and shorten it (the segments overlap
		// when folded), so the primaries cross over the tail.
		float armZ = glide * (0.14f + 0.04f * Mth.sin(t * 0.08f)) + flap * (0.12f + 0.85f * beat);
		float armY = glide * 0.05f + flap * 0.22f * Math.max(0, Mth.cos(ph)) + stoop * 1.35f + perch * 1.5f;
		float armX = flap * -0.12f * Mth.cos(ph) + stoop * -0.5f + perch * -1.2f;
		float fold = 1 - stoop * 0.2f - perch * 0.35f;
		float midZ = glide * 0.06f + flap * 0.45f * Mth.sin(ph - 0.7f);
		float midY = flap * -0.15f * Math.max(0, Mth.cos(ph - 0.7f)) + (stoop + perch) * 0.1f;
		float tipZ = glide * -0.05f + flap * 0.5f * Mth.sin(ph - 1.3f);
		float tipY = flap * 0.2f * Math.max(0, Mth.cos(ph - 1.3f)) + stoop * 0.2f + perch * 0.15f;
		float spread = glide + flap * (0.75f + 0.35f * Math.max(0, -Mth.cos(ph))) + stoop * 0.12f;
		for (int side = 0; side < 2; side++) {
			float m = side == 0 ? 1 : -1;
			arm[side].zRot += m * armZ;
			arm[side].yRot += m * armY;
			arm[side].xRot += armX;
			arm[side].xScale = fold;
			mid[side].zRot += m * midZ;
			mid[side].yRot += m * midY;
			tip[side].zRot += m * tipZ;
			tip[side].yRot += m * tipY;
			for (ModelPart p : primaries[side]) p.yRot = p.getInitialPose().yRot() * spread;
		}

		// Body bob against the wingbeat.
		body.y -= flap * 1.4f * beat;

		// Tail: fanned in a glide, closed in a stoop, lowered when perched, steering with the bank.
		float fan = glide + flap * 0.85f + stoop * 0.15f + perch * 0.3f;
		for (ModelPart p : tails) p.yRot = p.getInitialPose().yRot() * fan;
		tail.xRot += flap * 0.12f * Mth.sin(ph + 1f) + glide * 0.04f;
		tail.yRot += Mth.clamp(s.bank * 0.006f, -0.25f, 0.25f) * air;

		// Head: level while the body sits upright (the renderer tilts a perched hawk back
		// PERCH_PITCH degrees), looking about; stretched straight out in a stoop.
		head.yRot += perch * 0.6f * Mth.sin(t * 0.03f) * Mth.sin(t * 0.011f);
		head.xRot += perch * 0.15f * Mth.sin(t * 0.05f) - stoop * 0.1f;
		neck.xRot += perch * 0.55f + stoop * 0.15f;
		neck.z -= stoop * 1.2f;

		// Legs: straight down under the upright body when perched, tucked back in flight.
		for (ModelPart l : leg) l.xRot += (1 - perch) * 1.35f + perch * 0.52f;
	}
}
