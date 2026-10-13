package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.Lasso;
import com.sparky.lanternring.ModParticles;
import com.sparky.lanternring.RingFx;
import com.sparky.lanternring.RingPowers;
import com.sparky.lanternring.RingTuning;
import com.sparky.lanternring.ally.ConstructAlly;
import com.sparky.lanternring.net.RingFxPayload.Kind;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.level.Explosion;
import net.minecraft.world.level.ExplosionDamageCalculator;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * How a Blue Lantern villager fights (J, 2026-10-12): it stands its ground, points its ring at the
 * monster and fires the ring's Beam (a small blast where it hits), a charged Beam with a bigger
 * blast at big monsters, or throws its lasso, swings the mob round over its head and flings it
 * away in a long arc so the bubble slams down far from the village. Every attack comes out of the
 * ring on its right hand, which the client draws (BlueVillagerRenderer) with the arm pointing at
 * the target. Its blasts and flung mobs only hurt monsters, never players, villagers or animals,
 * and never break blocks.
 */
final class BlueCombat {
	/** How far it sees monsters to fight, and how close one has to be to lasso. */
	private static final double SIGHT = 24, LASSO_RANGE = 16;
	/** Ticks the ring arm takes to come up before the first shot. */
	private static final int RAISE = 6;
	private static final float BEAM_DAMAGE = 7f, CHARGED_DAMAGE = 15f;
	/** Monsters with this much health or more get the charged Beam. */
	private static final float BIG = 40f;
	/** The lasso's swing over its head: height above the head, radius, and turn per tick. */
	private static final double SWING_HEIGHT = 3.5, SWING_RADIUS = 3.2, SWING_TURN = 0.32;
	/** The fling: speed out and up (blocks per tick); the bubble falls in an arc and slams down. */
	private static final double FLING_OUT = 0.75, FLING_UP = 1.35;
	/** A flyer's slam: how high it lifts the bubble, for how many ticks, and how fast it drives it down. */
	private static final double SLAM_HEIGHT = 6, SLAM_SPEED = 2.6;
	private static final int SLAM_LIFT = 24;
	/**
	 * The warrior's hammer leap (J, 2026-10-13: 22): how near and far a monster has to be, how many
	 * ticks the arc lasts, the shockwave's reach, and the inner part where monsters are smashed
	 * down instead of blown away.
	 */
	private static final double LEAP_MIN = 3, LEAP_MAX = 12, SMASH_REACH = 5.5, SMASH_CORE = 2.6;
	private static final int LEAP_TICKS = 14, LEAP_COOLDOWN = 70;
	private static final float SMASH_DAMAGE = 14f, EDGE_DAMAGE = 6f;

	private final CorpsVillager v;
	@Nullable
	private LivingEntity target;
	private int cooldown = 20, raised, swing;
	private double swingAngle;
	/** Where a flyer's lassoed mob was caught: it's lifted straight up over it and slammed back down. */
	@Nullable
	private Vec3 slamFrom;
	/** The warrior's leap: ticks into it (0 when on its feet), where it took off and where it lands. */
	private int leap, leapRest;
	@Nullable
	private Vec3 leapFrom, leapTo;

	BlueCombat(CorpsVillager v) {
		this.v = v;
	}

	/** Whether it's fighting right now (it stands still and doesn't panic). */
	boolean fighting() {
		return target != null || Lasso.npcCaught(v) != null;
	}

	void tick(ServerLevel level) {
		// A rescue flyer carrying someone in holds its bubble gently, it doesn't swing or fling it.
		if (BlueRescue.carrying(v) || BluePrison.carrying(v)) {
			target = null;
			return;
		}
		if (leap > 0) {
			leap(level);
			return;
		}
		if (leapRest > 0) leapRest--;
		LivingEntity caught = Lasso.npcCaught(v);
		if (caught != null) {
			// A rescue squad's flyer slams it into the ground to be caged (J: 21a); others fling it away.
			if (v.squadRole() == BlueSquad.Role.FLYER) slam(level, caught);
			else swing(level, caught);
			return;
		}
		swing = 0;
		if (target != null && (!target.isAlive() || Lasso.isCaught(target) || v.distanceToSqr(target) > SIGHT * SIGHT * 1.5)) target = null;
		if (target == null || v.tickCount % 10 == 0) target = pick(level);
		if (target == null) {
			raised = 0;
			v.aimAt(null);
			return;
		}
		v.aimAt(target);
		v.getLookControl().setLookAt(target, 30f, 30f);
		raised++;
		// A squad warrior leaps in with its construct hammer whenever it can (J: 22), between its ring shots.
		if (v.squadRole() == BlueSquad.Role.WARRIOR && leapRest == 0 && v.onGround() && target.onGround()) {
			double gap = v.distanceTo(target);
			if (gap >= LEAP_MIN && gap <= LEAP_MAX) {
				startLeap(level, target);
				return;
			}
		}
		if (--cooldown > 0 || raised < RAISE) return;
		cooldown = RingTuning.BLUE_ATTACK.ticks() + v.getRandom().nextInt(10);
		double d = v.distanceTo(target);
		float roll = v.getRandom().nextFloat();
		// Lassoing needs both hands free of a construct, so not while it's building.
		float lassoChance = v.squadRole() == BlueSquad.Role.FLYER ? 0.65f : 0.4f;
		if (d <= LASSO_RANGE && !v.building() && roll < lassoChance && lasso(level, target)) return;
		beam(level, target, target.getMaxHealth() >= BIG && roll < 0.75f);
	}

	/** The nearest monster it can see. */
	private @Nullable LivingEntity pick(ServerLevel level) {
		// In a rescue squad it goes for the monster its role picked (see BlueSquad).
		LivingEntity focus = v.squadFocus();
		if (focus != null && !Lasso.isCaught(focus) && v.distanceToSqr(focus) < SIGHT * SIGHT && v.hasLineOfSight(focus)) return focus;
		LivingEntity best = null;
		double bestD = SIGHT * SIGHT;
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, v.getBoundingBox().inflate(SIGHT), ConstructAlly::isBadMob)) {
			if (Lasso.isCaught(e)) continue;
			double d = v.distanceToSqr(e);
			if (d < bestD && v.hasLineOfSight(e)) {
				bestD = d;
				best = e;
			}
		}
		return best;
	}

	// ---- the Beam ------------------------------------------------------------------------------

	private void beam(ServerLevel level, LivingEntity target, boolean charged) {
		Vec3 hit = target.getBoundingBox().getCenter();
		Vec3 from = CorpsVillager.ringPos(v, 1f, hit);
		Corps before = Corps.enter(v.corps());
		try {
			RingFx.send(level, charged ? Kind.BEAM_CHARGED : Kind.BEAM, from, hit);
			RingPowers.lightShot(level, from, hit);
		} finally {
			Corps.restore(before);
		}
		v.fired();
		Vec3 push = hit.subtract(from).normalize();
		target.hurtServer(level, level.damageSources().indirectMagic(v, v), charged ? CHARGED_DAMAGE : BEAM_DAMAGE);
		target.push(push.x * 0.6, 0.2, push.z * 0.6);
		RingPowers.syncVelocity(target);
		// A blast at the hit: shakes and throws monsters, leaves blocks, people and animals alone.
		level.explode(v, null, MONSTERS_ONLY, hit.x, hit.y, hit.z, charged ? 3f : 1.5f, false, Level.ExplosionInteraction.NONE);
		level.playSound(null, v.getX(), v.getY(), v.getZ(), SoundEvents.BEACON_ACTIVATE, SoundSource.NEUTRAL,
				charged ? 1.2f : 0.8f, charged ? 1.0f : 2.0f);
	}

	private static final ExplosionDamageCalculator MONSTERS_ONLY = new ExplosionDamageCalculator() {
		@Override
		public boolean shouldDamageEntity(Explosion explosion, Entity entity) {
			return entity instanceof LivingEntity l && ConstructAlly.isBadMob(l) && super.shouldDamageEntity(explosion, entity);
		}

		@Override
		public float getKnockbackMultiplier(Entity entity) {
			return entity instanceof LivingEntity l && ConstructAlly.isBadMob(l) ? super.getKnockbackMultiplier(entity) : 0f;
		}
	};

	// ---- the lasso -----------------------------------------------------------------------------

	private boolean lasso(ServerLevel level, LivingEntity target) {
		if (!Lasso.npcCatch(level, v, target)) return false;
		Vec3 from = CorpsVillager.ringPos(v, 1f, target.getBoundingBox().getCenter());
		Corps before = Corps.enter(v.corps());
		try {
			RingFx.send(level, Kind.TETHER, from, target.getBoundingBox().getCenter());
		} finally {
			Corps.restore(before);
		}
		v.fired();
		swing = 0;
		Vec3 off = target.position().subtract(v.position());
		swingAngle = Math.atan2(off.z, off.x);
		return true;
	}

	/**
	 * A flyer's capture: it hauls the bubble up under itself, holds it a moment, then drives it
	 * straight down into the ground (the slam hurts it) and the cage closes on it (BlueCage).
	 */
	private void slam(ServerLevel level, LivingEntity caught) {
		v.aimAt(caught);
		swing++;
		if (swing == 1) {
			slamFrom = caught.position();
			level.playSound(null, caught.blockPosition(), SoundEvents.BEACON_POWER_SELECT, SoundSource.NEUTRAL, 1f, 1.6f);
		}
		Vec3 base = slamFrom == null ? caught.position() : slamFrom;
		Vec3 hold = new Vec3(base.x, base.y + SLAM_HEIGHT + caught.getBbHeight() / 2, base.z);
		Lasso.npcHold(v, hold);
		v.getLookControl().setLookAt(hold.x, hold.y, hold.z);
		if (swing < SLAM_LIFT) return;
		Lasso.npcFling(v, new Vec3(0, -SLAM_SPEED, 0));
		BlueCage.slammed(level, caught);
		v.fired();
		level.playSound(null, v.getX(), v.getY(), v.getZ(), SoundEvents.TRIDENT_RIPTIDE_3, SoundSource.NEUTRAL, 1f, 0.8f);
		cooldown = RingTuning.BLUE_ATTACK.ticks();
		swing = 0;
		slamFrom = null;
	}

	/** Hauls the bubble up over its head and round, then lets it fly. */
	private void swing(ServerLevel level, LivingEntity caught) {
		v.aimAt(caught);
		swing++;
		// It winds up faster as it goes, like a hammer thrower.
		swingAngle += SWING_TURN * Math.min(1, 0.4 + swing / 20.0);
		double r = SWING_RADIUS * Math.min(1, swing / 10.0 + 0.3);
		Vec3 over = v.position().add(Math.cos(swingAngle) * r, v.getBbHeight() + SWING_HEIGHT, Math.sin(swingAngle) * r);
		Lasso.npcHold(v, over);
		v.getLookControl().setLookAt(over.x, over.y, over.z);
		if (swing < Math.max(10, RingTuning.BLUE_LASSO_SWING.ticks())) return;
		// Away from home, so the mob comes down outside the village.
		Vec3 out = caught.position().subtract(Vec3.atBottomCenterOf(v.homePos()));
		out = new Vec3(out.x, 0, out.z);
		if (out.lengthSqr() < 4) out = new Vec3(Math.cos(swingAngle), 0, Math.sin(swingAngle));
		out = out.normalize();
		Lasso.npcFling(v, out.scale(FLING_OUT).add(0, FLING_UP, 0));
		v.fired();
		cooldown = RingTuning.BLUE_ATTACK.ticks();
		swing = 0;
	}

	// ---- the warrior's hammer ------------------------------------------------------------------

	/** Whether it's in the air on a hammer leap (it doesn't walk meanwhile). */
	boolean leaping() {
		return leap > 0;
	}

	/** Crouches and springs at the monster, a hammer of light forming over its head. */
	private void startLeap(ServerLevel level, LivingEntity target) {
		Vec3 from = v.position();
		Vec3 flat = new Vec3(target.getX() - from.x, 0, target.getZ() - from.z);
		double d = flat.length();
		// It lands just short of the monster so the hammer comes down on it.
		Vec3 land = from.add(flat.normalize().scale(Math.max(0, d - 1.4)));
		land = new Vec3(land.x, BlueSquad.groundY(level, land.x, land.z, target.getY()), land.z);
		leapFrom = from;
		leapTo = land;
		leap = 1;
		v.getNavigation().stop();
		v.fired();
		level.playSound(null, v.getX(), v.getY(), v.getZ(), SoundEvents.MACE_SMASH_AIR, SoundSource.NEUTRAL, 1f, 0.8f);
		level.sendParticles(ModParticles.of(ModParticles.MOTE, Corps.BLUE), from.x, from.y + 0.1, from.z, 10, 0.4, 0.05, 0.4, 0.05);
	}

	private void leap(ServerLevel level) {
		if (leapFrom == null || leapTo == null) {
			leap = 0;
			return;
		}
		double t = Math.min(1, leap / (double) LEAP_TICKS);
		double span = leapFrom.distanceTo(leapTo);
		double peak = 3 + span * 0.25;
		Vec3 at = leapFrom.lerp(leapTo, t).add(0, 4 * peak * t * (1 - t), 0);
		Vec3 dir = new Vec3(leapTo.x - leapFrom.x, 0, leapTo.z - leapFrom.z);
		if (dir.lengthSqr() < 1e-4) dir = Vec3.directionFromRotation(0, v.getYRot());
		dir = dir.normalize();
		v.getNavigation().stop();
		v.teleportTo(at.x, at.y, at.z);
		v.setDeltaMovement(Vec3.ZERO);
		v.resetFallDistance();
		float yaw = (float) Math.toDegrees(Math.atan2(-dir.x, dir.z));
		v.setYRot(yaw);
		v.setYHeadRot(yaw);
		v.yBodyRot = yaw;
		hammer(level, at, dir, t);
		if (leap++ >= LEAP_TICKS) {
			leap = 0;
			leapRest = LEAP_COOLDOWN + v.getRandom().nextInt(30);
			smash(level, leapTo, dir);
		}
	}

	/** The hammer of light: lifted behind its head on the way up, swung down in front as it lands. */
	private void hammer(ServerLevel level, Vec3 at, Vec3 dir, double t) {
		// The swing: from straight back over the head (t 0.5) down to the ground in front (t 1).
		double swingT = Math.max(0, (t - 0.5) * 2);
		double angle = Math.PI * (0.85 - 0.85 * swingT) - Math.PI * 0.35 * swingT;
		Vec3 grip = at.add(0, 1.4, 0);
		Vec3 reach = dir.scale(-Math.cos(angle)).add(0, Math.sin(angle), 0).normalize();
		var mote = ModParticles.of(ModParticles.MOTE, Corps.BLUE);
		for (int i = 1; i <= 4; i++) {
			Vec3 p = grip.add(reach.scale(i * 0.45));
			level.sendParticles(mote, p.x, p.y, p.z, 1, 0, 0, 0, 0);
		}
		// The head: a block of light across the handle's end.
		Vec3 head = grip.add(reach.scale(2.2));
		Vec3 side = new Vec3(-dir.z, 0, dir.x);
		for (int i = -2; i <= 2; i++) {
			Vec3 p = head.add(side.scale(i * 0.22));
			level.sendParticles(mote, p.x, p.y, p.z, 2, 0.12, 0.12, 0.12, 0);
		}
	}

	/**
	 * The hammer lands: monsters right in front are smashed down into the dirt (hard hit, pinned
	 * slow); those out at the shockwave's edge are blown away. The ground cracks and throws up dirt,
	 * but no block is broken (the squad never wrecks what it's guarding).
	 */
	private void smash(ServerLevel level, Vec3 land, Vec3 dir) {
		Vec3 centre = land.add(dir.scale(1.6));
		for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, new net.minecraft.world.phys.AABB(centre, centre).inflate(SMASH_REACH, 3, SMASH_REACH), ConstructAlly::isBadMob)) {
			Vec3 off = new Vec3(e.getX() - centre.x, 0, e.getZ() - centre.z);
			double r = off.length();
			if (r > SMASH_REACH) continue;
			if (r <= SMASH_CORE) {
				e.hurtServer(level, level.damageSources().indirectMagic(v, v), SMASH_DAMAGE);
				e.setDeltaMovement(0, -1.2, 0);
				e.addEffect(new net.minecraft.world.effect.MobEffectInstance(net.minecraft.world.effect.MobEffects.SLOWNESS, 60, 4));
				net.minecraft.world.level.block.state.BlockState under = level.getBlockState(e.blockPosition().below());
				if (!under.isAir()) level.sendParticles(new net.minecraft.core.particles.BlockParticleOption(net.minecraft.core.particles.ParticleTypes.BLOCK, under),
						e.getX(), e.getY() + 0.2, e.getZ(), 25, 0.4, 0.2, 0.4, 0.2);
			} else {
				e.hurtServer(level, level.damageSources().indirectMagic(v, v), EDGE_DAMAGE);
				Vec3 out = r < 1e-3 ? dir : off.normalize();
				double power = 1.1 + (r - SMASH_CORE) / (SMASH_REACH - SMASH_CORE) * 0.8;
				e.setDeltaMovement(out.x * power, 0.75, out.z * power);
			}
			RingPowers.syncVelocity(e);
		}
		Corps before = Corps.enter(Corps.BLUE);
		try {
			RingFx.send(level, Kind.SHOCKWAVE, centre, centre.add(SMASH_REACH, 0, 0));
		} finally {
			Corps.restore(before);
		}
		// Cracked ground: dirt thrown up in a ring and a burst of the ground's own block.
		net.minecraft.world.level.block.state.BlockState ground = level.getBlockState(net.minecraft.core.BlockPos.containing(centre.x, centre.y - 0.5, centre.z));
		if (!ground.isAir()) {
			var dust = new net.minecraft.core.particles.BlockParticleOption(net.minecraft.core.particles.ParticleTypes.BLOCK, ground);
			level.sendParticles(dust, centre.x, centre.y + 0.1, centre.z, 60, 1.2, 0.1, 1.2, 0.35);
			for (int i = 0; i < 24; i++) {
				double a = i * Math.PI * 2 / 24;
				level.sendParticles(dust, centre.x + Math.cos(a) * SMASH_REACH * 0.8, centre.y + 0.1, centre.z + Math.sin(a) * SMASH_REACH * 0.8, 3, 0.2, 0.05, 0.2, 0.15);
			}
		}
		level.playSound(null, centre.x, centre.y, centre.z, SoundEvents.MACE_SMASH_GROUND_HEAVY, SoundSource.NEUTRAL, 1.4f, 0.8f);
		level.playSound(null, centre.x, centre.y, centre.z, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.NEUTRAL, 1f, 0.6f);
		cooldown = RingTuning.BLUE_ATTACK.ticks();
	}
}
