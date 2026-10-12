package com.sparky.lanternring.ally;

import java.util.EnumSet;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.player.Player;

/** With nothing to fight, walks back to its owner, and jumps to them if they get far away. */
final class FollowOwnerGoal extends Goal {
	private final ConstructAlly ally;
	private final double speed;
	private int repath;

	FollowOwnerGoal(ConstructAlly ally, double speed) {
		this.ally = ally;
		this.speed = speed;
		setFlags(EnumSet.of(Goal.Flag.MOVE, Goal.Flag.LOOK));
	}

	@Override
	public boolean canUse() {
		Player owner = ally.owner();
		return owner != null && !owner.isSpectator() && ally.getTarget() == null && ally.distanceToSqr(owner) > 6 * 6;
	}

	@Override
	public boolean canContinueToUse() {
		Player owner = ally.owner();
		return owner != null && ally.getTarget() == null && ally.distanceToSqr(owner) > 3 * 3;
	}

	@Override
	public void start() {
		repath = 0;
	}

	@Override
	public void stop() {
		ally.getNavigation().stop();
	}

	@Override
	public void tick() {
		Player owner = ally.owner();
		if (owner == null) return;
		ally.getLookControl().setLookAt(owner, 10f, ally.getMaxHeadXRot());
		if (--repath > 0) return;
		repath = 10;
		if (ally.distanceToSqr(owner) > 28 * 28 && owner.onGround()) {
			// Too far to walk: it reforms beside them.
			ally.snapTo(owner.getX() - owner.getLookAngle().x * 2, owner.getY(), owner.getZ() - owner.getLookAngle().z * 2, ally.getYRot(), ally.getXRot());
			ally.getNavigation().stop();
		} else {
			ally.getNavigation().moveTo(owner, speed);
		}
	}
}
