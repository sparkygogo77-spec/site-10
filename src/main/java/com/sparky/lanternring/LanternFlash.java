package com.sparky.lanternring;

import com.sparky.lanternring.ally.ConstructAlly;
import com.sparky.lanternring.net.LanternFlashPayload;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.phys.Vec3;

/**
 * Charging at the lantern is a defence: the light pouring out of the ring is a flashbang in the
 * corps' colour. Everyone near gets told how bright it is, and each client blinds its own screen
 * for as long as it looks at the charger (client LanternFlash). Hostile mobs, and any mob after the
 * charger, that are looking at them lose their target, turn away and stagger off.
 */
public final class LanternFlash {
	/**
	 * How far the light is sent. Clients stop being blinded well before this, but the daylight
	 * drains away round the charger out to client SunDim.STEAL_RADIUS.
	 */
	private static final double RANGE = 96;
	/** How far mobs are dazzled. */
	private static final double MOB_RANGE = 12;
	/** The power of the burst when the ring fills, above the build-up's 1. */
	public static final float BURST = 1.6f;

	private LanternFlash() {
	}

	/**
	 * Called every tick of a lantern charge, {@code held} ticks after right-click went down. The
	 * light starts when the ring touches the lens, swells to full, and bursts as the ring fills.
	 */
	public static void tick(ServerLevel level, ServerPlayer bearer, int held) {
		int contact = LanternCharge.hold() + LanternCharge.reach();
		int done = LanternCharge.done();
		if (held < contact || held > done) return;
		float power;
		float x = (held - contact) / (float) Math.max(1, done - contact);
		// The bearer becomes a sun: the lantern lights everything round them (ChargeLight).
		if (held == done || (held - contact) % 4 == 0) ChargeLight.light(level, bearer, x, held == done);
		if (held == done) {
			power = BURST;
		} else {
			if ((held - contact) % 2 != 0) return;
			power = 0.25f + 0.75f * (float) Math.pow(x, 1.5);
		}
		Corps corps = Corps.of(bearer.getMainHandItem());
		LanternFlashPayload payload = new LanternFlashPayload(bearer.getId(), power, corps.ordinal());
		for (ServerPlayer player : PlayerLookup.around(level, bearer.position(), RANGE)) {
			if (ServerPlayNetworking.canSend(player, LanternFlashPayload.TYPE)) ServerPlayNetworking.send(player, payload);
		}
		if (held == done || (held - contact) % 10 == 0 && power > 0.4f) dazzleMobs(level, bearer, power);
	}

	/** Mobs looking at the charger look away: they drop their target and stumble off, slowed. */
	private static void dazzleMobs(ServerLevel level, ServerPlayer bearer, float power) {
		Vec3 eyes = bearer.getEyePosition();
		for (Mob mob : level.getEntitiesOfClass(Mob.class, bearer.getBoundingBox().inflate(MOB_RANGE), m -> m.isAlive() && !(m instanceof ConstructAlly))) {
			if (!(mob instanceof Enemy) && mob.getTarget() != bearer) continue;
			Vec3 to = eyes.subtract(mob.getEyePosition());
			double dist = to.length();
			if (dist > MOB_RANGE || dist < 1e-3) continue;
			// Only those facing the light (or right up close to it) are caught by it.
			if (mob.getViewVector(1f).dot(to.scale(1 / dist)) < 0.3 && dist > 3) continue;
			if (!mob.hasLineOfSight(bearer)) continue;
			int ticks = Math.round(20 + 40 * Math.min(1f, power));
			mob.setTarget(null);
			mob.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, ticks, power > 1f ? 2 : 1, false, false), bearer);
			mob.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, ticks, 0, false, false), bearer);
			// Turn away from the light and stagger a few blocks off.
			Vec3 away = mob.position().subtract(bearer.position()).multiply(1, 0, 1);
			away = away.lengthSqr() < 1e-4 ? new Vec3(1, 0, 0) : away.normalize();
			Vec3 to2 = mob.position().add(away.scale(6));
			float yaw = (float) (Math.toDegrees(Math.atan2(away.z, away.x)) - 90);
			mob.setYRot(yaw);
			mob.setYHeadRot(yaw);
			mob.getNavigation().moveTo(to2.x, to2.y, to2.z, 1.1);
		}
	}
}
