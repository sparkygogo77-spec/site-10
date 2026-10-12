package com.sparky.lanternring.client.mixin;

import java.util.List;
import net.minecraft.client.renderer.fog.FogRenderer;
import net.minecraft.client.renderer.fog.environment.FogEnvironment;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;

/** The game's list of fog environments, so the Fear fog can go first (see FearFog). */
@Mixin(FogRenderer.class)
public interface FogRendererAccessor {
	@Accessor("FOG_ENVIRONMENTS")
	static List<FogEnvironment> lanternring$environments() {
		throw new AssertionError();
	}
}
