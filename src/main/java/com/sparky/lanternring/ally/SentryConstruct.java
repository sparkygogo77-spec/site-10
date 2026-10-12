package com.sparky.lanternring.ally;

import com.sparky.lanternring.ModParticles;
import java.util.List;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The Sentry construct: a spiked hard-light eye that guards the spot it was summoned. It drifts
 * in a slow loop around that spot, and shoots any hostile mob that comes near with a beam that
 * hits lightly but knocks the mob flying. It never breaks blocks and stays put when its owner
 * leaves, so it can watch a base or a farm while you do something else.
 */
public class SentryConstruct extends FlyingConstruct {
	private static final float BEAM_DAMAGE = 4f;
	/** How far from its post it looks for mobs. */
	public static final double GUARD_RANGE = 20;

	/** Client side: spikes out while it has a target, and its tail sways. */
	public float spikes;
	public float oSpikes;
	public float tail;
	public float oTail;

	public SentryConstruct(EntityType<? extends SentryConstruct> type, Level level) {
		super(type, level);
		xpReward = 0;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Mob.createMobAttributes()
				.add(Attributes.MAX_HEALTH, 200)
				.add(Attributes.MOVEMENT_SPEED, 0.4)
				.add(Attributes.FLYING_SPEED, 0.4)
				.add(Attributes.FOLLOW_RANGE, GUARD_RANGE);
	}

	@Override
	public Formation.Stance stance() {
		return Formation.Stance.PICKET;
	}

	/** Sentries summoned within this many blocks of each other share one post. */
	private static final double SHARED_POST = 10;

	/** The middle of the post it shares with the sentries summoned near it (its own home if alone). */
	@Nullable
	private Vec3 post;
	/** Where the picket faces: the owner's heading, smoothed so it doesn't swing with every look. */
	private Vec3 heading = new Vec3(0, 0, 1);
	private boolean picket;

	@Override
	protected boolean sameGroup(ConstructAlly other) {
		return other instanceof SentryConstruct s && home != null && s.home != null && s.home.distanceToSqr(home) < SHARED_POST * SHARED_POST;
	}

	@Override
	protected void formed(List<ConstructAlly> group) {
		Vec3 sum = Vec3.ZERO;
		int n = 0;
		for (ConstructAlly ally : group) {
			if (ally instanceof SentryConstruct s && s.home != null) {
				sum = sum.add(s.home);
				n++;
			}
		}
		post = n == 0 ? home : sum.scale(1.0 / n);
	}

	@Override
	protected Vec3 goal(@Nullable LivingEntity target) {
		Vec3 post = this.post != null ? this.post : home;
		Formation.Place place = place();
		Player owner = owner();
		double bob = Math.sin(tickCount * 0.06) * 0.6;
		picket = target == null && owner != null && owner.distanceToSqr(post) < GUARD_RANGE * GUARD_RANGE * 0.64;
		if (picket) {
			// You're at the post: they fan out in an arc a few blocks ahead of you, the middle
			// one furthest out, and screen the way you're facing.
			heading = heading.lerp(Formation.forward(owner), 0.08).normalize();
			double spread = place.spread();
			double side = spread * 1.6 * (place.count() - 1);
			Vec3 at = Formation.around(owner, heading, side, 5 - Math.abs(spread) * 1.5, 2.2 + bob);
			// Never so far that it leaves its post behind.
			Vec3 off = at.subtract(post);
			double leash = GUARD_RANGE * 0.6;
			return off.lengthSqr() > leash * leash ? post.add(off.normalize().scale(leash)) : at;
		}
		// Alone at the post: they share a slow ring round it, evenly spaced and staggered in
		// height, each one looking outward like a lighthouse. Faster while they fight.
		double a = level().getGameTime() * (target != null ? 0.03 : 0.018) + place.phase();
		double radius = 4 + (place.count() - 1);
		return post.add(Math.cos(a) * radius, bob + (place.index() % 2) * 1.2, Math.sin(a) * radius);
	}

	@Override
	@Nullable
	protected Vec3 idleLook() {
		if (picket) return position().add(heading.scale(10)).add(0, -1, 0);
		Vec3 post = this.post != null ? this.post : home;
		if (post == null) return null;
		Vec3 out = position().subtract(post).multiply(1, 0, 1);
		return out.lengthSqr() < 0.01 ? null : position().add(out.normalize().scale(10)).add(0, -0.5, 0);
	}

	@Override
	public boolean canAttack(LivingEntity target) {
		return super.canAttack(target) && (home == null || target.distanceToSqr(home) < GUARD_RANGE * GUARD_RANGE);
	}

	@Override
	protected double maxSpeed() {
		return 0.25;
	}

	@Override
	protected double shotRange() {
		return GUARD_RANGE;
	}

	@Override
	protected int shotInterval() {
		return 20;
	}

	@Override
	protected void shoot(ServerLevel level, LivingEntity target, Vec3 from) {
		playSound(SoundEvents.GUARDIAN_ATTACK, 1f, 1.6f);
		playSound(SoundEvents.BEACON_ACTIVATE, 0.6f, 2f);
		Vec3 at = target.position().add(0, target.getBbHeight() * 0.5, 0);
		level.sendParticles(ModParticles.SPARK, at.x, at.y, at.z, 10, 0.3, 0.3, 0.3, 0.25);
		if (target.hurtServer(level, level.damageSources().indirectMagic(this, owner() != null ? owner() : this), BEAM_DAMAGE)) {
			// Knocks it flying, away from the sentry.
			Vec3 dir = at.subtract(from).multiply(1, 0, 1).normalize();
			target.push(dir.x * 1.9, 0.8, dir.z * 1.9);
			WardenConstruct.knock(target);
		}
	}

	@Override
	public void tick() {
		super.tick();
		if (level().isClientSide()) {
			oSpikes = spikes;
			oTail = tail;
			spikes += ((aimed() != null ? 1f : 0.25f) - spikes) * 0.15f;
			tail += 0.12f;
		}
	}
}
