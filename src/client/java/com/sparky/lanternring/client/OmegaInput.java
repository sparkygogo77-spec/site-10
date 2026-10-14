package com.sparky.lanternring.client;

import com.sparky.lanternring.OmegaBeams;
import com.sparky.lanternring.item.PowerRingItem;
import com.sparky.lanternring.net.OmegaInputPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The omega beams' key (server side: OmegaBeams). Held with a charged ring carried, any corps, it
 * starts the beams in the Ring Lab's Omega start style. Player movement is client side, so the brake
 * to a hover in the air and the slow walk on the ground happen here, for as long as the server holds
 * the body (its OmegaBeams.LOCK modifier). E1 snap also turns the head onto the target at once.
 */
public final class OmegaInput {
	/** How much of the speed is kept each tick while braking: a hard stop, and E3's longer air brake. */
	private static final double BRAKE = 0.5, AIR_BRAKE = 0.82;
	/** The fastest walk while firing (blocks a tick). */
	private static final double SLOW_WALK = 0.045;
	private static boolean held;
	private static OmegaBeams.@Nullable Start start;

	private OmegaInput() {
	}

	static void tick(Minecraft mc, KeyMapping key) {
		LocalPlayer p = mc.player;
		boolean down = p != null && key.isDown() && mc.gui.screen() == null;
		if (!held && down && chargedRing(p) != null && !p.isSpectator()) {
			held = true;
			start = OmegaBeams.Start.values()[LabSettings.get().omegaStart.ordinal()];
			if (ClientPlayNetworking.canSend(OmegaInputPayload.TYPE)) ClientPlayNetworking.send(new OmegaInputPayload(true, start.ordinal()));
			if (start == OmegaBeams.Start.SNAP) snap(mc, p);
		} else if (held && !down) {
			held = false;
			start = null;
			if (p != null && ClientPlayNetworking.canSend(OmegaInputPayload.TYPE)) ClientPlayNetworking.send(new OmegaInputPayload(false, 0));
		}
		if (!held || p == null || mc.isPaused() || !locked(p)) return;
		p.setSprinting(false);
		Vec3 v = p.getDeltaMovement();
		if (p.onGround()) {
			// A slow walk while firing.
			double h = v.horizontalDistance();
			if (h > SLOW_WALK) p.setDeltaMovement(v.x * SLOW_WALK / h, v.y, v.z * SLOW_WALK / h);
		} else {
			double keep = start == OmegaBeams.Start.AIR_BRAKE ? AIR_BRAKE : BRAKE;
			p.setDeltaMovement(v.scale(keep));
		}
	}

	/** Whether the server still holds the body (a barrage's line lets go of it once it is long). */
	private static boolean locked(LocalPlayer p) {
		var speed = p.getAttribute(Attributes.MOVEMENT_SPEED);
		return speed != null && speed.getModifier(OmegaBeams.LOCK) != null;
	}

	/** E1: the head snaps onto the creature nearest the crosshair. */
	private static void snap(Minecraft mc, LocalPlayer p) {
		LivingEntity target = null;
		Vec3 eye = p.getEyePosition();
		Vec3 look = p.getLookAngle();
		double bestCos = Math.cos(Math.toRadians(10));
		for (LivingEntity e : mc.level.getEntitiesOfClass(LivingEntity.class, p.getBoundingBox().inflate(64), e -> e != p && e.isAlive() && !e.isSpectator())) {
			Vec3 to = e.position().add(0, e.getBbHeight() * 0.55, 0).subtract(eye);
			double dist = to.length();
			if (dist < 1 || dist > 64) continue;
			double cos = to.dot(look) / dist;
			if (cos > bestCos) {
				bestCos = cos;
				target = e;
			}
		}
		if (target == null) return;
		Vec3 to = target.position().add(0, target.getBbHeight() * 0.55, 0).subtract(eye);
		float yaw = (float) (Mth.atan2(-to.x, to.z) * Mth.RAD_TO_DEG);
		float pitch = (float) (-Mth.atan2(to.y, to.horizontalDistance()) * Mth.RAD_TO_DEG);
		p.setYRot(yaw);
		p.setXRot(Mth.clamp(pitch, -90f, 90f));
		p.setYHeadRot(yaw);
	}

	private static @Nullable ItemStack chargedRing(LocalPlayer p) {
		var inventory = p.getInventory();
		for (int i = 0; i < inventory.getContainerSize(); i++) {
			ItemStack stack = inventory.getItem(i);
			if (stack.getItem() instanceof PowerRingItem && PowerRingItem.getCharge(stack) > 0) return stack;
		}
		return null;
	}
}
