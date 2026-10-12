package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.BlastDrills;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import net.fabricmc.fabric.api.client.rendering.v1.level.LevelRenderContext;
import net.minecraft.client.Minecraft;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;

/**
 * The Blast's spinning jade drill (blast_drill.bbmodel), flown tip first down the tunnel at the
 * server's speed, so it is always where blocks are breaking. Each tick it also leaves the chosen
 * Blast style's particles along the stretch it just covered (LabFx.blastStretch).
 */
public final class BlastDrillFx {
	private static final int FULL_BRIGHT = 0xF000F0;
	/** Spin, in degrees per tick: about two and a half turns a second, clockwise seen from behind. */
	private static final float SPIN = 45f;
	/** Ticks the drill takes to shrink away once it has reached the end of its tunnel. */
	private static final float VANISH = 4f;

	private static final class Drill {
		final Vec3 from;
		final Vec3 dir;
		final double length;
		final double speed;
		final long start;
		double covered;
		boolean ended;

		Drill(Vec3 from, Vec3 dir, double length, double speed, long start) {
			this.from = from;
			this.dir = dir;
			this.length = length;
			this.speed = speed;
			this.start = start;
			this.covered = 0.5;
		}

		double tip(float age) {
			return Math.min(length, BlastDrills.startTip() + speed * age);
		}

		float travel() {
			return (float) ((length - BlastDrills.startTip()) / speed);
		}
	}

	private static final List<Drill> DRILLS = new ArrayList<>();
	private static BbModel model;

	private BlastDrillFx() {
	}

	public static void fire(Vec3 from, Vec3 to, double speed) {
		Minecraft mc = Minecraft.getInstance();
		Vec3 d = to.subtract(from);
		double length = d.length();
		if (mc.level == null || length < 0.5) return;
		Drill drill = new Drill(from, d.scale(1 / length), length, speed > 0 ? speed : BlastDrills.speed(), mc.level.getGameTime());
		DRILLS.add(drill);
		step(drill, 0);
	}

	public static void clear() {
		DRILLS.clear();
	}

	static void tick(Minecraft mc) {
		long now = mc.level.getGameTime();
		for (Iterator<Drill> it = DRILLS.iterator(); it.hasNext(); ) {
			Drill drill = it.next();
			float age = now - drill.start;
			step(drill, age);
			if (age > drill.travel() + VANISH || age < -1) it.remove();
		}
	}

	/** Particles along the stretch covered since the last tick; the finale once the end is reached. */
	private static void step(Drill drill, float age) {
		double tip = drill.tip(age);
		if (tip > drill.covered) {
			LabFx.blastStretch(drill.from, drill.dir, drill.covered, tip);
			drill.covered = tip;
		}
		if (!drill.ended && tip >= drill.length) {
			drill.ended = true;
			LabFx.blastEnd(drill.from, drill.from.add(drill.dir.scale(drill.length)));
		}
	}

	public static void render(LevelRenderContext ctx) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) {
			DRILLS.clear();
			return;
		}
		if (DRILLS.isEmpty()) return;
		if (model == null) model = BbModel.load("blast_drill");
		float now = mc.level.getGameTime() + ctx.levelState().worldPartialTicks;
		Vec3 cam = ctx.levelState().cameraRenderState.pos;
		for (Drill drill : DRILLS) {
			float age = Math.max(0, now - drill.start);
			float past = age - drill.travel();
			float size = past <= 0 ? 1f : 1f - past / VANISH;
			if (size <= 0) continue;
			Vec3 tip = drill.from.add(drill.dir.scale(drill.tip(age)));
			PoseStack pose = ctx.poseStack();
			pose.pushPose();
			pose.translate(tip.x - cam.x, tip.y - cam.y, tip.z - cam.z);
			// The model points its tip at -Z; turn that onto the tunnel, then hang it back from the tip.
			pose.rotate(new Quaternionf().rotationTo(0f, 0f, -1f, (float) drill.dir.x, (float) drill.dir.y, (float) drill.dir.z));
			pose.scale(size, size, size);
			pose.translate(0f, 0f, (float) BlastDrills.DRILL_LENGTH);
			pose.rotateDegrees(Axis.ZP, age * SPIN);
			model.render(pose, ctx.submitNodeCollector(), FULL_BRIGHT, BbModel.glow(1f));
			pose.popPose();
		}
	}
}
