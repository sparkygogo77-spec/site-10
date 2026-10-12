package com.sparky.lanternring.corps;

import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.AvoidEntityGoal;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.animal.feline.Cat;
import net.minecraft.world.entity.animal.feline.CatVariants;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;

/**
 * A rage cat: the Red Lantern sanctuary's blue cat with a red ring (the Dex-Starr look). It can't
 * be tamed, doesn't run from people, and goes for anyone who isn't holding a red ring.
 */
public class RageCat extends Cat {
	public RageCat(EntityType<? extends Cat> type, Level level) {
		super(type, level);
		setPersistenceRequired();
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Cat.createAttributes()
				.add(Attributes.MAX_HEALTH, 24)
				.add(Attributes.ATTACK_DAMAGE, 6)
				.add(Attributes.MOVEMENT_SPEED, 0.35)
				.add(Attributes.FOLLOW_RANGE, 24);
	}

	@Override
	protected void registerGoals() {
		super.registerGoals();
		goalSelector.removeAllGoals(g -> g instanceof AvoidEntityGoal<?> || g instanceof TemptGoal);
		goalSelector.addGoal(2, new MeleeAttackGoal(this, 1.4, true));
		targetSelector.addGoal(1, new HurtByTargetGoal(this));
		targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, 10, true, false,
				(target, level) -> !RedSanctuary.friend(target)));
	}

	/** The blue-grey British Shorthair coat. */
	void blueCoat(ServerLevel level) {
		applyImplicitComponent(DataComponents.CAT_VARIANT,
				level.registryAccess().lookupOrThrow(Registries.CAT_VARIANT).getOrThrow(CatVariants.BRITISH_SHORTHAIR));
	}

	@Override
	public InteractionResult mobInteract(Player player, InteractionHand hand) {
		return InteractionResult.PASS;
	}

	@Override
	public boolean removeWhenFarAway(double distance) {
		return false;
	}
}
