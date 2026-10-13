package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.Corps;
import java.util.ArrayList;
import java.util.EnumMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;

/**
 * The Fear Nuke's bomb (fear_nuke.bbmodel, a simple Fallout-style bomb in hard light), on the
 * server's clock (corps/FearNuke): it grows out of the ring, falls nose first onto the marker, then
 * sits there drinking fear, its glowing seams brightening and then flickering white-hot, until it
 * goes off and the green aura (NukeAuraFx) takes over.
 */
public final class FearNukeFx {
	/** How many times life size it is drawn: the model is 3.5 blocks long, so about 10. */
	private static final float SCALE = 3f;
	/** The nose's depth below the model's middle, in model units (fear_nuke.bbmodel: NOSE - 1). */
	private static final float NOSE = 23f;
	/** How far the server's landing point stands above the ground (FearNuke: ORB * 0.6). */
	private static final double LAND_HEIGHT = 2.4;

	private record Nuke(Vec3 from, Vec3 land, int half, int consume, long start, Corps corps) {
		float total() {
			return 2f * half + consume;
		}
	}

	private static final List<Nuke> NUKES = new ArrayList<>();
	private static final Map<Corps, BbModel> MODELS = new EnumMap<>(Corps.class);

	private FearNukeFx() {
	}

	public static void start(Vec3 from, Vec3 land, int half, int consume) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		NUKES.add(new Nuke(from, land, Math.max(1, half), Math.max(1, consume), mc.level.getGameTime(), CorpsTint.current()));
	}

	public static void clear() {
		NUKES.clear();
	}

	static void tick(Minecraft mc) {
		long now = mc.level.getGameTime();
		for (Iterator<Nuke> it = NUKES.iterator(); it.hasNext(); ) {
			Nuke n = it.next();
			float age = now - n.start;
			if (age > n.total() || age < -1) it.remove();
		}
	}

	public static void render(LevelRenderContext ctx) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) {
			NUKES.clear();
			return;
		}
		if (NUKES.isEmpty()) return;
		float now = mc.level.getGameTime() + ctx.levelState().worldPartialTicks;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		for (Nuke n : NUKES) {
			float age = Math.max(0, now - n.start);
			if (age >= n.total()) continue;
			// Where its middle is, how big it is, how far it leans along its fall and how bright it is.
			Vec3 at;
			float size, lean = 0f, bright;
			float wobble = 0f;
			// Its middle stands so the nose just touches the ground once it has landed.
			double rest = NOSE / 16f * SCALE - LAND_HEIGHT;
			Vec3 landed = n.land.add(0, rest, 0);
			if (age < n.half) {
				float k = age / n.half;
				at = n.from.add(0, rest, 0);
				size = 0.1f + 0.9f * k * k * (3 - 2 * k);
				bright = 0.6f;
				wobble = (1 - k) * 25f;
			} else if (age < 2f * n.half) {
				double k = (age - n.half) / n.half;
				at = new Vec3(Mth.lerp(k, n.from.x, landed.x), Mth.lerp(k * k, n.from.y + rest, landed.y), Mth.lerp(k, n.from.z, landed.z));
				size = 1f;
				bright = 0.6f;
				// Tipped a little toward where it is heading, straightening as it comes down.
				lean = (float) (1 - k) * 20f;
			} else {
				float k = (age - 2f * n.half) / n.consume;
				at = landed;
				// It swells a little and shudders harder as it fills with fear.
				size = 1f + 0.15f * k * k;
				bright = k < 0.85f ? 0.45f + 0.55f * Math.min(1f, k / 0.7f) : (((int) age) % 4 < 2 ? 1f : 0.7f);
				wobble = k * k * 2.5f * Mth.sin(age * 2.1f);
			}
			Vec3 drift = n.land.subtract(n.from).multiply(1, 0, 1);
			float heading = drift.lengthSqr() < 1e-4 ? 0f : (float) Math.toDegrees(Math.atan2(drift.x, drift.z));
			PoseStack pose = ctx.poseStack();
			pose.pushPose();
			pose.translate(at.x - cam.x, at.y - cam.y, at.z - cam.z);
			pose.rotateDegrees(Axis.YP, heading);
			// The nose (model -Y) swings toward +Z, the way it is falling.
			pose.rotateDegrees(Axis.XN, lean + wobble * 0.3f);
			pose.rotateDegrees(Axis.ZP, wobble * 0.2f);
			pose.rotateDegrees(Axis.YP, age * 1.5f);
			float s = size * SCALE;
			pose.scale(s, s, s);
			BbModel model = MODELS.computeIfAbsent(n.corps, corps -> BbModel.load("fear_nuke").forCorps(corps));
			model.renderLit(pose, ctx.submitNodeCollector(), BbModel.glow(bright));
			pose.popPose();
		}
	}
}
