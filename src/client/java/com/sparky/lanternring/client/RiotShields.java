package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.RingMode;
import com.sparky.lanternring.ShieldReflect;
import com.sparky.lanternring.item.PowerRingItem;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderEvents;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/**
 * The Shield construct: a flat riot shield of jade hard light, body height, held upright in front
 * of anyone holding a ring's Shield (see ShieldReflect for its outline and what it reflects). It
 * is a see-through slab with smoke swirling inside (the Shockwave's animated glass sheet), bright
 * edges and a slight thickness, and snaps out from the ring over a few ticks. Every client draws
 * every bearer's shield, so it needs no packets.
 */
public final class RiotShields {
	private static final RenderType GLASS = RenderTypes.entityTranslucentEmissive(LanternRing.id("textures/entity/shockwave_glass.png"));
	private static final int FULL_BRIGHT = 0xF000F0;
	/** Half the slab's thickness, in blocks. */
	private static final float HALF_THICK = 0.04f;
	/** How wide the bright band along the edge is, on the faces. */
	private static final float RIM = 0.07f;
	/** Ticks the shield takes to grow to full size. */
	private static final float GROW = 4f;
	/** The face is see-through so you can watch what you're blocking; the edge glows solid. */
	private static final float FACE_ALPHA = 0.45f;
	/** Your own shield, seen from behind in first person, is fainter so you can aim past it. */
	private static final float FIRST_PERSON_FACE_ALPHA = 0.28f;
	private static final float RIM_ALPHA = 0.95f;
	private static final float[] JADE = {0.80f, 1f, 0.85f};
	private static final float[] EDGE = {0.85f, 1f, 0.9f};
	/** Smoke animation, as ShockwaveDomes: 64 frames in an 8x8 grid, 3 ticks each. */
	private static final int FRAMES = 64;
	private static final int GRID = 8;
	private static final int FRAME_TICKS = 3;
	private static final float INSET = 0.5f / 1024f;
	/** One smoke frame spans this many blocks of shield, so it isn't stretched. */
	private static final float TILE = 2.7f;

	private RiotShields() {
	}

	public static void register() {
		LevelRenderEvents.COLLECT_SUBMITS.register(RiotShields::submit);
	}

	private static boolean holdsShield(Player player) {
		if (!player.isUsingItem()) return false;
		ItemStack used = player.getUseItem();
		return used.getItem() instanceof PowerRingItem && PowerRingItem.getMode(used) == RingMode.SHIELD;
	}

	private static void submit(LevelRenderContext ctx) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float partial = ctx.levelState().worldPartialTicks;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		float now = mc.level.getGameTime() + partial;
		int frame = Math.floorMod((int) (now / FRAME_TICKS), FRAMES);
		for (Player player : mc.level.players()) {
			if (!holdsShield(player)) continue;
			float grow = Math.min(1f, player.getTicksUsingItem(partial) / GROW);
			float size = 0.3f + 0.7f * Mth.sqrt(grow);
			Vec3 feet = player.getPosition(partial);
			float yaw = player.getViewYRot(partial);
			PoseStack pose = ctx.poseStack();
			pose.pushPose();
			pose.translate(feet.x - cam.x, feet.y - cam.y, feet.z - cam.z);
			pose.rotateDegrees(Axis.YP, -yaw);
			// Local +z is now the way the bearer faces; the shield floats a little, bobbing gently.
			pose.translate(0, 0.03f * Mth.sin(now * 0.12f + player.getId()), ShieldReflect.DISTANCE);
			// Grows out from about chest height.
			pose.translate(0, 1.2f, 0);
			pose.scale(size, size, 1f);
			pose.translate(0, -1.2f, 0);
			float alpha = 0.4f + 0.6f * grow;
			boolean own = player == mc.player && mc.options.getCameraType().isFirstPerson();
			float face = own ? FIRST_PERSON_FACE_ALPHA : FACE_ALPHA;
			ctx.submitNodeCollector().submitCustomGeometry(pose, GLASS, (p, vc) -> mesh(p, vc, frame, alpha, face));
			pose.popPose();
		}
	}

	private static void mesh(PoseStack.Pose pose, VertexConsumer vc, int frame, float alpha, float faceAlpha) {
		double[][] o = ShieldReflect.OUTLINE;
		float cell = 1f / GRID;
		float fu = (frame % GRID) * cell, fv = (frame / GRID) * cell;
		float[] smoke = {fu, fv, cell};
		for (int i = 1; i < o.length; i++) {
			float y0 = (float) o[i - 1][0], w0 = (float) o[i - 1][1];
			float y1 = (float) o[i][0], w1 = (float) o[i][1];
			// The see-through face, front and back, inset by the rim.
			float iy0 = i == 1 ? y0 + RIM : y0, iy1 = i == o.length - 1 ? y1 - RIM : y1;
			float jw0 = lerpWidth(y0, w0, y1, w1, iy0) - RIM, jw1 = lerpWidth(y0, w0, y1, w1, iy1) - RIM;
			for (float z : new float[] {HALF_THICK, -HALF_THICK}) {
				quad(pose, vc, smoke, -jw0, iy0, jw0, iy0, jw1, iy1, -jw1, iy1, z, JADE, alpha * faceAlpha);
			}
			// The bright rim on both faces, down each side.
			for (int s = -1; s <= 1; s += 2) {
				for (float z : new float[] {HALF_THICK, -HALF_THICK}) {
					quad(pose, vc, smoke, s * jw0, iy0, s * w0, y0, s * w1, y1, s * jw1, iy1, z, EDGE, alpha * RIM_ALPHA);
				}
				// The slab's side wall, joining front and back.
				wall(pose, vc, smoke, s * w0, y0, s * w1, y1, alpha * RIM_ALPHA);
			}
		}
		// Bottom and top: a rim band across each face, and the end walls.
		double[] bottom = o[0], top = o[o.length - 1];
		for (double[] end : new double[][] {bottom, top}) {
			float y = (float) end[0], w = (float) end[1];
			float in = end == bottom ? y + RIM : y - RIM;
			float iw = (float) ShieldReflect.halfWidth(in) - RIM;
			for (float z : new float[] {HALF_THICK, -HALF_THICK}) {
				quad(pose, vc, smoke, -w, y, w, y, iw, in, -iw, in, z, EDGE, alpha * RIM_ALPHA);
			}
			wall(pose, vc, smoke, -w, y, w, y, alpha * RIM_ALPHA);
		}
	}

	private static float lerpWidth(float y0, float w0, float y1, float w1, float y) {
		return y1 == y0 ? w0 : w0 + (w1 - w0) * (y - y0) / (y1 - y0);
	}

	/** A flat quad on the face at depth z, drawn both ways round so it shows from either side. */
	private static void quad(PoseStack.Pose pose, VertexConsumer vc, float[] smoke, float x0, float y0, float x1, float y1,
			float x2, float y2, float x3, float y3, float z, float[] tint, float alpha) {
		float nz = z >= 0 ? 1 : -1;
		vertex(pose, vc, smoke, x0, y0, z, tint, alpha, 0, 0, nz);
		vertex(pose, vc, smoke, x1, y1, z, tint, alpha, 0, 0, nz);
		vertex(pose, vc, smoke, x2, y2, z, tint, alpha, 0, 0, nz);
		vertex(pose, vc, smoke, x3, y3, z, tint, alpha, 0, 0, nz);
		vertex(pose, vc, smoke, x3, y3, z, tint, alpha, 0, 0, -nz);
		vertex(pose, vc, smoke, x2, y2, z, tint, alpha, 0, 0, -nz);
		vertex(pose, vc, smoke, x1, y1, z, tint, alpha, 0, 0, -nz);
		vertex(pose, vc, smoke, x0, y0, z, tint, alpha, 0, 0, -nz);
	}

	/** The slab's edge between two outline points, across its thickness, both ways round. */
	private static void wall(PoseStack.Pose pose, VertexConsumer vc, float[] smoke, float x0, float y0, float x1, float y1, float alpha) {
		float dx = x1 - x0, dy = y1 - y0;
		float len = Math.max(1e-4f, Mth.sqrt(dx * dx + dy * dy));
		float nx = dy / len, ny = -dx / len;
		vertex(pose, vc, smoke, x0, y0, HALF_THICK, EDGE, alpha, nx, ny, 0);
		vertex(pose, vc, smoke, x1, y1, HALF_THICK, EDGE, alpha, nx, ny, 0);
		vertex(pose, vc, smoke, x1, y1, -HALF_THICK, EDGE, alpha, nx, ny, 0);
		vertex(pose, vc, smoke, x0, y0, -HALF_THICK, EDGE, alpha, nx, ny, 0);
		vertex(pose, vc, smoke, x0, y0, -HALF_THICK, EDGE, alpha, -nx, -ny, 0);
		vertex(pose, vc, smoke, x1, y1, -HALF_THICK, EDGE, alpha, -nx, -ny, 0);
		vertex(pose, vc, smoke, x1, y1, HALF_THICK, EDGE, alpha, -nx, -ny, 0);
		vertex(pose, vc, smoke, x0, y0, HALF_THICK, EDGE, alpha, -nx, -ny, 0);
	}

	private static void vertex(PoseStack.Pose pose, VertexConsumer vc, float[] smoke, float x, float y, float z,
			float[] tint, float alpha, float nx, float ny, float nz) {
		// The smoke frame is mapped flat across the shield by position, centred on it.
		float span = smoke[2] - 2 * INSET;
		float u = smoke[0] + INSET + span * Mth.clamp(0.5f + x / TILE, 0f, 1f);
		float v = smoke[1] + INSET + span * Mth.clamp(1f - y / TILE, 0f, 1f);
		vc.addVertex(pose, x, y, z)
				.setColor(tint[0], tint[1], tint[2], alpha)
				.setUv(u, v)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(FULL_BRIGHT)
				.setNormal(pose, nx, ny, nz);
	}
}
