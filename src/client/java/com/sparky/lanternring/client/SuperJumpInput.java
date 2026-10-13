package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.SuperJumps;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.SuperJumpPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.network.chat.Component;
import net.minecraft.util.Mth;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The super jump's controls (server side: SuperJumps). With a charged ring carried and not flying,
 * sprinting charges the jump (J: "I want to have to be sprinting"). Once you've sprinted long
 * enough (RingTuning super_jump_arm) a jump goes super, and the longer you've run the higher it
 * goes, up to 85 blocks at full charge (super_jump_charge); the action bar counts the charge.
 * In the air you steer like flying, WASD along where you look, but gravity is untouched. Player
 * movement is client-side, so the launch and the steering happen here and the server is told.
 * Holding left-click in the air primes the ring for a bigger landing (the server times it).
 */
public final class SuperJumpInput {
	/** Forward speed carried into the jump on top of the run, as a multiple of the run's speed. */
	private static final double CARRY = 1.25;
	/** Mid-air steering: the top speed WASD pushes toward (blocks a tick) and how quickly it gets there. */
	private static final double STEER_SPEED = 0.85, STEER_GRIP = 0.1;

	private static int sprintTicks;
	private static boolean jumpWas, wasOnGround, airborne, priming;
	private static int airTicks;
	private static LabSettings.@Nullable SuperSprint sentSprint;
	private static LabSettings.@Nullable SuperCrater sentCrater;

	private SuperJumpInput() {
	}

	/** How charged the local player's jump is (0..1), or negative while it isn't armed (for the wind-up pose). */
	public static float charge() {
		return SuperJumps.jumpCharge(sprintTicks);
	}

	/** 0..1: how far the local player's sprint has built up (for the run pose). */
	public static float ramp() {
		return SuperJumps.sprintRamp(sprintTicks);
	}

	static void tick(Minecraft mc) {
		LocalPlayer p = mc.player;
		if (p == null || mc.level == null) {
			sprintTicks = 0;
			airborne = false;
			sentSprint = null;
			sentCrater = null;
			return;
		}
		// Tell the server this player's Super sprint pick, on joining and whenever it changes.
		LabSettings.SuperSprint pick = LabSettings.get().superSprint;
		if (pick != sentSprint && ClientPlayNetworking.canSend(SuperJumpPayload.TYPE)) {
			ClientPlayNetworking.send(new SuperJumpPayload(SuperJumpPayload.SPRINT, pick.boost()));
			sentSprint = pick;
		}
		LabSettings.SuperCrater crater = LabSettings.get().superCrater;
		if (crater != sentCrater && ClientPlayNetworking.canSend(SuperJumpPayload.TYPE)) {
			ClientPlayNetworking.send(new SuperJumpPayload(SuperJumpPayload.CRATER, crater.ordinal()));
			sentCrater = crater;
		}
		if (mc.isPaused()) return;

		boolean jumpDown = mc.options.keyJump.isDown();
		boolean pressed = jumpDown && !jumpWas;
		jumpWas = jumpDown;
		boolean grounded = wasOnGround;
		wasOnGround = p.onGround();
		ItemStack ring = chargedRing(p);
		boolean able = ring != null && pick != LabSettings.SuperSprint.OFF && p.getAbilities().flying == false && !p.isFallFlying()
				&& !p.isPassenger() && !p.isInWater() && !p.isSpectator();
		if (airborne) steer(mc, p, able);
		if (!able) {
			sprintTicks = 0;
			return;
		}
		if (!p.isSprinting()) {
			sprintTicks = 0;
			return;
		}
		sprintTicks++;
		float charge = SuperJumps.jumpCharge(sprintTicks);
		// Vanilla has already jumped this tick when the key went down; take that jump over.
		if (pressed && charge >= 0f && grounded && !airborne) {
			launch(p, charge);
			sprintTicks = 0;
			return;
		}
		if (charge >= 0f && p.onGround()) charging(p, ring, charge);
	}

	private static @Nullable ItemStack chargedRing(LocalPlayer p) {
		var inventory = p.getInventory();
		for (int i = 0; i < inventory.getContainerSize(); i++) {
			ItemStack stack = inventory.getItem(i);
			if (stack.getItem() instanceof PowerRingItem && PowerRingItem.getCharge(stack) > 0) return stack;
		}
		return null;
	}

	/** While a sprint charges the jump: the charge on the action bar and light streaming off your heels. */
	private static void charging(LocalPlayer p, ItemStack ring, float charge) {
		p.sendOverlayMessage(Component.translatable("message.lanternring.super_jump_charge", Math.round(charge * 100)));
		RandomSource r = p.getRandom();
		if (r.nextFloat() > 0.3f + 0.7f * charge) return;
		Corps before = CorpsTint.enter(Corps.of(ring));
		try {
			Vec3 back = p.getDeltaMovement().multiply(-2, 0, -2);
			Vec3 at = p.position().add(back).add((r.nextDouble() - 0.5) * 0.6, 0.1 + r.nextDouble() * 0.8, (r.nextDouble() - 0.5) * 0.6);
			LabFx.spawn(charge >= 1f && r.nextInt(3) == 0 ? ModParticles.SPARK : ModParticles.MOTE, at, new Vec3(0, 0.02, 0), 0.6f + 0.5f * charge);
		} finally {
			CorpsTint.restore(before);
		}
	}

	private static void launch(LocalPlayer p, float charge) {
		double height = Mth.lerp(charge, SuperJumps.MIN_HEIGHT, SuperJumps.MAX_HEIGHT);
		Vec3 v = p.getDeltaMovement();
		p.setDeltaMovement(v.x * CARRY, speedFor(height), v.z * CARRY);
		p.setOnGround(false);
		p.sendOverlayMessage(Component.empty());
		airborne = true;
		airTicks = 0;
		if (ClientPlayNetworking.canSend(SuperJumpPayload.TYPE)) {
			ClientPlayNetworking.send(new SuperJumpPayload(SuperJumpPayload.JUMP, charge));
		}
	}

	/** In the air: WASD steers along where you look, like flight, but up and down are left to gravity. */
	private static void steer(Minecraft mc, LocalPlayer p, boolean able) {
		airTicks++;
		if (!able || airTicks > 3 && (p.onGround() || p.isInWater() || p.onClimbable())) {
			airborne = false;
			prime(false);
			return;
		}
		prime(mc.options.keyAttack.isDown() && mc.gui.screen() == null);
		float forward = (mc.options.keyUp.isDown() ? 1 : 0) - (mc.options.keyDown.isDown() ? 1 : 0);
		float strafe = (mc.options.keyLeft.isDown() ? 1 : 0) - (mc.options.keyRight.isDown() ? 1 : 0);
		if (forward == 0 && strafe == 0) return;
		float yaw = p.getYRot() * Mth.DEG_TO_RAD;
		Vec3 ahead = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw));
		Vec3 left = new Vec3(Mth.cos(yaw), 0, Mth.sin(yaw));
		Vec3 want = ahead.scale(forward).add(left.scale(strafe)).normalize().scale(STEER_SPEED);
		Vec3 v = p.getDeltaMovement();
		p.setDeltaMovement(v.x + (want.x - v.x) * STEER_GRIP, v.y, v.z + (want.z - v.z) * STEER_GRIP);
	}

	/** Tells the server when left-click goes down or up in the air. */
	private static void prime(boolean down) {
		if (down == priming) return;
		priming = down;
		if (ClientPlayNetworking.canSend(SuperJumpPayload.TYPE)) ClientPlayNetworking.send(new SuperJumpPayload(SuperJumpPayload.PRIME, down ? 1f : 0f));
	}

	/** The upward speed that peaks at height blocks: each tick you move by it, then lose 0.08 and 2% to drag. */
	static double speedFor(double height) {
		double lo = 0, hi = 8;
		for (int i = 0; i < 40; i++) {
			double mid = (lo + hi) / 2;
			if (peak(mid) < height) lo = mid;
			else hi = mid;
		}
		return hi;
	}

	private static double peak(double v) {
		double y = 0;
		while (v > 0) {
			y += v;
			v = (v - 0.08) * 0.98;
		}
		return y;
	}
}
