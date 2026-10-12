package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.net.GolemPayload;
import java.util.HashMap;
import java.util.Map;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;

/**
 * Draws Loot Golems (loot_golem.bbmodel) where the server says they are, smoothed between ticks,
 * with the glowing sack on its back (loot_golem_bag.bbmodel) growing as it fills. It sways as it
 * floats and trails a few motes.
 */
public final class GolemFx {
	private static final int FULL_BRIGHT = 0xF000F0;
	/** Drawn a little bigger than a vanilla copper golem so it reads at a distance. */
	private static final float SCALE = 1.15f;

	private static final class Golem {
		Vec3 prev;
		Vec3 pos;
		float prevYaw;
		float yaw;
		float fill;
		boolean visible;
		long seen;

		Golem(Vec3 pos, float yaw) {
			this.prev = pos;
			this.pos = pos;
			this.prevYaw = yaw;
			this.yaw = yaw;
		}
	}

	private static final Map<Integer, Golem> GOLEMS = new HashMap<>();
	private static ClientLevel seenLevel;
	private static BbModel body;
	private static BbModel bag;

	private GolemFx() {
	}

	public static void handle(GolemPayload payload) {
		ClientLevel level = Minecraft.getInstance().level;
		if (level == null) return;
		if (payload.fill() < 0) {
			GOLEMS.remove(payload.id());
			return;
		}
		Golem g = GOLEMS.get(payload.id());
		if (g == null || g.pos.distanceToSqr(payload.pos()) > 64) {
			g = new Golem(payload.pos(), payload.yaw());
			GOLEMS.put(payload.id(), g);
		}
		g.prev = g.pos;
		g.prevYaw = g.yaw;
		g.pos = payload.pos();
		g.yaw = payload.yaw();
		g.fill = payload.fill();
		if (payload.visible() && !g.visible) LabFx.burst(g.pos.add(0, 0.6, 0), 6, 0.08);
		g.visible = payload.visible();
		g.seen = level.getGameTime();
	}

	static void tick(Minecraft mc) {
		if (mc.level != seenLevel) {
			GOLEMS.clear();
			seenLevel = mc.level;
		}
		if (mc.level == null || GOLEMS.isEmpty()) return;
		long now = mc.level.getGameTime();
		GOLEMS.values().removeIf(g -> now - g.seen > 40);
		for (Golem g : GOLEMS.values()) {
			if (g.visible && mc.level.getRandom().nextFloat() < 0.4f) {
				LabFx.spawn(ModParticles.MOTE, g.pos.add(LabFx.jitter(mc.level.getRandom(), 0.6)), new Vec3(0, -0.02, 0), 0.5f);
			}
		}
	}

	public static void render(LevelRenderContext ctx) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null || GOLEMS.isEmpty() || mc.level != seenLevel) return;
		if (body == null) {
			body = BbModel.load("loot_golem");
			bag = BbModel.load("loot_golem_bag");
		}
		float partial = ctx.levelState().worldPartialTicks;
		float now = mc.level.getGameTime() + partial;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		for (Map.Entry<Integer, Golem> e : GOLEMS.entrySet()) {
			Golem g = e.getValue();
			if (!g.visible) continue;
			Vec3 at = g.prev.lerp(g.pos, partial);
			float yaw = Mth.rotLerp(partial, g.prevYaw, g.yaw);
			Vec3 move = g.pos.subtract(g.prev);
			PoseStack pose = ctx.poseStack();
			pose.pushPose();
			pose.translate(at.x - cam.x, at.y - cam.y - 0.5, at.z - cam.z);
			pose.rotateDegrees(Axis.YP, 180f - yaw);
			// Leans into its flight and sways a little while it floats.
			float lean = (float) Math.min(25, move.horizontalDistance() * 60);
			pose.rotateDegrees(Axis.XP, -lean);
			pose.rotateDegrees(Axis.ZP, 4f * Mth.sin(now * 0.15f + e.getKey()));
			pose.scale(SCALE, SCALE, SCALE);
			body.render(pose, ctx.submitNodeCollector(), FULL_BRIGHT, BbModel.glow(1f));
			if (g.fill > 0) {
				float s = 0.45f + 0.75f * g.fill;
				pose.translate(0f, 8f / 16f, 5f / 16f);
				pose.scale(s, s, s);
				bag.render(pose, ctx.submitNodeCollector(), FULL_BRIGHT, BbModel.glow(0.85f));
			}
			pose.popPose();
		}
	}
}
