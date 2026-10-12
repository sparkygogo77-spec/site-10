package com.sparky.lanternring.mixin;

import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityReference;
import net.minecraft.world.entity.projectile.ShulkerBullet;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;

/** Lets the Shield turn a shulker bullet back on the shulker that fired it (see ShieldReflect). */
@Mixin(ShulkerBullet.class)
public interface ShulkerBulletAccessor {
	@Accessor("finalTarget")
	void lanternring$setFinalTarget(EntityReference<Entity> target);

	@Accessor("flightSteps")
	void lanternring$setFlightSteps(int steps);

	@Accessor("targetDeltaX")
	void lanternring$setTargetDeltaX(double dx);

	@Accessor("targetDeltaY")
	void lanternring$setTargetDeltaY(double dy);

	@Accessor("targetDeltaZ")
	void lanternring$setTargetDeltaZ(double dz);
}
