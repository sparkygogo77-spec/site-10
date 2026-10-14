package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.core.BlockPos;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.phys.Vec3;
import org.joml.Matrix3f;
import org.joml.Matrix4f;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * Moving constructs (block displays: the falling Anvil, one stretched display per box) drawn as one
 * piece of hard light instead of block models (J, 2026-10-13):
 * <ul>
 * <li>the strip keeps its size in the world, 64 px a block over 4 blocks like the placed constructs,
 *     however big the box is (a 2.5x Anvil no longer stretches it) and lines up across boxes;</li>
 * <li>a face against another box of light isn't drawn, so no grid of block edges shows inside;</li>
 * <li>see-through at the Ring Lab's construct opacity, blended and lit like the placed constructs (not fullbright);
 *     solid under a shader pack, which drew the see-through boxes as pale glass.</li>
 * </ul>
 * Turned boxes (the tank's spinning drill) are drawn here too, in the drill's own turned frame, so only
 * their outer shell shows (J, 2026-10-14: a big drop's full block models filled the memory). A glass look
 * (X3D1) is cut out at full alpha, no blending. The vanilla renderer skips the displays drawn here
 * (BlockDisplayRendererMixin asks {@link #takes}).
 */
public final class ConstructDisplays {
	private static final double RANGE = 128;
	/** OverlayTexture.NO_OVERLAY. */
	private static final int NO_OVERLAY = 10 << 16;

	/** A box in its frame's coordinates; glass boxes are cut out at full alpha. */
	private record Box(double x0, double y0, double z0, double x1, double y1, double z1, TextureAtlasSprite sprite, int light, boolean glass) {
	}

	/**
	 * Boxes that share axes: the world (origin 0, no turn) or one turned drill (origin at its display,
	 * turned by its rotation). Faces between touching boxes of one frame are left out.
	 */
	private static final class Frame {
		final double ox, oy, oz;
		final Quaternionf turn;
		final List<Box> boxes = new ArrayList<>();
		final Set<Long> cells = new HashSet<>();

		Frame(double ox, double oy, double oz, Quaternionf turn) {
			this.ox = ox;
			this.oy = oy;
			this.oz = oz;
			this.turn = turn;
		}
	}

	/** A display's transformation split into move, turn (null if none) and positive scale. */
	private record Parts(Vector3f move, Quaternionf turn, Vector3f scale) {
	}

	private ConstructDisplays() {
	}

	/** On a block display's render state: drawn here, so the vanilla renderer leaves it out. */
	public interface Taken {
		boolean lanternring$taken();

		void lanternring$setTaken(boolean taken);
	}

	public static void register() {
		LevelRenderEvents.COLLECT_SUBMITS.register(ConstructDisplays::submit);
	}

	/** Whether this display is drawn here (a construct with a strip, a moved, turned and scaled box) rather than as a block. */
	public static boolean takes(Display.BlockDisplay display, float partial) {
		return ConstructLooks.displaySprite(display.getBlockState()) != null && parts(display, partial) != null;
	}

	/** The display's transformation as a move, a turn and a positive scale, or null if it shears or flips. */
	private static Parts parts(Display.BlockDisplay display, float partial) {
		Display.RenderState rs = display.renderState();
		Matrix4f m = rs == null ? new Matrix4f()
				: new Matrix4f(rs.transformation().get(display.calculateInterpolationProgress(partial)).getMatrix());
		Vector3f move = new Vector3f(m.m30(), m.m31(), m.m32());
		if (Math.abs(m.m01()) + Math.abs(m.m02()) + Math.abs(m.m10()) + Math.abs(m.m12()) + Math.abs(m.m20()) + Math.abs(m.m21()) <= 1e-4) {
			if (m.m00() <= 0 || m.m11() <= 0 || m.m22() <= 0) return null;
			return new Parts(move, null, new Vector3f(m.m00(), m.m11(), m.m22()));
		}
		Vector3f c0 = new Vector3f(m.m00(), m.m01(), m.m02()), c1 = new Vector3f(m.m10(), m.m11(), m.m12()),
				c2 = new Vector3f(m.m20(), m.m21(), m.m22());
		Vector3f scale = new Vector3f(c0.length(), c1.length(), c2.length());
		if (scale.x < 1e-4 || scale.y < 1e-4 || scale.z < 1e-4) return null;
		c0.div(scale.x);
		c1.div(scale.y);
		c2.div(scale.z);
		if (Math.abs(c0.dot(c1)) + Math.abs(c0.dot(c2)) + Math.abs(c1.dot(c2)) > 1e-3) return null;
		if (new Vector3f(c0).cross(c1).dot(c2) < 0) return null;
		Quaternionf turn = new Matrix3f(c0, c1, c2).getNormalizedRotation(new Quaternionf());
		return new Parts(move, turn, scale);
	}

	private static void submit(LevelRenderContext ctx) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float partial = ctx.levelState().worldPartialTicks;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		Frame world = new Frame(0, 0, 0, null);
		Map<String, Frame> frames = new LinkedHashMap<>();
		frames.put("world", world);
		for (Entity e : mc.level.entitiesForRendering()) {
			if (!(e instanceof Display.BlockDisplay d) || d.distanceToSqr(cam) > RANGE * RANGE) continue;
			TextureAtlasSprite sprite = ConstructLooks.displaySprite(d.getBlockState());
			if (sprite == null) continue;
			Parts parts = parts(d, partial);
			if (parts == null) continue;
			Vec3 p = d.getPosition(partial);
			Frame f;
			Vector3f lo;
			if (parts.turn == null) {
				f = world;
				lo = new Vector3f(parts.move);
			} else {
				// a turned drill: its pieces share the display's spot and the turn, so they line up in that frame
				Quaternionf q = parts.turn;
				String key = Math.round(p.x * 64) + "/" + Math.round(p.y * 64) + "/" + Math.round(p.z * 64) + "/"
						+ Math.round(q.x * 1000) + "/" + Math.round(q.y * 1000) + "/" + Math.round(q.z * 1000) + "/" + Math.round(q.w * 1000);
				f = frames.computeIfAbsent(key, k -> new Frame(p.x, p.y, p.z, new Quaternionf(q)));
				lo = q.transformInverse(new Vector3f(parts.move));
			}
			Vector3f size = parts.scale;
			// lit like the placed constructs (their own light 10, or the world's if brighter), not fullbright:
			// J's see-through layers washed out into a glowing blob
			Vector3f mid = new Vector3f(size).mul(0.5f);
			if (parts.turn != null) parts.turn.transform(mid);
			mid.add(parts.move);
			BlockPos at = BlockPos.containing(p.x + mid.x, p.y + mid.y, p.z + mid.z);
			int block = Math.max(10, mc.level.getBrightness(LightLayer.BLOCK, at)), sky = mc.level.getBrightness(LightLayer.SKY, at);
			// box corners in the frame: world boxes in world coordinates, turned ones about the display's spot
			double bx = f == world ? p.x + lo.x : lo.x, by = f == world ? p.y + lo.y : lo.y, bz = f == world ? p.z + lo.z : lo.z;
			boolean glass = ConstructLooks.glass(d.getBlockState());
			// a glass look's strands glow softly under the patched shader pack (J's pick, 2026-10-14): cut out,
			// so no see-through layers stack into a blob
			// Under the patched pack every falling box glows in its own colour, as the placed construct blocks do
			// (the pack gives those emission by their block ID; an entity has none, so it came out a pale, unlit
			// shell once the Anvil and the other drops started to fall: J, 2026-10-14).
			int light = ShaderGlow.patchedPackOn() ? ShaderGlow.light(glass ? 0.55f : 0.6f) : block << 4 | sky << 20;
			Box b = new Box(bx, by, bz, bx + size.x, by + size.y, bz + size.z, sprite, light, glass);
			f.boxes.add(b);
			// every block of light in it, by its centre, so touching faces can be left out
			int nx = Math.max(1, Math.round(size.x)), ny = Math.max(1, Math.round(size.y)), nz = Math.max(1, Math.round(size.z));
			for (int i = 0; i < nx; i++) {
				for (int j = 0; j < ny; j++) {
					for (int k = 0; k < nz; k++) f.cells.add(key(b.x0 + i + 0.5, b.y0 + j + 0.5, b.z0 + k + 0.5));
				}
			}
		}
		// Under a shader pack the boxes are drawn solid: Iris puts translucent entity geometry in the pack's
		// translucent entity pass, where Complementary showed the falling Anvil as pale, colourless glass while
		// the placed blocks it came from stayed jade (J, 2026-10-13). Without a pack: see-through as picked,
		// except a glass look, which is cut out at full alpha.
		boolean pack = SoulSight.shaderPackOn();
		int alpha = ConstructLooks.alpha();
		for (Frame f : frames.values()) {
			if (f.boxes.isEmpty()) continue;
			for (int pass = 0; pass < 2; pass++) {
				boolean cutout = pass == 0;
				List<Box> these = new ArrayList<>();
				for (Box b : f.boxes) if ((pack || b.glass) == cutout) these.add(b);
				if (these.isEmpty()) continue;
				int a = cutout ? 255 : alpha;
				// and with no stale Iris entity/item ID, which gave it another object's material (glass) in the pack
				IrisIds.cleared(() -> ctx.submitNodeCollector().submitCustomGeometry(ctx.poseStack(),
						cutout ? RenderTypes.entityCutout(TextureAtlas.LOCATION_BLOCKS) : RenderTypes.entityTranslucent(TextureAtlas.LOCATION_BLOCKS),
						(pose, buffer) -> {
							for (Box b : these) box(pose, buffer, b, f, cam, a);
						}));
			}
		}
	}

	/** A block centre's key, on a quarter-block grid (all a drop's boxes share its height's fraction). */
	private static long key(double x, double y, double z) {
		long kx = Math.round(x * 4), ky = Math.round(y * 4), kz = Math.round(z * 4);
		return (kx & 0x1FFFFF) << 42 | (ky & 0x1FFFFF) << 21 | (kz & 0x1FFFFF);
	}

	private static void box(PoseStack.Pose pose, VertexConsumer buffer, Box b, Frame f, Vec3 cam, int alpha) {
		double[] lo = {b.x0, b.y0, b.z0}, hi = {b.x1, b.y1, b.z1};
		for (int axis = 0; axis < 3; axis++) {
			for (int sign = -1; sign <= 1; sign += 2) {
				// in-plane axes: u and v as FlowConstructModel lays a placed construct's face
				int ua = axis == 0 ? 2 : 0, va = axis == 1 ? 2 : 1;
				boolean vDown = axis != 1;
				int nu = Math.max(1, (int) Math.round(hi[ua] - lo[ua])), nv = Math.max(1, (int) Math.round(hi[va] - lo[va]));
				double du = (hi[ua] - lo[ua]) / nu, dv = (hi[va] - lo[va]) / nv;
				double plane = sign > 0 ? hi[axis] : lo[axis];
				for (int i = 0; i < nu; i++) {
					for (int j = 0; j < nv; j++) {
						double[] c = new double[3];
						c[axis] = plane + sign * 0.5;
						c[ua] = lo[ua] + (i + 0.5) * du;
						c[va] = lo[va] + (j + 0.5) * dv;
						if (f.cells.contains(key(c[0], c[1], c[2]))) continue;   // against more light: inside
						cell(pose, buffer, b.sprite, b.light, axis, sign, plane, ua, va, vDown,
								lo[ua] + i * du, lo[ua] + (i + 1) * du, lo[va] + j * dv, lo[va] + (j + 1) * dv, f, cam, alpha);
					}
				}
			}
		}
	}

	/** One face cell, cut where it crosses a whole block so each piece maps into the strip once. */
	private static void cell(PoseStack.Pose pose, VertexConsumer buffer, TextureAtlasSprite s, int light, int axis, int sign, double plane,
			int ua, int va, boolean vDown, double u0, double u1, double v0, double v1, Frame f, Vec3 cam, int alpha) {
		Vector3f n = new Vector3f(axis == 0 ? sign : 0, axis == 1 ? sign : 0, axis == 2 ? sign : 0);
		if (f.turn != null) f.turn.transform(n);
		Vector3f v = new Vector3f();
		for (double[] us : pieces(u0, u1)) {
			for (double[] vs : pieces(v0, v1)) {
				float[][] uv = new float[2][2];
				for (int k = 0; k < 2; k++) {
					uv[0][k] = strip(us[k], us[2], false, s.getU0(), s.getU1());
					uv[1][k] = strip(vs[k], vs[2], vDown, s.getV0(), s.getV1());
				}
				// corners wound to face outward: the plain order faces -x, -y and +z, so +x, +y and -z go the other way
				int[][] order = sign > 0 == (axis != 2) ? new int[][] {{0, 0}, {0, 1}, {1, 1}, {1, 0}} : new int[][] {{0, 0}, {1, 0}, {1, 1}, {0, 1}};
				for (int[] o : order) {
					double[] p = new double[3];
					p[axis] = plane;
					p[ua] = us[o[0]];
					p[va] = vs[o[1]];
					if (f.turn == null) {
						v.set((float) (p[0] - cam.x), (float) (p[1] - cam.y), (float) (p[2] - cam.z));
					} else {
						f.turn.transform(v.set((float) p[0], (float) p[1], (float) p[2]));
						v.add((float) (f.ox - cam.x), (float) (f.oy - cam.y), (float) (f.oz - cam.z));
					}
					buffer.addVertex(pose, v.x, v.y, v.z)
							.setColor(255, 255, 255, alpha)
							.setUv(uv[0][o[0]], uv[1][o[1]])
							.setOverlay(NO_OVERLAY)
							.setLight(light)
							.setNormal(pose, n.x, n.y, n.z);
				}
			}
		}
	}

	/** [a, b] cut at whole numbers: {start, end, centre} for each piece. */
	private static List<double[]> pieces(double a, double b) {
		List<double[]> out = new ArrayList<>(2);
		double from = a;
		for (double cut = Math.floor(a) + 1; cut < b - 1e-4; cut++) {
			if (cut - from > 1e-4) out.add(new double[] {from, cut, (from + cut) / 2});
			from = cut;
		}
		out.add(new double[] {from, b, (from + b) / 2});
		return out;
	}

	/** Where world coordinate w (in the piece centred at mid) falls in the strip, which covers 4 blocks. */
	private static float strip(double w, double mid, boolean down, float lo, float hi) {
		double base = 4 * Math.floor(mid / 4);
		float f = (float) Mth.clamp((w - base) / 4, 0, 1);
		if (down) f = 1 - f;
		return lo + (hi - lo) * f;
	}
}
