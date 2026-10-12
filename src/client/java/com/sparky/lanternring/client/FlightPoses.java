package com.sparky.lanternring.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import com.sparky.lanternring.item.PowerRingItem;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.player.PlayerModel;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Avatar;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

/**
 * Third-person ring flight poses. Flying slowly (or hovering) keeps the body upright with a lean
 * into the direction of travel and the legs trailing the other way instead of walking. Sprint-flying
 * lays the body out like an elytra glide, with the ring arm reaching ahead. Firing the ring, in the air
 * or on the ground, snaps the ring arm to point where the player is looking.
 */
public final class FlightPoses {
	/** Per-player blend values, eased each tick and interpolated per frame. */
	private static final class Track {
		float flying, prevFlying;
		float fast, prevFast;
		float forward, prevForward;
		float side, prevSide;
		float aim, prevAim;
		int aimTicks;
		int airTicks;
		boolean seen;
	}

	/** What the renderer needs for one frame; lives on the {@link AvatarRenderState}. */
	public static final class Pose {
		/** 0 = not ring-flying, 1 = fully in a flight pose. */
		public float flying;
		/** 0 = slow upright lean, 1 = elytra-style glide. */
		public float fast;
		/** Horizontal travel relative to the body, -1..1 (forward and to the right are positive). */
		public float forward, side;
		/** 0..1: how far the ring arm is pointing where the player looks, after a shot. */
		public float aim;
		/** The arm that reaches ahead in the glide: the one holding the ring. */
		public HumanoidArm ringArm = HumanoidArm.RIGHT;
	}

	public interface Holder {
		Pose lanternring$flightPose();
	}

	/** Remote players' flight isn't synced, so a ring holder airborne this long counts as flying. */
	private static final int REMOTE_AIR_TICKS = 14;
	/** Horizontal speed (blocks per tick) that counts as full lean. */
	private static final float LEAN_SPEED = 0.45f;
	private static final float MIN_FAST_SPEED = 0.15f;
	/** Ticks the ring arm keeps pointing after the last shot. */
	private static final int AIM_HOLD = 12;
	/** How close to a player a power's start point must be to count as theirs. */
	private static final double SHOOTER_RANGE = 3;

	private static final float SLOW_PITCH = 20f;
	private static final float SLOW_ROLL = 12f;
	/** Height of the turning point, so the body tips around its middle rather than its feet. */
	private static final float PIVOT = 0.9f;
	private static final float HALF_PI = Mth.PI / 2;

	private static final Int2ObjectMap<Track> TRACKS = new Int2ObjectOpenHashMap<>();

	static void tick(Minecraft mc) {
		if (mc.level == null) {
			TRACKS.clear();
			return;
		}
		for (Track t : TRACKS.values()) t.seen = false;
		for (AbstractClientPlayer p : mc.level.players()) {
			Track t = TRACKS.computeIfAbsent(p.getId(), id -> new Track());
			t.seen = true;
			update(t, p, p == mc.player, mc);
		}
		TRACKS.values().removeIf(t -> !t.seen);
	}

	/** A ring power went off at {@code from}: the player it came from points their ring arm. */
	public static void shot(Vec3 from) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		Player shooter = null;
		double best = SHOOTER_RANGE * SHOOTER_RANGE;
		for (AbstractClientPlayer p : mc.level.players()) {
			double d = Math.min(p.getEyePosition().distanceToSqr(from), p.position().distanceToSqr(from));
			if (d < best) {
				best = d;
				shooter = p;
			}
		}
		if (shooter == null) return;
		Track t = TRACKS.get(shooter.getId());
		if (t != null) t.aimTicks = AIM_HOLD;
	}

	private static void update(Track t, Player p, boolean local, Minecraft mc) {
		t.prevAim = t.aim;
		// Holding a power (Wall, Dome) keeps aiming; one-shot powers arrive through shot().
		boolean holding = p.isUsingItem() && isRing(p.getUseItem());
		if (local) holding |= mc.options.keyUse.isDown() && !p.isShiftKeyDown() && (isRing(p.getMainHandItem()) || isRing(p.getOffhandItem()));
		t.aimTicks = holding ? AIM_HOLD : Math.max(0, t.aimTicks - 1);
		// Snaps in fast, eases back down.
		t.aim = t.aimTicks > 0 ? approach(t.aim, 1, 0.7f) : approach(t.aim, 0, 0.2f);

		t.prevFlying = t.flying;
		t.prevFast = t.fast;
		t.prevForward = t.forward;
		t.prevSide = t.side;

		t.airTicks = p.onGround() ? 0 : t.airTicks + 1;
		double vx = p.getX() - p.xo;
		double vy = p.getY() - p.yo;
		double vz = p.getZ() - p.zo;

		boolean flying;
		if (p.isSpectator() || p.isFallFlying() || p.isPassenger() || p.isInWater() || p.onGround()) {
			flying = false;
		} else if (local) {
			flying = p.getAbilities().flying && carriesRing(p);
		} else {
			flying = (isRing(p.getMainHandItem()) || isRing(p.getOffhandItem())) && t.airTicks >= REMOTE_AIR_TICKS && vy > -0.4;
		}

		float yaw = p.yBodyRot * Mth.DEG_TO_RAD;
		float sin = Mth.sin(yaw);
		float cos = Mth.cos(yaw);
		float forward = (float) (vx * -sin + vz * cos);
		float right = (float) (vx * -cos + vz * -sin);
		// 3D speed, so a steep climb or dive in the glide stays fast.
		float speed = Mth.sqrt((float) (vx * vx + vy * vy + vz * vz));
		boolean fast = flying && p.isSprinting() && speed > MIN_FAST_SPEED;

		t.flying = approach(t.flying, flying ? 1 : 0, 0.25f);
		t.fast = approach(t.fast, fast ? 1 : 0, fast ? 0.2f : 0.12f);
		t.forward = approach(t.forward, flying ? Mth.clamp(forward / LEAN_SPEED, -1, 1) : 0, 0.2f);
		t.side = approach(t.side, flying ? Mth.clamp(right / LEAN_SPEED, -1, 1) : 0, 0.2f);
	}

	private static float approach(float from, float to, float rate) {
		float next = from + (to - from) * rate;
		return Math.abs(to - next) < 0.002f ? to : next;
	}

	static boolean carriesRing(Player p) {
		var inventory = p.getInventory();
		for (int i = 0; i < inventory.getContainerSize(); i++) {
			if (isRing(inventory.getItem(i))) return true;
		}
		return false;
	}

	/** 0..1: how far this player's ring arm is raised to point where they look (third person). */
	static float aim(Player p, float partialTick) {
		Track t = TRACKS.get(p.getId());
		return t == null ? 0f : Mth.lerp(partialTick, t.prevAim, t.aim);
	}

	static boolean isRing(ItemStack stack) {
		return stack != null && stack.getItem() instanceof PowerRingItem;
	}

	/** Copies this frame's blend values onto the render state. */
	public static void extract(Avatar avatar, AvatarRenderState state, float partialTick) {
		Pose pose = ((Holder) state).lanternring$flightPose();
		Track t = TRACKS.get(avatar.getId());
		if (t == null) {
			pose.flying = 0;
			pose.aim = 0;
			return;
		}
		pose.aim = Mth.lerp(partialTick, t.prevAim, t.aim);
		pose.flying = Mth.lerp(partialTick, t.prevFlying, t.flying);
		pose.fast = Mth.lerp(partialTick, t.prevFast, t.fast);
		pose.forward = Mth.lerp(partialTick, t.prevForward, t.forward);
		pose.side = Mth.lerp(partialTick, t.prevSide, t.side);
		if (isRing(avatar.getMainHandItem())) pose.ringArm = avatar.getMainArm();
		else if (isRing(avatar.getOffhandItem())) pose.ringArm = avatar.getMainArm().getOpposite();
		else pose.ringArm = avatar.getMainArm();
	}

	private static Pose active(AvatarRenderState state) {
		Pose pose = ((Holder) state).lanternring$flightPose();
		if (pose.flying <= 0 || state.isFallFlying || state.swimAmount > 0) return null;
		return pose;
	}

	/** Slow-flight body tilt in degrees: forward travel tips the head forward (negative X). */
	private static float slowPitch(Pose pose) {
		return -SLOW_PITCH * pose.forward;
	}

	/** Whole-body tilt, after vanilla has turned the body to face its yaw. */
	public static void rotate(AvatarRenderState state, PoseStack poseStack) {
		Pose pose = active(state);
		if (pose == null) return;
		float pitch = Mth.lerp(pose.fast, slowPitch(pose), -90f - state.xRot);
		float roll = Mth.lerp(pose.fast, -SLOW_ROLL * pose.side, -SLOW_ROLL * 0.5f * pose.side);
		poseStack.translate(0, PIVOT, 0);
		poseStack.rotateDegrees(Axis.XP, pitch * pose.flying);
		poseStack.rotateDegrees(Axis.ZP, roll * pose.flying);
		poseStack.translate(0, -PIVOT, 0);
	}

	/** Limbs and head: still, trailing legs instead of walking, and the ring arm out front when gliding. */
	public static void pose(PlayerModel model, AvatarRenderState state) {
		Pose pose = ((Holder) state).lanternring$flightPose();
		// Where the player looks, relative to the (possibly tilted) body: the aiming arm follows it.
		float lookX = model.head.xRot;
		if (active(state) != null) {
			lookX = flightPose(model, state, pose);
		}
		if (pose.aim > 0) {
			ModelPart arm = pose.ringArm == HumanoidArm.RIGHT ? model.rightArm : model.leftArm;
			arm.xRot = Mth.lerp(pose.aim, arm.xRot, lookX - HALF_PI);
			arm.yRot = Mth.lerp(pose.aim, arm.yRot, model.head.yRot);
			arm.zRot = Mth.lerp(pose.aim, arm.zRot, 0);
		}
	}

	/** Poses the flying body and returns the look pitch relative to it. */
	private static float flightPose(PlayerModel model, AvatarRenderState state, Pose pose) {
		float f = pose.flying;
		float fast = pose.fast;
		float sway = Mth.sin(state.ageInTicks * 0.09f) * 0.06f;

		// Legs drift opposite the direction of travel, one knee a little further back, like the comic panel.
		float trail = 0.2f + 0.55f * pose.forward;
		float spread = -0.35f * pose.side;
		set(model.rightLeg, f, Mth.lerp(fast, trail + 0.18f + sway, 0.08f), Mth.lerp(fast, 0.06f + spread, 0.03f));
		set(model.leftLeg, f, Mth.lerp(fast, trail - 0.04f - sway, 0.08f), Mth.lerp(fast, -0.06f + spread, -0.03f));
		model.rightLeg.yRot = Mth.lerp(f, model.rightLeg.yRot, 0);
		model.leftLeg.yRot = Mth.lerp(f, model.leftLeg.yRot, 0);

		// Head keeps looking where the player looks: undo the slow lean, look ahead in the glide
		// (the glide lies along the look direction, so "ahead" is straight up the body).
		float slowHead = model.head.xRot + slowPitch(pose) * Mth.DEG_TO_RAD;
		float lookX = Mth.lerp(f, model.head.xRot, Mth.lerp(fast, slowHead, -HALF_PI));
		model.head.xRot = Mth.lerp(f, model.head.xRot, Mth.lerp(fast, slowHead, -1.1f));

		if (!state.isUsingItem) {
			// Arms: relaxed and a little forward when slow; at the sides when gliding, ring arm reaching ahead.
			boolean ringRight = pose.ringArm == HumanoidArm.RIGHT;
			arm(model.rightArm, f, fast, ringRight, 1, sway);
			arm(model.leftArm, f, fast, !ringRight, -1, -sway);
		}
		return lookX;
	}

	/** {@code out} is +1 for the right arm and -1 for the left, so positive Z swings it away from the body. */
	private static void arm(ModelPart arm, float f, float fast, boolean ring, float out, float sway) {
		float glideX = ring ? -Mth.PI + 0.15f : 0.2f;
		float glideZ = ring ? -0.05f * out : 0.12f * out;
		set(arm, f, Mth.lerp(fast, -0.25f + sway, glideX), Mth.lerp(fast, 0.12f * out, glideZ));
		arm.yRot = Mth.lerp(f, arm.yRot, 0);
	}

	private static void set(ModelPart part, float f, float xRot, float zRot) {
		part.xRot = Mth.lerp(f, part.xRot, xRot);
		part.zRot = Mth.lerp(f, part.zRot, zRot);
	}

	private FlightPoses() {
	}
}
