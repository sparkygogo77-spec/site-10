package com.sparky.lanternring.client.ally;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ally.DreadRunner;
import com.sparky.lanternring.client.BbRig;
import com.sparky.lanternring.client.ShaderGlow;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.EntityRenderer;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import org.joml.Matrix4f;
import org.joml.Vector3f;

/**
 * The Yellow Lantern's Dread Runner, from J's Blender rig: one Blockbench model per body part
 * (bbmodel/dread_runner_&lt;part&gt;.bbmodel, each with its joint at the origin) and
 * bbmodel/dread_runner_rig.json, which holds every joint's pivot (Blockbench axes, pixels), its
 * parent, and a 12-frame sprint (0.5 s a stride). The parts are drawn down the chain, each turned
 * about its joint; the body drops each frame until the lower foot is on the ground, as in Blender.
 * Re-exporting the rig (tools/runner_bbmodel.py, variant a/b/c) changes the runner with no code change.
 *
 * <p>The rig's angles are Blender XYZ Euler degrees in the generator's frame (x right, y forward,
 * z up); Blockbench's frame is (-x, z, y) of that, so a turn about generator X is a turn about
 * Blockbench -X, Y about Z and Z about Y. Blockbench space, scaled down from pixels, is the
 * runner's own space here, facing +Z.
 */
public class DreadRunnerRenderer extends EntityRenderer<DreadRunner, DreadRunnerRenderer.State> {
	private static final float FADE_IN = 6f;
	/** Ticks a stride takes when the rig doesn't say. */
	private static final float STRIDE_TICKS = 10f;
	/** The rig's 0.5 s stride, stretched to suit the slower run (0.7 s a stride). */
	private static final float STRIDE_SLOW = 1.4f;

	public static class State extends EntityRenderState {
		float yaw;
		float alpha = 1f;
		/** Where in the stride it is, in frames (0 to the frame count). */
		float frame;
	}

	private record Part(String name, int parent, float[] pivot, ModelPart model, Identifier texture, List<Integer> children) {
	}

	private final List<Part> parts = new ArrayList<>();
	/** Per frame, per part: the three generator-frame angles in degrees. */
	private final List<float[][]> frames = new ArrayList<>();
	/** Per frame: how far the body sits from its rest height (pixels), so a foot is on the ground. */
	private final List<Float> drops = new ArrayList<>();
	private float strideTicks = STRIDE_TICKS;

	public DreadRunnerRenderer(EntityRendererProvider.Context context) {
		super(context);
		shadowRadius = 0.9f;
		try {
			load();
		} catch (Exception e) {
			LanternRing.LOGGER.warn("Couldn't load the Dread Runner rig", e);
			parts.clear();
			frames.clear();
		}
	}

	private void load() throws Exception {
		JsonObject rig;
		String path = "/assets/" + LanternRing.MOD_ID + "/bbmodel/dread_runner_rig.json";
		try (InputStream in = DreadRunnerRenderer.class.getResourceAsStream(path)) {
			if (in == null) throw new IllegalStateException("missing " + path);
			rig = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
		}
		JsonArray list = rig.getAsJsonArray("parts");
		for (JsonElement e : list) {
			JsonObject p = e.getAsJsonObject();
			String name = p.get("name").getAsString();
			ModelPart root = BbRig.load("dread_runner_" + name).solid().bakeRoot();
			// The part's joint is at its origin: undo BbRig's feet-on-y=24 offset.
			root.getChild("rig").y = 0;
			parts.add(new Part(name, p.get("parent").getAsInt(), vec(p.getAsJsonArray("pivot_bb")), root,
					LanternRing.id("textures/entity/bb/dread_runner_" + name + ".png"), new ArrayList<>()));
		}
		for (int i = 0; i < parts.size(); i++) {
			int parent = parts.get(i).parent;
			if (parent >= 0) parts.get(parent).children.add(i);
		}
		if (rig.has("stride_seconds")) strideTicks = rig.get("stride_seconds").getAsFloat() * 20f;
		// J: fluid, not TOO fast. The run is slower now (RingTuning dread_run 9 s), so the legs turn over slower too.
		strideTicks *= STRIDE_SLOW;
		float[][] shinBounds = new float[parts.size()][];
		for (int i = 0; i < parts.size(); i++) {
			if (parts.get(i).name.startsWith("shin")) shinBounds[i] = bounds("dread_runner_" + parts.get(i).name);
		}
		for (JsonElement f : rig.getAsJsonArray("frames")) {
			JsonObject frame = f.getAsJsonObject();
			float[][] angles = new float[parts.size()][];
			for (int i = 0; i < parts.size(); i++) {
				JsonArray a = frame.getAsJsonArray(parts.get(i).name);
				angles[i] = a == null ? new float[3] : vec(a);
			}
			frames.add(angles);
			float bob = frame.has("bob") ? frame.get("bob").getAsFloat() : 0f;
			drops.add(bob - lowest(angles, shinBounds));
		}
	}

	/** The lowest point of the feet (pixels above the ground) with the body at its rest height. */
	private float lowest(float[][] angles, float[][] shinBounds) {
		Matrix4f[] world = new Matrix4f[parts.size()];
		float low = Float.MAX_VALUE;
		for (int i = 0; i < parts.size(); i++) {
			Part p = parts.get(i);
			Matrix4f m = p.parent < 0 ? new Matrix4f().translate(p.pivot[0], p.pivot[1], p.pivot[2])
					: new Matrix4f(world[p.parent]).translate(p.pivot[0] - parts.get(p.parent).pivot[0],
							p.pivot[1] - parts.get(p.parent).pivot[1], p.pivot[2] - parts.get(p.parent).pivot[2]);
			float[] a = angles[i];
			m.rotateY(a[2] * Mth.DEG_TO_RAD).rotateZ(a[1] * Mth.DEG_TO_RAD).rotateX(-a[0] * Mth.DEG_TO_RAD);
			world[i] = m;
			float[] b = shinBounds[i];
			if (b == null) continue;
			for (int c = 0; c < 8; c++) {
				Vector3f v = m.transformPosition(new Vector3f((c & 1) == 0 ? b[0] : b[3], (c & 2) == 0 ? b[1] : b[4], (c & 4) == 0 ? b[2] : b[5]));
				low = Math.min(low, v.y);
			}
		}
		return low == Float.MAX_VALUE ? 0f : low;
	}

	/** A Blockbench model's box (min xyz, max xyz) in its own pixels. */
	private static float[] bounds(String name) throws Exception {
		String path = "/assets/" + LanternRing.MOD_ID + "/bbmodel/" + name + ".bbmodel";
		float[] b = {Float.MAX_VALUE, Float.MAX_VALUE, Float.MAX_VALUE, -Float.MAX_VALUE, -Float.MAX_VALUE, -Float.MAX_VALUE};
		try (InputStream in = DreadRunnerRenderer.class.getResourceAsStream(path)) {
			if (in == null) throw new IllegalStateException("missing " + path);
			JsonObject json = JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8)).getAsJsonObject();
			for (JsonElement e : json.getAsJsonArray("elements")) {
				JsonObject el = e.getAsJsonObject();
				if (!el.has("from")) continue;
				float[] from = vec(el.getAsJsonArray("from"));
				float[] to = vec(el.getAsJsonArray("to"));
				for (int k = 0; k < 3; k++) {
					b[k] = Math.min(b[k], Math.min(from[k], to[k]));
					b[k + 3] = Math.max(b[k + 3], Math.max(from[k], to[k]));
				}
			}
		}
		return b;
	}

	private static float[] vec(JsonArray a) {
		float[] out = new float[a.size()];
		for (int i = 0; i < out.length; i++) out[i] = a.get(i).getAsFloat();
		return out;
	}

	@Override
	public void submit(State state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
		if (!parts.isEmpty() && !frames.isEmpty() && state.alpha > 0.01f) {
			int n = frames.size();
			int f0 = Mth.floor(state.frame) % n;
			int f1 = (f0 + 1) % n;
			float t = state.frame - Mth.floor(state.frame);
			// Fluid, not frame to frame: a Catmull-Rom curve through the rig's frames on either side,
			// so the limbs ease through each pose instead of turning at a constant rate between them.
			int fp = (f0 + n - 1) % n, fn = (f1 + 1) % n;
			float[][] a = smooth(frames.get(fp), frames.get(f0), frames.get(f1), frames.get(fn), t);
			float drop = catmull(drops.get(fp), drops.get(f0), drops.get(f1), drops.get(fn), t);
			float[][] b = a;
			t = 0f;
			int tint = Math.round(state.alpha * 255) << 24 | 0xFFFFFF;
			int light = ShaderGlow.light();
			poseStack.pushPose();
			poseStack.rotateDegrees(Axis.YP, -state.yaw);
			poseStack.scale(DreadRunner.SCALE, DreadRunner.SCALE, DreadRunner.SCALE);
			for (int i = 0; i < parts.size(); i++) {
				if (parts.get(i).parent < 0) draw(i, null, a, b, t, drop, poseStack, collector, tint, light);
			}
			poseStack.popPose();
		}
		super.submit(state, poseStack, collector, camera);
	}

	private static float catmull(float p0, float p1, float p2, float p3, float t) {
		float t2 = t * t, t3 = t2 * t;
		return 0.5f * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (3 * p1 - p0 - 3 * p2 + p3) * t3);
	}

	private static float[][] smooth(float[][] p0, float[][] p1, float[][] p2, float[][] p3, float t) {
		float[][] out = new float[p1.length][3];
		for (int i = 0; i < p1.length; i++) {
			for (int k = 0; k < 3; k++) out[i][k] = catmull(p0[i][k], p1[i][k], p2[i][k], p3[i][k], t);
		}
		return out;
	}

	/** Draws a part turned about its joint, then its children from there. */
	private void draw(int i, Part parent, float[][] a, float[][] b, float t, float drop, PoseStack poseStack, SubmitNodeCollector collector,
			int tint, int light) {
		Part p = parts.get(i);
		poseStack.pushPose();
		if (parent == null) {
			poseStack.translate(p.pivot[0] / 16f, (p.pivot[1] + drop) / 16f, p.pivot[2] / 16f);
		} else {
			poseStack.translate((p.pivot[0] - parent.pivot[0]) / 16f, (p.pivot[1] - parent.pivot[1]) / 16f, (p.pivot[2] - parent.pivot[2]) / 16f);
		}
		poseStack.rotateDegrees(Axis.YP, Mth.lerp(t, a[i][2], b[i][2]));
		poseStack.rotateDegrees(Axis.ZP, Mth.lerp(t, a[i][1], b[i][1]));
		poseStack.rotateDegrees(Axis.XP, -Mth.lerp(t, a[i][0], b[i][0]));
		// The baked part is in entity-model space, which is Blockbench's turned about Z.
		poseStack.pushPose();
		poseStack.scale(-1f, -1f, 1f);
		collector.submitModelPart(p.model, poseStack, RenderTypes.entityTranslucentEmissive(p.texture), light, OverlayTexture.NO_OVERLAY, null, tint);
		poseStack.popPose();
		for (int c : p.children) draw(c, p, a, b, t, drop, poseStack, collector, tint, light);
		poseStack.popPose();
	}

	@Override
	protected int getBlockLightLevel(DreadRunner entity, BlockPos pos) {
		return 15;
	}

	@Override
	public State createRenderState() {
		return new State();
	}

	@Override
	public void extractRenderState(DreadRunner entity, State state, float partialTicks) {
		super.extractRenderState(entity, state, partialTicks);
		state.yaw = entity.getYRot(partialTicks);
		float in = Mth.clamp((entity.tickCount + partialTicks) / FADE_IN, 0.05f, 1f);
		int stopped = entity.stopped();
		float out = stopped < 0 ? 1f : Mth.clamp(1f - (stopped + partialTicks) / DreadRunner.FADE, 0f, 1f);
		state.alpha = in * out;
		// The sprint plays at the rig's own pace while it runs and freezes once it stops.
		float age = stopped < 0 ? entity.tickCount + partialTicks : entity.tickCount - stopped;
		int n = Math.max(1, frames.size());
		state.frame = (age / strideTicks * n) % n;
	}
}
