package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import com.sparky.lanternring.ConstructHammers;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModRegistry;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.net.CombatFxPayload;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.core.Direction;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;
import org.joml.Matrix3f;
import org.joml.Quaternionf;
import org.joml.Vector3f;

/**
 * Every client draws the construct hammer (pass 503 R2, server side ConstructHammers), as Blender's 503 script keys
 * it: 36 construct pixels fly in along the haft (ticks 10-22) while the hammer grows from its pivot, it swings from
 * 115 degrees (26-33, angle with progress squared), the head settles 0.45 blocks into the hit, and after
 * RingTuning hammer_linger it breaks into 16 pixels and shrinks away. The pivot sits so the head ends 0.35 blocks off
 * the face it hits.
 * <ul>
 * <li>R2a overhead: the swing plane is upright through your forward line, from 115 degrees above it to 45 below.
 * <li>R2b from the side: the plane runs from your ring side to 45 degrees down into the target, from 115 round to 0.
 * </ul>
 * Which one each viewer sees follows their Ring Lab "Hammer swing" row: J's pick R2a with R2b on walls.
 */
final class ConstructHammerFx {
	private static final float LENGTH = 2.4f, HAFT = 0.07f;
	private static final float HEAD_LONG = 0.375f, HEAD = 0.275f;
	private static final float OFF_FACE = 0.35f, SINK = 0.45f;
	private static final int FORM_PIXELS = 36, BREAK_PIXELS = 16, GROW = 12, SHRINK = 6;
	private static final float ALPHA = 0.8f;

	private static final class Swing {
		final int bearer;
		final Corps corps;
		final long start;
		final Vec3 pivot, u, v, forward, side, into;
		final float a0, a1;
		final Vec3[] src = new Vec3[FORM_PIXELS], dest = new Vec3[FORM_PIXELS];
		boolean hit, broke;

		Swing(int bearer, Corps corps, long start, Vec3 pivot, Vec3 u, Vec3 v, Vec3 forward, Vec3 side, Vec3 into, float a0, float a1) {
			this.bearer = bearer;
			this.corps = corps;
			this.start = start;
			this.pivot = pivot;
			this.u = u;
			this.v = v;
			this.forward = forward;
			this.side = side;
			this.into = into;
			this.a0 = a0;
			this.a1 = a1;
		}

		Vec3 dir(float a) {
			return u.scale(Mth.cos(a)).add(v.scale(Mth.sin(a)));
		}

		/** The swing angle at age (ticks since the press). */
		float angle(float age) {
			if (age < ConstructHammers.SWING) return a0;
			if (age >= ConstructHammers.HIT) return a1;
			float w = (age - ConstructHammers.SWING) / (ConstructHammers.HIT - ConstructHammers.SWING);
			return a0 + (a1 - a0) * w * w;
		}

		float sink(float age) {
			return age < ConstructHammers.HIT + 2 ? 0f : Math.min(SINK, 0.15f * (age - ConstructHammers.HIT - 1));
		}

		int breakAt() {
			return ConstructHammers.HIT + RingTuning.HAMMER_LINGER.ticks();
		}

		/** How big the hammer is: grows from the pivot as it forms, shrinks once it's broken. */
		float scale(float age) {
			if (age < ConstructHammers.FORM) return 0f;
			if (age < breakAt()) return SuperJumpPoses.smooth(Math.min(1f, (age - ConstructHammers.FORM) / GROW));
			return Math.max(0f, 1f - (age - breakAt()) / SHRINK);
		}

		Vec3 head(float age) {
			return pivot.add(dir(angle(age)).scale(LENGTH)).add(into.scale(sink(age)));
		}
	}

	private static final List<Swing> SWINGS = new ArrayList<>();

	private ConstructHammerFx() {
	}

	static boolean active() {
		return !SWINGS.isEmpty();
	}

	/** HAMMER_FORM: the bearer's hammer, landing at fx.from() (see CombatFxPayload). */
	static void form(ClientLevel level, CombatFxPayload fx, Player bearer) {
		long start = level.getGameTime() - Math.round(fx.value());
		Vec3 forward = fx.to().subtract(fx.from());
		forward = forward.lengthSqr() < 1e-6 ? new Vec3(0, 0, 1) : forward.normalize();
		boolean wall = fx.variant() >= 8;
		Vec3 normal = fx.variant() < 0 ? new Vec3(0, 1, 0) : unit(Direction.from3DDataValue(fx.variant() & 7));
		// Into a wall the forward line runs straight into it.
		if (wall && Math.abs(normal.y) < 0.5) forward = normal.scale(-1);
		LabSettings.HammerSwing pick = LabSettings.get().hammerSwing;
		boolean fromSide = pick == LabSettings.HammerSwing.R2B || pick == LabSettings.HammerSwing.AUTO && wall;
		Vec3 up = new Vec3(0, 1, 0);
		Vec3 right = forward.cross(up);
		right = right.lengthSqr() < 1e-6 ? new Vec3(1, 0, 0) : right.normalize();
		boolean ringRight = bearer == null || RingEmit.ringArm(bearer) == HumanoidArm.RIGHT;
		Vec3 side = ringRight ? right : right.scale(-1);
		Vec3 u, v;
		float a0 = 115 * Mth.DEG_TO_RAD, a1;
		if (fromSide) {
			u = forward.add(0, -1, 0).normalize();
			v = side;
			a1 = 0f;
		} else {
			u = forward;
			v = up;
			a1 = -45 * Mth.DEG_TO_RAD;
		}
		Vec3 headAt = fx.from().add(normal.scale(OFF_FACE));
		Vec3 end = u.scale(Mth.cos(a1)).add(v.scale(Mth.sin(a1)));
		Swing s = new Swing(fx.bearer(), fx.corps(), start, headAt.subtract(end.scale(LENGTH)), u, v, forward, side, normal.scale(-1), a0, a1);
		RandomSource r = RandomSource.create(fx.bearer() * 31L + start);
		Vec3 e0 = s.dir(a0);
		for (int i = 0; i < FORM_PIXELS; i++) {
			s.dest[i] = s.pivot.add(e0.scale(LENGTH * (0.35 + 0.65 * r.nextDouble())));
			s.src[i] = s.dest[i].add(r.nextGaussian() * 1.2, r.nextGaussian() * 1.2, r.nextGaussian() * 1.2);
		}
		SWINGS.removeIf(o -> o.bearer == fx.bearer() && o.bearer >= 0);
		SWINGS.add(s);
		CombatPoses.hammer(fx.bearer(), Math.round(fx.value()));
	}

	/** HAMMER_HIT: the ring flares as the hammer lands (Blender glow 26 for 3 ticks). */
	static void hit(Player bearer) {
		for (Swing s : SWINGS) {
			if (s.bearer == bearer.getId()) s.hit = true;
		}
		RingEmit.flash(bearer, 2f);
	}

	private static Vec3 unit(Direction d) {
		return new Vec3(d.getStepX(), d.getStepY(), d.getStepZ());
	}

	static void tick(Minecraft mc, ClientLevel level) {
		long now = level.getGameTime();
		for (Swing s : SWINGS) {
			float age = now - s.start;
			Player bearer = RingEmit.bearer(s.bearer);
			// The ring burns brighter while it forms and swings the hammer (Blender glow 10 against 3).
			if (bearer != null && age >= ConstructHammers.FORM && age < ConstructHammers.HIT) {
				Corps before = CorpsTint.enter(s.corps);
				try {
					RingEmit.hold(bearer, s.head(age), 0.45f);
				} finally {
					CorpsTint.restore(before);
				}
			}
			if (!s.broke && age >= s.breakAt()) {
				s.broke = true;
				CombatFx.burst(s.corps, s.head(age), s.into.scale(-1), BREAK_PIXELS);
			}
		}
		SWINGS.removeIf(s -> now - s.start > s.breakAt() + SHRINK + 2 || now < s.start - 40);
	}

	static void clear() {
		SWINGS.clear();
	}

	static void draw(PoseStack.Pose pose, VertexConsumer vc, Vec3 cam, float now) {
		for (Swing s : SWINGS) {
			float age = now - s.start;
			TextureAtlasSprite sprite = SuperLandConstruct.sprite(ModRegistry.LIGHT_CONSTRUCT, s.corps);
			float[] tint = PowerLandingFx.tint(s.corps);
			int light = ShaderGlow.light(0.8f);
			// The pixels gathering into the hammer.
			float k = age - ConstructHammers.FORM;
			if (k >= 0 && k < GROW + 1) {
				float w = SuperJumpPoses.smooth(Math.min(1f, k / GROW));
				float half = 0.045f * (1 - 0.8f * w);
				for (int i = 0; i < FORM_PIXELS; i++) {
					Vec3 p = s.src[i].lerp(s.dest[i], w);
					PowerLandingFx.cube(pose, vc, cam, p, null, half, half, half, sprite, (i % 7) / 8f, (i % 5) / 6f, 0.15f,
							PowerLandingFx.bright(tint, i % 3 == 0 ? 0.4f : 0.15f), 0.9f, light);
				}
			}
			float sc = s.scale(age);
			if (sc <= 0.01f) continue;
			Vec3 e = s.dir(s.angle(age));
			Vec3 base = s.pivot.add(s.into.scale(s.sink(age)));
			// Blender keys the hammer as the minimal turn from its rest (haft along forward, head across it) to the swing.
			Quaternionf q = new Quaternionf().rotationTo(vec(s.forward), vec(e));
			Vector3f along = q.transform(vec(s.side));
			Vector3f haft = vec(e);
			Vector3f third = new Vector3f(along).cross(haft).normalize();
			Quaternionf turn = new Matrix3f(along, haft, third).getNormalizedRotation(new Quaternionf());
			boolean flare = age >= ConstructHammers.HIT && age < ConstructHammers.HIT + 3;
			float[] haftCol = PowerLandingFx.bright(tint, flare ? 0.5f : 0.2f), headCol = PowerLandingFx.bright(tint, flare ? 0.6f : 0.1f);
			PowerLandingFx.cube(pose, vc, cam, base.add(e.scale(LENGTH * sc / 2)), turn, HAFT * sc, LENGTH * sc / 2, HAFT * sc, sprite, 0f, 0f, 1f,
					haftCol, ALPHA, light);
			PowerLandingFx.cube(pose, vc, cam, base.add(e.scale(LENGTH * sc)), turn, HEAD_LONG * sc, HEAD * sc, HEAD * sc, sprite, 0f, 0f, 1f,
					headCol, ALPHA, light);
		}
	}

	private static Vector3f vec(Vec3 v) {
		return new Vector3f((float) v.x, (float) v.y, (float) v.z);
	}
}
