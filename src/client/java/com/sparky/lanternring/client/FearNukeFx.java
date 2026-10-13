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
 * server's clock (corps/FearNuke). Built on the bearer's raised fist (NukeHold), it leaves the hand
 * nose first, swelling to full size as it arcs out over the target, then hangs in the air drinking
 * fear, its glowing seams brightening and then flickering white-hot, until it airbursts and the
 * yellow aura (NukeAuraFx) and the burst itself (AirburstFx) take over.
 */
public final class FearNukeFx {
	/** How many times life size it is drawn: the model is 3.5 blocks long, so about 10. */
	private static final float SCALE = 3f;
	/** Its size as it leaves the hand, as a share of the full size. */
	private static final float IN_HAND = NukeHold.handLength / (3.5f * SCALE);

	private record Nuke(Vec3 from, Vec3 burst, int fly, int hang, long start, Corps corps) {
		float total() {
			return fly + hang;
		}

		/** Where it is {@code age} ticks in (as the server's FearNuke.step). */
		Vec3 at(float age) {
			if (age >= fly) return burst;
			double k = Math.max(0, age / fly);
			double arc = Math.sin(k * Math.PI) * Math.max(4, from.distanceTo(burst) * 0.25);
			return new Vec3(Mth.lerp(k, from.x, burst.x), Mth.lerp(k, from.y, burst.y) + arc, Mth.lerp(k, from.z, burst.z));
		}
	}

	private static final List<Nuke> NUKES = new ArrayList<>();
	private static final Map<Corps, BbModel> MODELS = new EnumMap<>(Corps.class);

	private FearNukeFx() {
	}

	public static void start(Vec3 from, Vec3 burst, int fly, int hang) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		NUKES.add(new Nuke(from, burst, Math.max(1, fly), Math.max(1, hang), mc.level.getGameTime(), CorpsTint.current()));
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
			Vec3 at = n.at(age);
			float size, bright, wobble = 0f;
			// How far the nose leans off straight down, and which way.
			float lean, heading;
			if (age < n.fly) {
				float k = age / n.fly;
				size = IN_HAND + (1 - IN_HAND) * k * k * (3 - 2 * k);
				bright = 0.75f;
				// Nose first along its flight.
				Vec3 v = n.at(age + 0.5f).subtract(n.at(Math.max(0, age - 0.5f)));
				double flat = Math.sqrt(v.x * v.x + v.z * v.z);
				heading = (float) Math.toDegrees(Math.atan2(v.x, v.z));
				lean = (float) Math.toDegrees(Math.atan2(flat, -v.y));
			} else {
				float k = (age - n.fly) / n.hang;
				size = 1f + 0.15f * k * k;
				bright = k < 0.85f ? 0.45f + 0.55f * Math.min(1f, k / 0.7f) : (((int) age) % 4 < 2 ? 1f : 0.7f);
				wobble = k * k * 2.5f * Mth.sin(age * 2.1f);
				Vec3 drift = n.burst.subtract(n.from).multiply(1, 0, 1);
				heading = drift.lengthSqr() < 1e-4 ? 0f : (float) Math.toDegrees(Math.atan2(drift.x, drift.z));
				// Settling from its last lean to hanging nose down.
				lean = 20f * Math.max(0f, 1f - k * 4f);
			}
			PoseStack pose = ctx.poseStack();
			pose.pushPose();
			pose.translate(at.x - cam.x, at.y - cam.y, at.z - cam.z);
			pose.rotateDegrees(Axis.YP, heading);
			// The nose (model -Y) swings toward +Z, the way it is going.
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
