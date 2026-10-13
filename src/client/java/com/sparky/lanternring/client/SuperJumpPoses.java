package com.sparky.lanternring.client;

import com.sparky.lanternring.RingTuning;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;

/**
 * Third person: the super jump's body language, for every player (the server announces each jump
 * and landing, see SuperJumpFx). Placeholders in code until J's Blender pass (brief in
 * plans/super-jump-blender-brief.md):
 * <ul>
 * <li>wind-up (the local player only, while crouched and armed): arms swung back, head up;
 * <li>launch (first few ticks): arms driven down and back, body straight;
 * <li>rising: the ring fist punched straight up, the other arm back, the ring-side knee up;
 * <li>falling: arms spread out for balance, legs apart;
 * <li>landing: the superhero landing, one knee down, the ring fist on the ground, the other arm
 * back, held for RingTuning super_landing, then up again.
 * </ul>
 * Angles are model rotations in radians: -xRot raises an arm forward, +zRot swings the right arm out
 * (the left mirrored).
 */
public final class SuperJumpPoses {
	/** Ticks of the launch pose before the rising one. */
	private static final float LAUNCH = 5f;
	/** Ticks to blend into a pose and back out of the landing. */
	private static final float BLEND = 3f, STAND_UP = 8f;
	/** How far down the body sinks into the landing, in model pixels. */
	private static final float SINK = 5f;

	private static final class Jump {
		long jumped, landed = -1;
		float charge;
	}

	private static final Int2ObjectMap<Jump> JUMPS = new Int2ObjectOpenHashMap<>();

	private SuperJumpPoses() {
	}

	static void jumped(int id, float charge) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		Jump j = new Jump();
		j.jumped = mc.level.getGameTime();
		j.charge = charge;
		JUMPS.put(id, j);
	}

	static void landed(int id) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		Jump j = JUMPS.computeIfAbsent(id, k -> new Jump());
		j.landed = mc.level.getGameTime();
	}

	public static void pose(PlayerModel model, AvatarRenderState state) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null || !(mc.level.getEntity(state.id) instanceof Player player)) return;
		boolean right = player.getMainArm() == HumanoidArm.RIGHT;
		// "ring" and "free" are the ring arm and the other; out is the sign that swings each outward.
		ModelPart ring = right ? model.rightArm : model.leftArm, free = right ? model.leftArm : model.rightArm;
		ModelPart ringLeg = right ? model.rightLeg : model.leftLeg, freeLeg = right ? model.leftLeg : model.rightLeg;
		float ringOut = right ? 1f : -1f, freeOut = -ringOut;
		float partial = mc.getDeltaTracker().getGameTimeDeltaPartialTick(false);

		Jump j = JUMPS.get(player.getId());
		if (j == null) {
			if (player == mc.player) windup(model, ring, free, ringOut, freeOut, SuperJumpInput.windup());
			return;
		}
		float now = mc.level.getGameTime() + partial;
		if (j.landed >= 0) {
			float age = now - j.landed;
			float hold = RingTuning.SUPER_LANDING.ticks();
			if (age > hold + STAND_UP || age < -20) {
				JUMPS.remove(player.getId());
				return;
			}
			float w = age < hold ? Mth.clamp(age / 2f, 0f, 1f) : 1f - (age - hold) / STAND_UP;
			landing(model, state, ring, free, ringLeg, freeLeg, ringOut, freeOut, smooth(w));
			return;
		}
		float age = now - j.jumped;
		if (age > 600 || age < -20) {
			JUMPS.remove(player.getId());
			return;
		}
		float w = smooth(Mth.clamp(age / BLEND, 0f, 1f));
		double vy = player.getY() - player.yo;
		if (age < LAUNCH) {
			// Driven off the ground: arms thrust down and back, legs straight.
			set(ring, w, 0.55f, 0f, ringOut * 0.2f);
			set(free, w, 0.55f, 0f, freeOut * 0.2f);
			set(model.rightLeg, w, 0.1f, 0f, 0f);
			set(model.leftLeg, w, 0.1f, 0f, 0f);
			model.head.xRot = Mth.lerp(w, model.head.xRot, -0.35f);
		} else if (vy > -0.15) {
			// Rising: the ring fist punched straight up, the other arm back, a knee driven up.
			set(ring, w, -Mth.PI + 0.12f, 0f, ringOut * 0.12f);
			set(free, w, 0.45f, 0f, freeOut * 0.3f);
			set(ringLeg, w, -0.75f, 0f, 0f);
			set(freeLeg, w, 0.25f, 0f, 0f);
		} else {
			// Coming down: arms spread for balance, legs a little apart, ready to land.
			float f = smooth(Mth.clamp((float) (-vy - 0.15) * 4f, 0f, 1f));
			set(ring, f, -0.35f, 0f, ringOut * 1.25f);
			set(free, f, -0.35f, 0f, freeOut * 1.25f);
			set(ringLeg, f, -0.3f, 0f, ringOut * 0.15f);
			set(freeLeg, f, 0.2f, 0f, freeOut * 0.15f);
		}
	}

	/** Crouched and armed: both arms swung back, more as it charges. */
	private static void windup(PlayerModel model, ModelPart ring, ModelPart free, float ringOut, float freeOut, float charge) {
		if (charge <= 0f) return;
		float w = smooth(Math.min(1f, 0.4f + charge));
		set(ring, w, 0.9f + 0.3f * charge, 0f, ringOut * 0.25f);
		set(free, w, 0.9f + 0.3f * charge, 0f, freeOut * 0.25f);
		model.head.xRot = Mth.lerp(w, model.head.xRot, -0.25f);
	}

	/** The superhero landing: one knee down, ring fist on the ground in front, the other arm back. */
	private static void landing(PlayerModel model, AvatarRenderState state, ModelPart ring, ModelPart free, ModelPart ringLeg, ModelPart freeLeg,
			float ringOut, float freeOut, float w) {
		if (w <= 0f) return;
		if (!state.isCrouching) {
			// Like vanilla's crouch (which already did this when crouching), sunk further.
			model.body.y += (3.2f + SINK) * w;
			model.head.y += (4.2f + SINK) * w;
			model.rightArm.y += (3.2f + SINK) * w;
			model.leftArm.y += (3.2f + SINK) * w;
			model.rightLeg.y += (0.2f + SINK) * w;
			model.leftLeg.y += (0.2f + SINK) * w;
			model.rightLeg.z += 4f * w;
			model.leftLeg.z += 4f * w;
		}
		model.body.xRot = Mth.lerp(w, model.body.xRot, 0.6f);
		model.head.xRot = Mth.lerp(w, model.head.xRot, -0.45f);
		set(ring, w, -0.25f, 0f, ringOut * 0.1f);
		set(free, w, 1.0f, 0f, freeOut * 0.55f);
		// The ring-side foot planted forward, the other knee on the ground behind.
		set(ringLeg, w, -1.35f, 0f, ringOut * 0.1f);
		set(freeLeg, w, 0.95f, 0f, freeOut * 0.08f);
	}

	private static float smooth(float t) {
		t = Mth.clamp(t, 0f, 1f);
		return t * t * (3 - 2 * t);
	}

	private static void set(ModelPart part, float w, float x, float y, float z) {
		part.xRot = Mth.lerp(w, part.xRot, x);
		part.yRot = Mth.lerp(w, part.yRot, y);
		part.zRot = Mth.lerp(w, part.zRot, z);
	}
}
