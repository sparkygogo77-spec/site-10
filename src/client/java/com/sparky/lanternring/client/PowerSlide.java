package com.sparky.lanternring.client;

import com.sparky.lanternring.PowerLandings;
import com.sparky.lanternring.net.RingFxPayload;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.world.phys.Vec3;

/**
 * The local player's side of the power landing (PowerLandings): no run-out after a super jump.
 * At touchdown it holds you still until the server's POWER_LAND says how you land; then you either
 * stay stopped dead or skid along the slide, slowing at a constant rate and held level over the
 * trench being cleared under you, and halt on the block it ends over. The movement keys do nothing
 * meanwhile (LocalPlayerMixin). Player movement is client-side, so the slide happens here.
 */
public final class PowerSlide {
	/** Ticks to wait for the server's word, and to stand still after a slide and after stopping dead. */
	private static final int WAIT = 4, HOLD_SLIDE = 6, HOLD_STOP = 10;

	private enum State { NONE, WAITING, SLIDING, HOLDING }

	private static State state = State.NONE;
	private static int ticks, slideTicks, hold;
	private static Vec3 from = Vec3.ZERO, dir = Vec3.ZERO;
	private static double length, levelY;

	private PowerSlide() {
	}

	/** Whether the landing has the movement keys. */
	public static boolean locked() {
		return state != State.NONE;
	}

	/** Whether the local player is skidding along a slide right now. */
	static boolean sliding() {
		return state == State.SLIDING;
	}

	/** A super jump just touched down: stop where you are until the server says how you land. */
	static void touchdown(LocalPlayer p) {
		state = State.WAITING;
		ticks = 0;
		stop(p);
	}

	/** The server's POWER_LAND for the local player. */
	static void start(LocalPlayer p, RingFxPayload fx) {
		ticks = 0;
		Vec3 d = fx.to().subtract(fx.from());
		length = Math.sqrt(d.x * d.x + d.z * d.z);
		if (fx.variant() == PowerLandings.STOP || length < 0.05) {
			state = State.HOLDING;
			hold = HOLD_STOP;
			stop(p);
			return;
		}
		state = State.SLIDING;
		dir = new Vec3(d.x / length, 0, d.z / length);
		from = p.position();
		levelY = p.getY();
		slideTicks = PowerLandings.slideTicks(length, fx.value());
		stop(p);
	}

	static void tick(Minecraft mc) {
		LocalPlayer p = mc.player;
		if (p == null || mc.level == null || p.getAbilities().flying || p.isInWater() || p.isPassenger()) {
			state = State.NONE;
			return;
		}
		if (mc.isPaused() || state == State.NONE) return;
		switch (state) {
			case WAITING -> {
				stop(p);
				if (++ticks > WAIT) state = State.NONE;
			}
			case SLIDING -> step(p);
			case HOLDING -> {
				stop(p);
				if (++ticks >= hold) state = State.NONE;
			}
			default -> {
			}
		}
	}

	/** Sets the next tick's move along the slide; past its end (or blocked), holds you there. */
	private static void step(LocalPlayer p) {
		Vec3 was = from.add(dir.scale(PowerLandings.forward(length, slideTicks, ticks)));
		// Something stopped you short (a wall the server didn't see coming): halt here.
		if (ticks > 0 && Math.abs(p.getX() - was.x) + Math.abs(p.getZ() - was.z) > 0.6) {
			hold(p);
			return;
		}
		ticks++;
		Vec3 target = from.add(dir.scale(PowerLandings.forward(length, slideTicks, ticks)));
		// Level over the trench: the construct pad under the planted foot holds you up.
		p.setDeltaMovement(target.x - p.getX(), levelY - p.getY(), target.z - p.getZ());
		p.resetFallDistance();
		if (ticks >= slideTicks) {
			state = State.HOLDING;
			ticks = 0;
			hold = HOLD_SLIDE;
		}
	}

	private static void hold(LocalPlayer p) {
		state = State.HOLDING;
		ticks = 0;
		hold = HOLD_SLIDE;
		stop(p);
	}

	private static void stop(LocalPlayer p) {
		Vec3 v = p.getDeltaMovement();
		p.setDeltaMovement(0, v.y, 0);
	}
}
