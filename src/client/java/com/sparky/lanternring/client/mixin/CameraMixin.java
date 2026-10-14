package com.sparky.lanternring.client.mixin;

import com.sparky.lanternring.client.RingShake;
import com.sparky.lanternring.client.SuperJumpInput;
import net.minecraft.client.Camera;
import org.joml.Quaternionf;
import org.joml.Vector3f;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** The ring's shot kick (RingShake) and the super jump's arc tilt: turn the camera after it lines up with the player. */
@Mixin(Camera.class)
public abstract class CameraMixin {
	@Shadow private float xRot;
	@Shadow private float yRot;
	@Shadow @Final private Quaternionf rotation;
	@Shadow @Final private Vector3f forwards;
	@Shadow @Final private Vector3f up;
	@Shadow @Final private Vector3f left;

	@Shadow
	protected abstract void setRotation(float yRot, float xRot);

	@Inject(method = "alignWithEntity", at = @At("TAIL"))
	private void lanternring$shotKick(float partialTicks, CallbackInfo ci) {
		RingShake.update();
		float tilt = SuperJumpInput.tilt(partialTicks);
		if (RingShake.pitch == 0f && RingShake.yaw == 0f && RingShake.roll == 0f && tilt == 0f) return;
		setRotation(yRot + RingShake.yaw, xRot + RingShake.pitch + tilt);
		rotation.rotateZ(RingShake.roll * ((float) Math.PI / 180f));
		rotation.transform(0f, 0f, -1f, forwards);
		rotation.transform(0f, 1f, 0f, up);
		rotation.transform(-1f, 0f, 0f, left);
	}
}
