package com.sparky.lanternring.ally;

import java.util.EnumSet;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.target.TargetGoal;
import net.minecraft.world.entity.player.Player;

/** Goes for whatever hostile mob just hurt its owner, or the one its owner is fighting. */
final class DefendOwnerGoal extends TargetGoal {
	private final ConstructAlly ally;
	private LivingEntity picked;

	DefendOwnerGoal(ConstructAlly ally) {
		super(ally, false, false);
		this.ally = ally;
		setFlags(EnumSet.of(Goal.Flag.TARGET));
	}

	@Override
	public boolean canUse() {
		Player owner = ally.owner();
		if (owner == null || owner.distanceToSqr(ally) > 48 * 48) return false;
		LivingEntity hurtBy = owner.getLastHurtByMob();
		if (hurtBy != null && ConstructAlly.isBadMob(hurtBy) && owner.tickCount - owner.getLastHurtByMobTimestamp() < 200) {
			picked = hurtBy;
			return true;
		}
		LivingEntity fighting = owner.getLastHurtMob();
		if (fighting != null && ConstructAlly.isBadMob(fighting) && owner.tickCount - owner.getLastHurtMobTimestamp() < 200) {
			picked = fighting;
			return true;
		}
		return false;
	}

	@Override
	public void start() {
		mob.setTarget(picked);
		super.start();
	}
}
