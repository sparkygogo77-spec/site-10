package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.corps.CorpsVillager;
import com.sparky.lanternring.net.DismissPayload;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

/**
 * Dismissing a construct into the ring, the end of every ring power: the construct comes apart from
 * its furthest piece to its nearest (the server takes the blocks away in that order, see Dismissal),
 * and each piece's light flies back as a streak that speeds up into the bearer's ring, which flares
 * as it takes the light in. The Lasso's bubble does the same (LassoFx.dismiss) through {@link #streak}.
 * <p>As each piece goes, a glowing copy of it dissolves where it stood: J's round-3 "fill3" dissolve
 * (tools/construct_picks.py), the light going pixel by pixel in random order behind a sparkling front.
 */
public final class DismissFx {
	private static final Identifier TEXTURE = LanternRing.id("textures/entity/flight_trail.png");
	/** 16 frames of one block face dissolving, stacked vertically (white; tinted by the corps). */
	private static final Identifier DISSOLVE = LanternRing.id("textures/entity/construct_dissolve.png");
	private static final int DISSOLVE_FRAMES = 16;
	/** How long a piece takes to dissolve, in ticks (J: slow and smooth). */
	private static final float DISSOLVE_TICKS = 14;
	/** OverlayTexture.NO_OVERLAY. */
	private static final int NO_OVERLAY = 10 << 16;
	/** How long one piece's light takes to fly home, in ticks. */
	private static final float FLY_TICKS = 6;
	/** The streak's length, as a share of the way home. */
	private static final double TAIL = 0.3;

	/** A piece of a dismissed construct waiting for its turn to come apart. */
	private record Piece(int bearer, Corps corps, Vec3 pos, float due, int faces) {
	}

	/** A piece dissolving where it stood; {@code faces} has a bit per Direction that shows (not against another piece). */
	private record Ghost(Corps corps, BlockPos pos, float start, int faces) {
	}

	/** Light on its way back into a ring. */
	private record Streak(int bearer, Corps corps, Vec3 from, float start, float size) {
	}

	private static final List<Piece> PIECES = new ArrayList<>();
	private static final List<Streak> STREAKS = new ArrayList<>();
	private static final List<Ghost> GHOSTS = new ArrayList<>();
	private static int clock;

	private DismissFx() {
	}

	public static void handle(DismissPayload payload) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null || payload.blocks().isEmpty()) return;
		Entity bearer = mc.level.getEntity(payload.bearer());
		if (bearer == null) return;
		// The same order and timing as the server: furthest first, the front sweeping home evenly.
		Vec3 eye = bearer.getEyePosition();
		double far = 0, near = Double.MAX_VALUE;
		for (BlockPos pos : payload.blocks()) {
			double d = Vec3.atCenterOf(pos).distanceTo(eye);
			far = Math.max(far, d);
			near = Math.min(near, d);
		}
		Set<BlockPos> all = new HashSet<>(payload.blocks());
		for (BlockPos pos : payload.blocks()) {
			Vec3 at = Vec3.atCenterOf(pos);
			double f = far - near < 1e-3 ? 1 : (far - at.distanceTo(eye)) / (far - near);
			int faces = 0;
			for (Direction d : Direction.values()) {
				if (!all.contains(pos.relative(d))) faces |= 1 << d.ordinal();
			}
			PIECES.add(new Piece(payload.bearer(), payload.corps(), at, clock + (float) (f * payload.ticks()), faces));
		}
	}

	/** One piece of light leaving {@code from} and flying back into the bearer's ring, starting {@code delay} ticks from now. */
	public static void streak(int bearer, Corps corps, Vec3 from, float delay, float size) {
		STREAKS.add(new Streak(bearer, corps, from, clock + delay, size));
	}

	public static void tick(Minecraft mc) {
		clock++;
		if (mc.level == null) {
			PIECES.clear();
			STREAKS.clear();
			GHOSTS.clear();
			return;
		}
		RandomSource r = mc.level.getRandom();
		for (Iterator<Piece> it = PIECES.iterator(); it.hasNext(); ) {
			Piece p = it.next();
			if (p.due > clock) continue;
			it.remove();
			GHOSTS.add(new Ghost(p.corps, BlockPos.containing(p.pos), p.due, p.faces));
			streak(p.bearer, p.corps, p.pos.add(LabFx.jitter(r, 0.6)), p.due - clock, 1f);
			// The piece breaks into a few motes where it stood.
			if (r.nextInt(3) == 0) {
				Corps before = CorpsTint.enter(p.corps);
				LabFx.spawn(ModParticles.MOTE, p.pos.add(LabFx.jitter(r, 0.8)), LabFx.jitter(r, 0.04), 0.6f);
				CorpsTint.restore(before);
			}
		}
		for (Iterator<Streak> it = STREAKS.iterator(); it.hasNext(); ) {
			Streak s = it.next();
			if (clock - s.start < FLY_TICKS) continue;
			it.remove();
			// The ring flares as it takes the light back in (drawn with the hand, so it shows in first person).
			if (mc.level.getEntity(s.bearer) instanceof Player p) RingEmit.flare(p);
		}
		GHOSTS.removeIf(g -> clock - g.start >= DISSOLVE_TICKS);
	}

	/** Where this bearer's ring is this frame: a player's as drawn, a corps villager's on its hand. */
	static Vec3 ringOf(Entity bearer, float partial, Vec3 toward) {
		if (bearer instanceof Player p) return RingEmit.ringNow(p, partial);
		if (bearer instanceof LivingEntity l) return CorpsVillager.ringPos(l, partial, toward);
		return bearer.getEyePosition(partial);
	}

	public static void render(LevelRenderContext context) {
		if (STREAKS.isEmpty() && GHOSTS.isEmpty()) return;
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float partial = mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);
		Vec3 camera = context.levelState().cameraRenderState.pos;
		if (!GHOSTS.isEmpty()) renderGhosts(context, camera, clock + partial);
		if (STREAKS.isEmpty()) return;
		RenderType type = RenderTypes.entityTranslucentEmissive(TEXTURE);
		float now = clock + partial;
		context.submitNodeCollector().submitCustomGeometry(context.poseStack(), type, (pose, buffer) -> {
			for (Streak s : STREAKS) {
				float t = (now - s.start) / FLY_TICKS;
				if (t <= 0 || t >= 1) continue;
				Entity bearer = mc.level.getEntity(s.bearer);
				if (bearer == null) continue;
				Vec3 ring = ringOf(bearer, partial, s.from);
				// It speeds up as the ring pulls it in.
				double head = t * t;
				double tail = Math.max(0, head - TAIL * (0.3 + t));
				Vec3 a = s.from.lerp(ring, tail), b = s.from.lerp(ring, head);
				float fade = Mth.clamp((1 - t) * 4, 0, 1) * Mth.clamp(t * 6, 0, 1);
				float[] c = CorpsTint.apply(s.corps, 0.35f, 1f, 0.5f);
				float w = 0.12f * s.size;
				line(pose, buffer, a, b, camera, w * 2.4f, c[0], c[1], c[2], 0.4f * fade);
				line(pose, buffer, a, b, camera, w, Mth.lerp(0.55f, c[0], 1f), Mth.lerp(0.55f, c[1], 1f), Mth.lerp(0.55f, c[2], 1f), fade);
			}
		});
	}

	private static void renderGhosts(LevelRenderContext context, Vec3 camera, float now) {
		context.submitNodeCollector().submitCustomGeometry(context.poseStack(), RenderTypes.entityTranslucentEmissive(DISSOLVE), (pose, buffer) -> {
			for (Ghost g : GHOSTS) {
				float t = (now - g.start) / DISSOLVE_TICKS;
				if (t < 0 || t >= 1) continue;
				int frame = Math.min(DISSOLVE_FRAMES - 1, (int) (t * DISSOLVE_FRAMES));
				float v0 = frame / (float) DISSOLVE_FRAMES, v1 = (frame + 1) / (float) DISSOLVE_FRAMES;
				float[] c = CorpsTint.apply(g.corps, 0.35f, 1f, 0.5f);
				float r = c[0], gr = c[1], b = c[2];
				for (Direction d : Direction.values()) {
					if ((g.faces & 1 << d.ordinal()) == 0) continue;
					face(pose, buffer, g.pos, d, camera, v0, v1, r, gr, b);
				}
			}
		});
	}

	/** One face of a dissolving piece, a hair outside the block, wound to face outward. */
	private static void face(PoseStack.Pose pose, VertexConsumer buffer, BlockPos pos, Direction d, Vec3 camera,
			float v0, float v1, float r, float g, float b) {
		int a = d.getAxis().ordinal();
		int s1 = d.getAxisDirection() == Direction.AxisDirection.POSITIVE ? (a + 1) % 3 : (a + 2) % 3;
		int s2 = d.getAxisDirection() == Direction.AxisDirection.POSITIVE ? (a + 2) % 3 : (a + 1) % 3;
		double grow = 0.002;
		double[] centre = {pos.getX() + 0.5 - camera.x, pos.getY() + 0.5 - camera.y, pos.getZ() + 0.5 - camera.z};
		centre[a] += (0.5 + grow) * d.getAxisDirection().getStep();
		float[][] corners = {{-1, -1, 0, v1}, {1, -1, 1, v1}, {1, 1, 1, v0}, {-1, 1, 0, v0}};
		for (float[] k : corners) {
			double[] p = centre.clone();
			p[s1] += k[0] * (0.5 + grow);
			p[s2] += k[1] * (0.5 + grow);
			buffer.addVertex(pose, (float) p[0], (float) p[1], (float) p[2])
					.setColor(r, g, b, 1f)
					.setUv(k[2], k[3])
					.setOverlay(NO_OVERLAY)
					.setLight(ShaderGlow.light(0.8f))
					.setNormal(pose, d.getStepX(), d.getStepY(), d.getStepZ());
		}
	}

	/** A camera-facing strip from a (thin) to b (full width), so it reads as light moving toward b. */
	private static void line(PoseStack.Pose pose, VertexConsumer buffer, Vec3 a, Vec3 b, Vec3 camera, float half,
			float r, float g, float bl, float alpha) {
		if (alpha < 0.1f) return;
		Vec3 along = b.subtract(a);
		if (along.lengthSqr() < 1e-6) return;
		Vec3 side = along.cross(camera.subtract(b));
		if (side.lengthSqr() < 1e-8) return;
		side = side.normalize();
		// Right at the camera (your own ring) it thins out instead of filling the screen.
		float near = Mth.clamp((float) (b.distanceTo(camera) - 0.3) / 1.2f, 0.25f, 1f);
		Vec3 sa = side.scale(half * 0.3 * near), sb = side.scale(half * near);
		vertex(pose, buffer, a.subtract(sa), camera, 0, 1, r, g, bl, alpha * 0.5f);
		vertex(pose, buffer, a.add(sa), camera, 0, 0, r, g, bl, alpha * 0.5f);
		vertex(pose, buffer, b.add(sb), camera, 1, 0, r, g, bl, alpha);
		vertex(pose, buffer, b.subtract(sb), camera, 1, 1, r, g, bl, alpha);
	}

	private static void vertex(PoseStack.Pose pose, VertexConsumer buffer, Vec3 p, Vec3 camera, float u, float v,
			float r, float g, float b, float a) {
		buffer.addVertex(pose, (float) (p.x - camera.x), (float) (p.y - camera.y), (float) (p.z - camera.z))
				.setColor(r, g, b, a)
				.setUv(u, v)
				.setOverlay(NO_OVERLAY)
				.setLight(ShaderGlow.light(0.9f))
				.setNormal(pose, 0, 1, 0);
	}
}
