package com.sparky.lanternring.corps;

import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;

/**
 * The Hope sanctuary's turbine (J's A6 Battery + cone): the drum of Hope quartz, blue construct brick
 * and lamps with the Hope mark through its hub, turning once every 20 seconds over the lotus. It
 * holds no blocks; it stands where the turbine's axis meets its bottom, and the client draws the
 * turbine and mark parts of the sanctuary's plan round it (HopeTurbineRenderer).
 */
public class HopeTurbine extends Entity {
	/** One turn takes this many ticks (J: every 20 s). */
	public static final float TURN_TICKS = 400f;

	public HopeTurbine(EntityType<? extends HopeTurbine> type, Level level) {
		super(type, level);
		noPhysics = true;
		setNoGravity(true);
	}

	/** How far round the turbine is, in degrees, from the world's clock so every viewer agrees. */
	public static float angle(long gameTime, float partialTick) {
		return (float) (((gameTime % (long) TURN_TICKS) + partialTick) / TURN_TICKS * 360.0);
	}

	@Override
	public void tick() {
		// Nothing moves the entity itself; the spin is drawn from the clock.
	}

	@Override
	protected void defineSynchedData(SynchedEntityData.Builder builder) {
	}

	@Override
	public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
		return false;
	}

	/** It's big: seen from as far as the sanctuary itself, not just a small entity's 64 blocks. */
	@Override
	public boolean shouldRenderAtSqrDistance(double distance) {
		double far = 256 * getViewScale();
		return distance < far * far;
	}

	@Override
	public boolean isPickable() {
		return false;
	}

	@Override
	protected void readAdditionalSaveData(ValueInput input) {
	}

	@Override
	protected void addAdditionalSaveData(ValueOutput output) {
	}
}
