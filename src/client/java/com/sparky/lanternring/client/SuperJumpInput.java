package com.sparky.lanternring.client;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RingTuning;
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
 * crouch on the ground to wind up; once it's armed (RingTuning super_jump_arm) light gathers at your
 * feet and the action bar counts the charge up to full (super_jump_charge). Press jump (still
 * crouched, or just after letting go) and you're launched: 6 blocks high armed, about 28 at full,
 * and forward along your look if you're holding forward. Player movement is client-side, so the
 * launch happens here and the server is told.
 */
public final class SuperJumpInput {
	/** Heights for a just-armed and a full jump, in blocks. */
	private static final double MIN_HEIGHT = 6, MAX_HEIGHT = 28;
	/** Forward speed at take-off when holding forward (blocks a tick; air drag makes it go about 11 times this). */
	private static final double MIN_FORWARD = 0.35, MAX_FORWARD = 1.15;
	/** Ticks after letting go of crouch that a jump still uses the wind-up. */
	private static final int GRACE = 5;

	private static int crouchTicks, sinceCrouch;
	private static boolean jumpWas;
	private static LabSettings.@Nullable SuperSprint sentSprint;

	private SuperJumpInput() {
	}

	/** 0..1: how wound up the local player is (0 until armed). */
	public static float windup() {
		int arm = RingTuning.SUPER_JUMP_ARM.ticks();
		if (crouchTicks < arm || sinceCrouch > 0) return 0f;
		return charge();
	}

	private static float charge() {
		int arm = RingTuning.SUPER_JUMP_ARM.ticks();
		int full = Math.max(1, RingTuning.SUPER_JUMP_CHARGE.ticks() - arm);
		return Mth.clamp((crouchTicks - arm) / (float) full, 0f, 1f);
	}

	static void tick(Minecraft mc) {
		LocalPlayer p = mc.player;
		if (p == null || mc.level == null) {
			crouchTicks = 0;
			sentSprint = null;
			return;
		}
		// Tell the server this player's Super sprint pick, on joining and whenever it changes.
		LabSettings.SuperSprint sprint = LabSettings.get().superSprint;
		if (sprint != sentSprint && ClientPlayNetworking.canSend(SuperJumpPayload.TYPE)) {
			ClientPlayNetworking.send(new SuperJumpPayload(SuperJumpPayload.SPRINT, sprint.boost()));
			sentSprint = sprint;
		}
		if (mc.isPaused()) return;

		boolean jumpDown = mc.options.keyJump.isDown();
		boolean pressed = jumpDown && !jumpWas;
		jumpWas = jumpDown;
		ItemStack ring = chargedRing(p);
		if (ring == null || mc.gui.screen() != null || p.getAbilities().flying || p.isFallFlying() || p.isPassenger() || p.isInWater()
				|| p.isSpectator()) {
			crouchTicks = 0;
			return;
		}
		boolean armed = crouchTicks >= RingTuning.SUPER_JUMP_ARM.ticks();
		if (pressed && armed) {
			launch(p, charge());
			crouchTicks = 0;
			return;
		}
		if (p.isShiftKeyDown() && p.onGround()) {
			crouchTicks++;
			sinceCrouch = 0;
			if (crouchTicks >= RingTuning.SUPER_JUMP_ARM.ticks()) gather(mc, p, ring, charge());
		} else if (crouchTicks > 0 && ++sinceCrouch > GRACE) {
			crouchTicks = 0;
		}
	}

	private static @Nullable ItemStack chargedRing(LocalPlayer p) {
		var inventory = p.getInventory();
		for (int i = 0; i < inventory.getContainerSize(); i++) {
			ItemStack stack = inventory.getItem(i);
			if (stack.getItem() instanceof PowerRingItem && PowerRingItem.getCharge(stack) > 0) return stack;
		}
		return null;
	}

	/** Light gathering at your feet while wound up, and the charge on the action bar. */
	private static void gather(Minecraft mc, LocalPlayer p, ItemStack ring, float charge) {
		int percent = Math.round(charge * 100);
		p.sendOverlayMessage(Component.translatable("message.lanternring.super_jump_charge", percent));
		RandomSource r = p.getRandom();
		Corps before = CorpsTint.enter(Corps.of(ring));
		try {
			int n = 1 + Math.round(charge * 2);
			for (int i = 0; i < n; i++) {
				double a = r.nextDouble() * Math.PI * 2;
				double d = 0.9 - 0.4 * charge;
				Vec3 at = p.position().add(Math.cos(a) * d, 0.05, Math.sin(a) * d);
				// Drawn in towards your feet, faster as it fills.
				Vec3 in = new Vec3(-Math.cos(a), 0.4, -Math.sin(a)).scale(0.03 + 0.04 * charge);
				LabFx.spawn(charge >= 1f && i == 0 ? ModParticles.SPARK : ModParticles.MOTE, at, in, 0.7f + 0.4f * charge);
			}
		} finally {
			CorpsTint.restore(before);
		}
	}

	private static void launch(LocalPlayer p, float charge) {
		double height = Mth.lerp(charge, MIN_HEIGHT, MAX_HEIGHT);
		double up = speedFor(height);
		Vec3 v = p.getDeltaMovement();
		Vec3 flat = new Vec3(v.x, 0, v.z);
		if (Minecraft.getInstance().options.keyUp.isDown()) {
			float yaw = p.getYRot() * Mth.DEG_TO_RAD;
			double forward = Mth.lerp(charge, MIN_FORWARD, MAX_FORWARD) * (p.isSprinting() ? 1.2 : 1.0);
			flat = new Vec3(-Mth.sin(yaw), 0, Mth.cos(yaw)).scale(forward);
		}
		p.setDeltaMovement(flat.x, up, flat.z);
		p.sendOverlayMessage(Component.empty());
		p.setOnGround(false);
		if (ClientPlayNetworking.canSend(SuperJumpPayload.TYPE)) {
			ClientPlayNetworking.send(new SuperJumpPayload(SuperJumpPayload.JUMP, charge));
		}
	}

	/** The upward speed that peaks at height blocks: each tick you move by it, then lose 0.08 and 2% to drag. */
	static double speedFor(double height) {
		double lo = 0, hi = 6;
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
