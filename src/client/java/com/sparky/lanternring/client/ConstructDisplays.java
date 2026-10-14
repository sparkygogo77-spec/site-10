package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
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
import org.joml.Matrix4f;

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
 * Turned boxes (the tank's spinning drill) keep the block model. The vanilla renderer skips the
 * displays drawn here (BlockDisplayRendererMixin asks {@link #takes}).
 */
public final class ConstructDisplays {
	private static final double RANGE = 128;
	/** OverlayTexture.NO_OVERLAY. */
	private static final int NO_OVERLAY = 10 << 16;

	private record Box(double x0, double y0, double z0, double x1, double y1, double z1, TextureAtlasSprite sprite, int light) {
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

	/** Whether this display is drawn here (a construct with a strip, an axis-aligned box) rather than as a block. */
	public static boolean takes(Display.BlockDisplay display, float partial) {
		return ConstructLooks.displaySprite(display.getBlockState()) != null && matrix(display, partial) != null;
	}

	/** The display's transformation if it is only a move and a positive scale, else null. */
	private static Matrix4f matrix(Display.BlockDisplay display, float partial) {
		Display.RenderState rs = display.renderState();
		Matrix4f m = rs == null ? new Matrix4f()
				: new Matrix4f(rs.transformation().get(display.calculateInterpolationProgress(partial)).getMatrix());
		if (Math.abs(m.m01()) + Math.abs(m.m02()) + Math.abs(m.m10()) + Math.abs(m.m12()) + Math.abs(m.m20()) + Math.abs(m.m21()) > 1e-4) {
			return null;
		}
		if (m.m00() <= 0 || m.m11() <= 0 || m.m22() <= 0) return null;
		return m;
	}

	private static void submit(LevelRenderContext ctx) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float partial = ctx.levelState().worldPartialTicks;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		List<Box> boxes = new ArrayList<>();
		Set<Long> cells = new HashSet<>();
		for (Entity e : mc.level.entitiesForRendering()) {
			if (!(e instanceof Display.BlockDisplay d) || d.distanceToSqr(cam) > RANGE * RANGE) continue;
			TextureAtlasSprite sprite = ConstructLooks.displaySprite(d.getBlockState());
			if (sprite == null) continue;
			Matrix4f m = matrix(d, partial);
			if (m == null) continue;
			Vec3 p = d.getPosition(partial);
			BlockPos at = BlockPos.containing(p.x + m.m30() + m.m00() / 2, p.y + m.m31() + m.m11() / 2, p.z + m.m32() + m.m22() / 2);
			// lit like the placed constructs (their own light 10, or the world's if brighter), not fullbright:
			// J's see-through layers washed out into a glowing blob
			int block = Math.max(10, mc.level.getBrightness(LightLayer.BLOCK, at)), sky = mc.level.getBrightness(LightLayer.SKY, at);
			Box b = new Box(p.x + m.m30(), p.y + m.m31(), p.z + m.m32(),
					p.x + m.m30() + m.m00(), p.y + m.m31() + m.m11(), p.z + m.m32() + m.m22(), sprite, block << 4 | sky << 20);
			boxes.add(b);
			// every block of light in it, by its centre, so touching faces can be left out
			int nx = Math.max(1, Math.round(m.m00())), ny = Math.max(1, Math.round(m.m11())), nz = Math.max(1, Math.round(m.m22()));
			for (int i = 0; i < nx; i++) {
				for (int j = 0; j < ny; j++) {
					for (int k = 0; k < nz; k++) cells.add(key(b.x0 + i + 0.5, b.y0 + j + 0.5, b.z0 + k + 0.5));
				}
			}
		}
		if (boxes.isEmpty()) return;
		// Under a shader pack the boxes are drawn solid: Iris puts translucent entity geometry in the pack's
		// translucent entity pass, where Complementary showed the falling Anvil as pale, colourless glass while
		// the placed blocks it came from stayed jade (J, 2026-10-13). Without a pack: see-through as picked.
		boolean pack = SoulSight.shaderPackOn();
		int alpha = pack ? 255 : ConstructLooks.alpha();
		ctx.submitNodeCollector().submitCustomGeometry(ctx.poseStack(),
				pack ? RenderTypes.entityCutout(TextureAtlas.LOCATION_BLOCKS) : RenderTypes.entityTranslucent(TextureAtlas.LOCATION_BLOCKS),
				(pose, buffer) -> {
					for (Box b : boxes) box(pose, buffer, b, cells, cam, alpha);
				});
	}

	/** A block centre's key, on a quarter-block grid (all a drop's boxes share its height's fraction). */
	private static long key(double x, double y, double z) {
		long kx = Math.round(x * 4), ky = Math.round(y * 4), kz = Math.round(z * 4);
		return (kx & 0x1FFFFF) << 42 | (ky & 0x1FFFFF) << 21 | (kz & 0x1FFFFF);
	}

	private static void box(PoseStack.Pose pose, VertexConsumer buffer, Box b, Set<Long> cells, Vec3 cam, int alpha) {
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
						if (cells.contains(key(c[0], c[1], c[2]))) continue;   // against more light: inside
						cell(pose, buffer, b.sprite, b.light, axis, sign, plane, ua, va, vDown,
								lo[ua] + i * du, lo[ua] + (i + 1) * du, lo[va] + j * dv, lo[va] + (j + 1) * dv, cam, alpha);
					}
				}
			}
		}
	}

	/** One face cell, cut where it crosses a whole world block so each piece maps into the strip once. */
	private static void cell(PoseStack.Pose pose, VertexConsumer buffer, TextureAtlasSprite s, int light, int axis, int sign, double plane,
			int ua, int va, boolean vDown, double u0, double u1, double v0, double v1, Vec3 cam, int alpha) {
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
					buffer.addVertex(pose, (float) (p[0] - cam.x), (float) (p[1] - cam.y), (float) (p[2] - cam.z))
							.setColor(255, 255, 255, alpha)
							.setUv(uv[0][o[0]], uv[1][o[1]])
							.setOverlay(NO_OVERLAY)
							.setLight(light)
							.setNormal(pose, axis == 0 ? sign : 0, axis == 1 ? sign : 0, axis == 2 ? sign : 0);
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
