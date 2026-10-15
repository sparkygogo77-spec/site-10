package com.sparky.lanternring.client;

import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.CombatPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.Direction;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
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
 * <li>while your primed crater is lined, left click on it is the rebuild's (REBUILD, every 2 ticks while held);
 * <li>pass 502: left click with the ring hand (not in flight) is a punch: posed here at once and passed on (PUNCH) for
 * everyone else to draw;
 * <li>pass 505, the dash strike (Ring Lab R3a-3): left click on a mob out of reach (up to 6.5 blocks, nothing solid in
 * between) leans for RingTuning dash_windup, then dashes up to 4 blocks at it in dash_time (3 ticks, 27 blocks a
 * second), stopping just short; the ring fist lands as the dash ends (DASH_HIT, the server's DashStrikes hurts it).
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
	/** The dash strike: the farthest mob it starts on (eyes to its middle), the longest dash, and how far short of the mob it stops. */
	private static final double DASH_REACH = 6.5, DASH_BLOCKS = 4.0, DASH_STOP = 0.9;
	/** Left click down last tick; the dash's age (-1 none), target, lean and dash ticks, and move per tick. */
	private static boolean attackWasDown;
	private static int dashAge = -1, dashTarget, dashWindup, dashTime;
	private static Vec3 dashStep = Vec3.ZERO;

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
			dashAge = -1;
			absorbSent = holding = attackWasDown = false;
			return;
		}
		absorb(mc, p);
		if (mc.isPaused()) return;
		rebuild(mc, p);
		attack(mc, p);
		dash(p);
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
		ItemStack worn = com.sparky.lanternring.RingSlot.worn(p);
		if (worn.getItem() instanceof PowerRingItem && PowerRingItem.getCharge(worn) > 0) return true;
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

	/** Pass 502 and 505: left click going down with the ring hand punches, or starts the dash strike at a mob out of reach. */
	private static void attack(Minecraft mc, LocalPlayer p) {
		boolean down = mc.gui.screen() == null && mc.options.keyAttack.isDown();
		boolean pressed = down && !attackWasDown;
		attackWasDown = down;
		if (!pressed || dashAge >= 0 || slam != Slam.NONE || p.isSpectator() || p.isUsingItem() || ownsLeftClick(mc)) return;
		if (!(com.sparky.lanternring.RingSlot.ring(p).getItem() instanceof PowerRingItem)) return;
		ItemStack main = p.getMainHandItem();
		if (!main.isEmpty() && !(main.getItem() instanceof PowerRingItem)) return;
		// In flight a hit is the flying flurry's.
		if (p.getAbilities().flying) return;
		if (LabSettings.get().dashStrike == LabSettings.DashStrike.R3A3 && startDash(mc, p)) return;
		CombatPoses.punch(p.getId());
		if (ClientPlayNetworking.canSend(CombatPayload.TYPE)) {
			ClientPlayNetworking.send(new CombatPayload(CombatPayload.PUNCH, p.getEyePosition(), p.getLookAngle(), 0f));
		}
	}

	/** The nearest living thing along your look out of reach but within DASH_REACH, nothing solid in between: dash at it. */
	private static boolean startDash(Minecraft mc, LocalPlayer p) {
		if (!chargedRing(p) || p.isPassenger() || p.isInWater() || mc.hitResult != null && mc.hitResult.getType() == HitResult.Type.ENTITY) return false;
		Vec3 eye = p.getEyePosition();
		Vec3 look = p.getLookAngle();
		LivingEntity best = null;
		double nearest = DASH_REACH;
		for (Entity e : mc.level.getEntities(p, p.getBoundingBox().expandTowards(look.scale(DASH_REACH)).inflate(1.0))) {
			if (!(e instanceof LivingEntity living) || !living.isAlive() || e.isSpectator()) continue;
			Vec3 to = e.getBoundingBox().getCenter().subtract(eye);
			double along = to.dot(look);
			if (along <= 0 || along > nearest || to.subtract(look.scale(along)).length() > 0.6 + e.getBbWidth() / 2) continue;
			best = living;
			nearest = along;
		}
		if (best == null) return false;
		Vec3 mid = best.getBoundingBox().getCenter();
		if (mc.level.clip(new ClipContext(eye, mid, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p)).getType() != HitResult.Type.MISS) return false;
		Vec3 flat = new Vec3(mid.x - p.getX(), 0, mid.z - p.getZ());
		double room = flat.length() - best.getBbWidth() / 2 - DASH_STOP;
		// Close enough to just punch.
		if (room < 1.0) return false;
		dashWindup = RingTuning.DASH_WINDUP.ticks();
		dashTime = Math.max(1, RingTuning.DASH_TIME.ticks());
		dashStep = flat.normalize().scale(Math.min(DASH_BLOCKS, room) / dashTime);
		dashTarget = best.getId();
		dashAge = 0;
		CombatPoses.dash(p.getId(), dashWindup, dashTime);
		DashGhosts.start(p.getId(), com.sparky.lanternring.Corps.of(com.sparky.lanternring.RingSlot.ring(p)), dashWindup, dashTime);
		RingEmit.flash(p, 1f);
		if (ClientPlayNetworking.canSend(CombatPayload.TYPE)) {
			ClientPlayNetworking.send(new CombatPayload(CombatPayload.DASH, p.position(), dashStep, dashTarget));
		}
		return true;
	}

	/** The dash: still through the lean, then dashStep a tick; as it ends the ring fist lands (DASH_HIT) and you stop. */
	private static void dash(LocalPlayer p) {
		if (dashAge < 0) return;
		int age = dashAge++;
		Vec3 v = p.getDeltaMovement();
		if (age < dashWindup) {
			p.setDeltaMovement(v.x * 0.3, v.y, v.z * 0.3);
			return;
		}
		if (age < dashWindup + dashTime) {
			p.setDeltaMovement(dashStep.x, v.y, dashStep.z);
			p.resetFallDistance();
			return;
		}
		dashAge = -1;
		p.setDeltaMovement(v.x * 0.1, v.y, v.z * 0.1);
		RingShake.kick(0.5f, true);
		if (ClientPlayNetworking.canSend(CombatPayload.TYPE)) {
			ClientPlayNetworking.send(new CombatPayload(CombatPayload.DASH_HIT, p.position(), Vec3.ZERO, dashTarget));
		}
	}

	/** Tells the server when left click goes down or up with a ring in hand. */
	private static void absorb(Minecraft mc, LocalPlayer p) {
		boolean ring = com.sparky.lanternring.RingSlot.ring(p).getItem() instanceof PowerRingItem;
		boolean down = ring && mc.gui.screen() == null && mc.options.keyAttack.isDown() && !p.isSpectator();
		if (down != absorbSent && ClientPlayNetworking.canSend(CombatPayload.TYPE)) {
			ClientPlayNetworking.send(new CombatPayload(CombatPayload.ABSORB, p.position(), Vec3.ZERO, down ? 1f : 0f));
			absorbSent = down;
		}
		if (!ring) holding = false;
	}
}
