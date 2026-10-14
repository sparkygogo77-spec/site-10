package com.sparky.lanternring.client;

import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.CombatPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.Direction;
import net.minecraft.util.Mth;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * The local player's side of the combat moves (server side: FlightSlams, FlyingFlurries, AbsorbBlasts). Player
 * movement is client-side, so:
 * <ul>
 * <li>the big flight slam fires here: in ring flight, pitched 40 degrees down or more, moving at a block a tick or
 * faster, within the Ring Lab's trigger height of the ground (H5 5 blocks). It drops out of flight and steers the
 * rest of the fall onto the ground in 2 to 4 ticks (the slam animation fits that), reports touchdown and holds you
 * for the lock (RingTuning flight_slam_lock). Shallower or slower dives land as normal;
 * <li>the flying flurry slows you to 10 blocks a second from the first hit and eases you to a hover after the
 * backfist;
 * <li>holding left click with the ring is reported for the absorb; once a shot is held, left click is the absorb's
 * (MinecraftMixin) until you let go.
 * </ul>
 */
public final class CombatInput {
	/** The slam's trigger: degrees pitched down, blocks a tick, and the fall's ticks it may take. */
	private static final float MIN_PITCH = 40f;
	private static final double MIN_SPEED = 1.0;
	private static final int MIN_TICKS = 2, MAX_TICKS = 4;
	/** The flurry: top speed while the string plays (10 blocks a second), and ticks of braking to the hover after it. */
	private static final double FLURRY_SPEED = 0.5;
	private static final int HOVER_TICKS = 10;

	private enum Slam { NONE, FALLING, LOCKED }

	private static Slam slam = Slam.NONE;
	private static int slamAge, slamTicks;
	private static double groundY;
	private static Vec3 step = Vec3.ZERO;
	/** The flurry: ticks since the jab (-1 none). */
	private static int flurryAge = -1;
	/** Left click reported held, and whether a shot is held at the ring. */
	private static boolean absorbSent, holding;

	private CombatInput() {
	}

	/** Whether the slam has the movement keys (the fall and the lock). */
	public static boolean locked() {
		return slam != Slam.NONE;
	}

	/** Whether the slam is steering the local player (FastFlight steps aside). */
	public static boolean controls() {
		return slam == Slam.FALLING;
	}

	/** Whether left click belongs to the absorb right now: a shot is held at the ring. */
	public static boolean ownsLeftClick(Minecraft mc) {
		return holding && mc.player != null;
	}

	/** CombatFx: the local player's ring caught a shot (true) or it's gone (false). */
	static void holding(boolean held) {
		holding = held;
	}

	/** CombatFx: the local player's flurry landed punch i. */
	static void punched(int i) {
		if (i == 0) flurryAge = 0;
	}

	static void tick(Minecraft mc) {
		LocalPlayer p = mc.player;
		if (p == null || mc.level == null) {
			slam = Slam.NONE;
			flurryAge = -1;
			absorbSent = holding = false;
			return;
		}
		absorb(mc, p);
		if (mc.isPaused()) return;
		flurry(p);
		switch (slam) {
			case NONE -> trigger(mc, p);
			case FALLING -> fall(p);
			case LOCKED -> {
				Vec3 v = p.getDeltaMovement();
				p.setDeltaMovement(0, Math.min(0, v.y), 0);
				if (++slamAge >= RingTuning.FLIGHT_SLAM_LOCK.ticks()) slam = Slam.NONE;
			}
		}
	}

	private static boolean chargedRing(LocalPlayer p) {
		var inventory = p.getInventory();
		for (int i = 0; i < inventory.getContainerSize(); i++) {
			ItemStack stack = inventory.getItem(i);
			if (stack.getItem() instanceof PowerRingItem && PowerRingItem.getCharge(stack) > 0) return true;
		}
		return false;
	}

	/** Checked once a tick in flight: a steep, fast dive near the ground fires the slam. */
	private static void trigger(Minecraft mc, LocalPlayer p) {
		if (!p.getAbilities().flying || p.isInWater() || p.isPassenger() || p.isSpectator() || FlightMoves.controls() || !chargedRing(p)) return;
		Vec3 moved = new Vec3(p.getX() - p.xo, p.getY() - p.yo, p.getZ() - p.zo);
		double speed = moved.length();
		if (p.getXRot() < MIN_PITCH || speed < MIN_SPEED || moved.y >= -0.2) return;
		double trigger = LabSettings.get().flightSlam.height;
		Vec3 feet = p.position();
		// Height above the ground: straight down.
		BlockHitResult down = mc.level.clip(new ClipContext(feet, feet.subtract(0, trigger + 0.5, 0), ClipContext.Block.COLLIDER,
				ClipContext.Fluid.ANY, p));
		if (down.getType() == HitResult.Type.MISS) return;
		double height = feet.y - down.getLocation().y;
		if (height > trigger || height < 0.3) return;
		// Where the dive meets the ground (along the way you're going), or straight below for a wall in the way.
		BlockHitResult ahead = mc.level.clip(new ClipContext(feet, feet.add(moved.scale(MAX_TICKS + 2)), ClipContext.Block.COLLIDER,
				ClipContext.Fluid.ANY, p));
		Vec3 land = ahead.getType() != HitResult.Type.MISS && ahead.getDirection() == Direction.UP ? ahead.getLocation() : down.getLocation();
		double fall = feet.y - land.y;
		slamTicks = Mth.clamp((int) Math.round(fall / Math.max(0.2, -moved.y)), MIN_TICKS, MAX_TICKS);
		groundY = land.y;
		step = new Vec3((land.x - feet.x) / slamTicks, 0, (land.z - feet.z) / slamTicks);
		slamAge = 0;
		slam = Slam.FALLING;
		// Out of flight: the slam drops you onto the ground.
		p.getAbilities().flying = false;
		p.onUpdateAbilities();
		if (ClientPlayNetworking.canSend(CombatPayload.TYPE)) {
			ClientPlayNetworking.send(new CombatPayload(CombatPayload.SLAM, feet, moved, slamTicks));
		}
		fall(p);
	}

	/** Sets the next tick's move so the feet meet the ground on the slam's last tick; touchdown reports it and locks. */
	private static void fall(LocalPlayer p) {
		if (slamAge > 0 && (p.onGround() || p.isInWater())) {
			if (ClientPlayNetworking.canSend(CombatPayload.TYPE) && !p.isInWater()) {
				ClientPlayNetworking.send(new CombatPayload(CombatPayload.SLAM_LAND, p.position(), step, 0f));
			}
			slam = Slam.LOCKED;
			slamAge = 0;
			p.setDeltaMovement(0, 0, 0);
			p.resetFallDistance();
			RingShake.kick(1.2f, true);
			return;
		}
		if (slamAge > slamTicks + 4) {
			slam = Slam.NONE;
			return;
		}
		int left = Math.max(1, slamTicks - slamAge);
		slamAge++;
		// A little past the ground on the last tick, so the move ends on it.
		double dy = (groundY - p.getY()) / left - (left == 1 ? 0.3 : 0);
		p.setDeltaMovement(left == 1 && slamAge > slamTicks ? 0 : step.x, Math.min(-0.2, dy), left == 1 && slamAge > slamTicks ? 0 : step.z);
		p.resetFallDistance();
	}

	/** The flurry slows you while it plays and brakes you to a hover after the backfist. */
	private static void flurry(LocalPlayer p) {
		if (flurryAge < 0) return;
		flurryAge++;
		int backfist = RingTuning.FLURRY_BACKFIST.ticks();
		if (flurryAge > backfist + HOVER_TICKS || !p.getAbilities().flying) {
			flurryAge = -1;
			return;
		}
		Vec3 v = p.getDeltaMovement();
		if (flurryAge <= backfist) {
			if (v.length() > FLURRY_SPEED) p.setDeltaMovement(v.normalize().scale(FLURRY_SPEED));
		} else {
			p.setDeltaMovement(v.scale(0.75));
		}
	}

	/** Tells the server when left click goes down or up with a ring in hand. */
	private static void absorb(Minecraft mc, LocalPlayer p) {
		boolean ring = p.getMainHandItem().getItem() instanceof PowerRingItem || p.getOffhandItem().getItem() instanceof PowerRingItem;
		boolean down = ring && mc.gui.screen() == null && mc.options.keyAttack.isDown() && !p.isSpectator();
		if (down != absorbSent && ClientPlayNetworking.canSend(CombatPayload.TYPE)) {
			ClientPlayNetworking.send(new CombatPayload(CombatPayload.ABSORB, p.position(), Vec3.ZERO, down ? 1f : 0f));
			absorbSent = down;
		}
		if (!ring) holding = false;
	}
}
