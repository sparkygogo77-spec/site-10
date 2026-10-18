package com.sparky.lanternring.client.ally;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;

/**
 * Blender pass 838 R4b (J's KEEP, 2026-10-15): construct plate armour over the real warden. The plates stand 1.5 px off
 * the skin and protrude: a cuirass with a keel and chest ridges, gorget, fauld, a helm with brow and crest, guards on both
 * faces of each tendril, pauldrons with lips, bracers, gauntlets, greaves with knee cops.
 * <p>
 * The model has the vanilla warden's bones (same names, pivots and parents), so {@code new WardenModel(root)} animates it
 * exactly with the warden; each armour piece is a child of its bone named {@code armour_<n>}, and {@link #FORM_HEIGHT}
 * gives the height (pixels above the ground at rest) of its lowest edge, so the armour can form feet first.
 * The numbers are docs/blender/blender_updates/838_warden_armour.update.py's, moved from Blender's rig (Z up, front -Y)
 * into model space (Y down, front -Z) bone by bone.
 */
public final class WardenArmourModel {
	public static final int TEX_W = 256, TEX_H = 256;
	/** Gap off the skin and plate thickness (px). */
	private static final float G = 1.5f, T = 1f;
	/** The lowest edge of each armour piece, by its path from the root ("bone/body/armour_body_0"): see the class note. */
	public static final java.util.Map<String, Float> FORM_HEIGHT = new java.util.HashMap<>();

	private WardenArmourModel() {
	}

	/** A shelf packer for box-UV footprints, so no two pieces share texels. */
	private static final class Packer {
		int x, y, row;

		int[] place(float dx, float dy, float dz) {
			int w = (int) Math.ceil(2 * (dx + dz)) + 1, h = (int) Math.ceil(dz + dy) + 1;
			if (x + w > TEX_W) {
				x = 0;
				y += row;
				row = 0;
			}
			int[] at = {x, y};
			x += w;
			row = Math.max(row, h);
			if (y + h > TEX_H) throw new IllegalStateException("warden armour texture too small");
			return at;
		}
	}

	/**
	 * One bone of the rig: Blender boxes (px, in the Blender bone's frame) go in as model cubes. {@code yoff} is the model
	 * Y of Blender's z = 0, {@code zoff} the model Z of Blender's y = 0, {@code ground} the bone pivot's height at rest.
	 */
	private static final class Bone {
		final PartDefinition part;
		final float yoff, zoff, ground;
		final String name, path;
		final Packer packer;
		final List<float[]> boxes = new ArrayList<>();

		Bone(PartDefinition part, String path, String name, float yoff, float zoff, float ground, Packer packer) {
			this.part = part;
			this.path = path;
			this.name = name;
			this.yoff = yoff;
			this.zoff = zoff;
			this.ground = ground;
			this.packer = packer;
		}

		/** A plate box between Blender corners a and b (any order). */
		Bone pb(float ax, float ay, float az, float bx, float by, float bz) {
			boxes.add(new float[] {Math.min(ax, bx), Math.min(ay, by), Math.min(az, bz), Math.max(ax, bx), Math.max(ay, by), Math.max(az, bz)});
			return this;
		}

		/** 838's slabs(): four side plates gap off an inner box, the front and back spanning the full width; top and bottom caps. */
		Bone slabs(float ax, float ay, float az, float bx, float by, float bz, float gap, float t, boolean top, boolean bottom) {
			float xo0 = ax - gap - t, xo1 = bx + gap + t, yi0 = ay - gap, yi1 = by + gap;
			pb(xo0, yi0 - t, az, xo1, yi0, bz);
			pb(xo0, yi1, az, xo1, yi1 + t, bz);
			pb(xo0, yi0, az, ax - gap, yi1, bz);
			pb(bx + gap, yi0, az, xo1, yi1, bz);
			if (top) pb(xo0, yi0 - t, bz + gap, xo1, yi1 + t, bz + gap + t);
			if (bottom) pb(xo0, yi0 - t, az - gap - t, xo1, yi1 + t, az - gap);
			return this;
		}

		/** Each box becomes its own child part, so it can form on its own. */
		void build() {
			for (int i = 0; i < boxes.size(); i++) {
				float[] b = boxes.get(i);
				float x0 = b[0], x1 = b[3], y0 = yoff - b[5], y1 = yoff - b[2], z0 = b[1] + zoff, z1 = b[4] + zoff;
				int[] uv = packer.place(x1 - x0, y1 - y0, z1 - z0);
				String n = "armour_" + name + "_" + i;
				part.addOrReplaceChild(n, CubeListBuilder.create().texOffs(uv[0], uv[1]).addBox(x0, y0, z0, x1 - x0, y1 - y0, z1 - z0),
						PartPose.ZERO);
				FORM_HEIGHT.put(path + "/" + n, ground - y1);
			}
		}
	}

	public static LayerDefinition create() {
		MeshDefinition mesh = new MeshDefinition();
		PartDefinition root = mesh.getRoot();
		// The vanilla warden's bones (WardenModel.createBodyLayer), without its cubes.
		PartDefinition bone = root.addOrReplaceChild("bone", CubeListBuilder.create(), PartPose.offset(0, 24, 0));
		PartDefinition body = bone.addOrReplaceChild("body", CubeListBuilder.create(), PartPose.offset(0, -21, 0));
		body.addOrReplaceChild("right_ribcage", CubeListBuilder.create(), PartPose.offset(-7, -2, -4));
		body.addOrReplaceChild("left_ribcage", CubeListBuilder.create(), PartPose.offset(7, -2, -4));
		PartDefinition head = body.addOrReplaceChild("head", CubeListBuilder.create(), PartPose.offset(0, -13, 0));
		PartDefinition rt = head.addOrReplaceChild("right_tendril", CubeListBuilder.create(), PartPose.offset(-8, -12, 0));
		PartDefinition lt = head.addOrReplaceChild("left_tendril", CubeListBuilder.create(), PartPose.offset(8, -12, 0));
		PartDefinition ra = body.addOrReplaceChild("right_arm", CubeListBuilder.create(), PartPose.offset(-13, -13, 1));
		PartDefinition la = body.addOrReplaceChild("left_arm", CubeListBuilder.create(), PartPose.offset(13, -13, 1));
		PartDefinition rl = bone.addOrReplaceChild("right_leg", CubeListBuilder.create(), PartPose.offset(-5.9f, -13, 0));
		PartDefinition ll = bone.addOrReplaceChild("left_leg", CubeListBuilder.create(), PartPose.offset(5.9f, -13, 0));

		Packer packer = new Packer();
		FORM_HEIGHT.clear();
		float bulk = 1f;
		// Body: Blender's body box is z 0-21 from the hips (13 px up), the model's body pivot is 21 px up and its cube
		// centred 1.5 px back.
		Bone b = new Bone(body, "bone/body", "body", 8, 1.5f, 21, packer);
		b.slabs(-9, -5.5f, 6, 9, 5.5f, 21, G, T, false, false);
		b.pb(-1.2f, -5.5f - G - T - 1.6f * bulk, 8, 1.2f, -5.5f - G - T, 20);
		b.pb(2.5f, -5.5f - G - T - 0.9f * bulk, 17, 8.5f, -5.5f - G - T, 19.5f);
		b.pb(-8.5f, -5.5f - G - T - 0.9f * bulk, 17, -2.5f, -5.5f - G - T, 19.5f);
		b.pb(-7, -5.5f - G - T, 21 + G, 7, 5.5f + G + T, 21 + G + 1.2f);
		b.slabs(-9, -5.5f, 0, 9, 5.5f, 4.5f, G + 0.5f, T, false, false);
		b.build();
		// Head: pivot 34 px up, the cube rising 16 from it, centred on the pivot.
		Bone h = new Bone(head, "bone/body/head", "head", 0, 0, 34, packer);
		h.slabs(-8, -5, 0, 8, 5, 16, G, T, true, false);
		h.pb(-8 - G - T, -5 - G - T - 1.4f * bulk, 9, 8 + G + T, -5 - G - T, 11);
		h.pb(-1, -6, 16 + G + T, 1, 6, 16 + G + T + 2.2f * bulk);
		h.build();
		// Tendrils: flat, 16 x 16 rising from 3 below the pivot (46 px up); guards on both faces and a cap along the top.
		for (int sx : new int[] {-1, 1}) {
			Bone t = new Bone(sx < 0 ? rt : lt, sx < 0 ? "bone/body/head/right_tendril" : "bone/body/head/left_tendril", sx < 0 ? "rt" : "lt", 3, 0, 46, packer);
			float x0 = sx > 0 ? 1.5f : -15.5f, x1 = sx > 0 ? 15.5f : -1.5f;
			t.pb(x0, -0.5f - G - T, 1, x1, -0.5f - G, 15);
			t.pb(x0, 0.5f + G, 1, x1, 0.5f + G + T, 15);
			t.pb(x0, -0.5f - G - T, 16 + G, x1, 0.5f + G + T, 16 + G + T);
			t.build();
		}
		// Arms: pivot 34 px up at the shoulder, hanging 28 down; the right arm's outside is -X.
		for (int sx : new int[] {-1, 1}) {
			Bone a = new Bone(sx < 0 ? ra : la, sx < 0 ? "bone/body/right_arm" : "bone/body/left_arm", sx < 0 ? "ra" : "la", 0, 0, 34, packer);
			float w = 4 + G + 1.5f + bulk;
			a.slabs(-4, -4, -6, 4, 4, 1, G + 0.5f, 1.5f, true, false);
			float l0 = 4 + G + 2, l1 = 4 + G + 2 + 1.5f * bulk;
			if (sx > 0) a.pb(l0, -w, -7.5f, l1, w, 0);
			else a.pb(-l1, -w, -7.5f, -l0, w, 0);
			a.slabs(-4, -4, -22, 4, 4, -11, G, T, false, false);
			a.slabs(-4, -4, -28, 4, 4, -23, G + 0.5f, 1.5f, false, true);
			a.build();
		}
		// Legs: pivot 13 px up, 13 down to the ground.
		for (int sx : new int[] {-1, 1}) {
			Bone l = new Bone(sx < 0 ? rl : ll, sx < 0 ? "bone/right_leg" : "bone/left_leg", sx < 0 ? "rl" : "ll", 0, 0, 13, packer);
			l.slabs(-3, -3, -13, 3, 3, -6, G, T, false, false);
			l.pb(-2.5f, -3 - G - T - 1.5f * bulk, -6.5f, 2.5f, -3 - G - T, -3);
			l.build();
		}
		return LayerDefinition.create(mesh, TEX_W, TEX_H);
	}

	/** The armour pieces of a baked root with their lowest edges, looked up once. */
	public static java.util.Map<ModelPart, Float> pieces(ModelPart root) {
		java.util.Map<ModelPart, Float> out = new java.util.HashMap<>();
		FORM_HEIGHT.forEach((path, at) -> {
			ModelPart p = root;
			for (String n : path.split("/")) p = p.getChild(n);
			out.put(p, at);
		});
		return out;
	}

	/** Shows the pieces whose lowest edge is under {@code height} px (the armour forming feet first). */
	public static void form(java.util.Map<ModelPart, Float> pieces, float height) {
		pieces.forEach((p, at) -> p.visible = at < height);
	}
}
