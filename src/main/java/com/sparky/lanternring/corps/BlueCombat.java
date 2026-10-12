package com.sparky.lanternring.corps;

import com.sparky.lanternring.Corps;
import com.sparky.lanternring.Lasso;
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

	private final CorpsVillager v;
	@Nullable
	private LivingEntity target;
	private int cooldown = 20, raised, swing;
	private double swingAngle;

	BlueCombat(CorpsVillager v) {
		this.v = v;
	}

	/** Whether it's fighting right now (it stands still and doesn't panic). */
	boolean fighting() {
		return target != null || Lasso.npcCaught(v) != null;
	}

	void tick(ServerLevel level) {
		LivingEntity caught = Lasso.npcCaught(v);
		if (caught != null) {
			swing(level, caught);
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
		if (--cooldown > 0 || raised < RAISE) return;
		cooldown = RingTuning.BLUE_ATTACK.ticks() + v.getRandom().nextInt(10);
		double d = v.distanceTo(target);
		float roll = v.getRandom().nextFloat();
		// Lassoing needs both hands free of a construct, so not while it's building.
		if (d <= LASSO_RANGE && !v.building() && roll < 0.4f && lasso(level, target)) return;
		beam(level, target, target.getMaxHealth() >= BIG && roll < 0.75f);
	}

	/** The nearest monster it can see. */
	private @Nullable LivingEntity pick(ServerLevel level) {
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
		Corps before = Corps.enter(Corps.BLUE);
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
		Corps before = Corps.enter(Corps.BLUE);
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
}
