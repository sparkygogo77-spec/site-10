package com.sparky.lanternring.client;

import com.sparky.lanternring.ModEffects;
import com.sparky.lanternring.client.mixin.FogRendererAccessor;
import net.minecraft.client.Camera;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.renderer.fog.FogData;
import net.minecraft.client.renderer.fog.environment.MobEffectFogEnvironment;
import net.minecraft.core.Holder;
import net.minecraft.util.Mth;
import net.minecraft.world.effect.MobEffect;
import org.joml.Vector3f;
import org.joml.Vector3fc;

/**
 * Fear's darkness for whoever has it: a dark amber fog that closes in from the usual view
 * distance to a few blocks over the first two seconds (see FearVignette.strength), and lifts
 * again as the Fear wears off. Shader packs draw their own fog; FearVignette still closes in.
 */
public class FearFog extends MobEffectFogEnvironment {
	/** How far you can still see with the Fear at its worst. */
	private static final float NEAR = 5f;
	private static final Vector3fc COLOR = new Vector3f(0.07f, 0.05f, 0.01f);

	public static void register() {
		FogRendererAccessor.lanternring$environments().add(0, new FearFog());
	}

	@Override
	public Holder<MobEffect> getMobEffect() {
		return ModEffects.FEAR;
	}

	@Override
	public void setupFog(FogData fog, Camera camera, ClientLevel level, float renderDistance, DeltaTracker delta) {
		float s = FearVignette.strength(delta.getGameTimeDeltaPartialTick(false));
		float end = Mth.lerp(s, Math.max(renderDistance, 24f), NEAR);
		fog.environmentalStart = end * 0.15f;
		fog.environmentalEnd = end;
		fog.skyEnd = end;
		fog.cloudEnd = end;
	}

	@Override
	public Vector3fc getBaseColor(ClientLevel level, Camera camera, int renderDistance, float partialTick) {
		return COLOR;
	}

	@Override
	public boolean providesColor() {
		return true;
	}

	@Override
	public boolean modifiesDarkness() {
		return false;
	}
}
