package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.net.RingFxPayload;
import it.unimi.dsi.fastutil.ints.Int2LongMap;
import it.unimi.dsi.fastutil.ints.Int2LongOpenHashMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import org.joml.Matrix3f;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * The looks of pass 515 super speed, on every client, for every flyer in it (the flyer's client reports it,
 * SuperSpeedFlight, MoveFxPayload.SUPER) or in the ring glide; all scaled by speed above 30 b/s, in the ring's corps
 * colour, drawn shader-safe (entityTranslucentEmissive, ShaderGlow light):
 * <ul>
 * <li>the green light trail's 3 strands (FlightTrail, from {@link #amount});
 * <li>afterimages above 40 b/s: 4 construct copies of the flyer laid out in flight, alpha 0.22, 1 tick apart;
 * <li>the ground wake below 4 blocks: 4 grass and dirt pixels a tick kicked up in a V (30 degrees) behind, and a flat
 * construct ripple on the ground every 3 ticks, bigger the lower you fly;
 * <li>the ring's glow rising with speed (Blender 3 to 9; {@link #glow}, RingModels.glintBoost).
 * </ul>
 * S2's tap burst also booms with 16 pixels (SonicBoom).
 */
public final class SuperSpeedFx {
	/** Blocks a tick: the looks start above 30 b/s, the afterimages above 40, all full at 60. */
	private static final double LOOKS = 1.5, GHOSTS = 2.0, FULL = 3.0;
	/** The afterimages: how many, and how see-through. */
	private static final int GHOST_COUNT = 4;
	private static final float GHOST_ALPHA = 0.22f;
	/** The wake: under this height, pixels a tick, the V's half angle, a ripple every so many ticks and how long it lasts. */
	private static final double WAKE_HEIGHT = 4;
	private static final int WAKE_PIXELS = 4, RIPPLE_EVERY = 3, RIPPLE_LIFE = 11;
	private static final double WAKE_ANGLE = Math.toRadians(30);
	/** A remote flyer's report holds this long without a fresh one (it's re-sent every second). */
	private static final int REPORT_LAPSE = 30;

	/**
	 * The flyer laid out in flight, in blocks about the middle of the body, +z the way they fly and +y their back:
	 * {centre x, y, z, half x, y, z} for the head, body, ring arm reaching ahead, free arm along the side, and legs.
	 */
	private static final float[][] FIGURE = {
			{0f, 0f, 0.625f, 0.25f, 0.25f, 0.25f},
			{0f, 0f, 0f, 0.25f, 0.125f, 0.375f},
			{-0.375f, 0f, 0.625f, 0.125f, 0.125f, 0.375f},
			{0.375f, 0f, -0.125f, 0.125f, 0.125f, 0.375f},
			{-0.125f, 0f, -0.75f, 0.125f, 0.125f, 0.375f},
			{0.125f, 0f, -0.75f, 0.125f, 0.125f, 0.375f}};

	private record Ghost(Vec3 pos, Vec3 dir) {
	}

	private record Ripple(Vec3 at, Vec3 dir, float size, long start, Corps corps) {
	}

	private static final class Flyer {
		final ArrayDeque<Ghost> trail = new ArrayDeque<>();
		Corps corps = Corps.GREEN;
		double speed;
		int wake;
		boolean seen;
	}

	private static final Int2ObjectMap<Flyer> FLYERS = new Int2ObjectOpenHashMap<>();
	/** Remote flyers in super speed, by entity id: when their last report came (game time). */
	private static final Int2LongMap REPORTED = new Int2LongOpenHashMap();
	private static final List<Ripple> RIPPLES = new ArrayList<>();

	private SuperSpeedFx() {
	}

	/** SUPER_SPEED from the server (variant: the flyer). */
	static void handle(RingFxPayload fx) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		if (fx.value() > 0) REPORTED.put(fx.variant(), mc.level.getGameTime());
		else REPORTED.remove(fx.variant());
	}

	/** Whether this player is in super speed (your own straight from SuperSpeedFlight, anyone else's by report). */
	static boolean on(Player p) {
		Minecraft mc = Minecraft.getInstance();
		if (p == mc.player) return SuperSpeedFlight.active();
		return mc.level != null && REPORTED.containsKey(p.getId()) && mc.level.getGameTime() - REPORTED.get(p.getId()) < REPORT_LAPSE;
	}

	/** 0..1: how much of super speed's looks this speed (blocks a tick) makes: nothing at 30 b/s, all at 60. */
	static float amount(double speed) {
		return (float) Mth.clamp((speed - LOOKS) / (FULL - LOOKS), 0, 1);
	}

	/** 0..1: how much brighter this flyer's ring burns (RingModels.glintBoost): Blender's 3 to 9 with speed. */
	static float glow(Player p) {
		Flyer f = FLYERS.get(p.getId());
		return f == null ? 0f : amount(f.speed);
	}

	static void tick(Minecraft mc) {
		if (mc.level == null) {
			FLYERS.clear();
			REPORTED.clear();
			RIPPLES.clear();
			return;
		}
		long now = mc.level.getGameTime();
		RandomSource r = mc.level.getRandom();
		for (Flyer f : FLYERS.values()) f.seen = false;
		for (AbstractClientPlayer p : mc.level.players()) {
			Vec3 pos = p.position();
			Vec3 move = pos.subtract(p.xo, p.yo, p.zo);
			double speed = move.length();
			boolean flying = (on(p) || FlightPoses.fast(p) > 0.5f) && !p.onGround() && !p.isInWater() && !p.isPassenger() && !p.isSpectator();
			if (!flying || speed <= LOOKS) {
				Flyer gone = FLYERS.get(p.getId());
				if (gone != null) {
					gone.speed = 0;
					gone.trail.clear();
				}
				continue;
			}
			Flyer f = FLYERS.computeIfAbsent(p.getId(), k -> new Flyer());
			f.seen = true;
			f.corps = FlightTrail.ringCorps(p);
			f.speed = speed;
			Vec3 dir = move.normalize();
			f.trail.addFirst(new Ghost(pos, dir));
			while (f.trail.size() > GHOST_COUNT + 1) f.trail.removeLast();
			wake(mc, p, f, pos, dir, speed, now, r);
		}
		FLYERS.values().removeIf(f -> !f.seen);
		REPORTED.values().removeIf(t -> now - t > REPORT_LAPSE * 4L);
		RIPPLES.removeIf(rp -> now - rp.start > RIPPLE_LIFE);
	}

	/** Low and fast: dirt and grass kicked up in a V behind, and a construct ripple on the ground every few ticks. */
	private static void wake(Minecraft mc, Player p, Flyer f, Vec3 pos, Vec3 dir, double speed, long now, RandomSource r) {
		BlockHitResult down = mc.level.clip(new ClipContext(pos, pos.subtract(0, WAKE_HEIGHT, 0), ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p));
		if (down.getType() == HitResult.Type.MISS) return;
		double height = pos.y - down.getLocation().y;
		float k = (float) Mth.clamp(1 - height / WAKE_HEIGHT, 0, 1);
		float amount = amount(speed);
		Vec3 ground = down.getLocation();
		BlockPos below = down.getBlockPos();
		BlockState state = mc.level.getBlockState(below);
		Vec3 flat = new Vec3(dir.x, 0, dir.z);
		flat = flat.lengthSqr() < 1e-4 ? new Vec3(0, 0, 1) : flat.normalize();
		Vec3 side = new Vec3(-flat.z, 0, flat.x);
		// Where you passed over, a block behind you.
		Vec3 at = ground.subtract(flat.scale(1.0)).add(0, 0.05, 0);
		if (!state.isAir()) {
			for (int i = 0; i < WAKE_PIXELS; i++) {
				double s = i % 2 == 0 ? 1 : -1;
				double out = Math.sin(WAKE_ANGLE) * s, back = -Math.cos(WAKE_ANGLE);
				double push = (0.12 + 0.12 * r.nextDouble()) * (0.6 + k);
				Vec3 vel = side.scale(out * push).add(flat.scale(back * push * 0.5)).add(0, (0.12 + 0.12 * r.nextDouble()) * (0.6 + k), 0);
				mc.level.addParticle(new BlockParticleOption(ParticleTypes.BLOCK, state), at.x, at.y, at.z, vel.x, vel.y, vel.z);
			}
		}
		if (++f.wake >= RIPPLE_EVERY) {
			f.wake = 0;
			RIPPLES.add(new Ripple(at, flat, (0.5f + k) * (0.6f + 0.4f * amount), now, f.corps));
		}
	}

	public static void render(LevelRenderContext ctx) {
		if (FLYERS.isEmpty() && RIPPLES.isEmpty()) return;
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float partial = ctx.levelState().worldPartialTicks;
		float now = mc.level.getGameTime() + partial;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		ctx.submitNodeCollector().submitCustomGeometry(ctx.poseStack(), RenderTypes.entityTranslucentEmissive(TextureAtlas.LOCATION_BLOCKS), (pose, vc) -> {
			int light = ShaderGlow.light(0.8f);
			for (Flyer f : FLYERS.values()) {
				if (f.speed <= GHOSTS || f.trail.size() < 2) continue;
				TextureAtlasSprite s = SuperLandConstruct.sprite(ModRegistry.LIGHT_CONSTRUCT, f.corps);
				float[] tint = PowerLandingFx.bright(PowerLandingFx.tint(f.corps), 0.35f);
				float on = (float) Mth.clamp((f.speed - GHOSTS) / 0.25, 0, 1);
				Ghost[] g = f.trail.toArray(new Ghost[0]);
				// Copy i sits i ticks behind, moving with the flyer between ticks.
				for (int i = 1; i < g.length; i++) {
					Vec3 at = g[i].pos.lerp(g[i - 1].pos, partial);
					if (at.distanceToSqr(cam) < 2.25) continue;
					Quaternionf turn = facing(g[i].dir);
					float alpha = GHOST_ALPHA * on * (1f - 0.15f * (i - 1));
					for (float[] part : FIGURE) {
						Vector3f c = turn.transform(new Vector3f(part[0], part[1], part[2]));
						PowerLandingFx.cube(pose, vc, cam, at.add(c.x, c.y + 0.6, c.z), turn, part[3], part[4], part[5], s, 0f, 0f, 0.5f, tint, alpha, light);
					}
				}
			}
			for (Ripple rp : RIPPLES) {
				float t = Mth.clamp((now - rp.start) / RIPPLE_LIFE, 0f, 1f);
				TextureAtlasSprite s = SuperLandConstruct.sprite(ModRegistry.LIGHT_CONSTRUCT, rp.corps);
				ripple(pose, vc, cam, rp, s, PowerLandingFx.bright(PowerLandingFx.tint(rp.corps), 0.3f), t, light);
			}
		});
	}

	/** A flat construct ring on the ground growing out from where you passed (1.6 times longer along your way) and fading. */
	private static void ripple(com.mojang.blaze3d.vertex.PoseStack.Pose pose, com.mojang.blaze3d.vertex.VertexConsumer vc, Vec3 cam, Ripple rp,
			TextureAtlasSprite s, float[] tint, float t, int light) {
		float radius = (0.4f + 2.75f * t) * rp.size, width = 0.12f + 0.1f * rp.size;
		float alpha = 0.6f * (1 - t);
		if (alpha <= 0.02f) return;
		Vec3 u = rp.dir.scale(1.6), v = new Vec3(-rp.dir.z, 0, rp.dir.x);
		int count = 32;
		float[][] uv = {{s.getU0(), s.getV1()}, {s.getU1(), s.getV1()}, {s.getU1(), s.getV0()}, {s.getU0(), s.getV0()}};
		for (int i = 0; i < count; i++) {
			float a0 = i * Mth.TWO_PI / count, a1 = (i + 1) * Mth.TWO_PI / count;
			float in = Math.max(0f, radius - width);
			Vec3[] q = {
					rp.at.add(u.scale(Mth.cos(a0) * in)).add(v.scale(Mth.sin(a0) * in)),
					rp.at.add(u.scale(Mth.cos(a1) * in)).add(v.scale(Mth.sin(a1) * in)),
					rp.at.add(u.scale(Mth.cos(a1) * radius)).add(v.scale(Mth.sin(a1) * radius)),
					rp.at.add(u.scale(Mth.cos(a0) * radius)).add(v.scale(Mth.sin(a0) * radius))};
			for (int side = 0; side < 2; side++) {
				float f = side == 0 ? 1 : -1;
				for (int k = 0; k < 4; k++) {
					int idx = side == 0 ? k : 3 - k;
					PowerLandingFx.vertex(pose, vc, cam, (float) q[idx].x, (float) q[idx].y, (float) q[idx].z, uv[idx][0], uv[idx][1], tint, alpha, light,
							0f, f, 0f);
				}
			}
		}
	}

	/** The turn that lays the figure (+z ahead, +y up) along dir, its back to the sky. */
	private static Quaternionf facing(Vec3 dir) {
		Vector3f ahead = new Vector3f((float) dir.x, (float) dir.y, (float) dir.z).normalize();
		Vector3f up = Math.abs(ahead.y) > 0.95f ? new Vector3f(1, 0, 0) : new Vector3f(0, 1, 0);
		Vector3f side = new Vector3f(up).cross(ahead).normalize();
		Vector3f back = new Vector3f(ahead).cross(side).normalize();
		return new Matrix3f(side, back, ahead).getNormalizedRotation(new Quaternionf());
	}
}
