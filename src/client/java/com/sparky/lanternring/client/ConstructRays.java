package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.block.ConstructBrickBlock;
import com.sparky.lanternring.block.LightConstructBlock;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/**
 * Light round the block constructs (Walls, Domes, held shapes, builds): Blender pass 305 D2 "shafts+", J's keep
 * (2026-10-15), which is pass 304's L2 shafts with the detail. Every side glows, the glow fading out over 4 blocks;
 * each open side throws a row of narrow beams (16° wide, fanned up to 14° apart) through a haze that is thickest at
 * the construct and thins to nothing by 6 blocks, so the beams fade instead of lighting the sky; and dust motes
 * drift slowly in the light (tiny MOTE particles). The Blender scene's block-grid ground and figure were only for
 * scale. Ring Lab "Construct light rays" (D2 or Off).
 *
 * <p>The client finds constructs through their animateTick (LabFx.constructAmbient): the first block seen pulls in the
 * construct blocks joined to it, and each block is dropped once it is gone. Additive light without a shader pack;
 * under one, see-through emissive like LaserBeams (additive draws black there). Colours follow each block's corps.
 */
public final class ConstructRays {
	private static final Identifier HAZE = LanternRing.id("textures/misc/laser/laser_haze.png");
	private static final Identifier GLOW = LanternRing.id("textures/misc/laser/laser_flare.png");
	private static final float GREEN_R = 0.3f, GREEN_G = 1f, GREEN_B = 0.45f;
	/** How far the glow reaches from a construct, in blocks. */
	private static final float REACH = 4f;
	/** How far a beam shows before the haze runs out. */
	private static final float BEAM = 6f;
	/** A beam's half-angle (Blender's 16° spot) and how far apart a side's beams fan. */
	private static final float HALF_ANGLE = 8f * Mth.DEG_TO_RAD;
	private static final float FAN = 14f * Mth.DEG_TO_RAD;
	/** Half the glow's strength next to the beams (L2: "glow at half strength so the beams read"). */
	private static final float GLOW_STRENGTH = 0.11f;
	private static final float BEAM_STRENGTH = 0.32f;
	/**
	 * Under a shader pack (J's glow bug, 2026-10-15): the see-through quads stack into a pale green haze and the
	 * patched pack blooms each one, so the round glow is left to the pack's own block light, fewer and fainter beams
	 * show, they are shorter, and they bloom softly.
	 */
	private static final float PACK_BEAM_STRENGTH = 0.4f, PACK_BEAM = 4f, PACK_LIGHT = 0.5f;
	private static final int BEAM_SHARE = 72, PACK_BEAM_SHARE = 30;
	/** A beam passing this close to the eye fades out, so none sweeps across the view as a flat pane. */
	private static final double EYE_CLEAR = 1.5, EYE_FADE = 2.5;
	/** Blocks pulled in from one sighting, blocks kept in all, and how far from the camera they are drawn. */
	private static final int FLOOD = 512;
	private static final int MAX_BLOCKS = 1500;
	private static final double DRAW_RANGE = 48;
	/** Dust motes per construct block per tick, and at most this many a tick in all. */
	private static final float MOTE_CHANCE = 0.08f;
	private static final int MOTES_PER_TICK = 4;

	/** One construct block: its corps, its share of the glow where several overlap, and which sides are open. */
	private static final class Lit {
		final Corps corps;
		float share = 1f;
		int open;

		Lit(Corps corps) {
			this.corps = corps;
		}
	}

	private static final Map<BlockPos, Lit> BLOCKS = new HashMap<>();
	private static boolean dirty;

	private ConstructRays() {
	}

	private static boolean on() {
		return LabSettings.get().constructRays == LabSettings.ConstructRays.D2;
	}

	static boolean isConstruct(BlockState state) {
		return state.getBlock() instanceof LightConstructBlock || state.getBlock() instanceof ConstructBrickBlock;
	}

	/** A construct block ticked on this client: track it and every construct block joined to it. */
	public static void seen(Level level, BlockPos pos) {
		if (!on() || BLOCKS.containsKey(pos) || BLOCKS.size() >= MAX_BLOCKS) return;
		ArrayDeque<BlockPos> queue = new ArrayDeque<>();
		queue.add(pos.immutable());
		int added = 0;
		while (!queue.isEmpty() && added < FLOOD && BLOCKS.size() < MAX_BLOCKS) {
			BlockPos at = queue.poll();
			if (BLOCKS.containsKey(at)) continue;
			BlockState state = level.getBlockState(at);
			if (!isConstruct(state)) continue;
			BLOCKS.put(at, new Lit(Corps.of(state)));
			added++;
			for (Direction d : Direction.values()) {
				BlockPos next = at.relative(d);
				if (!BLOCKS.containsKey(next)) queue.add(next);
			}
		}
		dirty = true;
	}

	static void tick(Minecraft mc, RandomSource r) {
		if (mc.level == null || mc.player == null || !on()) {
			BLOCKS.clear();
			return;
		}
		if (BLOCKS.isEmpty()) return;
		Level level = mc.level;
		Vec3 eye = mc.player.getEyePosition();
		if (mc.level.getGameTime() % 10 == 0 || dirty) {
			int before = BLOCKS.size();
			BLOCKS.entrySet().removeIf(e -> !isConstruct(level.getBlockState(e.getKey())) || Vec3.atCenterOf(e.getKey()).distanceToSqr(eye) > 96 * 96);
			if (BLOCKS.size() != before || dirty) relight(level);
			dirty = false;
		}
		// Dust motes hanging in the light: tiny, slow, rising a little (the Blender scene's 170 drifting pixels).
		int left = LabFx.count(MOTES_PER_TICK);
		for (Map.Entry<BlockPos, Lit> e : BLOCKS.entrySet()) {
			if (left <= 0) break;
			if (e.getValue().open == 0 || r.nextFloat() >= MOTE_CHANCE) continue;
			Vec3 c = Vec3.atCenterOf(e.getKey());
			if (c.distanceToSqr(eye) > DRAW_RANGE * DRAW_RANGE) continue;
			Vec3 at = c.add((r.nextDouble() - 0.5) * 5, -0.5 + r.nextDouble() * 4.5, (r.nextDouble() - 0.5) * 5);
			if (!level.getBlockState(BlockPos.containing(at)).isAir()) continue;
			Corps before = CorpsTint.enter(e.getValue().corps);
			ConstructParticle p = LabFx.spawn(ModParticles.MOTE, at,
					new Vec3((r.nextDouble() - 0.5) * 0.006, 0.002 + r.nextDouble() * 0.003, (r.nextDouble() - 0.5) * 0.006), 0.3f);
			if (p != null) p.lasting(60 + r.nextInt(60));
			CorpsTint.restore(before);
			left--;
		}
	}

	/** Which sides of each block are open to the air, and how much of the glow each gives where many overlap. */
	private static void relight(Level level) {
		for (Map.Entry<BlockPos, Lit> e : BLOCKS.entrySet()) {
			BlockPos pos = e.getKey();
			Lit lit = e.getValue();
			lit.open = 0;
			for (Direction d : Direction.values()) {
				BlockPos n = pos.relative(d);
				if (!BLOCKS.containsKey(n) && level.getBlockState(n).isAir()) lit.open |= 1 << d.ordinal();
			}
			int near = 0;
			for (int dx = -3; dx <= 3; dx++) {
				for (int dy = -3; dy <= 3; dy++) {
					for (int dz = -3; dz <= 3; dz++) {
						if (dx * dx + dy * dy + dz * dz <= 9 && BLOCKS.containsKey(pos.offset(dx, dy, dz))) near++;
					}
				}
			}
			lit.share = Math.min(1f, 6f / Math.max(1, near));
		}
	}

	public static void render(LevelRenderContext ctx) {
		if (BLOCKS.isEmpty() || !on()) return;
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		Vec3 camera = ctx.levelState().cameraRenderState.pos;
		float time = mc.level.getGameTime() + ctx.levelState().worldPartialTicks;
		boolean pack = SoulSight.shaderPackOn();
		List<Map.Entry<BlockPos, Lit>> shown = new ArrayList<>();
		for (Map.Entry<BlockPos, Lit> e : BLOCKS.entrySet()) {
			if (e.getValue().open != 0 && Vec3.atCenterOf(e.getKey()).distanceToSqr(camera) < DRAW_RANGE * DRAW_RANGE) shown.add(e);
		}
		if (shown.isEmpty()) return;
		if (!pack) {
			submit(ctx, GLOW, pack, (pose, buf) -> {
				for (Map.Entry<BlockPos, Lit> e : shown) glow(pose, buf, e.getKey(), e.getValue(), camera, pack);
			});
		}
		submit(ctx, HAZE, pack, (pose, buf) -> {
			for (Map.Entry<BlockPos, Lit> e : shown) {
				for (Direction d : Direction.values()) {
					if ((e.getValue().open & 1 << d.ordinal()) != 0) beam(pose, buf, e.getKey(), d, e.getValue(), camera, time, pack);
				}
			}
		});
	}

	/** The glow round one block: a soft round light 2 x REACH + 1 blocks across, facing the camera. */
	private static void glow(PoseStack.Pose pose, VertexConsumer buf, BlockPos pos, Lit lit, Vec3 camera, boolean pack) {
		Vec3 at = Vec3.atCenterOf(pos);
		Vec3 view = camera.subtract(at);
		double dist = view.length();
		if (dist < 1e-3) return;
		view = view.scale(1 / dist);
		Vec3 right = view.cross(new Vec3(0, 1, 0));
		right = right.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : right.normalize();
		Vec3 up = right.cross(view).normalize();
		float half = REACH + 0.5f;
		// Inside the glow it would fill the screen: fade it as the camera comes within a block or two.
		float k = GLOW_STRENGTH * lit.share * Mth.clamp((float) (dist - 1.0) / 2f, 0f, 1f);
		if (k <= 0.002f) return;
		float[] c = CorpsTint.apply(lit.corps, GREEN_R, GREEN_G, GREEN_B);
		Vec3 r = right.scale(half), u = up.scale(half);
		vertex(pose, buf, at.subtract(r).subtract(u), camera, 0, 1, c, k, pack);
		vertex(pose, buf, at.add(r).subtract(u), camera, 1, 1, c, k, pack);
		vertex(pose, buf, at.add(r).add(u), camera, 1, 0, c, k, pack);
		vertex(pose, buf, at.subtract(r).add(u), camera, 0, 0, c, k, pack);
	}

	/**
	 * One narrow beam out of an open side, or none: about three sides in four throw one, so a row of them reads along
	 * a Wall. Each leans a little off the side (fanned up to FAN, as Blender's rows), widens at HALF_ANGLE and fades
	 * out by BEAM blocks.
	 */
	private static void beam(PoseStack.Pose pose, VertexConsumer buf, BlockPos pos, Direction side, Lit lit, Vec3 camera, float time, boolean pack) {
		long h = hash(pos.getX() * 3129871L ^ pos.getZ() * 116129781L ^ pos.getY() ^ side.ordinal() * 0x9E3779B97F4A7C15L);
		if (Math.floorMod(h, 100) >= (pack ? PACK_BEAM_SHARE : BEAM_SHARE)) return;
		float a = ((h >>> 8 & 0xFF) / 255f - 0.5f) * 2f;
		float b = ((h >>> 16 & 0xFF) / 255f - 0.5f) * 2f;
		Vec3 n = new Vec3(side.getStepX(), side.getStepY(), side.getStepZ());
		// Two directions across the side: the fan swings along the first, a smaller tilt along the second.
		Vec3 across1 = side.getAxis() == Direction.Axis.Y ? new Vec3(1, 0, 0) : new Vec3(0, 1, 0).cross(n);
		Vec3 across2 = n.cross(across1);
		Vec3 dir = n.add(across1.scale(Math.tan(FAN * a))).add(across2.scale(Math.tan(FAN * 0.7f * b))).normalize();
		Vec3 base = Vec3.atCenterOf(pos).add(n.scale(0.52)).add(across1.scale(0.3 * b)).add(across2.scale(0.3 * a));
		// A slow shimmer in the haze, never fully steady.
		float shimmer = 0.85f + 0.15f * Mth.sin(time * 0.05f + (h & 0xFF));
		float k = (pack ? PACK_BEAM_STRENGTH * BEAM_STRENGTH : BEAM_STRENGTH) * shimmer
				* Mth.clamp((float) (base.distanceTo(camera) - 0.8) / 1.5f, 0f, 1f);
		float length = pack ? PACK_BEAM : BEAM;
		if (k <= 0.002f) return;
		float[] c = CorpsTint.apply(lit.corps, GREEN_R, GREEN_G, GREEN_B);
		int segments = 4;
		for (int i = 0; i < segments; i++) {
			float s0 = length * i / segments, s1 = length * (i + 1) / segments;
			Vec3 p0 = base.add(dir.scale(s0)), p1 = base.add(dir.scale(s1));
			float clear = eyeClear(p0, p1, camera);
			if (clear <= 0.002f) continue;
			Vec3 side0 = width(p0, dir, camera, 0.18 + s0 * Math.tan(HALF_ANGLE));
			Vec3 side1 = width(p1, dir, camera, 0.18 + s1 * Math.tan(HALF_ANGLE));
			// The haze thins with distance: strongest at the construct, a trace by BEAM blocks.
			float k0 = k * clear * fade(s0 / length), k1 = k * clear * fade(s1 / length);
			vertex(pose, buf, p0.subtract(side0), camera, 0, 0, c, k0, pack);
			vertex(pose, buf, p0.add(side0), camera, 1, 0, c, k0, pack);
			vertex(pose, buf, p1.add(side1), camera, 1, 1, c, k1, pack);
			vertex(pose, buf, p1.subtract(side1), camera, 0, 1, c, k1, pack);
		}
	}

	/** A well-mixed hash (splitmix64's finaliser), so neighbouring sides pick unrelated beams. */
	private static long hash(long z) {
		z = (z ^ z >>> 30) * 0xBF58476D1CE4E5B9L;
		z = (z ^ z >>> 27) * 0x94D049BB133111EBL;
		return z ^ z >>> 31;
	}

	/** How far along the beam (0..1) to how strong its haze is there. */
	private static float fade(float s) {
		float t = 1f - s;
		return t * t;
	}

	/** 1 for a beam segment well clear of the eye, falling to 0 as it passes within EYE_CLEAR blocks of it. */
	private static float eyeClear(Vec3 p0, Vec3 p1, Vec3 camera) {
		Vec3 seg = p1.subtract(p0);
		double t = Mth.clamp(camera.subtract(p0).dot(seg) / Math.max(1e-6, seg.lengthSqr()), 0, 1);
		double d = p0.add(seg.scale(t)).distanceTo(camera);
		return Mth.clamp((float) ((d - EYE_CLEAR) / EYE_FADE), 0f, 1f);
	}

	/** Half the beam's width across it at {@code p}, turned to face the camera. */
	private static Vec3 width(Vec3 p, Vec3 dir, Vec3 camera, double half) {
		Vec3 side = dir.cross(camera.subtract(p));
		if (side.lengthSqr() < 1e-6) side = dir.cross(new Vec3(0, 1, 0));
		if (side.lengthSqr() < 1e-6) side = new Vec3(1, 0, 0);
		return side.normalize().scale(half);
	}

	private static void submit(LevelRenderContext ctx, Identifier texture, boolean pack, Geometry geometry) {
		RenderType type = pack ? RenderTypes.entityTranslucentEmissive(texture) : RenderTypes.energySwirl(texture, 0, 0);
		ctx.submitNodeCollector().submitCustomGeometry(ctx.poseStack(), type, geometry::draw);
	}

	@FunctionalInterface
	private interface Geometry {
		void draw(PoseStack.Pose pose, VertexConsumer buffer);
	}

	/** Additive: the brightness rides in the colour. Under a shader pack it becomes how see-through it is (as LaserBeams). */
	private static void vertex(PoseStack.Pose pose, VertexConsumer buf, Vec3 p, Vec3 camera, float u, float v, float[] c, float strength, boolean pack) {
		float k = pack ? 1f : strength;
		float a = pack ? Mth.clamp(strength * 0.6f, 0f, 1f) : 1f;
		buf.addVertex(pose, (float) (p.x - camera.x), (float) (p.y - camera.y), (float) (p.z - camera.z))
				.setColor(c[0] * k, c[1] * k, c[2] * k, a)
				.setUv(u, v)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(pack ? ShaderGlow.light(PACK_LIGHT) : ShaderGlow.light())
				.setNormal(pose, 0, 1, 0);
	}
}
