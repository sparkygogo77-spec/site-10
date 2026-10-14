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
 * (MinecraftMixin) until you let go;
 * <li>the primed slam (pass 518 P1): shift held in hyper speed (FastFlight) and diving 40 degrees or more locks you
 * into the dive at once; the ground coming up within 3 ticks fires the slam (PRIMED_SLAM) and it lands as the big
 * slam does, into PrimedSlams' instant crater;
 * <li>while your primed crater is lined, left click on it is the rebuild's (REBUILD, every 2 ticks while held).
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

	/** The primed dive: degrees pitched down, and how many ticks ahead the ground fires it. */
	private static final float PRIMED_PITCH = 40f;
	private static final int PRIMED_AHEAD = 3;
	/** How far you can be from your crater and still rebuild it (blocks), and ticks between rebuild reports while held. */
	private static final double REBUILD_REACH = 48;
	private static final int REBUILD_EVERY = 2;

	private static Slam slam = Slam.NONE;
	/** Locked into the primed dive (before it fires), and whether the slam that fired was primed. */
	private static boolean primedDive, primedSlam;
	/** Your primed crater while it's lined: its landing block, reach and the game time it goes (-1 none). */
	private static net.minecraft.core.BlockPos crater = net.minecraft.core.BlockPos.ZERO;
	private static int craterReach;
	private static long craterUntil = -1;
	private static int rebuildTick;
	/** Your super jump is primed (P2, crouch on the way down): touchdown locks you on the landing block. */
	private static boolean jumpPrimed;
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

	/** Whether left click belongs to the absorb right now (a shot is held at the ring) or to rebuilding your crater. */
	public static boolean ownsLeftClick(Minecraft mc) {
		return mc.player != null && (holding || rebuildAim(mc) != null);
	}

	/** True locked into the primed dive or its slam (for tests and the first-person arm). */
	public static boolean primed() {
		return primedDive || primedSlam && slam != Slam.NONE;
	}

	/** CombatFx: your super jump was primed. */
	static void jumpPrimed() {
		jumpPrimed = true;
	}

	/** CombatFx: your primed slam touched down; its crater is lined (and rebuildable) for ticks. */
	static void crater(net.minecraft.core.BlockPos centre, int reach, int ticks) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.level == null) return;
		crater = centre;
		craterReach = reach;
		craterUntil = mc.level.getGameTime() + ticks;
	}

	/** Where you're looking on your lined crater, or null. */
	private static @org.jspecify.annotations.Nullable Vec3 rebuildAim(Minecraft mc) {
		LocalPlayer p = mc.player;
		if (p == null || mc.level == null || craterUntil < 0 || mc.level.getGameTime() >= craterUntil || mc.gui.screen() != null) return null;
		Vec3 eye = p.getEyePosition();
		BlockHitResult hit = mc.level.clip(new ClipContext(eye, eye.add(p.getLookAngle().scale(REBUILD_REACH)), ClipContext.Block.OUTLINE,
				ClipContext.Fluid.NONE, p));
		if (hit.getType() == HitResult.Type.MISS) return null;
		Vec3 at = hit.getLocation();
		double dx = at.x - (crater.getX() + 0.5), dz = at.z - (crater.getZ() + 0.5);
		if (Math.abs(dx) > craterReach + 1.5 || Math.abs(dz) > craterReach + 1.5 || Math.abs(at.y - crater.getY()) > 4) return null;
		return at;
	}

	/** Left click held on your lined crater: tells the server where, every couple of ticks. */
	private static void rebuild(Minecraft mc, LocalPlayer p) {
		if (craterUntil >= 0 && mc.level.getGameTime() >= craterUntil) craterUntil = -1;
		if (!mc.options.keyAttack.isDown()) {
			rebuildTick = 0;
			return;
		}
		Vec3 at = rebuildAim(mc);
		if (at == null) return;
		if (rebuildTick++ % REBUILD_EVERY == 0 && ClientPlayNetworking.canSend(CombatPayload.TYPE)) {
			ClientPlayNetworking.send(new CombatPayload(CombatPayload.REBUILD, at, Vec3.ZERO, 0f));
			CombatPoses.rebuild(p.getId());
		}
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
		rebuild(mc, p);
		flurry(p);
		if (jumpPrimed && (p.onGround() || p.isInWater() || p.getAbilities().flying)) {
			// Locked on the landing block for the slam's lock, not carried on into the crater.
			jumpPrimed = false;
			if (p.onGround()) {
				slam = Slam.LOCKED;
				slamAge = 0;
				p.setDeltaMovement(0, Math.min(0, p.getDeltaMovement().y), 0);
			}
		}
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

	/** Checked once a tick in flight: a steep, fast dive near the ground fires the slam (primed with shift in hyper speed). */
	private static void trigger(Minecraft mc, LocalPlayer p) {
		boolean able = p.getAbilities().flying && !p.isInWater() && !p.isPassenger() && !p.isSpectator() && !FlightMoves.controls() && chargedRing(p);
		Vec3 moved = new Vec3(p.getX() - p.xo, p.getY() - p.yo, p.getZ() - p.zo);
		double speed = moved.length();
		boolean diving = able && speed >= MIN_SPEED && moved.y < -0.2;
		// Shift in hyper speed, diving: locked into the primed dive at once (J: "it should lock me into the landing motion").
		boolean prime = diving && mc.options.keyShift.isDown() && FastFlight.hyper() && p.getXRot() >= PRIMED_PITCH;
		if (prime != primedDive) {
			primedDive = prime;
			if (prime) CombatPoses.primeDive(p.getId(), 0);
			else CombatPoses.primeCancel(p.getId());
		}
		if (prime) {
			primed(mc, p, moved);
			return;
		}
		if (!diving || p.getXRot() < MIN_PITCH) return;
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
		primedSlam = false;
		// Out of flight: the slam drops you onto the ground.
		p.getAbilities().flying = false;
		p.onUpdateAbilities();
		if (ClientPlayNetworking.canSend(CombatPayload.TYPE)) {
			ClientPlayNetworking.send(new CombatPayload(CombatPayload.SLAM, feet, moved, slamTicks));
		}
		fall(p);
	}

	/** The primed dive: the ground within PRIMED_AHEAD ticks along the dive fires it into the slam's fall. */
	private static void primed(Minecraft mc, LocalPlayer p, Vec3 moved) {
		Vec3 feet = p.position();
		BlockHitResult ahead = mc.level.clip(new ClipContext(feet, feet.add(moved.scale(PRIMED_AHEAD)), ClipContext.Block.COLLIDER,
				ClipContext.Fluid.ANY, p));
		if (ahead.getType() == HitResult.Type.MISS) return;
		Vec3 land = ahead.getLocation();
		if (ahead.getDirection() != Direction.UP) {
			// Into a wall or a slope: come down on the ground below where it hits.
			BlockHitResult down = mc.level.clip(new ClipContext(land, land.subtract(0, 4, 0), ClipContext.Block.COLLIDER, ClipContext.Fluid.ANY, p));
			if (down.getType() == HitResult.Type.MISS) return;
			land = down.getLocation();
		}
		double fall = Math.max(0.3, feet.y - land.y);
		slamTicks = Mth.clamp((int) Math.ceil(fall / Math.max(0.2, -moved.y)), 1, MAX_TICKS);
		groundY = land.y;
		step = new Vec3((land.x - feet.x) / slamTicks, 0, (land.z - feet.z) / slamTicks);
		slamAge = 0;
		slam = Slam.FALLING;
		primedSlam = true;
		primedDive = false;
		p.getAbilities().flying = false;
		p.onUpdateAbilities();
		if (ClientPlayNetworking.canSend(CombatPayload.TYPE)) {
			ClientPlayNetworking.send(new CombatPayload(CombatPayload.PRIMED_SLAM, feet, moved, slamTicks));
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
