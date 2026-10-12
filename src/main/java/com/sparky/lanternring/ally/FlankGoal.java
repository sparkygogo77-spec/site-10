package com.sparky.lanternring.ally;

import java.util.EnumSet;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

/**
 * With nothing to fight, a ground ally walks to its guard slot beside its owner (see
 * Formation.flankSlot) and holds it. The slots turn with the way the owner walks, not every flick
 * of their camera, so the guards don't run in circles while you look around. Walking, they march
 * facing your way; when you stop they turn outward and watch your sides. Too far to walk, it
 * reforms in its slot.
 */
final class FlankGoal extends Goal {
	private final ConstructAlly ally;
	private final double speed;
	private Vec3 heading = new Vec3(0, 0, 1);
	private Vec3 slot = Vec3.ZERO;
	private int repath;

	FlankGoal(ConstructAlly ally, double speed) {
		this.ally = ally;
		this.speed = speed;
		setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK));
	}

	@Override
	public boolean canUse() {
		Player owner = ally.owner();
		return owner != null && !owner.isSpectator() && ally.getTarget() == null && ally.distanceToSqr(owner) < 96 * 96;
	}

	@Override
	public boolean canContinueToUse() {
		return canUse();
	}

	@Override
	public void start() {
		repath = 0;
		Player owner = ally.owner();
		if (owner != null) heading = Formation.forward(owner);
	}

	@Override
	public void stop() {
		ally.getNavigation().stop();
	}

	@Override
	public boolean requiresUpdateEveryTick() {
		return true;
	}

	@Override
	public void tick() {
		Player owner = ally.owner();
		if (owner == null) return;
		Vec3 motion = ally.ownerMotion().multiply(1, 0, 1);
		boolean walking = motion.lengthSqr() > 0.06 * 0.06;
		if (walking) heading = heading.lerp(motion.normalize(), 0.2).normalize();
		Vec3 want = Formation.flankSlot(owner, heading, ally.place());
		double dist = ally.position().multiply(1, 0, 1).distanceTo(want.multiply(1, 0, 1));

		if (dist > 28 && owner.onGround()) {
			ally.snapTo(want.x, owner.getY(), want.z, ally.getYRot(), ally.getXRot());
			ally.getNavigation().stop();
			return;
		}
		if (dist > 1.2) {
			if (--repath <= 0 || want.distanceToSqr(slot) > 1.5 * 1.5) {
				repath = 10;
				slot = want;
				// Catches up at a run when it has fallen behind.
				ally.getNavigation().moveTo(want.x, want.y, want.z, dist > 7 ? speed * 1.4 : speed);
			}
		} else if (!ally.getNavigation().isDone()) {
			ally.getNavigation().stop();
		}

		Vec3 eye = ally.getEyePosition();
		if (walking || dist > 1.2) {
			// Marching: eyes front, the way you're heading.
			ally.getLookControl().setLookAt(eye.x + heading.x * 8, eye.y, eye.z + heading.z * 8);
		} else {
			// Holding: faces out from you, watching your flank (or your back).
			Vec3 out = ally.position().subtract(owner.position()).multiply(1, 0, 1);
			if (out.lengthSqr() < 0.01) out = heading;
			out = out.normalize();
			ally.getLookControl().setLookAt(eye.x + out.x * 8, eye.y, eye.z + out.z * 8);
		}
	}
}
