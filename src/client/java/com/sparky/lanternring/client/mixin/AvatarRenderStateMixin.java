package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.FlightPoses;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Unique;

@Mixin(AvatarRenderState.class)
public abstract class AvatarRenderStateMixin implements FlightPoses.Holder {
	@Unique
	private final FlightPoses.Pose lanternring$flightPose = new FlightPoses.Pose();

	@Override
	public FlightPoses.Pose lanternring$flightPose() {
		return lanternring$flightPose;
	}
}
