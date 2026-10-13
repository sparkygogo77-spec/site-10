package com.sparky.lanternring.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.LanternRing;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.renderer.SubmitNodeCollector;
import org.joml.Matrix4f;
import org.joml.Vector3f;
import org.jspecify.annotations.Nullable;

/**
 * A Blockbench model made to sit on a vanilla-style entity model (a Blender export in one flat group,
 * modelled on the entity's boxes at rest, feet at y = 0) that moves with that model's parts: each
 * cube is given to the part it sits on (the nearest part's box at rest, unless {@link Pick} says
 * otherwise) and drawn after that part's current turn, so armour plates swing with the arms and
 * legs and a helmet turns with the head.
 */
public final class RiggedBb {
	/** Chooses a cube's part itself (by its Blockbench name and centre), or null to take the nearest part. */
	public interface Pick {
		@Nullable String pick(String cubeName, float bx, float by, float bz);
	}

	private record Bone(String[] path, BbModel model, Matrix4f undoRest) {
	}

	private final List<Bone> bones = new ArrayList<>();

	private RiggedBb() {
	}

	/**
	 * Loads bbmodel/{name} split over the parts of {@code root} named in {@code partPaths}
	 * ("neck/head" for a part inside another).
	 */
	public static RiggedBb load(String name, ModelPart root, List<String> partPaths, @Nullable Pick pick) {
		RiggedBb rig = new RiggedBb();
		int n = partPaths.size();
		float[][] boxes = new float[n][];
		Matrix4f[] rests = new Matrix4f[n];
		for (int i = 0; i < n; i++) {
			String[] path = partPaths.get(i).split("/");
			Matrix4f m = rest(root.getInitialPose());
			ModelPart part = root;
			for (String step : path) {
				part = part.getChild(step);
				m.mul(rest(part.getInitialPose()));
			}
			rests[i] = m;
			boxes[i] = box(part, m, partPaths, partPaths.get(i));
		}
		JsonArray elements = read(name).getAsJsonArray("elements");
		List<Set<Integer>> owned = new ArrayList<>();
		for (int i = 0; i < n; i++) owned.add(new HashSet<>());
		for (int e = 0; e < elements.size(); e++) {
			JsonObject el = elements.get(e).getAsJsonObject();
			float[] from = vec(el.getAsJsonArray("from")), to = vec(el.getAsJsonArray("to"));
			float bx = (from[0] + to[0]) / 2, by = (from[1] + to[1]) / 2, bz = (from[2] + to[2]) / 2;
			String cubeName = el.has("name") ? el.get("name").getAsString() : "";
			String chosen = pick == null ? null : pick.pick(cubeName, bx, by, bz);
			int best = chosen == null ? -1 : partPaths.indexOf(chosen);
			if (best < 0) {
				// Entity model space: x and y turned over, y measured down from 24 pixels up.
				float mx = -bx, my = 24 - by, mz = bz;
				float bestD = Float.MAX_VALUE;
				for (int i = 0; i < n; i++) {
					if (boxes[i] == null) continue;
					float d = distance(boxes[i], mx, my, mz);
					if (d < bestD) {
						bestD = d;
						best = i;
					}
				}
			}
			if (best >= 0) owned.get(best).add(e);
		}
		for (int i = 0; i < n; i++) {
			if (owned.get(i).isEmpty()) continue;
			Set<Integer> mine = owned.get(i);
			Matrix4f undo = new Matrix4f(rests[i]).invert();
			rig.bones.add(new Bone(partPaths.get(i).split("/"), BbModel.load(name, mine::contains), undo));
		}
		return rig;
	}

	/**
	 * Draws it on the model as it's posed now: call from a render layer, where the pose stack is the
	 * entity model's own space.
	 */
	public void render(PoseStack pose, SubmitNodeCollector collector, ModelPart root, int light, int glowColor) {
		for (Bone b : bones) {
			pose.pushPose();
			root.translateAndRotate(pose);
			ModelPart part = root;
			for (String step : b.path) {
				part = part.getChild(step);
				part.translateAndRotate(pose);
			}
			// Back out of where the part sits at rest, then from model space into Blockbench's.
			pose.mulPose(b.undoRest);
			pose.translate(0f, 1.5f, 0f);
			pose.rotateDegrees(Axis.ZP, 180f);
			b.model.render(pose, collector, light, glowColor);
			pose.popPose();
		}
	}

	/** The part's rest transform in blocks, as ModelPart.translateAndRotate applies it. */
	private static Matrix4f rest(PartPose p) {
		return new Matrix4f().translate(p.x() / 16f, p.y() / 16f, p.z() / 16f)
				.rotateZYX(p.zRot(), p.yRot(), p.xRot()).scale(p.xScale(), p.yScale(), p.zScale());
	}

	/** The part's cubes at rest, in model pixels, leaving out any child that is a part of its own. */
	private static float @Nullable [] box(ModelPart part, Matrix4f m, List<String> partPaths, String path) {
		float[] b = {Float.MAX_VALUE, Float.MAX_VALUE, Float.MAX_VALUE, -Float.MAX_VALUE, -Float.MAX_VALUE, -Float.MAX_VALUE};
		boolean[] any = {false};
		PoseStack ps = new PoseStack();
		ps.last().pose().set(m);
		// visit() applies the part's own pose again: start from its parent's.
		ps.last().pose().mul(new Matrix4f(rest(part.getInitialPose())).invert());
		part.visit(ps, (p, name, index, cube) -> {
			String full = path + (name.isEmpty() ? "" : "/" + name);
			for (String other : partPaths) {
				if (!other.equals(path) && full.startsWith(other)) return;
			}
			for (int c = 0; c < 8; c++) {
				Vector3f v = new Vector3f((c & 1) == 0 ? cube.minX : cube.maxX, (c & 2) == 0 ? cube.minY : cube.maxY,
						(c & 4) == 0 ? cube.minZ : cube.maxZ).div(16f);
				p.pose().transformPosition(v).mul(16f);
				b[0] = Math.min(b[0], v.x);
				b[1] = Math.min(b[1], v.y);
				b[2] = Math.min(b[2], v.z);
				b[3] = Math.max(b[3], v.x);
				b[4] = Math.max(b[4], v.y);
				b[5] = Math.max(b[5], v.z);
				any[0] = true;
			}
		});
		return any[0] ? b : null;
	}

	private static float distance(float[] b, float x, float y, float z) {
		float dx = Math.max(Math.max(b[0] - x, 0), x - b[3]);
		float dy = Math.max(Math.max(b[1] - y, 0), y - b[4]);
		float dz = Math.max(Math.max(b[2] - z, 0), z - b[5]);
		return dx * dx + dy * dy + dz * dz;
	}

	private static JsonObject read(String name) {
		String path = "/assets/" + LanternRing.MOD_ID + "/bbmodel/" + name + ".bbmodel";
		try (InputStream in = RiggedBb.class.getResourceAsStream(path)) {
			if (in == null) throw new IllegalStateException("missing " + path);
			return JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
		} catch (Exception e) {
			throw new IllegalStateException("Couldn't read " + path, e);
		}
	}

	private static float[] vec(JsonArray a) {
		float[] out = new float[a.size()];
		for (int i = 0; i < out.length; i++) out[i] = a.get(i).getAsFloat();
		return out;
	}
}
