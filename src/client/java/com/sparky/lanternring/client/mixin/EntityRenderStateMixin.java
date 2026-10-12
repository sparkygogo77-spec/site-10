package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.SoulSight;
import net.minecraft.client.renderer.entity.state.EntityRenderState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;

/** Remembers whether this frame's entity shows through walls for the Soul Stone (see SoulSight). */
@Mixin(EntityRenderState.class)
public abstract class EntityRenderStateMixin implements SoulSight.Holder {
	@Unique
	private boolean lanternring$soulSight;

	@Override
	public boolean lanternring$soulSight() {
		return lanternring$soulSight;
	}

	@Override
	public void lanternring$setSoulSight(boolean seen) {
		lanternring$soulSight = seen;
	}
}
