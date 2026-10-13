package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.mojang.math.Axis;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RamBarrier;
import com.sparky.lanternring.net.RingFxPayload;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.util.EnumMap;
import java.util.Map;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.Vec3;

/**
 * Draws fast flight's ram barrier ({@link RamBarrier}): a thin cap of hard light the Dome's size
 * held out ahead of the flyer, a faint sheet with bright edges and motes of light drifting off it,
 * in their ring's corps colour. It shatters into shards when it hits a wall.
 *
 * <p><b>Model hook.</b> J's barrier is being modelled in Blender. Until it lands this draws a
 * placeholder mesh. To swap the real one in, export it as {@code bbmodel/ram_barrier.bbmodel}
 * (texture {@code textures/entity/bb/ram_barrier.png}) with its origin at the flyer's middle,
 * facing north (Blockbench -Z) and sized for a 4.5 block radius; {@link #model} then finds it and
 * draws it instead of the placeholder, turned to face the way the flyer is going. Glow cubes go
 * through the pack-safe path, so it blooms under the patched Complementary pack.
 */
public final class RamBarrierFx {
	private static final Identifier GLASS = LanternRing.id("textures/entity/shockwave_glass.png");
	private static final String MODEL = "ram_barrier";
	/** Ticks the shell takes to fade in and out. */
	private static final float FADE_IN = 6f;
	private static final float FADE_OUT = 5f;
	/** A barrier not re-announced for this long is dropped (its "gone" may have been missed). */
	private static final int STALE = 30;
	private static final int RINGS = 12;
	private static final int SEGMENTS = 40;
	/** How see-through the sheet is: a thin field, not the Dome's solid blocks. */
	private static final float BODY_ALPHA = 0.09f;
	private static final float RIM_ALPHA = 0.85f;
	/** Your own barrier is fainter, so it doesn't fill your view. */
	private static final float OWN = 0.45f;
	private static final int FRAMES = 64;
	private static final int GRID = 8;
	private static final int FRAME_TICKS = 2;

	private static final class Barrier {
		Vec3 dir;
		Corps corps;
		int lastSeen;
		float shown;
		boolean up;
	}

	private static final Int2ObjectMap<Barrier> BARRIERS = new Int2ObjectOpenHashMap<>();
	private static final Map<Corps, BbModel> MODELS = new EnumMap<>(Corps.class);
	private static Boolean hasModel;
	private static int clock;

	private RamBarrierFx() {
	}

	/** RAM_BARRIER, RAM_HIT and RAM_BREAK, while LabFx has the effect's corps current. */
	static void handle(RingFxPayload fx) {
		Minecraft mc = Minecraft.getInstance();
		switch (fx.kind()) {
			case RAM_BARRIER -> {
				Barrier b = BARRIERS.get(fx.variant());
				if (fx.value() <= 0) {
					if (b != null) b.up = false;
					return;
				}
				if (b == null) BARRIERS.put(fx.variant(), b = new Barrier());
				Vec3 d = fx.to().subtract(fx.from());
				if (d.lengthSqr() > 1e-4) b.dir = d.normalize();
				else if (b.dir == null) b.dir = new Vec3(0, 0, 1);
				b.corps = CorpsTint.current();
				b.lastSeen = clock;
				b.up = true;
			}
			case RAM_HIT -> {
				LabFx.burst(fx.from(), 28, 0.3 + fx.value() * 0.08);
				RingShake.impact(fx);
			}
			case RAM_BREAK -> {
				Barrier b = BARRIERS.remove(fx.variant());
				Entity flyer = mc.level.getEntity(fx.variant());
				if (flyer != null && b != null) shatter(flyer.getBoundingBox().getCenter(), b.dir);
				LabFx.burst(fx.from(), 60, 0.5);
				if (mc.player != null && mc.player.getId() == fx.variant()) {
					FastFlight.stop(mc.player);
					RingShake.kick(2.2f);
				}
			}
			default -> {
			}
		}
	}

	/** The whole shell bursts into shards flying out off its face. */
	private static void shatter(Vec3 mid, Vec3 dir) {
		RandomSource r = Minecraft.getInstance().level.getRandom();
		Vec3[] basis = basis(dir);
		for (int i = 0; i < LabFx.count(70); i++) {
			Vec3 out = onCap(basis, r.nextFloat(), r.nextFloat());
			LabFx.spawn(i % 2 == 0 ? ModParticles.SHARD : ModParticles.MOTE, mid.add(out.scale(RamBarrier.RADIUS)),
					out.scale(0.15 + r.nextDouble() * 0.25).add(LabFx.jitter(r, 0.1)), 1.2f);
		}
	}

	static void tick(Minecraft mc) {
		if (mc.level == null) {
			BARRIERS.clear();
			return;
		}
		if (mc.isPaused()) return;
		clock++;
		RandomSource r = mc.level.getRandom();
		var it = BARRIERS.int2ObjectEntrySet().iterator();
		while (it.hasNext()) {
			var e = it.next();
			Barrier b = e.getValue();
			Entity flyer = mc.level.getEntity(e.getIntKey());
			if (flyer == null || clock - b.lastSeen > STALE) b.up = false;
			b.shown = b.up ? Math.min(1f, b.shown + 1f / FADE_IN) : b.shown - 1f / FADE_OUT;
			if (b.shown <= 0 || flyer == null) {
				it.remove();
				continue;
			}
			// Steer by the flyer's own motion here, so the shell turns with them between updates.
			Vec3 move = flyer.position().subtract(flyer.xo, flyer.yo, flyer.zo);
			if (move.length() > 0.3) b.dir = b.dir.scale(0.5).add(move.normalize().scale(0.5)).normalize();
			// The field sheds motes of light that stream off past its edge.
			Corps before = CorpsTint.enter(b.corps);
			try {
				Vec3 mid = flyer.getBoundingBox().getCenter();
				Vec3[] basis = basis(b.dir);
				for (int i = 0; i < LabFx.count(4 * b.shown); i++) {
					Vec3 out = onCap(basis, r.nextFloat(), r.nextFloat());
					LabFx.spawn(ModParticles.MOTE, mid.add(out.scale(RamBarrier.RADIUS)), move.scale(0.7).add(LabFx.jitter(r, 0.04)), 0.7f);
				}
			} finally {
				CorpsTint.restore(before);
			}
		}
	}

	/** Right, up and forward for a shell facing dir. */
	private static Vec3[] basis(Vec3 dir) {
		Vec3 up = Math.abs(dir.y) > 0.95 ? new Vec3(1, 0, 0) : new Vec3(0, 1, 0);
		Vec3 right = dir.cross(up).normalize();
		return new Vec3[] {right, right.cross(dir).normalize(), dir};
	}

	/** A unit direction on the cap: a is 0 at its middle to 1 at its rim, b goes round. */
	private static Vec3 onCap(Vec3[] basis, double a, double b) {
		double theta = Math.acos(RamBarrier.CAP_COS) * a;
		double phi = b * Math.PI * 2;
		double s = Math.sin(theta);
		return basis[0].scale(s * Math.cos(phi)).add(basis[1].scale(s * Math.sin(phi))).add(basis[2].scale(Math.cos(theta)));
	}

	public static void render(LevelRenderContext ctx) {
		if (BARRIERS.isEmpty()) return;
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		float partial = ctx.levelState().worldPartialTicks;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		LocalPlayer self = mc.player;
		float now = mc.level.getGameTime() + partial;
		for (Int2ObjectMap.Entry<Barrier> e : BARRIERS.int2ObjectEntrySet()) {
			Barrier b = e.getValue();
			Entity flyer = mc.level.getEntity(e.getIntKey());
			if (flyer == null) continue;
			float fade = Mth.clamp(b.shown + (b.up ? partial / FADE_IN : -partial / FADE_OUT), 0f, 1f);
			if (fade <= 0) continue;
			if (flyer == self) fade *= OWN;
			Vec3 mid = flyer.getPosition(partial).add(0, flyer.getBbHeight() / 2, 0);
			PoseStack pose = ctx.poseStack();
			pose.pushPose();
			pose.translate(mid.x - cam.x, mid.y - cam.y, mid.z - cam.z);
			BbModel model = model(b.corps);
			if (model != null) {
				// J's model faces north (-Z): turn it to the flight's heading, then tip it up or down.
				float yaw = (float) Math.toDegrees(Math.atan2(-b.dir.x, -b.dir.z));
				float pitch = (float) Math.toDegrees(Math.asin(Mth.clamp(b.dir.y, -1, 1)));
				pose.rotateDegrees(Axis.YP, yaw);
				pose.rotateDegrees(Axis.XP, pitch);
				model.renderPackSafe(pose, ctx.submitNodeCollector(), ShaderGlow.light(), BbModel.glow(fade), 1f, fade);
			} else {
				Vec3[] basis = basis(b.dir);
				Vec3 eye = cam.subtract(mid);
				int frame = Math.floorMod((int) (now / FRAME_TICKS), FRAMES);
				float f = fade;
				RenderType glass = RenderTypes.entityTranslucentEmissive(CorpsTint.texture(GLASS, b.corps));
				ctx.submitNodeCollector().submitCustomGeometry(pose, glass, (p, vc) -> shell(p, vc, basis, eye, f, frame, now));
			}
			pose.popPose();
		}
	}

	/** J's Blender barrier for this corps once it is in the jar, else null (the placeholder is drawn). */
	private static BbModel model(Corps corps) {
		if (hasModel == null) {
			hasModel = RamBarrierFx.class.getResource("/assets/" + LanternRing.MOD_ID + "/bbmodel/" + MODEL + ".bbmodel") != null;
		}
		if (!hasModel) return null;
		return MODELS.computeIfAbsent(corps, c -> BbModel.load(MODEL).forCorps(c));
	}

	/** The placeholder: a thin see-through cap with bright edges and a ripple running out across it. */
	private static void shell(PoseStack.Pose pose, VertexConsumer vc, Vec3[] basis, Vec3 eye, float fade, int frame, float now) {
		float cell = 1f / GRID;
		float fu = (frame % GRID) * cell, fv = (frame / GRID) * cell;
		for (int ring = 0; ring < RINGS; ring++) {
			float a0 = ring / (float) RINGS, a1 = (ring + 1) / (float) RINGS;
			for (int seg = 0; seg < SEGMENTS; seg++) {
				float b0 = seg / (float) SEGMENTS, b1 = (seg + 1) / (float) SEGMENTS;
				float u0 = fu + cell * (seg % 4) / 4f, u1 = fu + cell * (seg % 4 + 1) / 4f;
				float v0 = fv + cell * (ring % 4) / 4f, v1 = fv + cell * (ring % 4 + 1) / 4f;
				vertex(pose, vc, basis, eye, fade, now, a0, b0, u0, v0);
				vertex(pose, vc, basis, eye, fade, now, a1, b0, u0, v1);
				vertex(pose, vc, basis, eye, fade, now, a1, b1, u1, v1);
				vertex(pose, vc, basis, eye, fade, now, a0, b1, u1, v0);
			}
		}
	}

	private static void vertex(PoseStack.Pose pose, VertexConsumer vc, Vec3[] basis, Vec3 eye, float fade, float now,
			float a, float b, float u, float v) {
		Vec3 n = onCap(basis, a, b);
		Vec3 p = n.scale(RamBarrier.RADIUS);
		Vec3 view = eye.subtract(p);
		float facing = (float) Math.abs(view.normalize().dot(n));
		// Bright where it is seen edge-on and toward its rim, and a ripple running outward.
		float rim = Math.max((float) Math.pow(1 - facing, 3), a * a * a * a);
		float ripple = 0.5f + 0.5f * Mth.sin(a * 9f - now * 0.6f);
		float alpha = fade * Mth.lerp(rim, BODY_ALPHA + 0.1f * ripple, RIM_ALPHA) * (a > 0.97f ? 0.5f : 1f);
		float white = 0.4f * rim;
		vc.addVertex(pose, (float) p.x, (float) p.y, (float) p.z)
				.setColor(0.75f + white * 0.6f, 0.85f + white * 0.3f, 0.8f + white * 0.5f, alpha)
				.setUv(u, v)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(ShaderGlow.light(0.6f + 0.4f * rim))
				.setNormal(pose, (float) n.x, (float) n.y, (float) n.z);
	}
}
