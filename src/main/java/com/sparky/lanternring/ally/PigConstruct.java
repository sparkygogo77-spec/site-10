package com.sparky.lanternring.ally;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;

/**
 * The Pig construct (Blender pass 828, J kept P2 H1 hex and P3 W1 weave): a hard-light pig in the vanilla
 * pig's proportions that trots with its owner and rams hostile mobs, bowling them up and back. The cheapest
 * Army construct: a light skirmisher next to the Warden. Its look (which construct texture it wears) is the
 * Ring Lab's "Construct pig" row, drawn by the client (PigConstructRenderer).
 */
public class PigConstruct extends ConstructAlly {
	public PigConstruct(EntityType<? extends PigConstruct> type, Level level) {
		super(type, level);
		xpReward = 0;
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Mob.createMobAttributes()
				.add(Attributes.MAX_HEALTH, 200)
				.add(Attributes.MOVEMENT_SPEED, 0.32)
				.add(Attributes.ATTACK_DAMAGE, 6)
				.add(Attributes.ATTACK_KNOCKBACK, 1.4)
				.add(Attributes.FOLLOW_RANGE, 24)
				.add(Attributes.STEP_HEIGHT, 1.1);
	}

	@Override
	public Formation.Stance stance() {
		return Formation.Stance.FLANK;
	}

	@Override
	protected void registerGoals() {
		super.registerGoals();
		goalSelector.addGoal(0, new FloatGoal(this));
		goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.4, true));
		goalSelector.addGoal(3, new FlankGoal(this, 1.2));
		goalSelector.addGoal(8, new LookAtPlayerGoal(this, Player.class, 8f));
		goalSelector.addGoal(9, new RandomLookAroundGoal(this));
	}

	@Override
	public boolean doHurtTarget(ServerLevel level, Entity target) {
		boolean hit = super.doHurtTarget(level, target);
		if (hit) {
			// A ram: up and back off its snout.
			target.push(0, 0.3, 0);
			WardenConstruct.knock(target);
			level.playSound(null, getX(), getY(), getZ(), SoundEvents.AMETHYST_BLOCK_HIT, SoundSource.NEUTRAL, 1f, 0.8f);
		}
		return hit;
	}

	@Override
	protected void playStepSound(net.minecraft.core.BlockPos pos, net.minecraft.world.level.block.state.BlockState state) {
		level().playSound(null, getX(), getY(), getZ(), SoundEvents.AMETHYST_BLOCK_STEP, SoundSource.NEUTRAL, 0.35f, 1.6f);
	}
}
