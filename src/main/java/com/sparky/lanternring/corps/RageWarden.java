package com.sparky.lanternring.corps;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Unit;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.monster.warden.Warden;
import net.minecraft.world.level.Level;

/**
 * The Red Lantern sanctuary's guardian: a warden that took a red ring. It never turns on the other
 * residents or on red ring bearers, and it doesn't dig back underground: the sanctuary is its home.
 */
public class RageWarden extends Warden {
	public RageWarden(EntityType<? extends Warden> type, Level level) {
		super(type, level);
		setPersistenceRequired();
	}

	public static AttributeSupplier.Builder createAttributes() {
		return Warden.createAttributes().add(Attributes.FOLLOW_RANGE, 32);
	}

	@Override
	public boolean canTargetEntity(Entity entity) {
		return !RedSanctuary.friend(entity) && super.canTargetEntity(entity);
	}

	@Override
	protected void customServerAiStep(ServerLevel level) {
		// A warden left calm for a minute digs down and leaves; this one stays.
		if (!getBrain().hasMemoryValue(MemoryModuleType.DIG_COOLDOWN)) getBrain().setMemoryWithExpiry(MemoryModuleType.DIG_COOLDOWN, Unit.INSTANCE, 1200L);
		super.customServerAiStep(level);
	}

	@Override
	public boolean removeWhenFarAway(double distance) {
		return false;
	}
}
