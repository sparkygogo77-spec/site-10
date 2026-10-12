package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.Portals;
import com.sparky.lanternring.net.PortalPayload;
import java.util.HashMap;
import java.util.Map;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.Vec3;

/**
 * Draws the Portal mode's portals: a Rick and Morty style oval of spinning green swirl
 * (portal_swirl.png, two layers turning opposite ways) that pops open and shrinks shut, with
 * motes drifting off its rim. Full-bright translucent emissive, like the Shockwave dome, so
 * shader packs draw it too.
 */
public final class PortalFx {
	private static final RenderType SWIRL = RenderTypes.entityTranslucentEmissive(LanternRing.id("textures/entity/portal_swirl.png"));
	private static final int FULL_BRIGHT = 0xF000F0;
	private static final int SEGMENTS = 48;
	/** Ticks to pop open and to shrink shut. */
	private static final float OPEN = 6f;
	private static final float CLOSE = 6f;

	private static final class Portal {
		final Vec3 center;
		final float yaw;
		final long opened;
		long closeAt;

		Portal(Vec3 center, float yaw, long opened, long closeAt) {
			this.center = center;
			this.yaw = yaw;
			this.opened = opened;
			this.closeAt = closeAt;
		}
	}

	private static final Map<Integer, Portal> PORTALS = new HashMap<>();
	private static ClientLevel seenLevel;

	private PortalFx() {
	}

	public static void handle(PortalPayload payload) {
		ClientLevel level = Minecraft.getInstance().level;
		if (level == null) return;
		long now = level.getGameTime();
		Portal p = PORTALS.get(payload.id());
		if (p == null) {
			if (payload.ticksLeft() <= 0) return;
			PORTALS.put(payload.id(), new Portal(payload.center(), payload.yaw(), now, now + payload.ticksLeft()));
		} else {
			p.closeAt = now + payload.ticksLeft();
		}
	}

	static void tick(Minecraft mc) {
		if (mc.level != seenLevel) {
			PORTALS.clear();
			seenLevel = mc.level;
		}
		if (mc.level == null || PORTALS.isEmpty()) return;
		long now = mc.level.getGameTime();
		PORTALS.values().removeIf(p -> now > p.closeAt + CLOSE);
		RandomSource r = mc.level.getRandom();
		for (Portal p : PORTALS.values()) {
			if (now > p.closeAt) continue;
			Vec3 n = Portals.normal(p.yaw);
			Vec3 t = new Vec3(n.z, 0, -n.x);
			for (int i = 0; i < 2; i++) {
				double a = r.nextDouble() * Math.PI * 2;
				Vec3 rim = p.center.add(t.scale(Math.cos(a) * Portals.HALF_WIDTH)).add(0, Math.sin(a) * Portals.HALF_HEIGHT, 0);
				Vec3 drift = n.scale((r.nextBoolean() ? 1 : -1) * 0.02).add(0, 0.01, 0);
				LabFx.spawn(ModParticles.MOTE, rim, drift, 0.6f);
			}
		}
	}

	public static void render(LevelRenderContext ctx) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null || PORTALS.isEmpty() || mc.level != seenLevel) return;
		float now = mc.level.getGameTime() + ctx.levelState().worldPartialTicks;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		for (Portal p : PORTALS.values()) {
			float age = now - p.opened;
			float size;
			if (now > p.closeAt) {
				size = 1f - (now - p.closeAt) / CLOSE;
			} else if (age < OPEN) {
				// Pops open with a little overshoot.
				float k = age / OPEN;
				size = Mth.sin(k * Mth.PI * 0.75f) / Mth.sin(Mth.PI * 0.75f) * (1f + 0.1f * k);
			} else {
				size = 1f + 0.015f * Mth.sin(now * 0.4f);
			}
			if (size <= 0.01f) continue;
			PoseStack pose = ctx.poseStack();
			pose.pushPose();
			pose.translate(p.center.x - cam.x, p.center.y - cam.y, p.center.z - cam.z);
			float spin = now * 0.09f;
			float s = size;
			ctx.submitNodeCollector().submitCustomGeometry(pose, SWIRL, (pp, vc) -> {
				oval(pp, vc, p.yaw, s, spin, 1f, 0f);
				// A smaller layer turning the other way, just in front and behind, for depth.
				oval(pp, vc, p.yaw, s * 0.82f, -spin * 1.6f, 0.55f, 0.02f);
				oval(pp, vc, p.yaw, s * 0.82f, -spin * 1.6f, 0.55f, -0.02f);
			});
			pose.popPose();
		}
	}

	/** The oval as a fan of quads; the texture spins by {@code spin} radians. */
	private static void oval(PoseStack.Pose pose, VertexConsumer vc, float yaw, float size, float spin, float alpha, float offset) {
		Vec3 n = Portals.normal(yaw);
		float nx = (float) n.x, nz = (float) n.z;
		float tx = nz, tz = -nx;
		float hw = (float) Portals.HALF_WIDTH * size, hh = (float) Portals.HALF_HEIGHT * size;
		float ox = nx * offset, oz = nz * offset;
		for (int i = 0; i < SEGMENTS; i++) {
			float a0 = i * Mth.TWO_PI / SEGMENTS;
			float a1 = (i + 1) * Mth.TWO_PI / SEGMENTS;
			vertex(pose, vc, ox, 0, oz, 0, 0, spin, nx, nz, alpha);
			vertex(pose, vc, ox + tx * hw * Mth.cos(a0), hh * Mth.sin(a0), oz + tz * hw * Mth.cos(a0), Mth.cos(a0), Mth.sin(a0), spin, nx, nz, alpha);
			vertex(pose, vc, ox + tx * hw * Mth.cos(a1), hh * Mth.sin(a1), oz + tz * hw * Mth.cos(a1), Mth.cos(a1), Mth.sin(a1), spin, nx, nz, alpha);
			vertex(pose, vc, ox + tx * hw * Mth.cos(a1), hh * Mth.sin(a1), oz + tz * hw * Mth.cos(a1), Mth.cos(a1), Mth.sin(a1), spin, nx, nz, alpha);
		}
	}

	/** (cu, cv) is the point on the unit circle; the texture is sampled turned by spin. */
	private static void vertex(PoseStack.Pose pose, VertexConsumer vc, float x, float y, float z, float cu, float cv,
			float spin, float nx, float nz, float alpha) {
		float c = Mth.cos(spin), s = Mth.sin(spin);
		float u = 0.5f + 0.5f * (cu * c - cv * s);
		float v = 0.5f - 0.5f * (cu * s + cv * c);
		vc.addVertex(pose, x, y, z)
				.setColor(1f, 1f, 1f, alpha)
				.setUv(u, v)
				.setOverlay(OverlayTexture.NO_OVERLAY)
				.setLight(FULL_BRIGHT)
				.setNormal(pose, nx, 0, nz);
	}
}
