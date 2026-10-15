package com.sparky.lanternring.client;

import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.net.MoveFxPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * J's super speed on left click while ring-flying (Blender pass 515, Ring Lab Flight "Super speed"). The local
 * player's movement is client-side, so it runs here and FastFlight flies it (the glide takes this speed whenever it's
 * higher than its own, along where you look, with or without sprint and forward held):
 * <ul>
 * <li>S2 tap burst (J's pick): a click goes straight to 60 b/s with a sonic boom (its ring and 16 construct pixels,
 * SonicBoom), holds it RingTuning super_speed_hold (2 s), then eases back to 20 b/s over super_speed_ease (1 s).
 * Another click on the way down boosts it again.
 * <li>S3 hold to ramp: holding left click ramps 20 to 60 b/s over super_speed_ramp (1.5 s, smoothstep); letting go
 * eases back over super_speed_ease. A hard dive at that speed still fires the pass 510 flight slam: its trigger
 * height becomes max(Ring Lab height, 3 x the fall per tick) at super speed (CombatInput), so the slam keeps its 3 ticks.
 * </ul>
 * Left click is only super speed's when nothing else wants it: not with the crosshair on a creature (that's a punch,
 * the flying flurry), not on a block in reach while hovering (that still mines; in the glide it's super speed), and
 * never while the Anvil, Deluge recall, lantern charge, Lasso, a held absorb shot or your lined crater has it
 * (MinecraftMixin asks those first). Super speed ends when ring flight does, or when the slam takes over.
 * Everyone sees the looks (SuperSpeedFx): the flyer reports it (MoveFxPayload.SUPER) and every client draws it.
 */
public final class SuperSpeedFlight {
	/** Speeds in blocks a tick: 20 b/s (where it eases back to) and 60 b/s (the top). */
	public static final float BASE = 1f, TOP = 3f;
	/** Ticks between the reports to everyone else while it lasts. */
	private static final int REPORT_EVERY = 20;

	private enum State { NONE, BURST, RAMP, EASE }

	private static State state = State.NONE;
	private static int age, reportTick;
	/** The speed now (blocks a tick), and where the ease back started from. */
	private static float speed, easeFrom;
	/** A click super speed took, waiting for this tick (S2), and whether the button was held last tick (S3). */
	private static boolean clicked, wasDown;

	private SuperSpeedFlight() {
	}

	/** True while super speed drives the glide. */
	public static boolean active() {
		return state != State.NONE;
	}

	/** The glide's super speed now, in blocks a tick (0 when off). */
	public static float speed() {
		return state == State.NONE ? 0f : speed;
	}

	/** Whether ring flight can take super speed now. */
	private static boolean able(Minecraft mc, LocalPlayer p) {
		return p.getAbilities().flying && !p.isInWater() && !p.isPassenger() && !p.isSpectator() && !p.isFallFlying()
				&& FlightPoses.carriesRing(p) && !FlightMoves.controls() && !CombatInput.locked() && !PowerSlide.locked();
	}

	/**
	 * Whether a left click (or holding it) is super speed's: in ring flight, nothing else wanting it, the crosshair on
	 * no creature, and on no block in reach unless you're already gliding.
	 */
	public static boolean ownsLeftClick(Minecraft mc) {
		LocalPlayer p = mc.player;
		if (p == null || mc.level == null || mc.gui.screen() != null || !able(mc, p)) return false;
		// Every other left-click use comes first (the same ones MinecraftMixin keeps from hitting and mining).
		if (AnvilInput.ownsLeftClick(mc) || DelugeRecallInput.ownsLeftClick(mc) || LanternChargeInput.ownsLeftClick(mc) || LassoFx.picking(mc)
				|| CombatInput.ownsLeftClick(mc)) return false;
		HitResult hit = mc.hitResult;
		if (hit != null && hit.getType() == HitResult.Type.ENTITY) return false;
		return hit == null || hit.getType() == HitResult.Type.MISS || FastFlight.speed() > 0f || active();
	}

	/** MinecraftMixin: a left click vanilla would swing or mine with. True when super speed takes it instead. */
	public static boolean click(Minecraft mc) {
		if (!ownsLeftClick(mc)) return false;
		clicked = true;
		return true;
	}

	static void tick(Minecraft mc) {
		LocalPlayer p = mc.player;
		if (p == null || mc.level == null) {
			state = State.NONE;
			clicked = wasDown = false;
			return;
		}
		if (mc.isPaused()) return;
		if (!able(mc, p)) {
			stop(p);
			clicked = wasDown = false;
			return;
		}
		boolean down = mc.options.keyAttack.isDown() && ownsLeftClick(mc);
		boolean tap = clicked || down && !wasDown;
		clicked = false;
		wasDown = down;
		int hold = Math.max(1, RingTuning.SUPER_SPEED_HOLD.ticks()), ramp = Math.max(1, RingTuning.SUPER_SPEED_RAMP.ticks());
		int ease = Math.max(1, RingTuning.SUPER_SPEED_EASE.ticks());
		State was = state;
		if (LabSettings.get().superSpeed == LabSettings.SuperSpeed.S3) {
			if (down) {
				if (state != State.RAMP) {
					// Picks the ramp up wherever it is (easing back, or from 20 b/s).
					state = State.RAMP;
					age = Math.round(ramp * inverseSmooth((Math.max(speed, BASE) - BASE) / (TOP - BASE)));
					if (was == State.NONE) age = 0;
				}
				age++;
				speed = BASE + (TOP - BASE) * smooth(age / (float) ramp);
			} else if (state == State.RAMP || state == State.BURST) {
				easeBack();
			}
		} else {
			if (tap) {
				boolean boom = state == State.NONE || speed < TOP - 0.1f;
				state = State.BURST;
				age = 0;
				speed = TOP;
				if (boom) boom(p);
			} else if (state == State.BURST && ++age >= hold) {
				easeBack();
			} else if (state == State.RAMP) {
				easeBack();
			}
		}
		if (state == State.EASE) {
			age++;
			speed = Mth.lerp(Math.min(1f, age / (float) ease), easeFrom, BASE);
			if (age >= ease) state = State.NONE;
		}
		if (state != State.NONE && (was == State.NONE || ++reportTick >= REPORT_EVERY)) {
			reportTick = 0;
			send(p, 1f);
		} else if (state == State.NONE && was != State.NONE) {
			send(p, 0f);
		}
	}

	private static void easeBack() {
		state = State.EASE;
		easeFrom = speed;
		age = 0;
	}

	/** Out of ring flight (or the slam took over): super speed is over at once. */
	private static void stop(LocalPlayer p) {
		if (state == State.NONE) return;
		state = State.NONE;
		send(p, 0f);
	}

	/** S2's sonic boom: the flyer's own crack, jitter and FOV kick, and the ring with its pixels for everyone. */
	private static void boom(LocalPlayer p) {
		Vec3 dir = p.getLookAngle();
		SonicBoom.own(p, dir);
		if (ClientPlayNetworking.canSend(MoveFxPayload.TYPE)) {
			ClientPlayNetworking.send(new MoveFxPayload(MoveFxPayload.BOOM, p.position(), dir, TOP));
		}
	}

	private static void send(LocalPlayer p, float value) {
		if (ClientPlayNetworking.canSend(MoveFxPayload.TYPE)) {
			ClientPlayNetworking.send(new MoveFxPayload(MoveFxPayload.SUPER, p.position(), p.getLookAngle(), value));
		}
	}

	private static float smooth(float t) {
		t = Mth.clamp(t, 0f, 1f);
		return t * t * (3f - 2f * t);
	}

	/** The t whose smoothstep is y (by bisection; it's monotonic on 0..1). */
	private static float inverseSmooth(float y) {
		y = Mth.clamp(y, 0f, 1f);
		float lo = 0f, hi = 1f;
		for (int i = 0; i < 16; i++) {
			float mid = (lo + hi) / 2;
			if (smooth(mid) < y) lo = mid;
			else hi = mid;
		}
		return (lo + hi) / 2;
	}
}
